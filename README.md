# AI Job Consultant Chatbot

This is a job consultant chatbot that uses AI to analyze a candidate's CV and provide personalized career advice based on the job market data.

## Features

- CV Analysis: Analyze a candidate's CV and provide personalized career advice based on the job market data.
- Career Advice: Provide personalized career advice based on the job market data.
- Job Market Data: Provide job market data based on the job market data.

# AI Job Consultant Chatbot - Application Flow Documentation

## 1. Overview
The **AI Job Consultant Chatbot** is a Streamlit-based application designed to help users bridge the gap between their current skills and market demands. It combines **Real-Time Web Scraping**, **RAG (Retrieval-Augmented Generation)**, and **LLM Analysis** to provide personalized career roadmaps.

## 2. High-Level Architecture
The application consists of four main pillars:
1.  **Frontend**: Built with Streamlit for user interaction.
2.  **Data Acquisition**: A custom LinkedIn scraper to fetch real-time job market data.
3.  **Knowledge Base (RAG)**: A Vector Database (Qdrant) to store and semantically search job descriptions.
4.  **Intelligence Layer**: OpenAI GPT-4 for analyzing resumes and generating advice.

---

## 3. Step-by-Step Data Flow

### Step 1: User Input & CV Analysis
*   **Action**: User uploads a PDF Resume and enters a "Target Position" (e.g., "Data Scientist").
*   **Module**: `pdf_cv_extraction.py`
*   **Process**: The app reads the PDF and extracts raw text to form a "Candidate Profile Summary".

### Step 2: Real-Time Market Scraping
*   **Action**: The app searches LinkedIn for the user's "Target Position".
*   **Module**: `linkedin_scrapper.py`
*   **Process**:
    *   Uses a guest API strategy to fetch job postings (Title, Company, Description, Industry).
    *   **New Feature**: Extracts "Industry" data specifically from the job criteria section.
    *   Saves raw data to `linkedin_jobs.json`.
    *   Logs activities to the `logs/` directory.

### Step 3: RAG Ingestion (Knowledge Base Update)
*   **Action**: The raw job data is processed into a vector format.
*   **Module**: `vector_db.py` -> `ingest_jobs_from_file()`
*   **Process**:
    *   Reads `linkedin_jobs.json`.
    *   Converts each job into a **Document** object (Metadata: ID, Title, Company, Industry).
    *   Uses **OpenAI Embeddings** (`text-embedding-3-small`) to turn text into vectors.
    *   Stores these vectors in a local **Qdrant** collection named `linkedin_jobs`.

### Step 4: Semantic Retrieval (RAG)
*   **Action**: The app asks the database, *"What are the most relevant jobs for this Target Position?"*
*   **Module**: `vector_db.py` -> `retrieve_qdrant()`
*   **Process**:
    *   Performs a cosine similarity search in Qdrant.
    *   Retrieves the top 5 most relevant job descriptions that match the query context.
    *   Formats this into a text block called `Market Data Summary`.

### Step 5: Gap Analysis (LLM)
*   **Module**: `app.py`
*   **Process**:
    *   Constructs a prompt containing:
        1.  **Candidate Profile** (from Step 1)
        2.  **Market Data Summary** (from Step 4)
    *   Sends this prompt to **GPT-4o**.
    *   **Output**: A detailed report containing:
        *   Skill Gap Identification
        *   Learning Roadmap
        *   Project Recommendations

### Step 6: Interactive Consultation
*   **Action**: User chats with the AI about the results.
*   **Process**: The chat history and previous analysis context are fed back into the LLM, effectively acting as a specialized Career Consultant agent.

---

## 4. Key File Descriptions

| File | Purpose |
| :--- | :--- |
| **`app.py`** | **Main Application Entry Point.** Handles UI, session state, and orchestrates the flow between all other modules. |
| **`linkedin_scrapper.py`** | **Scraper Engine.** Fetches live job data from LinkedIn, handles HTML parsing, and logs execution. |
| **`vector_db.py`** | **RAG Engine.** Manages the Qdrant vector database connection, document embedding, ingestion, and semantic retrieval. |
| **`pdf_cv_extraction.py`**| **PDF Utility.** Simple wrapper to extract text strings from uploaded PDF files. |
| **`.env`** | **Configuration.** Stores API Keys (OpenAI, Qdrant) securely. |

## 5. Technology Stack
*   **Language**: Python 3.12+
*   **Frontend**: Streamlit
*   **LLM**: OpenAI GPT-4o
*   **Embeddings**: OpenAI `text-embedding-3-small`
*   **Vector DB**: Qdrant (Local memory mode)
*   **Scraping**: Requests + BeautifulSoup4


https://ai-job-consultation-miqdam.streamlit.app
