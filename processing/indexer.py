# File: processing/indexer.py

import json
import chromadb
from openai import OpenAI
import os
import time
from dotenv import load_dotenv

# --- 1. INITIALIZATION ---
print("🚀 Initializing the New, Lightweight Indexer...")

# Load environment variables from a .env file for local execution
load_dotenv()

# Securely get your API key from environment variables
# Make sure you have a .env file in your project root or have this set in your terminal
api_key = os.getenv("AIPROXY_API_KEY")
if not api_key:
    print("❌ FATAL ERROR: AIPROXY_API_KEY not found. Please set it in a .env file or your terminal.")
    exit()

# Set up the OpenAI client pointing to the AI Proxy
client = OpenAI(
    base_url="http://aiproxy.sanand.workers.dev/openai/v1/",
    api_key=api_key,
)

# Connect to ChromaDB. We will overwrite the old collection.
db_path = os.path.join(os.path.dirname(__file__), '..', 'db')
client_db = chromadb.PersistentClient(path=db_path)

collection_name = "tds_knowledge_base"
print(f"   🗃️  Re-creating ChromaDB collection: '{collection_name}'...")
# Delete the old collection to ensure no dimension mismatch
try:
    client_db.delete_collection(name=collection_name)
except Exception as e:
    print(f"   Note: Could not delete old collection (it may not exist). Proceeding. Error: {e}")
collection = client_db.create_collection(name=collection_name)


# --- 2. HELPER FUNCTION TO GET EMBEDDINGS (Same as in the API) ---
def get_embedding(text: str, model="text-embedding-3-small"):
   """Generates an embedding for text using the AI Proxy API."""
   return client.embeddings.create(input=[text.replace("\n", " ")], model=model).data[0].embedding


# --- 3. DATA LOADING & INDEXING ---
print("\n📂 Loading scraped data...")
try:
    with open('../data/course_content.json', 'r', encoding='utf-8') as f:
        course_content = json.load(f)
    print(f"   Loaded {len(course_content)} course documents.")

    with open('../data/discourse_posts.json', 'r', encoding='utf-8') as f:
        discourse_posts = json.load(f)
    print(f"   Loaded {len(discourse_posts)} discourse posts.")
except FileNotFoundError as e:
    print(f"❌ Error: {e}. Make sure JSON files are in the 'data' folder.")
    exit()

all_documents = course_content + discourse_posts
print(f"\n🧠 Processing and indexing {len(all_documents)} total documents...")

for i, doc in enumerate(all_documents):
    content = doc.get('full_content') or doc.get('content', '')
    if not content or len(content) < 50:
        continue # Skip empty or very short documents

    try:
        # This now uses the API call, creating 1536-dimension embeddings
        embedding = get_embedding(content)
        
        doc_id = f"doc_{i}_{hash(doc.get('title', ''))}"
        metadata = {
            'url': doc.get('url', ''),
            'title': doc.get('title', 'Untitled'),
            'source': 'discourse' if 'author' in doc else 'course'
        }

        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )
        print(f"   ✅ Indexed document {i+1}/{len(all_documents)}: {metadata['title'][:50]}...")
        time.sleep(0.1) # Add a small delay to be polite to the API

    except Exception as e:
        print(f"   ❌ Error indexing document {i}: {e}")
        continue

print("\n🎉 New database created successfully with 1536-dimension embeddings!")
print(f"   Total documents in collection: {collection.count()}")

