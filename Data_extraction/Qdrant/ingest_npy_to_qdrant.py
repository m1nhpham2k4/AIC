# ingest_npy_to_qdrant.py
import os, uuid, json, argparse
import numpy as np
from tqdm import tqdm
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature_dir", required=True,
                    help="Thư mục chứa *.npy và video2folder.json (ví dụ: feature_ViT_G_14)")
    ap.add_argument("--collection", default="clip_keyframes",
                    help="Tên collection Qdrant")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=6333)
    ap.add_argument("--recreate", action="store_true", help="Xoá & tạo lại collection")
    ap.add_argument("--batch", type=int, default=4096, help="Kích thước batch upsert")
    args = ap.parse_args()

    feature_dir = args.feature_dir
    coll = args.collection

    # Kết nối Qdrant
    client = QdrantClient(host=args.host, port=args.port, prefer_grpc=True)

    # Tìm 1 file mẫu để lấy D
    npy_files = [f for f in os.listdir(feature_dir) if f.endswith(".npy")]
    if not npy_files:
        raise RuntimeError("Không thấy file .npy nào trong thư mục!")

    sample = np.load(os.path.join(feature_dir, npy_files[0]))
    if sample.ndim != 2:
        raise RuntimeError(f"File mẫu có shape {sample.shape}, cần dạng (K, D)")

    D = int(sample.shape[1])

    # Tạo (hoặc recreate) collection
    if args.recreate and client.collection_exists(coll):
        client.delete_collection(collection_name=coll)

    if not client.collection_exists(coll):
        client.recreate_collection(
            collection_name=coll,
            vectors_config=VectorParams(size=D, distance=Distance.COSINE),
        )

    # đọc mapping folder
    v2f_path = os.path.join(feature_dir, "video2folder.json")
    video2folder = {}
    if os.path.exists(v2f_path):
        with open(v2f_path, "r", encoding="utf-8") as f:
            video2folder = json.load(f)

    points_buf = []
    total_points = 0

    for fname in tqdm(sorted(npy_files), desc="Index videos"):
        video_id = os.path.splitext(fname)[0]           # ví dụ "L01_V001"
        arr = np.load(os.path.join(feature_dir, fname)) # (K, D)
        if arr.dtype != np.float32:
            arr = arr.astype(np.float32, copy=False)

        folder = video2folder.get(video_id)

        # mỗi hàng = 1 keyframe
        for frame_idx, vec in enumerate(arr):
            payload = {
                "video_id": video_id,
                "frame_idx": int(frame_idx),
                "folder": folder
            }
            points_buf.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec.tolist(),
                    payload=payload
                )
            )

            if len(points_buf) >= args.batch:
                client.upsert(collection_name=coll, points=points_buf)
                total_points += len(points_buf)
                points_buf.clear()

    if points_buf:
        client.upsert(collection_name=coll, points=points_buf)
        total_points += len(points_buf)
        points_buf.clear()

    # (tuỳ chọn) tối ưu HNSW sau khi nạp
    client.update_collection(
        collection_name=coll,
        hnsw_config={"m": 32, "ef_construct": 128},
    )

    print(f"✅ Đã nạp xong {total_points} keyframes vào collection '{coll}' (D={D}).")

if __name__ == "__main__":
    main()
