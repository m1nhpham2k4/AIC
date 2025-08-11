# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import time

from app.routes.chat import router as chat_router  # lấy router từ chat.py

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent      # .../AIC/app
ROOT_DIR = BASE_DIR.parent                      # .../AIC

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
else:
    print("[WARN] Không tìm thấy static:", STATIC_DIR)

DATA_ROOT = ROOT_DIR / "Data_extraction"
KEYFRAMES_DIR = DATA_ROOT / "Keyframes_test"
VIDEOS_DIR    = DATA_ROOT / "Videos_test"

if KEYFRAMES_DIR.exists():
    app.mount("/keyframes", StaticFiles(directory=KEYFRAMES_DIR), name="keyframes")
else:
    print("[WARN] Không thấy:", KEYFRAMES_DIR)

if VIDEOS_DIR.exists():
    app.mount("/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
else:
    print("[WARN] Không thấy:", VIDEOS_DIR)

templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(chat_router)  # <-- gắn router Ở ĐÂY

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "timestamp": int(time.time())}
    )
