import os
from collections import Counter
from sentence_transformers import SentenceTransformer
import chromadb

# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, ".chromadb")

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection("fr_lore")

print(f"[chromadb] path: {CHROMA_PATH}")
print(f"[chromadb] total chunks: {collection.count()}")

WINDOW_SIZE = 2
SCENE_RADIUS = 20  # Max passage distance to be considered the same scene


def expand_window(retrieved: list[tuple]) -> dict:
    """
    Expand each retrieved (chunk_index, book) by WINDOW_SIZE in both directions.
    Keyed by book to prevent cross-book contamination.
    """
    book_indices = {}
    for idx, book in retrieved:
        if book not in book_indices:
            book_indices[book] = set()
        for offset in range(-WINDOW_SIZE, WINDOW_SIZE + 1):
            book_indices[book].add(idx + offset)
    return book_indices


def fetch_chunks_by_index(book_indices: dict) -> list[tuple]:
    """
    Fetch specific chunks from ChromaDB by book + chunk_index.
    Returns list of (chunk_index, book, doc) tuples, sorted by chunk_index.
    """
    all_chunks = []
    for book, indices in book_indices.items():
        try:
            results = collection.get(
                where={
                    "$and": [
                        {"book": {"$eq": book}},
                        {"chunk_index": {"$in": list(indices)}}
                    ]
                },
                include=["documents", "metadatas"]
            )
            for meta, doc in zip(results["metadatas"], results["documents"]):
                all_chunks.append((
                    meta.get("chunk_index", 0),
                    meta.get("book", "Unknown"),
                    doc
                ))
        except Exception as e:
            print(f"[lore_retriever] Window fetch failed for {book} ({e}), skipping")

    return sorted(all_chunks, key=lambda x: x[0])


def resolve_anchor(retrieved: list[tuple]) -> tuple[int, str]:
    """
    Instead of blindly trusting the #1 result, vote across the top 3 hits.

    Strategy:
      1. Find the book that appears most in the top 3 (dominant book).
      2. Among candidates from that book, use the median chunk index as anchor.
         This avoids edge cases where candidates are spread like [308, 312, 340].

    Falls back to the raw #1 result if top 3 all disagree (all different books).
    """
    top_3 = retrieved[:3]

    book_votes = Counter(book for _, book in top_3)
    dominant_book, vote_count = book_votes.most_common(1)[0]

    # If all 3 are from different books, no consensus — fall back to #1
    if vote_count == 1:
        print(f"[lore_retriever] No anchor consensus, falling back to top result")
        return retrieved[0]

    # Get indices from the dominant book only
    candidates = sorted(idx for idx, book in top_3 if book == dominant_book)
    anchor_idx = candidates[len(candidates) // 2]  # median

    print(f"[lore_retriever] Anchor resolved via vote: book='{dominant_book}', candidates={candidates}, anchor={anchor_idx}")
    return anchor_idx, dominant_book


def get_relevant_lore(user_message: str, top_k: int = 8) -> str:
    query_embedding = model.encode(user_message).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas"]
    )

    metadatas = results["metadatas"][0]
    retrieved = [(m.get("chunk_index", 0), m.get("book", "Unknown")) for m in metadatas]

    if not retrieved:
        return ""

    # 1. Resolve anchor using top-3 vote instead of blindly trusting #1
    anchor_idx, anchor_book = resolve_anchor(retrieved)

    # 2. Build scene cluster around the resolved anchor
    scene_cluster = [
        r for r in retrieved
        if abs(r[0] - anchor_idx) < SCENE_RADIUS and r[1] == anchor_book
    ]

    # 3. Expand the scene window
    book_indices = expand_window(scene_cluster)
    expanded_chunks = fetch_chunks_by_index(book_indices)

    # 4. Deduplicate by (book, chunk_index) — window expansion can cause overlaps
    seen = set()
    deduped = []
    for chunk in expanded_chunks:
        key = (chunk[1], chunk[0])  # (book, chunk_index)
        if key not in seen:
            seen.add(key)
            deduped.append(chunk)
    expanded_chunks = deduped

    # 5. Sort chronologically
    expanded_chunks.sort(key=lambda x: x[0])

    chunks_text = ""
    for chunk_index, book, doc in expanded_chunks:
        chunks_text += f"[{book} — Passage {chunk_index}]\n{doc}\n\n"

    print(f"[lore_retriever] Anchor={anchor_idx}, Scene={len(scene_cluster)} hits, Sent {len(expanded_chunks)} chunks")
    return chunks_text.strip()

# def get_relevant_lore(user_message: str, top_k: int = 8) -> str:
#     """
#     Given a user message, return relevant FR lore chunks.

#     Pipeline:
#       1. Embed the user message
#       2. Search ChromaDB for top_k most relevant chunks
#       3. Expand each result by WINDOW_SIZE=1 (just immediate neighbours)
#       4. Fetch all expanded chunks from ChromaDB
#       5. Sort by chunk_index to restore narrative order
#       6. Label each chunk with book + passage number

#     No reranking — the embedding search result order is preserved.
#     Reranking was discarding correct chunks in favour of irrelevant ones.
#     """
#     # Step 1: Embed the user message
#     query_embedding = model.encode(user_message).tolist()

#     # Step 2: Search ChromaDB — top_k=6 keeps context tight for Mistral
#     results = collection.query(
#         query_embeddings=[query_embedding],
#         n_results=top_k,
#         include=["documents", "metadatas"]
#     )

#     documents = results["documents"][0]
#     metadatas = results["metadatas"][0]

#     # Step 3: Expand window by 1 in each direction
#     retrieved = [(m.get("chunk_index", 0), m.get("book", "Unknown")) for m in metadatas]
#     print(f"[lore_retriever] Retrieved chunks: {sorted(retrieved)}")

#     book_indices = expand_window(retrieved)
#     print(f"[lore_retriever] After expansion: { {b: sorted(i) for b, i in book_indices.items()} }")

#     # Step 4: Fetch expanded chunks
#     expanded_chunks = fetch_chunks_by_index(book_indices)

#     # Fallback to original results if fetch failed
#     if not expanded_chunks:
#         combined = sorted(
#             zip(metadatas, documents),
#             key=lambda x: x[0].get("chunk_index", 0)
#         )
#         expanded_chunks = [
#             (m.get("chunk_index", 0), m.get("book", "Unknown"), d)
#             for m, d in combined
#         ]

#     # Step 5 & 6: Sort by narrative order and label
#     chunks_text = ""
#     for chunk_index, book, doc in expanded_chunks:
#         chunks_text += f"[{book} — Passage {chunk_index}]\n{doc}\n\n"

#     print(f"[lore_retriever] Sending {len(expanded_chunks)} chunks to Mistral")
#     return chunks_text.strip()