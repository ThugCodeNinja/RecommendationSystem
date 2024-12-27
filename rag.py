import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.files import SnowflakeFile
import pandas as pd
from config import *
from snowflake.core import Root
from langchain.text_splitter import RecursiveCharacterTextSplitter
from snowflake.snowpark.types import StringType, StructField, StructType
import PyPDF2
import io
from trulens_eval import Tru, Feedback, Record

# TruLens setup
tru = Tru()
feedback = Feedback().text()


# Connection parameters
connection_parameters = {
    "account": account,
    "user": user,
    "password": password,
    "database": database,
    "schema": schema,
    "role": role,
    "warehouse": warehouse
}

# Create session
session = Session.builder.configs(connection_parameters).create()

# Constants
slide_window = 7  # Number of chat messages to remember

# Main app function
def main():
    st.title(":speech_balloon: Software Issue Assistant")
    st.sidebar.title("Configuration")

    # Sidebar configuration options
    configure_sidebar()

    # Initialize messages
    initialize_messages()

    # File upload option
    uploaded_file = st.file_uploader("Upload a document (PDF) for troubleshooting assistance", type=["pdf","txt"])
    if uploaded_file:
        process_uploaded_document(uploaded_file)
        st.success("Document uploaded and processed successfully!")

    st.write("Available Documents:")
    list_available_documents()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input and response generation
    if question := st.chat_input("Ask a software troubleshooting question:"):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            with st.spinner("Generating response..."):
                response = generate_response(question)
                placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


def process_uploaded_document(file):
    """
    Processes an uploaded PDF or TXT file, extracts its text, and displays it in the app.
    """
    file_name = file.name
    file_extension = file_name.split(".")[-1].lower()

    if file_extension not in ["pdf", "txt"]:
        st.error("Only PDF and TXT files are supported.")
        return

    # Read the file content
    text = None
    if file_extension == "pdf":
        text = read_pdf(file)
    elif file_extension == "txt":
        text = read_txt(file)

    # Check if text extraction succeeded
    if text:
        st.subheader(f"Contents of {file_name}:")
        st.text_area("File Content", value=text, height=300, key="file_content", disabled=True)
        st.info("You can copy content from above and paste it into the chatbox below.")
    else:
        st.error(f"Failed to read the content of {file_name}. Please try another file.")


# Function to read PDF files
def read_pdf(file):
    """
    Extracts text from a PDF file.
    """
    try:
        buffer = io.BytesIO(file.read())
        reader = PyPDF2.PdfReader(buffer)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text.replace("\n", " ").replace("\0", " ") + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return None


# Function to read TXT files
def read_txt(file):
    """
    Reads text from a TXT file.
    """
    try:
        return file.read().decode("utf-8").strip()
    except Exception as e:
        st.error(f"Error reading TXT file: {str(e)}")
        return None



# Sidebar options
def configure_sidebar():
    st.sidebar.selectbox("Select your model:", [
        "mistral-large",
        "llama2-70b-chat",
        "snowflake-arctic",
        "mixtral-8x7b"
    ], key="model_name")
    st.sidebar.checkbox("Remember chat history?", key="use_chat_history", value=True)
    st.sidebar.button("Start Over", key="clear_conversation")
    st.sidebar.expander("Session State").write(st.session_state)


# Initialize chat history
def initialize_messages():
    if st.session_state.get("clear_conversation", False) or "messages" not in st.session_state:
        st.session_state.messages = []


# List available documents
def list_available_documents():
    docs = session.sql("LS @docs").collect()
    doc_list = [doc["name"] for doc in docs]
    st.dataframe(doc_list)


# Retrieve similar context using Cortex Search service
def get_similar_context(question):
    # Fetch Cortex Search service
    cortex_search_service = (
        Root(session)
        .databases[database]
        .schemas[schema]
        .cortex_search_services["question_search"]
    )
    context_documents = cortex_search_service.search(
        question,
        columns=["answer"],
        filter={},
        limit=3)
    
    for ans in context_documents.results:
        temp =[]
        temp.append(ans['answer'])
        return " ".join(temp)



# Summarize chat history
def summarize_chat_history(chat_history, question):
    prompt = f"""
    Summarize the following chat history and integrate the question for context:

    <chat_history>{chat_history}</chat_history>
    <question>{question}</question>
    """
    query = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response"
    response = session.sql(query, params=[st.session_state.model_name, prompt]).collect()
    return clean_response(str(response[0]))


# Create a final prompt for the model
def create_prompt(question):
    if st.session_state.use_chat_history:
        chat_history = get_chat_history()
        summarized_question = summarize_chat_history(chat_history, question) if chat_history else question
    else:
        summarized_question = question

    # Retrieve context from Cortex Search
    context = get_similar_context(summarized_question)

    prompt = f"""
    You are an expert software troubleshooting assistant. Use the CONTEXT  and CHAT HISTORY to answer the QUESTION :

    <chat_history>{summarized_question}</chat_history>
    <context>{context}</context>
    <question>{question}</question>

    Answer concisely. If the answer is not available in the CONTEXT, respond with 'Information not available.' and give generic advice for the issue.
    """
    return prompt


# Generate response using the model
def generate_response(question):
    prompt = create_prompt(question)
    query = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response"
    response = session.sql(query, params=[st.session_state.model_name, prompt]).collect()
    return clean_response(str(response[0]))


# Get chat history
def get_chat_history():
    start_index = max(0, len(st.session_state.messages) - slide_window)
    history = [msg["content"] for msg in st.session_state.messages[start_index:]]
    return " ".join(history)

def clean_response(raw_response):
    """
    Cleans the raw response from the Cortex Search or model output.
    Removes unnecessary prefixes, suffixes, and newlines.
    """
    # Extract the RESPONSE field content
    if raw_response.startswith("Row(RESPONSE="):
        cleaned_response = raw_response[len("Row(RESPONSE="):-1].strip()  # Remove prefix and trailing parenthesis
    else:
        cleaned_response = raw_response.strip()

    # Replace double newlines with a single space
    cleaned_response = cleaned_response.replace("\\n\\n", " ").replace("\n\n", " ").replace("\n", " ")

    # Return the cleaned response
    return cleaned_response

if __name__ == "__main__":
    main()
