import os
import chromadb
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Initialize Chroma (persist on disk) using new API
client = chromadb.PersistentClient(path=".chromadb")

# Create / get collection
collection = client.get_or_create_collection("fr_lore")

# Folder with subfolders
lore_dir = "lore_chunks"

# Walk the directory recursively
for root, dirs, files in os.walk(lore_dir):
    for filename in files:
        if filename.endswith(".txt"):
            path = os.path.join(root, filename)
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
                # Create embedding
                embedding = model.encode(text).tolist()
                # Use relative path as unique id
                doc_id = os.path.relpath(path, lore_dir)
                collection.add(
                    documents=[text],
                    metadatas=[{"source": doc_id}],
                    ids=[doc_id],
                    embeddings=[embedding]
                )
                print(f"Added {doc_id}")
