import json
import chromadb
from sentence_transformers import SentenceTransformer
import os
from datetime import datetime

# --- 1. INITIALIZATION ---
print("🚀 Initializing TDS Virtual TA Indexer...")

# Initialize the embedding model
print("   📦 Loading embedding model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB client
db_path = os.path.join(os.path.dirname(__file__), '..', 'db')
client = chromadb.PersistentClient(path=db_path)

# Create or get collection
collection_name = "tds_knowledge_base"
print(f"   🗃️  Connecting to ChromaDB collection: '{collection_name}'...")

# Delete existing collection to start fresh (optional)
try:
    client.delete_collection(name=collection_name)
    print("   🗑️  Cleared existing collection")
except:
    pass

collection = client.create_collection(name=collection_name)

# --- 2. DATA LOADING ---
print("\n📂 Loading scraped data...")

# Load course content
try:
    course_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'course_content.json')
    with open(course_path, 'r', encoding='utf-8') as f:
        course_content = json.load(f)
    print(f"   ✅ Loaded {len(course_content)} course documents")
except FileNotFoundError:
    print("   ⚠️  course_content.json not found, skipping...")
    course_content = []

# Load discourse posts
try:
    discourse_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'discourse_posts.json')
    with open(discourse_path, 'r', encoding='utf-8') as f:
        discourse_posts = json.load(f)
    print(f"   ✅ Loaded {len(discourse_posts)} discourse posts")
except FileNotFoundError:
    print("   ⚠️  discourse_posts.json not found, skipping...")
    discourse_posts = []

# --- 3. PROCESSING AND INDEXING ---
print("\n🧠 Processing and indexing documents...")

def clean_and_validate_content(text):
    """Clean and validate content before indexing"""
    if not text or len(text.strip()) < 50:
        return None
    # Remove excessive whitespace and clean up
    cleaned = ' '.join(text.strip().split())
    return cleaned

def index_documents(documents, source_name):
    """Process and add documents to ChromaDB"""
    if not documents:
        print(f"   📭 No documents from '{source_name}' to index")
        return 0

    indexed_count = 0
    skipped_count = 0
    
    print(f"   📋 Processing {len(documents)} {source_name} documents...")
    
    for i, doc in enumerate(documents):
        try:
            # Extract content (prefer full_content over content)
            content = doc.get('full_content') or doc.get('content', '')
            cleaned_content = clean_and_validate_content(content)
            
            if not cleaned_content:
                skipped_count += 1
                continue
            
            # Create unique ID
            doc_id = f"{source_name}_{i}_{hash(doc.get('title', 'untitled')) % 10000}"
            
            # Prepare metadata based on source type
            if source_name == "discourse":
                metadata = {
                    'source': source_name,
                    'title': doc.get('title', 'Untitled'),
                    'url': doc.get('url', ''),
                    'author': doc.get('author', 'Unknown'),
                    'date': doc.get('date', ''),
                    'replies': doc.get('replies', 0),
                    'content_length': len(cleaned_content)
                }
            else:  # course content
                metadata = {
                    'source': source_name,
                    'title': doc.get('title', 'Untitled'),
                    'url': doc.get('url', ''),
                    'content_length': len(cleaned_content)
                }
            
            # Generate embedding
            if i % 10 == 0:  # Progress update every 10 docs
                print(f"      🔄 Processing document {i+1}/{len(documents)}")
            
            embedding = embedder.encode(cleaned_content)
            
            # Add to collection
            collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[cleaned_content],
                metadatas=[metadata]
            )
            
            indexed_count += 1
            
        except Exception as e:
            print(f"      ❌ Error processing document {i}: {str(e)[:100]}...")
            skipped_count += 1
            continue
    
    print(f"   ✅ Indexed {indexed_count} documents from '{source_name}'")
    if skipped_count > 0:
        print(f"   ⚠️  Skipped {skipped_count} documents (too short or invalid)")
    
    return indexed_count

# Index both datasets
total_indexed = 0
total_indexed += index_documents(course_content, "course")
total_indexed += index_documents(discourse_posts, "discourse")

# --- 4. VERIFICATION & FINALIZATION ---
print(f"\n🎉 Indexing complete!")
print(f"   📊 Total documents indexed: {total_indexed}")
print(f"   🗃️  Collection '{collection_name}' contains: {collection.count()} documents")
print(f"   💾 Database saved in: {db_path}")

# Test the index with a sample query
print(f"\n🔍 Testing search functionality...")
try:
    test_query = "What is Tools in Data Science course about?"
    test_embedding = embedder.encode(test_query)
    
    results = collection.query(
        query_embeddings=[test_embedding.tolist()],
        n_results=3
    )
    
    print(f"   ✅ Search test successful! Found {len(results['documents'][0])} relevant documents")
    print(f"   📝 Sample result: {results['documents'][0][0][:100]}...")
    
except Exception as e:
    print(f"   ❌ Search test failed: {e}")

print(f"\n🚀 Ready for Phase 3: API Development!")
