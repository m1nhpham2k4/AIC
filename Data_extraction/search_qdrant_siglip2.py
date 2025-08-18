#!/usr/bin/env python3
"""
Search a Qdrant collection using a query vector (e.g., another SigLIP2 embedding).

Usage:
  export QDRANT_URL="http://localhost:6333"
  # export QDRANT_API_KEY="..."
  python search_qdrant_siglip2.py --collection siglip2_384 --query-npy ./query.npy --top-k 10 --normalize
"""

import argparse
import os
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest


def maybe_l2_normalize(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec / norm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", type=str, required=True)
    parser.add_argument("--query-npy", type=str, required=True, help="Path to .npy file containing (D,) or (1, D) query vector")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--normalize", action="store_true", help="L2-normalize the query vector (useful for cosine)")
    args = parser.parse_args()

    url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    api_key = os.environ.get("QDRANT_API_KEY")

    client = QdrantClient(url=url, api_key=api_key)

    q = np.load(Path(args.query_npy))
    if q.ndim == 2:
        if q.shape[0] != 1:
            raise SystemExit(f"Expected single query vector; got shape {q.shape}")
        q = q[0]
    if q.ndim != 1:
        raise SystemExit(f"Expected 1D query vector; got shape {q.shape}")

    q = q.astype(np.float32, copy=False)
    if args.normalize:
        q = maybe_l2_normalize(q)

    results = client.search(
        collection_name=args.collection,
        query_vector=q.tolist(),
        limit=args.top_k,
        with_payload=True
    )

    print(f"Top-{args.top_k} results:")
    for r in results:
        file = r.payload.get("file")
        row = r.payload.get("row")
        print(f"ID={r.id} score={r.score:.6f} file={file} row={row}")


if __name__ == "__main__":
    main()
