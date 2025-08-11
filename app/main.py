from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys, time

# Đường dẫn
BASE_DIR = Path(__file__).resolve().parent          # app/
ROOT_DIR = BASE_DIR.parent                          # repo gốc

# Cho phép import các module ngoài app/
sys.path.append(str(ROOT_DIR))

# Routers
from app.routes import chat

app = FastAPI()

# CORS (tuỳ nhu cầu)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # thay bằng domain thật khi deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Mount keyframes & videos (chỉ khi tồn tại)
keyframes_dir = ROOT_DIR / "Data_extraction" / "Keyframes_test"
videos_dir    = ROOT_DIR / "Data_extraction" / "Videos_test"
if keyframes_dir.exists():
    app.mount("/keyframes", StaticFiles(directory=keyframes_dir), name="keyframes")
if videos_dir.exists():
    app.mount("/videos", StaticFiles(directory=videos_dir), name="videos")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Gắn router FastAPI (có /api/search, /api/preview_image, /api/keyframes-...)
app.include_router(chat.router)

# Home
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "timestamp": int(time.time())}
    )
