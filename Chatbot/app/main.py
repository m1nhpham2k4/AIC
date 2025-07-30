from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from gridfs import GridFS
from bson.objectid import ObjectId
import io
from routes import chat
import os
from pathlib import Path
from dbs import db
from datetime import datetime
from io import BytesIO

timestamp = int(datetime.utcnow().timestamp())

# Lấy đường dẫn gốc (thư mục chứa thư mục 'app')
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI()

# Mount static and templates
app.mount('/static', StaticFiles(directory= BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory= BASE_DIR / 'templates')

# Include routers
app.include_router(chat.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "timestamp": int(datetime.now().timestamp())})

@app.get("/folder-json")
async def get_keyframes_json():
    doc = db["keyframes_json"].find_one()
    folders = []
    subfolders_map = {}

    if doc:
        for group in doc["Keyframes"]:
            for folder_name, subfolders in group.items():
                folders.append(folder_name)
                subfolders_map[folder_name] = [list(sub.keys())[0] for sub in subfolders]

    return {"folders": folders, "subfolders_map": subfolders_map}

@app.get("/keyframes/{subfolder}", response_class=HTMLResponse)
async def keyframes_subfolder(request: Request, subfolder: str):
    # Truy xuất ảnh từ MongoDB GridFS (ví dụ)
    files = fs.find({"metadata.level3": subfolder})
    image_urls = [f"/image/{file.filename}" for file in files]

    return templates.TemplateResponse("keyframes_subfolder.html", {
        "request": request,
        "subfolder": subfolder,
        "images": image_urls
    })

fs = GridFS(db)

@app.get("/image/{filename}")
async def get_image(filename: str):
    try:
        file = fs.find_one({"filename": filename})
        if not file:
            return JSONResponse(status_code=404, content={"error": "Image not found"})

        content_type = file.metadata.get("contentType", "image/png") if file.metadata else "image/png"
        return StreamingResponse(BytesIO(file.read()), media_type=content_type)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/images/{subfolder}")
async def get_images(subfolder: str):
    try:
        files = fs.find({"metadata.level3": subfolder})
        image_urls = [f"/image/{file.filename}" for file in files]
        return {"images": image_urls}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

