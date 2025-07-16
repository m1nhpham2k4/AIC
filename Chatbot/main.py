from fastapi import FastAPI
from pydantic import BaseModel
from chatbot_chain import chat_with_bot

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    result = chat_with_bot(req.message, session_id=req.session_id)
    return ChatResponse(response=result)
