# query.py
import os, json
import numpy as np
import torch, open_clip
from PIL import Image
from qdrant_client import QdrantClient

QDRANT_URL = "http://localhost:6333"
COLLECTION  = "clip_ViT_g_14_cosine"

MODEL_NAME  = "ViT-g-14"
PRETRAINED  = "laion2b_s34b_b88k"
DEVICE      = "cuda" if torch.cuda.is_available() else "cpu"
TOPK        = 5

# Đặt root keyframes nếu bạn muốn suy ra đường dẫn ảnh để xem trực tiếp
ROOT_KEYFRAMES = r"/kaggle/input/keyframes-2024/Keyframes_test"  # hoặc r"D:\...\Keyframes_test"
VIDEO2FOLDER_JSON = r"./video2folder.json"  # {"L05_V005": "Keyframes_L05", ...}

# ===== Model & tokenizer =====
model, _, _ = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED, device=DEVICE)
tokenizer = open_clip.get_tokenizer(MODEL_NAME)

@torch.no_grad()
def encode_text(text: str) -> np.ndarray:
    toks = tokenizer([text]).to(DEVICE)
    feat = model.encode_text(toks).float()
    feat /= feat.norm(dim=-1, keepdim=True)      # cosine normalize
    return feat.cpu().numpy()[0].astype(np.float32)

# ===== Qdrant =====
client = QdrantClient(url=QDRANT_URL)  # , prefer_grpc=True

# ===== Mapping video -> keyframes folder =====
video2folder = {}
if os.path.exists(VIDEO2FOLDER_JSON):
    with open(VIDEO2FOLDER_JSON, "r", encoding="utf-8") as f:
        video2folder = json.load(f)

def image_path_from_payload(payload: dict) -> str | None:
    """Dựng đường dẫn ảnh jpg từ payload (video, frame_idx, keyframes) + ROOT_KEYFRAMES."""
    video = payload.get("video")
    frame_idx = payload.get("frame_idx")
    kf_dir = payload.get("keyframes") or video2folder.get(video)
    if not (ROOT_KEYFRAMES and video and isinstance(frame_idx, int) and kf_dir):
        return None
    img_dir = os.path.join(ROOT_KEYFRAMES, kf_dir, "keyframes", video)
    if not os.path.isdir(img_dir):
        return None
    jpgs = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])
    if 0 <= frame_idx < len(jpgs):
        return os.path.join(img_dir, jpgs[frame_idx])
    return None

def query_and_show(q: str, topk: int = TOPK):
    qv = encode_text(q)
    res = client.query_points(
        collection_name=COLLECTION,
        query=qv.tolist(),
        limit=topk,
        with_payload=True
    )
    print(f"\n— Query: {q}")
    for p in res.points:
        img_path = image_path_from_payload(p.payload)
        out = {
            "video": p.payload.get("video"),
            "frame_idx": p.payload.get("frame_idx"),
            "keyframes": p.payload.get("keyframes") or video2folder.get(p.payload.get("video")),
            "feature_path": p.payload.get("feature_path"),
            "image": img_path or "N/A",
            "score": float(p.score),
            "id": p.id
        }
        print(out)
        # Nếu chạy Notebook và muốn xem ảnh:
        # if img_path and os.path.exists(img_path):
        #     display(Image.open(img_path).resize((320, 180)))

if __name__ == "__main__":
    queries = [
        "a cat sitting on a wooden table",
        "a red sports car on a mountain road",
    ]
    for q in queries:
        query_and_show(q)
