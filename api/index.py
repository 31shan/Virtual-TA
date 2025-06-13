from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
from openai import OpenAI
import os

app = FastAPI()

embedder = SentenceTransformer('all-MiniLM-L6-v2')
db_path = os.path.join(os.path.dirname(__file__), 'db')
client_db = chromadb.PersistentClient(path=db_path)
collection = client_db.get_collection("tds_knowledge_base")

# Set up AI Proxy OpenAI client
client = OpenAI(
    base_url="http://aiproxy.sanand.workers.dev/openai/v1/",
    api_key="key_removed_for_security"
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    links: list

@app.post("/api/", response_model=QueryResponse)
async def query_api(request: QueryRequest):
    question_embedding = embedder.encode(request.question)
    results = collection.query(
        query_embeddings=[question_embedding.tolist()],
        n_results=3
    )
    context = "\n\n".join([doc for doc in results['documents'][0]])
    links = []
    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
        if meta.get('url'):
            links.append({
                "url": meta['url'],
                "text": meta.get('title', 'Link')
            })
    prompt = f"""You are a helpful teaching assistant for the IIT Madras Online Degree in Data Science.
Answer the following student question using only the provided context. Be clear and concise.

Question: {request.question}

Context:
{context}

Answer:"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful teaching assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.2
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Sorry, there was an error generating the answer: {e}"

    return QueryResponse(answer=answer, links=links)
