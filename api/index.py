# File: api/index.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORT THIS
from pydantic import BaseModel
from openai import OpenAI
import chromadb
import os
from typing import Optional

# --- Initialization ---
print("Initializing API with CORS enabled...")
app = FastAPI()

# --- THIS IS THE CRITICAL FIX FOR THE SUBMISSION PORTAL ---
# We are adding CORS middleware to allow the submission website
# to make requests to our API.
origins = [
    "*"  # Allows all origins. For a student project, this is perfectly fine.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# -------------------------------------------------------------

api_key = os.getenv("AIPROXY_API_KEY")
if not api_key:
    print("FATAL ERROR: The AIPROXY_API_KEY environment variable is not set!")

client = OpenAI(
    base_url="http://aiproxy.sanand.workers.dev/openai/v1/",
    api_key=api_key,
)

db_path = os.path.join(os.path.dirname(__file__), '..', 'db')
client_db = chromadb.PersistentClient(path=db_path)
collection = client_db.get_collection("tds_knowledge_base")

print("API Initialized successfully.")

# --- Pydantic Models and the rest of your code (no changes needed here) ---
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    links: list

def get_embedding(text: str, model="text-embedding-3-small"):
   return client.embeddings.create(input=[text.replace("\n", " ")], model=model).data[0].embedding

@app.post("/api/", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    # Your improved query_api function with prioritized context
    # This code does not need to change.
    try:
        question_embedding = get_embedding(request.question)
        results = collection.query(query_embeddings=[question_embedding], n_results=3)
        documents = results.get('documents', [[]])[0]
        if not documents:
            return QueryResponse(answer="I could not find any relevant information to answer your question.", links=[])

        primary_context = documents[0]
        additional_context = "\n\n".join(documents[1:])
        links = []
        for meta in results.get('metadatas', [[]])[0]:
            if meta and meta.get('url'):
                links.append({"url": meta.get('url', ''), "text": meta.get('title', 'Source Link')})

        prompt = f"""You are a precise and literal teaching assistant for the IIT Madras Online Degree.
Your task is to answer the student's question based on the context provided below.
You MUST prioritize the information in the "PRIMARY CONTEXT". If it contains a direct instruction, your answer must be based on that instruction. Use the "ADDITIONAL CONTEXT" only for supplementary information if needed.

### PRIMARY CONTEXT (Most Important):
{primary_context}

### ADDITIONAL CONTEXT:
{additional_context}

### Question:
{request.question}

### Answer:
"""
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful teaching assistant. You must follow the provided context hierarchy and prioritize the PRIMARY CONTEXT."}, {"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.0
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"ERROR during API request processing: {e}")
        answer = f"Sorry, an error occurred. Please try again. Details: {e}"
        links = []
    return QueryResponse(answer=answer, links=links)

@app.get("/")
def root():
    return {"status": "ok", "message": "TDS Virtual TA is running. Use the /api/ endpoint to ask questions."}
