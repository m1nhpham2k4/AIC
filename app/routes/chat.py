from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from services.gemini_service import get_gemini_response
import os

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "Data_extraction" / "Keyframes_test"

@router.post("/chat")
async def chat(message: str = Form(...)) -> str:
    reply = get_gemini_response(message)
    return JSONResponse(content={"reply":reply})

@router.get("/api/keyframes-tree")
async def get_keyframes_tree():
    tree = []
    for folder in os.listdir(DATA_DIR): # folder = "Keyframes_L01"
        folder_path = DATA_DIR / folder / "keyframes" # "keyframes"
        if os.path.isdir(folder_path):
            subfolders = [
                name for name in os.listdir(folder_path)
                if os.path.isdir(folder_path / name)
            ]
            tree.append({
                "name":folder, # Keyframes_L01
                "subfolders":subfolders # L01_V001
            })
    return JSONResponse(content={"keyframes" : tree})

@router.get("/api/keyframes-images")
async def get_images(folder: str, subfolder: str):
    folder_path = DATA_DIR / folder / "keyframes" / subfolder
    image_urls = []
    if folder_path.exists():
        for file in sorted(os.listdir(folder_path)):
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                image_urls.append(f"keyframes/{folder}/keyframes/{subfolder}/{file}")
    return {"images": image_urls}

@router.get("/api/video-info")
async def get_videos(folder: str, subfolder: str):
    video_path = DATA_DIR.parent / "Videos_test" / folder / "video" / f"{subfolder}.mp4"

    if video_path.exists():
        video_url = f"/videos/{folder}/video/{subfolder}.mp4"
        return {"video_url":video_url}
    
    return JSONResponse(status_code=404, content={"error":"Video không tồn tại"})

