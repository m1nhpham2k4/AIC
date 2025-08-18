#!/usr/bin/env python3
"""
Ingest multiple .npy embedding files (e.g., ViT-SO400M-SigLIP2-384) into a Qdrant collection,
with optional sidecar path lists to map rows back to original images.

- Mỗi <stem>.npy có shape (N, D) hoặc (D,). Nếu (D,), coi như N=1.
- Nếu có <stem>.paths.txt (mỗi dòng 1 path) hoặc <stem>.paths.json (list string),
  payload của từng point sẽ có thêm: image_path, folder, filename.
- Payload mặc định luôn có: {"file": "<stem>.npy", "row": <index>}.

Usage (local):
  set QDRANT_URL=http://localhost:6333
  # set QDRANT_API_KEY=...   # KHÔNG cần nếu chạy local (free)
  python ingest_qdrant_siglip2_with_paths.py ^
    --data-dir "D:/Summer_2025/AIC/Data_extraction/features" ^
    --collection siglip2_384 ^
    --normalize
"""

import argparse
import os
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Optional, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest


# ---------- Helpers ----------

def iter_vectors_from_npy(file_path: Path) -> Iterable[Tuple[int, np.ndarray]]:
    """
    Yield (row_idx, vector<float32>) từ .npy: (D,) hoặc (N, D)
    """
    arr = np.load(file_path)
    if arr.ndim == 1:
        yield 0, arr.astype(np.float32, copy=False)
    elif arr.ndim == 2:
        for i in range(arr.shape[0]):
            yield i, arr[i].astype(np.float32, copy=False)
    else:
        raise ValueError(f"Unsupported array shape {arr.shape} in {file_path}")


def maybe_l2_normalize(vec: np.ndarray) -> np.ndarray:
    """
    Chuẩn hoá L2 cho 1 vector (hữu ích với cosine).
    """
    n = np.linalg.norm(vec)
    if n == 0:
        return vec
    return vec / n


def detect_dim_from_first_npy(npy_files: List[Path]) -> int:
    if not npy_files:
        raise ValueError("No .npy files found to detect dimension.")
    first = np.load(npy_files[0])
    if first.ndim == 1:
        return int(first.shape[0])
    elif first.ndim == 2:
        return int(first.shape[1])
    else:
        raise ValueError(f"Unsupported array shape {first.shape} in {npy_files[0]}")


def load_paths_sidecar(npy_path: Path) -> Optional[List[str]]:
    """
    Đọc sidecar liệt kê path cho từng hàng:
      - <stem>.paths.txt  : mỗi dòng 1 path (local; nên dùng /)
      - <stem>.paths.json : JSON list string
    """
    txt = npy_path.with_suffix('').with_suffix('.paths.txt')
    js  = npy_path.with_suffix('').with_suffix('.paths.json')
    if txt.exists():
        lines = [ln.strip() for ln in txt.read_text(encoding='utf-8').splitlines() if ln.strip()]
        return lines
    if js.exists():
        import json
        data = json.loads(js.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError(f"{js} must be a JSON list of strings")
        return [str(x) for x in data]
    return None


def payload_from_local_pathlike(p: str) -> dict:
    """
    Tạo payload phụ từ 1 đường dẫn local (tương đối hay tuyệt đối đều được).
    """
    posix = PurePosixPath(p.replace("\\", "/"))
    filename = posix.name
    folder = posix.parent.name if posix.parent else ""
    return {
        "image_path": posix.as_posix(),
        "filename": filename,
        "folder": folder,
    }


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, type=str,
                    help="Folder chứa các <stem>.npy và (tuỳ chọn) <stem>.paths.txt/.json")
    ap.add_argument("--collection", required=True, type=str, help="Tên collection trong Qdrant")
    ap.add_argument("--batch-size", type=int, default=2048, help="Batch size khi upsert")
    ap.add_argument("--normalize", action="store_true", help="L2-normalize vector trước khi upsert (nên dùng cho cosine)")
    ap.add_argument("--recreate", action="store_true", help="Xoá & tạo lại collection (cẩn thận: mất dữ liệu cũ)")
    args = ap.parse_args()

    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    api_key = os.environ.get("QDRANT_API_KEY")

    client = QdrantClient(url=url, api_key=api_key)
    data_dir = Path(args.data_dir)

    # Lấy danh sách .npy
    npy_files = sorted(data_dir.glob("*.npy"))
    if not npy_files:
        raise SystemExit(f"No .npy files found under {data_dir}")

    dim = detect_dim_from_first_npy(npy_files)

    # Tạo/đảm bảo collection
    must_create = True
    try:
        _ = client.get_collection(args.collection)
        must_create = False
    except Exception:
        must_create = True

    if not must_create and args.recreate:
        try:
            client.delete_collection(args.collection)
        except Exception:
            pass
        must_create = True

    if must_create:
        client.recreate_collection(
            collection_name=args.collection,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE),
            optimizers_config=rest.OptimizersConfigDiff(
                memmap_threshold=20000,
                max_optimization_threads=0
                ),
            hnsw_config=rest.HnswConfigDiff(m=16, ef_construct=128),
            quantization_config=None,
            on_disk_payload=False
        )
        print(f"[OK] Created collection '{args.collection}' (dim={dim}, COSINE)")
    else:
        print(f"[OK] Using existing collection '{args.collection}' (assume dim={dim}, COSINE)")

    # Upsert theo batch
    next_id = 0
    ids: List[int] = []
    vecs: List[List[float]] = []
    payloads: List[dict] = []

    total_points = 0

    for npy_path in npy_files:
        rel_npy = str(npy_path.relative_to(data_dir))
        side_paths = load_paths_sidecar(npy_path)

        # kiểm tra sidecar length (nếu có)
        arr = np.load(npy_path)
        n = arr.shape[0] if arr.ndim == 2 else 1
        if side_paths is not None and len(side_paths) != n:
            raise SystemExit(
                f"[ERR] Sidecar length mismatch for {npy_path.name}: "
                f"{len(side_paths)} lines vs N={n}"
            )

        for row_idx, vec in iter_vectors_from_npy(npy_path):
            if args.normalize:
                vec = maybe_l2_normalize(vec)

            pl = {"file": rel_npy, "row": int(row_idx)}

            if side_paths is not None:
                extra = payload_from_local_pathlike(side_paths[row_idx])
                pl.update(extra)

            ids.append(next_id)
            vecs.append(vec.tolist())
            payloads.append(pl)
            next_id += 1

            if len(ids) >= args.batch_size:
                client.upsert(
                    collection_name=args.collection,
                    points=rest.Batch(ids=ids, vectors=vecs, payloads=payloads)
                )
                total_points += len(ids)
                print(f"[UPsert] +{len(ids)} points (through {npy_path.name})  total={total_points}")
                ids.clear()
                vecs.clear()
                payloads.clear()

    if ids:
        client.upsert(
            collection_name=args.collection,
            points=rest.Batch(ids=ids, vectors=vecs, payloads=payloads)
        )
        total_points += len(ids)
        print(f"[UPsert] Final +{len(ids)} points  total={total_points}")

    print("[DONE] Ingest completed.")


if __name__ == "__main__":
    main()
