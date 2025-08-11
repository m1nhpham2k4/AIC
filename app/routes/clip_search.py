# app/services/clip_search_service.py
import os
from Data_extraction.search.clip_engine import ClipSearchEngine

# Đọc config từ env (hoặc app.config)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
CLIP_COLLECTION = os.getenv("CLIP_COLLECTION", "clip_ViT_g_14_cosine")
MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "ViT-g-14")
PRETRAINED = os.getenv("CLIP_PRETRAINED", "laion2b_s34b_b88k")
DEVICE = os.getenv("CLIP_DEVICE")  # "cuda" / "cpu" / None -> auto
ROOT_KEYFRAMES = os.getenv("ROOT_KEYFRAMES", "./keyframes-2024/Keyframes_test")
VIDEO2FOLDER_JSON = os.getenv("VIDEO2FOLDER_JSON", "./video2folder.json")

# Singleton engine (tạo 1 lần)
_engine = ClipSearchEngine(
    qdrant_url=QDRANT_URL,
    collection=CLIP_COLLECTION,
    model_name=MODEL_NAME,
    pretrained=PRETRAINED,
    device=DEVICE,
    root_keyframes=ROOT_KEYFRAMES,
    video2folder_json=VIDEO2FOLDER_JSON,
)

def search_clip(query: str, topk: int = 5) -> list[dict]:
    return _engine.search(query, topk=topk)
