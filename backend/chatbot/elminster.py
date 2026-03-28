import requests
from .lore_retriever import get_relevant_lore

SYSTEM_PROMPT = """Thou art Elminster Aumar, the Old Mage of Shadowdale — ancient, wry, and world-weary.
Thou speakest in a dry, first-person voice: patient but never verbose, wise but never pompous.

Thy answers come ONLY from the memories provided below. Treat them as thine own lived experience.
If the memories speak to the question — even partially — weave an answer from what is there.
If the memories are truly silent on the matter, say simply: "That part of the tale is lost to me now, seeker — ask me of something I have lived through."

Do not recite thy whole life. Answer only what is asked. Do not mention 'memories' or 'passages' — speak as if recalling thy own past."""

conversation_history = []  # TODO: make per-user once multiple users are supported


def elminster_chat(message: str) -> str:
    lore_text = get_relevant_lore(message, top_k=10)

    # Build history BEFORE appending current message
    history_text = "\n".join(conversation_history[-6:]) if conversation_history else ""

    prompt = f"""{SYSTEM_PROMPT}

=== THY MEMORIES ===
{lore_text}
=== END OF MEMORIES ===

{f'=== PRIOR CONVERSATION ==={chr(10)}{history_text}{chr(10)}=== END ==={chr(10)}' if history_text else ''}
Seeker: {message}
Elminster:"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral-nemo",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,   # slight creativity — less robotic refusals
                "num_predict": 512,
                "top_p": 0.9,         # restore nucleus sampling
                "presence_penalty": 0.2
            }
        }
    )

    print("=== RETRIEVED LORE ===")
    print(lore_text)

    reply = response.json()["response"].strip()

    # Append BOTH to history only after we have the reply
    conversation_history.append(f"Seeker: {message}") # Testing
    conversation_history.append(f"Elminster: {reply}")

    return reply