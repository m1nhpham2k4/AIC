from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse

from datetime import datetime
from pathlib import Path
from io import BytesIO
import sys
import os
import torch
import open_clip

from app.routes import chat
# Lấy thư mục gốc của project (thư mục chứa thư mục 'app')
BASE_DIR = Path(__file__).resolve().parent.parent

# (Tùy chọn) nếu cần import từ cấp cao hơn (ví dụ thư mục 'Data_extraction' ở cùng cấp với 'AIC')
ROOT_DIR = BASE_DIR.parent
sys.path.append(str(ROOT_DIR))

# Khởi tạo FastAPI app
app = FastAPI()

# Mount static và templates
app.mount('/static', StaticFiles(directory=BASE_DIR / "app" / 'static'), name='static')
app.mount('/keyframes', StaticFiles(directory=BASE_DIR / "Data_extraction" / "Keyframes_test"), name='keyframes')
app.mount("/videos", StaticFiles(directory=BASE_DIR / "Data_extraction" / "Videos_test"), name="videos")
templates = Jinja2Templates(directory=BASE_DIR / 'app' / 'templates')

# Gắn router từ file routes/chat.py
app.include_router(chat.router)

# Route: Trang chủ
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "timestamp": int(datetime.utcnow().timestamp())
    })

