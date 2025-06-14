# TDS Virtual TA Project

> A Retrieval-Augmented Generation (RAG) based AI assistant designed to answer student questions for the IIT Madras BS in Data Science program. This API uses scraped data from the official course content and Discourse forums to provide accurate, context-aware answers.

---

### **Live API Endpoint**

The API is deployed and live on Render.

**Base URL:** `https://virtual-ta-8i6w.onrender.com`
**Query Endpoint (POST):** `https://virtual-ta-8i6w.onrender.com/api/`

---

## ✨ Features

-   **Context-Aware Answers:** Utilizes a vector database (ChromaDB) to retrieve relevant information before generating an answer.
-   **Up-to-Date Knowledge:** Built on a knowledge base scraped from the course website and recent Discourse forum posts.
-   **Source Linking:** Provides direct links to the source documents used to generate the answer.
-   **Robust API:** Built with FastAPI, providing a scalable and documented API endpoint.
-   **Image Handling:** The API is designed to accept image attachments (as base64 strings), though the current logic focuses on text-based queries.

---

## 🚀 Tech Stack

-   **Backend:** Python, FastAPI
-   **AI & ML:** OpenAI API (`gpt-4o-mini`, `text-embedding-3-small`), ChromaDB
-   **Deployment:** Render
-   **Data Processing:** Python scripts for web scraping and data indexing.
-   **Evaluation:** promptfoo

---

## 📂 Project Structure

├── api/ # Contains the FastAPI application (index.py) and its requirements.
├── data/ # Stores the raw scraped JSON data from course and forums.
├── db/ # The local ChromaDB vector database.
├── processing/ # Scripts for indexing data into ChromaDB (indexer.py).
├── Scraper/ # Python scripts for scraping course content and forums.
├── promptfooconfig.yaml # Configuration for automated testing with promptfoo.
└── README.md # This file.


---

## ⚙️ How to Run Locally

1.  **Clone the repository:**
    ```
    git clone https://github.com/31shan/Virtual-TA.git
    cd Virtual-TA
    ```

2.  **Create and activate a virtual environment:**
    ```
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .\.venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```
    pip install -r api/requirements.txt
    ```

4.  **Set up environment variables:**
    You must have an AI Proxy API key. Set it in your terminal:
    ```
    # On Windows PowerShell
    $env:AIPROXY_API_KEY="your_secret_api_key_here"
    ```

5.  **Run the API server:**
    ```
    uvicorn api.index:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

---

## 🧪 How to Evaluate

This project uses `promptfoo` for automated evaluation against a set of predefined test cases.

1.  **Install promptfoo:**
    ```
    npm install -g promptfoo
    ```

2.  **Set the API key for the grader:**
    The `llm-rubric` requires an API key to function. Set it in your terminal:
    ```
    # On Windows PowerShell
    $env:OPENAI_API_KEY="your_secret_api_key_here"
    ```

3.  **Run the evaluation:**
    ```
    npx -y promptfoo eval --config promptfooconfig.yaml
    ```

4.  **View detailed results:**
    ```
    promptfoo view
    ```

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.
