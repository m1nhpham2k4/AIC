# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# CORS (tuỳ frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # đặt domain thật nếu deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static (css/js/images)
app.mount("/static", StaticFiles(directory=Path(__file__).parents[1] / "static"), name="static")

# Mount keyframes & videos để frontend truy cập
DATA_ROOT = Path(__file__).parents[1] / "Data_extraction"
app.mount("/keyframes", StaticFiles(directory=DATA_ROOT / "Keyframes_test"), name="keyframes")
app.mount("/videos", StaticFiles(directory=DATA_ROOT / "Videos_test"), name="videos")

# Routes
app.include_router(chat_router)

# Chạy: uvicorn app.main:app --reload
