from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import sys

# Đảm bảo có thể import từ app.services
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.services.gemini_service import get_gemini_response
import os
import csv

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent   # app/
DATA_DIR = BASE_DIR.parent / "Data_extraction" / "Keyframes_test"
MAP_ROOT = DATA_DIR.parent / "map-keyframes"

@router.post("/chat")
async def chat(message: str = Form(...)) -> JSONResponse:
    reply = get_gemini_response(message)
    return JSONResponse(content={"reply": reply})

@router.get("/api/keyframes-tree")
async def get_keyframes_tree():
    tree = []
    for folder in os.listdir(DATA_DIR):  # e.g., "Keyframes_L01"
        folder_path = DATA_DIR / folder / "keyframes"
        if os.path.isdir(folder_path):
            subfolders = [
                name for name in os.listdir(folder_path)
                if os.path.isdir(folder_path / name)
            ]
            tree.append({
                "name": folder,
                "subfolders": subfolders
            })
    return JSONResponse(content={"keyframes" : tree})
CSV_CACHE = {}

def load_csv_map_frame(level: str, subfolder: str) -> dict:
    csv_path = MAP_ROOT / f"Keyframes_{level}" / "keyframes" / f"{subfolder}.csv"
    mtime = csv_path.stat().st_mtime if csv_path.exists() else None
    key = (level, subfolder)

    hit = CSV_CACHE.get(key)
    if hit and hit['mtime'] == mtime:
        return hit["map"]
    
    rec_map = {}
    if csv_path.exists():
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                n = str(int(row["n"]))  # 1-based -> "1","2",...
                rec_map[n] = {
                    "pts_time": float(row["pts_time"]),
                    "frame_idx": int(row["frame_idx"]),
                    "fps": float(row.get("fps", 0) or 0.0),
                }

    CSV_CACHE[key] = {"mtime": mtime, "map": rec_map}
    return rec_map

@router.get("/api/keyframes-images")
async def get_images(folder: str, subfolder: str, offset: int = 0, limit: int = 0):
    # map csv
    level = folder.split("_", 1)[1] if "_" in folder else folder  # "L01"
    rec_map = load_csv_map_frame(level, subfolder)

    # image
    folder_path = DATA_DIR / folder / "keyframes" / subfolder
    # image_urls = []
    files = []
    if folder_path.exists():
        # for file in sorted(os.listdir(folder_path)):
        #     if file.lower().endswith((".jpg", ".jpeg", ".png")):
        #         image_urls.append(f"keyframes/{folder}/keyframes/{subfolder}/{file}")
        files = [f for f in sorted(os.listdir(folder_path))
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        
    total = len(files)
    if limit and offset < total:
        files = files[offset: offset + limit]
    
    image_urls, items = [], []
    for file in files:
        url = f"keyframes/{folder}/keyframes/{subfolder}/{file}"
        image_urls.append(url)

        stem = os.path.splitext(file)[0]
        try:
            n = str(int(stem))
        except:
            n = None
        
        pts = rec_map.get(n, {}).get("pts_time")
        items.append({"src":url, "n":n, "pts_time": pts})

    csv_mtime = CSV_CACHE.get((level, subfolder), {}).get("mtime")
    headers = {"Cache-Control": "no-store"}
    resp = {"images": image_urls, "items": items, "total": total, "offset": offset, "limit": limit or total,
            "csv_mtime": csv_mtime}

    return JSONResponse(content=resp, headers=headers)
    # return {"images": image_urls}

@router.get("/api/video-info")
async def get_videos(folder: str, subfolder: str):
    video_path = DATA_DIR.parent / "Videos_test" / folder / "video" / f"{subfolder}.mp4"
    if video_path.exists():
        video_url = f"/videos/{folder}/video/{subfolder}.mp4"
        return {"video_url": video_url}
    return JSONResponse(status_code=404, content={"error": "Video không tồn tại"})
