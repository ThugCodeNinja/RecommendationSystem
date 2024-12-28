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
from trulens.apps.custom import instrument
from trulens.core import TruSession
from trulens.connectors.snowflake import SnowflakeConnector
from trulens.providers.cortex.provider import Cortex
from trulens.core import Feedback
from trulens.core import Select
import numpy as np
from trulens.apps.custom import TruCustomApp
import asyncio
from datetime import datetime
#from trulens.core.feedback import Groundedness

class RAG:
    def __init__(self):
        self.connection_parameters = {
            "account": account,
            "user": user,
            "password": password,
            "database": database,
            "schema": schema,
            "role": role,
            "warehouse": warehouse
        }
        self.session = Session.builder.configs(self.connection_parameters).create()
        self.tru_snowflake_connector = SnowflakeConnector(snowpark_session=self.session)
        self.tru_session = TruSession(connector=self.tru_snowflake_connector)
        self.provider = Cortex(self.session.connection, "mistral-large")
        self.slide_window = 7  # Number of chat messages to remember
        self.feedbacks = self.configure_feedbacks()

    def configure_feedbacks(self):
        """
        Configure TruLens feedback mechanisms.
        """
        query = Select.Record.app.retriever._get_relevant_documents.args.query  
        context = Select.Record.app.retriever.get_relevant_documents.rets[:].page_content

        f_context_relevance = (
            Feedback(self.provider.context_relevance, name="Context Relevance")
            .on(Select.RecordCalls.get_similar_context.args.question)
            .on(Select.RecordCalls.get_similar_context.rets[:])
            .aggregate(np.mean)
        )
        #return [f_groundedness, f_answer_relevance, f_context_relevance]
        return [f_context_relevance]

    def main(self):
        st.title(":speech_balloon: Software Issue Assistant")
        st.sidebar.title("Configuration")
        self.configure_sidebar()
        self.initialize_messages()

        uploaded_file = st.file_uploader("Upload a document (PDF/TXT) for troubleshooting", type=["pdf", "txt"])
        if uploaded_file:
            self.process_uploaded_document(uploaded_file)

        st.write("Available Documents:")
        self.list_available_documents()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if question := st.chat_input("Ask a software troubleshooting question:"):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                placeholder = st.empty()
                with st.spinner("Generating response..."):
                    response = self.generate_response(question)
                    feedback_results = asyncio.run(self.evaluate_feedback_async(question, response))
                    placeholder.markdown(response)
                # Display feedback results in the sidebar
                    self.display_feedback_results_in_sidebar(feedback_results)
                st.session_state.messages.append({"role": "assistant", "content": response})

    def process_uploaded_document(self, file):
        def read_pdf(file):
            try:
                buffer = io.BytesIO(file.read())
                reader = PyPDF2.PdfReader(buffer)
                text = "".join(page.extract_text().replace("\n", " ") for page in reader.pages)
                return text.strip()
            except Exception as e:
                st.error(f"Error reading PDF: {str(e)}")
                return None

        def read_txt(file):
            try:
                return file.read().decode("utf-8").strip()
            except Exception as e:
                st.error(f"Error reading TXT: {str(e)}")
                return None

        file_extension = file.name.split(".")[-1].lower()
        if file_extension == "pdf":
            text = read_pdf(file)
        elif file_extension == "txt":
            text = read_txt(file)
        else:
            st.error("Unsupported file type.")
            return

        if text:
            st.text_area("File Content", value=text, height=300, key="file_content", disabled=True)
            st.info("Copy content and paste it into the chatbox if needed.")
        else:
            st.error("Failed to process file.")

    def list_available_documents(self):
        docs = self.session.sql("LS @docs").collect()
        doc_list = [doc["name"] for doc in docs]
        st.dataframe(doc_list)

    @instrument
    def generate_response(self, question):
        prompt = self.create_prompt(question)
        query = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response"
        response = self.session.sql(query, params=[st.session_state.model_name, prompt]).collect()
        return self.clean_response(str(response[0]))
    
    @instrument
    def summarize_chat_history(self,chat_history, question):
        prompt = f"""
        Summarize the following chat history and integrate the question for context:

        <chat_history>{chat_history}</chat_history>
        <question>{question}</question>
        """
        query = "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS response"
        response = self.session.sql(query, params=[st.session_state.model_name, prompt]).collect()
        return self.clean_response(str(response[0]))

    @instrument
    def create_prompt(self, question):
        if st.session_state.use_chat_history:
            chat_history = self.get_chat_history()
            question = self.summarize_chat_history(chat_history, question) if chat_history else question
        context = self.get_similar_context(question)
        prompt = f"""
        Use CONTEXT and CHAT HISTORY to answer the QUESTION:

        <chat_history>{question}</chat_history>
        <context>{context}</context>
        <question>{question}</question>

        Answer concisely.
        """
        return prompt

    def get_chat_history(self):
        start_index = max(0, len(st.session_state.messages) - self.slide_window)
        history = [msg["content"] for msg in st.session_state.messages[start_index:]]
        return " ".join(history)

    @instrument
    def get_similar_context(self, question):
        """
        Fetch similar context using Cortex Search service.
        """
        cortex_search_service = (
            Root(self.session)
            .databases[database]
            .schemas[schema]
            .cortex_search_services["question_search"]
        )
        context_documents = cortex_search_service.search(
            question,
            columns=["answer"],
            filter={},
            limit=1
        )
        
        # Collect and return answers
        results = [doc["answer"] for doc in context_documents.results]
        return " ".join(results)


    def clean_response(self, raw_response):
        if raw_response.startswith("Row(RESPONSE="):
            cleaned_response = raw_response[len("Row(RESPONSE="):-1].strip()
        else:
            cleaned_response = raw_response.strip()
        return cleaned_response.replace("\\n\\n", " ").replace("\n\n", " ").replace("\n", " ")

    async def evaluate_feedback_async(self, question, response):
        """
        Asynchronously evaluate feedback for the given question and response.
        """
        feedback_results = {
            "Context Relevance": await asyncio.to_thread(self.feedbacks[0], question, response)
        }
        return feedback_results

    def configure_sidebar(self):
        st.sidebar.selectbox("Select your model:", ["mistral-large", "llama2-70b-chat"], key="model_name")
        st.sidebar.checkbox("Remember chat history?", key="use_chat_history", value=True)
        st.sidebar.button("Start Over", key="clear_conversation")
        # st.sidebar.expander("Trulens Dashboard").write(self.tru_session.get_leaderboard())
    
    def display_feedback_results_in_sidebar(self, feedback_results):
        """
        Display feedback results neatly in the sidebar.
        """
        with st.sidebar.expander("Feedback Results", expanded=True):
            # Display feedback results with a timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.write(f"**Feedback evaluated at {timestamp}:**")
            for feedback_name, score in feedback_results.items():
                st.write(f"- {feedback_name}: {score:.2f}")
            st.divider()

            # Optionally store results for later use
            if "feedback_history" not in st.session_state:
                st.session_state.feedback_history = []
            st.session_state.feedback_history.append({"timestamp": timestamp, "results": feedback_results})

    def initialize_messages(self):
        if st.session_state.get("clear_conversation", False) or "messages" not in st.session_state:
            st.session_state.messages = []


rag = RAG()
tru_rag = TruCustomApp(rag, app_name="RAG", app_version="1.0", feedbacks=rag.feedbacks)
rag.main()
