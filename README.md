# Personalized RAG Assistant – MVP (Proof of Concept)

**A local, personalized Retrieval-Augmented Generation (RAG) assistant for documents.**

This project is a **proof-of-concept implementation** of a personalized RAG chatbot using **Google Gemini AI**, allowing local users to ingest PDFs, ask natural language questions, and get context-aware answers. The solution is designed to be **modular and stack-agnostic** for future expansion.

---

## Features – Phase One

### PDF/Text Ingestion
- Upload PDFs, TXT, or Markdown files via the chat interface.
- Text is extracted, chunked, and embedded for vector search.
- All chunks stored in a persistent **ChromaDB** collection.

### Retrieval-Augmented Generation (RAG)
- User queries retrieve relevant passages from the vector database.
- Passages are used to create context-aware prompts for the Gemini LLM.
- Streaming responses for live token-by-token output.

### Interactive Chat
- View uploaded files with `show files`.
- Adjust model parameters with sliders: **Temperature, Top P, Top K**.
- Reset settings to defaults using `reset settings`.
- Help command shows all available commands.

### Robust Error Handling
- Gracefully handles API quota errors.
- Clear messages for file upload and processing errors.
- Handles database connection issues.

### Local Database Management
- Persistent vector database (ChromaDB) stored locally.
- Can be deleted to start a fresh session.

---

## Architecture – Phase One

      +---------------------+
      |      User Chat      |
      |  (Chainlit / UI)   |
      +----------+----------+
                 |
                 v
      +---------------------+
      |     RAG Chatbot     |
      |      (app.py)       |
      +----------+----------+
                 |
                 v
+---------------------------------+
| ChromaDB Vector Store<-> Gemini |
|   Embedding (Ingest/manage_db)  |
+----------------+----------------+
                 |
                 v
      +---------------------+
      |   LLM Model Layer   |
      | (Gemini AI / Alt..) |
      +----------+----------+


* **app.py:** Core chat logic, message handling, RAG query pipeline.
* **ingest.py:** PDF ingestion, chunking, embedding generation.
* **manage_db.py:** Database inspection and management tool.
* **ChromaDB:** Persistent vector database for document embeddings.
* **Gemini AI:** LLM for answering context-aware queries.

---

## Installation

1.  Clone the repository:
    ```bash
    git clone <repo-url>
    cd <repo-folder>
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up environment variables:
    * Create a `.env` file:
    ```bash
    GEMINI_API_KEY=<your-google-gemini-api-key>
    ```

4.  Run the app:
    ```bash
    chainlit run app.py
    ```

5.  Database management:
    ```bash
    python manage_db.py
    ```

## Usage

* Open the chat interface.
* Upload one or more PDFs.
* Ask questions about the uploaded documents.
* Use `show files` to see uploaded documents.
* Adjust model parameters with sliders for temperature, Top P, and Top K.
* Use `reset settings` to revert to default parameters.
* Type `help` for a list of supported commands.

---

## Phase Two – Future Vision

The next phase aims to make the RAG chatbot stack-agnostic, allowing it to:

* Use different LLMs beyond Gemini (e.g., OpenAI, Anthropic, local LLMs).
* Support multiple embedding and vector stores (e.g., FAISS, Pinecone, Milvus).
* Dynamically switch models or vector databases based on configuration.
* Expand multi-modal input (PDF, DOCX, images, etc.).
* Introduce role-based chat sessions, contextual memory, and fine-tuning options.

**Goal:** Build a fully modular RAG framework that is interoperable across AI/embedding stacks without major code changes.

---

## Project Highlights

* **MVP Focus:** Validate ingestion → embedding → retrieval → answer flow.
* **Extensible:** Modular code in `ingest.py` and `app.py`.
* **User-Friendly:** Simple commands and slider controls for customization.
* **Reliable:** Handles quota, API, and database errors gracefully.

---

## Requirements

* **Python 3.10+**
* **Chainlit**
* **PyPDF2**
* **ChromaDB**
* **LangChain**
* **Google Gemini API key**

---

## Contribution

Fork the repo and submit PRs. Suggested improvements:

* Add support for multi-format documents.
* Improve embedding efficiency.
* Implement RAG for multiple LLMs.
* Build automated tests for ingestion and retrieval.

---
