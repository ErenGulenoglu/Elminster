"""
build_database.py

Single-pass pipeline:
  1. Reads raw source .txt files from pdf_reader/Output/
  2. Chunks each file using the same logic as split_lore_file.py
  3. Tags each chunk with Mistral (characters, events, location, era)
  4. Embeds and stores directly into ChromaDB

Run:
    python build_database.py

To rebuild from scratch, delete .chromadb/ first:
    rm -rf .chromadb && python build_database.py
"""

import os
import re
import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
# Both folders are scanned automatically — add more entries if needed
SOURCE_DIRS = [
    "./lore",                  # web-scraped .txt files (e.g. Elminster.txt)
    "./pdf_reader/Output",     # PDF-scraped .txt files (e.g. The Making of a Mage.pdf.txt)
]
CHUNKS_DIR   = "./lore_chunks"         # human-readable chunks for inspection
CHROMA_PATH  = ".chromadb"
COLLECTION   = "fr_lore"
OLLAMA_URL   = "http://localhost:11434/api/generate"
# EMBED_MODEL  = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_MODEL  = "sentence-transformers/all-mpnet-base-v2"
MIN_WORDS    = 200
MAX_WORDS    = 500

NAME_ALIASES = {
    "elminster aumar":        "elminster",
    "the old mage":           "elminster",
    "the sage of shadowdale": "elminster",
    "el":                     "elminster",  # common shorthand in the books
    "lady of mysteries":      "mystra",
    "midnight":               "mystra",
    "mystra (midnight)":      "mystra",
}

# ── Chunking (from split_lore_file.py) ───────────────────────────────────────
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
    """
    Safely convert any metadata value to a plain string.
    Handles: str, list, None, int, float, or anything else Mistral might return.
    """
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
- events: short description of what happens (max 10 words)
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
            json={
                # "model": "mistral"
                "model": "mistral-nemo",
                "prompt": prompt, "stream": False},

            timeout=60
        )
        raw = response.json()["response"].strip()

        # Strip markdown fences
        clean = raw.replace("```json", "").replace("```", "").strip()

        # If Mistral returned multiple JSON blocks, take only the first complete one
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

# ── Disk output (human-readable inspection) ───────────────────────────────────
def save_chunk_to_disk(chunk_id: str, book_name: str, chunk_index: int, chunk_text: str, metadata: dict) -> None:
    """
    Save a chunk as a .txt file under lore_chunks/{book_name}/
    The file includes a metadata header so you can inspect both
    the tags and the raw content in one place.
    """
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

    # Init ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(COLLECTION)

    # Init embedding model
    print("\nLoading embedding model...")
    embed_model = SentenceTransformer(EMBED_MODEL)

    # Collect source files from all configured source dirs
    source_files = []
    for src_dir in SOURCE_DIRS:
        if not os.path.exists(src_dir):
            print(f"⚠️  Source dir not found, skipping: {src_dir}")
            continue
        found = [
            os.path.join(src_dir, f)
            for f in os.listdir(src_dir)
            if f.endswith(".txt")
        ]
        print(f"📂 {src_dir}: {len(found)} file(s) found")
        source_files.extend(found)

    if not source_files:
        print("No .txt files found in any source directory.")
        return

    print(f"\nTotal source files to process: {len(source_files)}\n")

    total_chunks_added = 0

    for file_path in source_files:
        # Strip all extensions (handles .pdf.txt, .txt etc.)
        raw_name = os.path.basename(file_path)
        book_name = raw_name.split(".")[0]  # takes only the part before first dot
        print(f"\n📖 Processing: {book_name}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = create_chunks(text)
        print(f"   Created {len(chunks)} chunks")

        for idx, chunk_text in enumerate(chunks, 1):
            chunk_id = f"{book_name}_chunk_{idx:03d}"

            # Skip if already in ChromaDB
            existing = collection.get(ids=[chunk_id])
            if existing["ids"]:
                print(f"   [{idx}/{len(chunks)}] Skipping (already exists): {chunk_id}")
                continue

            print(f"   [{idx}/{len(chunks)}] Tagging + embedding: {chunk_id} ...", end=" ", flush=True)

            # Tag
            metadata = extract_metadata(chunk_text)

            # Flatten for ChromaDB — every value must be str/int/float/bool
            flat_metadata = {
                "source":      chunk_id,
                "book":        book_name,
                "chunk_index": idx,
                "characters":  flatten_field(metadata.get("characters")),
                "events":      flatten_field(metadata.get("events")),
                "location":    flatten_field(metadata.get("location")),
            }

            # Embed enriched text — metadata tags + raw content combined
            # This improves retrieval by encoding the interpreted meaning
            # (characters, events, location) alongside the raw text
            enriched_text = (
                f"characters: {flat_metadata['characters']}\n"
                f"events: {flat_metadata['events']}\n"
                f"location: {flat_metadata['location']}\n\n"
                f"{chunk_text}"
            )
            embedding = embed_model.encode(enriched_text).tolist()

            # Store in ChromaDB
            collection.add(
                documents=[chunk_text],
                metadatas=[flat_metadata],
                ids=[chunk_id],
                embeddings=[embedding],
            )

            # Save human-readable copy for inspection
            save_chunk_to_disk(chunk_id, book_name, idx, chunk_text, metadata)

            total_chunks_added += 1
            print(f"✓  {flat_metadata['characters'] or 'no characters tagged'}")

    print("\n" + "=" * 60)
    print(f"Done. {total_chunks_added} chunks added to ChromaDB.")
    print(f"Total chunks in collection: {collection.count()}")
    print(f"Readable chunks saved to  : {CHUNKS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    build_database()