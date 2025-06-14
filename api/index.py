# File: api/index.py

# --- Step 1: Import only the necessary, lightweight libraries ---
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI  # We will use this for BOTH chat and embeddings
import chromadb
import os
from typing import Optional

# --- Step 2: Initialize the FastAPI app and other services ---
print("Initializing API...")

# This variable MUST be named 'app' for Render's uvicorn command to find it.
app = FastAPI()

# This is the SECURITY FIX: Read the API key from a secure environment variable.
# You must set this variable in your Render dashboard.
api_key = os.getenv("AIPROXY_API_KEY")
if not api_key:
    # This log will appear in Render if the environment variable is missing.
    print("FATAL ERROR: The AIPROXY_API_KEY environment variable is not set!")

# Set up the single OpenAI client pointing to your AI Proxy.
# This client will handle all AI calls, making the code cleaner.
client = OpenAI(
    base_url="http://aiproxy.sanand.workers.dev/openai/v1/",
    api_key=api_key,
)

# Connect to your local ChromaDB. The path points one level up from 'api' to the root.
# This is fine now because our app is lightweight and won't run out of memory.
db_path = os.path.join(os.path.dirname(__file__), '..', 'db')
client_db = chromadb.PersistentClient(path=db_path)
collection = client_db.get_collection("tds_knowledge_base")

print("API Initialized successfully.")

# --- Step 3: Define the data structures for API requests and responses ---
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None # Accepts an image but does not use it, per requirements.

class QueryResponse(BaseModel):
    answer: str
    links: list

# --- Step 4: Create a helper function to get embeddings via API ---
# This is the MEMORY FIX: We replaced the heavy local model with this light API call.
def get_embedding(text: str, model="text-embedding-3-small"):
   """Generates an embedding for text using the AI Proxy API."""
   # This API call is very fast and uses almost no memory on our server.
   return client.embeddings.create(input=[text.replace("\n", " ")], model=model).data[0].embedding

# --- Step 5: Define the main API endpoint ---
# In api/index.py, replace the entire query_api function with this:

@app.post("/api/", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    try:
        # a. Generate an embedding for the user's question.
        question_embedding = get_embedding(request.question)

        # b. Retrieve the top 3 most relevant documents from ChromaDB.
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=3
        )
        
        # c. THIS IS THE NEW, ADVANCED LOGIC: Separate the best context from the rest.
        documents = results.get('documents', [[]])[0]
        if not documents:
            return QueryResponse(answer="I could not find any relevant information to answer your question.", links=[])

        # The most relevant document is the first one.
        primary_context = documents[0]
        # The other documents are used as additional, secondary context.
        additional_context = "\n\n".join(documents[1:])

        # Prepare the source links as before.
        links = []
        for meta in results.get('metadatas', [[]])[0]:
            if meta and meta.get('url'):
                links.append({"url": meta.get('url', ''), "text": meta.get('title', 'Source Link')})

        # d. Build the final, structured prompt that emphasizes the best information.
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

        # e. Generate the final answer using the chat model.
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful teaching assistant. You must follow the provided context hierarchy and prioritize the PRIMARY CONTEXT."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.0 # Set temperature to 0.0 for maximum factuality and less creativity
        )
        answer = completion.choices[0].message.content.strip()

    except Exception as e:
        print(f"ERROR during API request processing: {e}")
        answer = f"Sorry, an error occurred. Please try again. Details: {e}"
        links = []

    return QueryResponse(answer=answer, links=links)


# A simple root endpoint to quickly check if the API is alive.
@app.get("/")
def root():
    return {"status": "ok", "message": "TDS Virtual TA API is running."}
