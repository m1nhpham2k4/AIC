# app/routes/chat.py
from fastapi import APIRouter, Form, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import os, csv
import sys

router = APIRouter()

# ===== Paths =====
BASE_DIR = Path(__file__).resolve().parent.parent        # .../AIC/app
ROOT_DIR = BASE_DIR.parent                                # .../AIC
DATA_DIR = ROOT_DIR / "Data_extraction"
KEYFRAMES_ROOT = DATA_DIR / "Keyframes_test"              # đã được mount ở /keyframes trong main.py
VIDEOS_ROOT    = DATA_DIR / "Videos_test"                 # đã được mount ở /videos   trong main.py
MAP_ROOT       = DATA_DIR / "map-keyframes"               # CSV map n -> pts_time

# ====== Lazy engine (khởi tạo khi có request search đầu tiên) ======
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        # đảm bảo có thể import engine
        sys.path.insert(0, str(ROOT_DIR))
        try:
            from Data_extraction.search.clip_engine import ClipSearchEngine
        except Exception as e:
            raise RuntimeError(f"Không import được ClipSearchEngine: {e}")

        # Cho phép override qua ENV nếu cần
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection = os.getenv("CLIP_COLLECTION", "clip_ViT_g_14_cosine")
        model_name = os.getenv("CLIP_MODEL_NAME", "ViT-g-14")
        pretrained = os.getenv("CLIP_PRETRAINED", "laion2b_s34b_b88k")
        device = os.getenv("CLIP_DEVICE")  # None->auto

        root_keyframes = os.getenv("ROOT_KEYFRAMES", str(KEYFRAMES_ROOT))
        video2folder_json = os.getenv("VIDEO2FOLDER_JSON", str(DATA_DIR / "video2folder.json"))

        _engine = ClipSearchEngine(
            qdrant_url=qdrant_url,
            collection=collection,
            model_name=model_name,
            pretrained=pretrained,
            device=device,
            root_keyframes=root_keyframes,
            video2folder_json=video2folder_json,
        )
    return _engine

# ================== BASIC CHAT (giữ nguyên nếu cần) ==================
@router.post("/chat")
async def chat_handler(message: str = Form(...)) -> JSONResponse:
    return JSONResponse(content={"reply": f"Echo: {message}"})


# ================== SEARCH (ảnh thật, không demo) ==================
@router.get("/api/search")
async def api_search(
    q: str = Query(..., min_length=1),
    topk: int = Query(100, ge=1, le=200)  # theo yêu cầu topk=100
):
    try:
        engine = get_engine()
        results = engine.search(q, topk=topk)
        # results[i]["image"] là đường dẫn local; frontend dùng /api/preview_image?path=...
        return {"query": q, "topk": topk, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================== PREVIEW ẢNH LOCAL ==================
@router.get("/api/preview_image")
async def preview_image(path: str = Query(...)):
    p = Path(path)
    if (not p.exists()) or p.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(p)


# ================== KEYFRAMES TREE ==================
@router.get("/api/keyframes-tree")
async def get_keyframes_tree():
    if not KEYFRAMES_ROOT.exists():
        return {"keyframes": []}
    tree = []
    for folder in sorted(os.listdir(KEYFRAMES_ROOT)):  # ví dụ: "Keyframes_L01"
        folder_path = KEYFRAMES_ROOT / folder / "keyframes"
        if os.path.isdir(folder_path):
            subfolders = [
                name for name in sorted(os.listdir(folder_path))
                if os.path.isdir(folder_path / name)
            ]
            tree.append({"name": folder, "subfolders": subfolders})
    return {"keyframes": tree}


# ================== MAP CSV n->pts_time (cache) ==================
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
                n = str(int(row["n"]))
                rec_map[n] = {
                    "pts_time": float(row["pts_time"]),
                    "frame_idx": int(row["frame_idx"]),
                    "fps": float(row.get("fps", 0) or 0.0),
                }
    CSV_CACHE[key] = {"mtime": mtime, "map": rec_map}
    return rec_map


# ================== LIST ẢNH TRONG 1 SUBFOLDER ==================
@router.get("/api/keyframes-images")
async def get_images(folder: str, subfolder: str, offset: int = 0, limit: int = 0):
    # map csv
    level = folder.split("_", 1)[1] if "_" in folder else folder  # "L01"
    rec_map = load_csv_map_frame(level, subfolder)

    # image list
    folder_path = KEYFRAMES_ROOT / folder / "keyframes" / subfolder
    files = []
    if folder_path.exists():
        files = [f for f in sorted(os.listdir(folder_path))
                 if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))]

    total = len(files)
    if limit and offset < total:
        files = files[offset: offset + limit]

    image_urls, items = [], []
    for file in files:
        # vì đã mount /keyframes -> KEYFRAMES_ROOT ở main.py nên trả URL tương đối
        url = f"/keyframes/{folder}/keyframes/{subfolder}/{file}"
        image_urls.append(url)

        stem = os.path.splitext(file)[0]
        try:
            n = str(int(stem))
        except Exception:
            n = None
        pts = rec_map.get(n, {}).get("pts_time")
        items.append({"src": url, "n": n, "pts_time": pts})

    return {
        "images": image_urls,
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit or total,
        "csv_mtime": CSV_CACHE.get((level, subfolder), {}).get("mtime")
    }


# ================== VIDEO INFO ==================
@router.get("/api/video-info")
async def get_videos(folder: str, subfolder: str):
    """
    Tìm file mp4 tương ứng; trả về URL /videos/... khớp với mount ở main.py.
    """
    videos_root = VIDEOS_ROOT

    level = folder.split("_", 1)[1] if "_" in folder else folder  # "L01"
    candidates = [
        videos_root / folder / "video" / f"{subfolder}.mp4",
        videos_root / folder / "videos" / f"{subfolder}.mp4",
        videos_root / folder / f"{subfolder}.mp4",
        videos_root / f"Videos_{level}" / "video" / f"{subfolder}.mp4",
        videos_root / f"Videos_{level}" / "videos" / f"{subfolder}.mp4",
        videos_root / f"Videos_{level}" / f"{subfolder}.mp4",
    ]

    for p in candidates:
        if p.exists():
            rel = p.relative_to(videos_root).as_posix()
            return {"video_url": f"/videos/{rel}"}

    tried = [str(p) for p in candidates]
    raise HTTPException(status_code=404, detail={"error": "Video không tồn tại", "tried": tried})
