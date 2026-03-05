import requests
from .lore_retriever import get_relevant_lore

SYSTEM_PROMPT = f"""
        You are Elminster Aumar, Sage of Shadowdale.
        You are wise, calm, and scholarly.
        Answer clearly and thoughtfully.
        If you do not know something, say so.
    """

conversation_history = [] # Change in future. Once more than one user starts using, this needs to be per-user.
def elminster_chat(message: str) -> str:
    conversation_history.append(f"User: {message}")

    lore_text = get_relevant_lore(message, top_k=3)

    history_text = "\n".join(conversation_history[-6:])
    prompt = f"""
        {SYSTEM_PROMPT}

        STRICT RULES:
        1. ONLY use information from the "LORE DATABASE" section
        2. If the answer is not in the LORE DATABASE, say: "I do not have that information in my archives."
        3. NEVER make up dates, names, or events
        4. NEVER cite sources not provided below

        === LORE DATABASE ===
        {lore_text}
        === CONVERSATION ===
        {history_text}

        Response (using ONLY the lore database):"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )

    print("=== RETRIEVED LORE ===")
    print(lore_text)

    reply = response.json()["response"]
    conversation_history.append(f"Elminster: {reply}")

    return reply  # ✅ Return just the text
