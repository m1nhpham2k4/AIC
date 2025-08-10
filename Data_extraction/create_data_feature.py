# create_data_feature.py
import os
import glob
import json
import numpy as np
from tqdm import tqdm

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# ========= CẤU HÌNH =========
USE_EMBEDDED   = False
QDRANT_PATH    = r"./Qdrant/qdrant"
QDRANT_URL     = "http://localhost:6333"
API_KEY        = None

COLLECTION     = "clip_ViT_g_14_cosine"   # 1024d + COSINE
FEATURE_DIM    = 1024
FEATURES_DIR   = r"./feature_Vit_G_14"    # nơi chứa các .npy
VIDEO2FOLDER_JSON = r"./video2folder.json"  # {"L01_V001":"Keyframes_L01", ...}

BATCH_SIZE     = 1000
DISTANCE       = Distance.COSINE
NORMALIZE      = True

# ========= KẾT NỐI =========
if USE_EMBEDDED:
    os.makedirs(QDRANT_PATH, exist_ok=True)
    client = QdrantClient(path=QDRANT_PATH)
else:
    # Bật prefer_grpc=True nếu bạn đã publish gRPC: -p 6334:6334
    client = QdrantClient(url=QDRANT_URL, api_key=API_KEY)  # , prefer_grpc=True

# ========= COLLECTION =========
if not client.collection_exists(COLLECTION):
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=FEATURE_DIM, distance=DISTANCE),
    )
    print(f"✅ Created collection: {COLLECTION}")
else:
    print(f"ℹ️ Collection đã tồn tại: {COLLECTION}")

# ========= LOAD MAPPING =========
video2folder = {}
if os.path.exists(VIDEO2FOLDER_JSON):
    with open(VIDEO2FOLDER_JSON, "r", encoding="utf-8") as f:
        video2folder = json.load(f)

# ========= NẠP VECTOR (ĐỆ QUY) =========
if not os.path.isdir(FEATURES_DIR):
    raise FileNotFoundError(f"Không thấy thư mục: {FEATURES_DIR}")

all_npy = sorted(glob.glob(os.path.join(FEATURES_DIR, "**", "*.npy"), recursive=True))
print("TOTAL .npy files found:", len(all_npy))

points_buffer = []
next_id = 0
total_upserted = 0

for feature_path in tqdm(all_npy, desc="npy files"):
    feats = np.load(feature_path, mmap_mode="r").astype(np.float32)

    # (N, D) hoặc (D,)
    if feats.ndim == 1:
        feats = feats.reshape(1, -1)

    if feats.shape[1] != FEATURE_DIM:
        raise ValueError(
            f"Feature size mismatch in {feature_path}: expect {FEATURE_DIM}, got {feats.shape[1]}"
        )

    if NORMALIZE:
        norms = np.linalg.norm(feats, axis=1, keepdims=True) + 1e-12
        feats = feats / norms

    # tên video từ file .npy (vd: L05_V005.npy -> L05_V005)
    video = os.path.splitext(os.path.basename(feature_path))[0]
    kf_dir = video2folder.get(video)  # ví dụ 'Keyframes_L05' (nếu có trong JSON)

    n_vec = feats.shape[0]
    ids = np.arange(next_id, next_id + n_vec, dtype=np.int64)

    # tạo payload/point cho từng frame
    for j, pid in enumerate(ids):
        payload = {
            "video": video,
            "frame_idx": int(j),
            "feature_path": feature_path,
        }
        if kf_dir is not None:
            payload["keyframes"] = kf_dir

        points_buffer.append(
            PointStruct(
                id=int(pid),
                vector=feats[j].tolist(),
                payload=payload
            )
        )

        if len(points_buffer) >= BATCH_SIZE:
            client.upsert(collection_name=COLLECTION, points=points_buffer, wait=True)
            total_upserted += len(points_buffer)
            points_buffer.clear()

    next_id += n_vec

# Flush phần cuối
if points_buffer:
    client.upsert(collection_name=COLLECTION, points=points_buffer, wait=True)
    total_upserted += len(points_buffer)
    points_buffer.clear()

print("Total points attempted to upsert:", total_upserted)
cnt = client.count(COLLECTION, exact=True).count
print("Count after upsert:", cnt)

# ========= TRUY VẤN KIỂM TRA NHANH =========
sample_vec = np.random.randn(FEATURE_DIM).astype(np.float32)
if NORMALIZE:
    sample_vec /= (np.linalg.norm(sample_vec) + 1e-12)

resp = client.query_points(
    collection_name=COLLECTION,
    query=sample_vec.tolist(),
    limit=5,
    with_payload=True
)

print("— Top 5 hits —")
for p in getattr(resp, "points", resp):
    print(p.id, float(p.score), p.payload)
