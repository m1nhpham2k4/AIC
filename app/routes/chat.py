from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.services.gemini_service import get_gemini_response

router = APIRouter()

@router.post("/chat")
async def chat(message: str = Form(...)) -> str:
    reply = get_gemini_response(message)
    return JSONResponse(content={"reply":reply})
