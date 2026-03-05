from fastapi import FastAPI
from schemas import ChatRequest
from fastapi.middleware.cors import CORSMiddleware
from chatbot.elminster import elminster_chat
import traceback

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,  # 👈 THIS LINE
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        reply = elminster_chat(req.message)
        return {"response": reply}
    except Exception as e:
        # Log full traceback
        traceback.print_exc()
        return {"error": str(e)}

