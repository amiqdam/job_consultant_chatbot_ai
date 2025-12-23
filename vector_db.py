# importing all libraries needed
import pandas as pd #for data processing
import getpass, os #for input password interface

from langchain_openai import OpenAIEmbeddings, ChatOpenAI #for embedding and LLM service


from langchain_core.documents import Document #for document format that stored to vector database collection
from langchain_qdrant import QdrantVectorStore #for langchain - qdrant vector database connector
from qdrant_client import QdrantClient #for qdrant client set up
from qdrant_client.http.models import Distance, VectorParams #for distance method and configuration of vector parameters

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")

# Initialize Qdrant Client
qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)

job = pd.read_json("linkedin_jobs.json")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Connect RAG from linkedin_jobs.json to summary
document = []
def create_document(job):
    for i in range(job.shape[0]):
        job_id = job["id"][i]
        job_title = job["title"][i]
        job_company = job["company"][i]
        job_description = job["description"][i]
        job_link = job["link"][i]
        document.append(Document(page_content=f"Title: {job_title}\nDescription: {job_description}\n", metadata={"id": job_id, "title": job_title, "company": job_company, "link": job_link}))

    qdrant = QdrantVectorStore.from_documents(
        document,
        embeddings,
        url=qdrant_url,
        prefer_grpc=True,
        api_key=qdrant_api_key,
        collection_name="linkedin_jobs",
    )

# Retrieve the QDRANT to use for RAG
def retrieve_qdrant(query_text, k=5):
    """
    Retrieve for RAG to recommend jobs that have similar description and skills required with uploaded CV or query.
    Returns a list of Documents.
    """
    if not query_text:
        return []

    qdrant = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name="linkedin_jobs",
        url=qdrant_url,
        api_key=qdrant_api_key
    )
    
    # Similarity Search
    docs = qdrant.similarity_search(query_text, k=k)
    return docs

def ingest_jobs_from_file(file_path="linkedin_jobs.json"):
    """
    Ingest jobs from a JSON file into Qdrant.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return 0

    job_df = pd.read_json(file_path)
    # Reuse create_document logic but ensure it runs
    create_document(job_df)
    print(f"Ingested {len(job_df)} jobs from {file_path}")
    return len(job_df)

def aggregate_skills_from_json(file_path="linkedin_jobs.json", limit=100):
    """
    Load raw JSON to extract common skills/responsibilities.
    Returns a string summary of many jobs.
    """
    if not os.path.exists(file_path):
        return "No job data available."
        
    job_df = pd.read_json(file_path)
    subset = job_df.head(limit) 
    
    combined_text = ""
    for _, row in subset.iterrows():
        combined_text += f"Job Title: {row.get('title', '')}\n"
        combined_text += f"Description: {row.get('description', '')[:500]}...\n\n"
        
    return combined_text