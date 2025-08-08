from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import sys

# Cấu hình thư mục
BASE_DIR = Path(__file__).resolve().parent         # app/
ROOT_DIR = BASE_DIR.parent                         # Dự án gốc (AIC)
sys.path.append(str(ROOT_DIR))

from app.routes import chat  # <-- dùng đúng kiểu import

# Khởi tạo app
app = FastAPI()

# Mount static & media folders
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/keyframes", StaticFiles(directory=ROOT_DIR / "Data_extraction" / "Keyframes_test"), name="keyframes")
app.mount("/videos", StaticFiles(directory=ROOT_DIR / "Data_extraction" / "Videos_test"), name="videos")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Gắn router
app.include_router(chat.router)

# Route: Trang chủ
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "timestamp": int(Path().stat().st_mtime)
    })
