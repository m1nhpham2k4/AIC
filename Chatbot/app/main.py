from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from gridfs import GridFS
from bson.objectid import ObjectId
import io
import torch
import open_clip
from routes import chat
import os
from pathlib import Path
from dbs import db
from datetime import datetime
from io import BytesIO
import sys
from pathlib import Path

# Lấy thư mục cha của thư mục Chatbot (tức là AIC/)
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from Data_extraction.encode_and_insert import qdrant, collection_name, model, tokenizer, device

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

@app.get("/search")
async def search_text(query: str, limit: int = 5):
    try:
        # Tokenize truy vấn
        text = tokenizer([query]).to(device)

        with torch.no_grad():
            text_vector = model.encode_text(text).cpu().numpy()[0]
            text_vector /= (text_vector ** 2).sum() ** 0.5  # Normalize

        # Truy vấn Qdrant
        hits = qdrant.search(
            collection_name=collection_name,
            query_vector=text_vector,
            limit=limit
        )

        # Trả kết quả
        results = []
        for hit in hits:
            results.append({
                "path": hit.payload.get("path", "unknown"),
                "score": round(hit.score, 4)
            })

        return {"query": query, "results": results}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})