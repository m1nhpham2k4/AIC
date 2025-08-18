from __future__ import annotations
import json
from typing import List, Dict, Any
import numpy as np
from app.config import INDEX_VEC_PATH, INDEX_META_PATH

class IndexStore:
    """
    Load & giữ nguyên bộ index trong RAM (mmap cũng được).
    - VECS: (N, D) float32, đã L2-normalize.
    - META: list[dict] có ít nhất {leaf, n, filename}.
    """
    def __init__(self, vec_path: str = INDEX_VEC_PATH, meta_path: str = INDEX_META_PATH):
        self.vec_path = vec_path
        self.meta_path = meta_path
        self.VECS: np.ndarray = np.load(self.vec_path, mmap_mode="r")  # (N, D)
        self.META: List[Dict[str, Any]] = []
        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    self.META.append(json.loads(line))
        if self.VECS.shape[0] != len(self.META):
            raise RuntimeError(f"Index size mismatch: vecs={self.VECS.shape[0]} meta={len(self.META)}")

    def search_dot(self, qvec: np.ndarray, k: int) -> List[Dict[str, Any]]:
        """Cosine tương đương dot vì đã normalize."""
        sims = self.VECS @ qvec  # (N,)
        k = int(min(k, self.VECS.shape[0]))
        idx = np.argpartition(sims, -k)[-k:]
        idx = idx[np.argsort(sims[idx])[::-1]]
        out: List[Dict[str, Any]] = []
        for i in idx:
            m = self.META[int(i)]
            out.append({
                "leaf": m.get("leaf"),
                "n": m.get("n"),
                "filename": m.get("filename"),
                "score": float(sims[int(i)]),
            })
        return out

# singleton tiện dụng
INDEX = IndexStore()
