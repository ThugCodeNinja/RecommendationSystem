# Software Issue Troubleshooting Assistant

## Overview
The **Software Issue Troubleshooting Assistant** is a Retrieval-Augmented Generation (RAG) application designed to assist in diagnosing and resolving software issues. This application leverages Snowflake Cortex for retrieval and LLM-powered generation (using models like `mistral-large`), with TruLens integration for performance evaluation. The frontend is built using Streamlit for a user-friendly interface.

---

## Features
- **File Upload:** Supports PDF and TXT document uploads for contextual troubleshooting.
- **Interactive Chat:** Users can ask questions, and the assistant provides concise, context-aware answers.
- **Context Retrieval:** Fetches relevant information using Cortex Search.
- **Feedback Mechanisms:** Evaluates response relevance and context usage with TruLens feedback.
- **Feedback Storage:** Persists feedback data into Snowflake for further analysis.
- **Streamlit Frontend:** Intuitive and dynamic interface.

---

## Technologies Used
- **Backend:**
  - Snowflake Cortex
  - Snowpark Python API
  - TruLens for feedback evaluation
  - PyPDF2 for PDF processing
- **Frontend:**
  - Streamlit Community Cloud
- **Libraries:**
  - `numpy`
  - `asyncio`
  - `datetime`

---

## Installation

### Prerequisites
- Python 3.8+
- Snowflake account with Cortex enabled
- Required Python libraries (see `requirements.txt`)

### Steps
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-repo/software-assistant
   cd software-assistant
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Configuration:**
   Create a `config.py` file with your Snowflake connection parameters:
   ```python
   account = "<your_account>"
   user = "<your_user>"
   password = "<your_password>"
   database = "<your_database>"
   schema = "<your_schema>"
   role = "<your_role>"
   warehouse = "<your_warehouse>"
   ```

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

---

## Usage
1. **Upload Documents:**
   - Drag and drop a PDF or TXT file for troubleshooting context.
2. **Ask Questions:**
   - Type your question into the chat box.
   - View responses generated using context from uploaded files or general knowledge.
3. **Feedback Results:**
   - View feedback scores for each response in the sidebar.
   - Feedback is stored in Snowflake for analytics.

---

## File Structure
```
software-assistant/
├── app.py                 # Main Streamlit app
├── config.py              # Snowflake configuration
├── requirements.txt       # Required Python libraries
├── README.md              # Project documentation
└── ... (other files)
```

---

## Feedback Evaluation
### Integrated Metrics:
- **Context Relevance:** Measures how well the response leverages retrieved context.
- **Answer Relevance:** Evaluates the overall relevance of the response.

Feedback results are displayed in real-time and stored in a Snowflake table (`feedback_history`) for detailed analysis.

---

## Future Enhancements
- Support for additional file formats (e.g., Word, Markdown).
- Improved summarization for lengthy documents.
- Enhanced analytics for feedback insights.
- Integration with additional LLMs.

---

## License
This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments
Special thanks to:
- Snowflake for Cortex and TruLens support
- OpenAI for providing foundational libraries

---

## Contact
For queries or issues, please contact [Your Name](mailto:your.email@example.com).
