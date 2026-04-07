"""
build_database.py

Single-pass pipeline:
  1. Reads raw source .txt files from SOURCE_DIRS
  2. Chunks each file
  3. Tags each chunk with Mistral (characters, events, location)
  4. Embeds and stores into ChromaDB

TWO COLLECTIONS:
  - fr_lore_wiki  : web-scraped summary files (./lore/)
  - fr_lore_books : PDF-scraped narrative files (./pdf_reader/Output/)

Run:
    python build_database.py

To rebuild from scratch:
    rm -rf .chromadb && python build_database.py
"""

import os
import re
import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
SOURCE_DIRS = {
    "wiki":  "./lore",                # web-scraped .txt files → fr_lore_wiki
    "books": "./pdf_reader/Output",   # PDF-scraped .txt files → fr_lore_books
}

COLLECTION_WIKI  = "fr_lore_wiki"
COLLECTION_BOOKS = "fr_lore_books"

CHUNKS_DIR  = "./lore_chunks"
CHROMA_PATH = ".chromadb"
OLLAMA_URL  = "http://localhost:11434/api/generate"
EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"
MIN_WORDS   = 200
MAX_WORDS   = 500

NAME_ALIASES = {
    "elminster aumar":        "elminster",
    "the old mage":           "elminster",
    "the sage of shadowdale": "elminster",
    "el":                     "elminster",
    "lady of mysteries":      "mystra",
    "midnight":               "mystra",
    "mystra (midnight)":      "mystra",
}

# ── Chunking ──────────────────────────────────────────────────────────────────
def count_words(text: str) -> int:
    return len(text.split())

def split_into_paragraphs(text: str) -> list:
    return [p.strip() for p in text.split("\n\n") if p.strip()]

def split_large_paragraph(paragraph: str, max_words: int = 150) -> list:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    chunks, current_chunk, current_words = [], [], 0
    for sentence in sentences:
        sw = count_words(sentence)
        if current_words + sw > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_words = [sentence], sw
        else:
            current_chunk.append(sentence)
            current_words += sw
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def create_chunks(text: str, min_words: int = MIN_WORDS, max_words: int = MAX_WORDS) -> list:
    chunks = []
    sections = re.split(r"(===\s+[^=]+\s+===)", text)
    current_chunk, current_words = "", 0

    for section in sections:
        if not section.strip():
            continue
        section_words = count_words(section)

        if section.strip().startswith("==="):
            if current_chunk and current_words >= min_words:
                chunks.append(current_chunk.strip())
                current_chunk, current_words = "", 0
            current_chunk = section + "\n"
            current_words = section_words
        else:
            for para in split_into_paragraphs(section):
                para_words = count_words(para)
                if para_words > 150:
                    for pc in split_large_paragraph(para, max_words=150):
                        pc_words = count_words(pc)
                        if current_words + pc_words > max_words:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk, current_words = pc + "\n\n", pc_words
                        else:
                            current_chunk += pc + "\n\n"
                            current_words += pc_words
                else:
                    if current_words + para_words > max_words and current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk, current_words = para + "\n\n", para_words
                    else:
                        current_chunk += para + "\n\n"
                        current_words += para_words

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# ── Tagging ───────────────────────────────────────────────────────────────────
def flatten_field(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    return str(value).strip()

def normalise_characters(names: list) -> list:
    seen, result = set(), []
    for name in names:
        normalised = NAME_ALIASES.get(name.lower().strip(), name.lower().strip())
        if normalised not in seen:
            seen.add(normalised)
            result.append(normalised)
    return result

def extract_metadata(chunk_text: str) -> dict:
    prompt = f"""Read this Forgotten Realms lore chunk and extract metadata.
Return ONLY a single JSON object with these fields:
- characters: list of character names present or implied in this chunk
- events: describe what happens and its significance to the characters, including whether this is a first meeting, betrayal, death, transformation, or other milestone. Max 15 words.
- location: list of place names mentioned, empty list if none

Rules for characters:
- Include characters even if not named directly. Use these rules:
  * A glowing woman, divine presence, or mysterious beautiful lady in a temple = "mystra"
  * "The goddess", "Lady of Mysteries", "Lady of Magic", "She" in a magical/divine context = "mystra"
  * A divine or magical female figure who grants power or speaks with authority = "mystra"
  * "The Old Mage", "The Sage", "The Sage of Shadowdale" = "elminster"
  * "El", "Elmara", "Elminster Aumar" = "elminster"
  * "The Srinshee", "the elf queen" = "srinshee"
- Character names must not contain commas (e.g. "Elmara Aumar" not "Aumar, Elmara")
- No titles in character names (e.g. "Elmara" not "Elmara priestess of Mystra")
- Return exactly ONE JSON object, never two
- No markdown, no explanation, just the JSON object

Chunk:
{chunk_text}

JSON:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": "mistral-nemo", "prompt": prompt, "stream": False},
            timeout=60
        )
        raw = response.json()["response"].strip()
        clean = raw.replace("```json", "").replace("```", "").strip()

        brace_count = 0
        end_index = 0
        for i, char in enumerate(clean):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end_index = i + 1
                    break

        first_json = clean[:end_index] if end_index > 0 else clean
        metadata = json.loads(first_json)
        metadata["characters"] = normalise_characters(metadata.get("characters", []))
        return metadata

    except Exception as e:
        print(f"    ⚠️  Tagging failed: {e}")
        return {"characters": [], "events": "", "location": []}

# ── Disk output ───────────────────────────────────────────────────────────────
def save_chunk_to_disk(chunk_id: str, book_name: str, chunk_index: int, chunk_text: str, metadata: dict) -> None:
    book_dir = os.path.join(CHUNKS_DIR, book_name)
    os.makedirs(book_dir, exist_ok=True)

    file_path = os.path.join(book_dir, f"{chunk_id}.txt")

    characters = flatten_field(metadata.get("characters")) or "none"
    events     = flatten_field(metadata.get("events")) or "none"
    location   = flatten_field(metadata.get("location")) or "none"

    content = (
        f"=== METADATA ===\n"
        f"chunk_index : {chunk_index}\n"
        f"characters  : {characters}\n"
        f"events      : {events}\n"
        f"location    : {location}\n"
        f"=== CONTENT ===\n"
        f"{chunk_text}\n"
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── Main pipeline ─────────────────────────────────────────────────────────────
def build_database():
    print("=" * 60)
    print("Building Elminster lore database")
    print("=" * 60)

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Two separate collections — wiki summaries vs book narratives
    wiki_collection  = chroma_client.get_or_create_collection(COLLECTION_WIKI)
    books_collection = chroma_client.get_or_create_collection(COLLECTION_BOOKS)

    print("\nLoading embedding model...")
    embed_model = SentenceTransformer(EMBED_MODEL)

    total_chunks_added = 0

    for source_type, src_dir in SOURCE_DIRS.items():
        if not os.path.exists(src_dir):
            print(f"⚠️  Source dir not found, skipping: {src_dir}")
            continue

        # Route to correct collection
        collection = wiki_collection if source_type == "wiki" else books_collection
        collection_name = COLLECTION_WIKI if source_type == "wiki" else COLLECTION_BOOKS

        found = [
            os.path.join(src_dir, f)
            for f in os.listdir(src_dir)
            if f.endswith(".txt")
        ]
        print(f"\n📂 {src_dir} → {collection_name}: {len(found)} file(s) found")

        for file_path in found:
            raw_name = os.path.basename(file_path)
            book_name = raw_name.split(".")[0]
            print(f"\n📖 Processing: {book_name}")

            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()

            chunks = create_chunks(text)
            print(f"   Created {len(chunks)} chunks")

            for idx, chunk_text in enumerate(chunks, 1):
                chunk_id = f"{book_name}_chunk_{idx:03d}"

                existing = collection.get(ids=[chunk_id])
                if existing["ids"]:
                    print(f"   [{idx}/{len(chunks)}] Skipping (already exists): {chunk_id}")
                    continue

                print(f"   [{idx}/{len(chunks)}] Tagging + embedding: {chunk_id} ...", end=" ", flush=True)

                metadata = extract_metadata(chunk_text)

                flat_metadata = {
                    "source":      chunk_id,
                    "book":        book_name,
                    "chunk_index": idx,
                    "characters":  flatten_field(metadata.get("characters")),
                    "events":      flatten_field(metadata.get("events")),
                    "location":    flatten_field(metadata.get("location")),
                }

                enriched_text = (
                    f"characters: {flat_metadata['characters']}\n"
                    f"events: {flat_metadata['events']}\n"
                    f"location: {flat_metadata['location']}\n\n"
                    f"{chunk_text}"
                )
                embedding = embed_model.encode(enriched_text).tolist()

                collection.add(
                    documents=[chunk_text],
                    metadatas=[flat_metadata],
                    ids=[chunk_id],
                    embeddings=[embedding],
                )

                save_chunk_to_disk(chunk_id, book_name, idx, chunk_text, metadata)

                total_chunks_added += 1
                print(f"✓  {flat_metadata['characters'] or 'no characters tagged'}")

    print("\n" + "=" * 60)
    print(f"Done. {total_chunks_added} chunks added.")
    print(f"  Wiki  collection : {wiki_collection.count()} chunks")
    print(f"  Books collection : {books_collection.count()} chunks")
    print(f"  Readable chunks  : {CHUNKS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    build_database()