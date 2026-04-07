import os
import json
import requests
from collections import Counter
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, ".chromadb")

client = chromadb.PersistentClient(path=CHROMA_PATH)
wiki_collection  = client.get_collection("fr_lore_wiki")
books_collection = client.get_collection("fr_lore_books")

print(f"[chromadb] path: {CHROMA_PATH}")
print(f"[chromadb] wiki  chunks: {wiki_collection.count()}")
print(f"[chromadb] books chunks: {books_collection.count()}")

WINDOW_SIZE  = 2
SCENE_RADIUS = 20

# ── Query type detection ──────────────────────────────────────────────────────
NARRATIVE_TRIGGERS = [
    "how did", "what happened", "tell me about", "when did",
    "first time", "the time", "story of", "how you met",
    "how did you", "what was it like", "describe", "recount",
    "how were you", "what did you do", "how did ye", "how did thou",
]

def is_narrative_query(message: str) -> bool:
    """
    Returns True if the question is asking for a specific event or story
    — these should hit the books collection first.
    """
    msg_lower = message.lower()
    return any(trigger in msg_lower for trigger in NARRATIVE_TRIGGERS)


# ── Name extraction ───────────────────────────────────────────────────────────
def extract_names_with_ollama(user_message: str, history: list[str]) -> list[str]:
    context = " ".join(history[-4:]) + " " + user_message

    prompt = f"""Extract all character names from this text. Include characters referred to by pronoun if the name is clear from context (e.g. "her" after mentioning Mystra = Mystra).

Return ONLY a JSON array of lowercase name strings. No explanation, no markdown.
Example: ["elminster", "mystra", "khelben"]

Text: {context}

JSON:"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral-nemo",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 64}
            },
            timeout=15
        )
        raw = response.json()["response"].strip()
        clean = raw.replace("```json", "").replace("```", "").strip()
        names = json.loads(clean)
        names = [n.lower().strip() for n in names if isinstance(n, str)]
    except Exception as e:
        print(f"[lore_retriever] Name extraction failed ({e}), falling back to empty")
        names = []

    if "elminster" not in names:
        names.insert(0, "elminster")

    print(f"[lore_retriever] Extracted names: {names}")
    return names


def enrich_query(user_message: str, history: list[str]) -> str:
    names = extract_names_with_ollama(user_message, history)
    return (
        f"characters: {', '.join(names)}\n"
        f"events: {user_message}\n\n"
        f"{user_message}"
    )


# ── Window + fetch ────────────────────────────────────────────────────────────
def expand_window(retrieved: list[tuple]) -> dict:
    book_indices = {}
    for idx, book in retrieved:
        if book not in book_indices:
            book_indices[book] = set()
        for offset in range(-WINDOW_SIZE, WINDOW_SIZE + 1):
            book_indices[book].add(idx + offset)
    return book_indices


def fetch_chunks_by_index(book_indices: dict, collection) -> list[tuple]:
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


# ── Anchor resolution ─────────────────────────────────────────────────────────
def resolve_anchor(retrieved: list[tuple]) -> tuple[int, str]:
    top_3 = retrieved[:3]
    book_votes = Counter(book for _, book in top_3)
    dominant_book, vote_count = book_votes.most_common(1)[0]

    if vote_count == 1:
        print(f"[lore_retriever] No anchor consensus, falling back to top result")
        return retrieved[0]

    candidates = sorted(idx for idx, book in top_3 if book == dominant_book)
    anchor_idx = candidates[len(candidates) // 2]

    print(f"[lore_retriever] Anchor resolved: book='{dominant_book}', candidates={candidates}, anchor={anchor_idx}")
    return anchor_idx, dominant_book


# ── Core retrieval ────────────────────────────────────────────────────────────
def retrieve_from_collection(query_embedding: list, collection, top_k: int) -> str:
    """
    Run the full anchor → scene cluster → window expand → dedupe pipeline
    against a single collection. Returns formatted chunks text.
    """
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas"]
    )

    metadatas = results["metadatas"][0]
    retrieved = [(m.get("chunk_index", 0), m.get("book", "Unknown")) for m in metadatas]

    if not retrieved:
        return ""

    anchor_idx, anchor_book = resolve_anchor(retrieved)

    scene_cluster = [
        r for r in retrieved
        if abs(r[0] - anchor_idx) < SCENE_RADIUS and r[1] == anchor_book
    ]

    book_indices = expand_window(scene_cluster)
    expanded_chunks = fetch_chunks_by_index(book_indices, collection)

    # Deduplicate
    seen = set()
    deduped = []
    for chunk in expanded_chunks:
        key = (chunk[1], chunk[0])
        if key not in seen:
            seen.add(key)
            deduped.append(chunk)

    deduped.sort(key=lambda x: x[0])

    chunks_text = ""
    for chunk_index, book, doc in deduped:
        chunks_text += f"[{book} — Passage {chunk_index}]\n{doc}\n\n"

    print(f"[lore_retriever] Anchor={anchor_idx}, Scene={len(scene_cluster)} hits, Sent {len(deduped)} chunks from {collection.name}")
    return chunks_text.strip()


# ── Public interface ──────────────────────────────────────────────────────────
def get_relevant_lore(user_message: str, top_k: int = 8, history: list[str] = []) -> str:
    """
    Query strategy:
    - Narrative questions (how did, what happened, first meeting etc.)
      → books first, wiki as fallback if books return nothing
    - General knowledge questions
      → wiki first, books as fallback
    """
    query_embedding = model.encode(enrich_query(user_message, history)).tolist()

    narrative = is_narrative_query(user_message)

    if narrative:
        print(f"[lore_retriever] Narrative query detected — books first")
        primary   = books_collection
        secondary = wiki_collection
    else:
        print(f"[lore_retriever] General query detected — wiki first")
        primary   = wiki_collection
        secondary = books_collection

    lore = retrieve_from_collection(query_embedding, primary, top_k)

    # Fallback to secondary collection if primary returned nothing
    if not lore:
        print(f"[lore_retriever] Primary collection empty, trying secondary")
        lore = retrieve_from_collection(query_embedding, secondary, top_k)

    return lore