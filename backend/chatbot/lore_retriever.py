from sentence_transformers import SentenceTransformer
import chromadb

# Load the same embedding model used to create the database
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Connect to the persisted Chroma DB
client = chromadb.PersistentClient(path=".chromadb")

# See all collections
collections = client.list_collections()
# print(f"Found {len(collections)} collections:")
# for c in collections:
#     print(f"  - {c.name} ({c.count()} documents)")
collection = client.get_collection("fr_lore")  # your collection name

def get_relevant_lore(user_message: str, top_k: int = 10) -> str:
    """
    Given a user message, return top-K relevant FR lore chunks.
    """
    # Step 1: Embed the user message
    query_embedding = model.encode(user_message).tolist()

    # Step 2: Query Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Step 3: Extract retrieved text
    # results['documents'] is a list of lists (one per query)
    retrieved_chunks = results['documents'][0]  # top-K chunks for this message

    # Combine chunks into a single string for prompt injection
    return "\n".join(retrieved_chunks)
