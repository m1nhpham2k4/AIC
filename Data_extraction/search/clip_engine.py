# Data_extraction/search/clip_engine.py
import os, json
import numpy as np
import torch, open_clip
from qdrant_client import QdrantClient

class ClipSearchEngine:
    def __init__(
        self,
        qdrant_url: str,
        collection: str,
        model_name: str = "ViT-g-14",
        pretrained: str = "laion2b_s34b_b88k",
        device: str | None = None,
        root_keyframes: str | None = None,
        video2folder_json: str | None = None,
    ):
        self.qdrant = QdrantClient(url=qdrant_url)
        self.collection = collection

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, _, _ = open_clip.create_model_and_transforms(
            model_name, pretrained=pretrained, device=self.device
        )
        self.tokenizer = open_clip.get_tokenizer(model_name)

        self.root_keyframes = root_keyframes
        self.video2folder = {}
        if video2folder_json and os.path.exists(video2folder_json):
            with open(video2folder_json, "r", encoding="utf-8") as f:
                self.video2folder = json.load(f)

    @torch.no_grad()
    def _encode_text(self, text: str) -> np.ndarray:
        toks = self.tokenizer([text]).to(self.device)
        feat = self.model.encode_text(toks).float()
        feat /= feat.norm(dim=-1, keepdim=True)
        return feat.cpu().numpy()[0].astype(np.float32)

    def _image_path_from_payload(self, payload: dict) -> str | None:
        video = payload.get("video")
        frame_idx = payload.get("frame_idx")
        kf_dir = payload.get("keyframes") or self.video2folder.get(video)
        if not (self.root_keyframes and video and isinstance(frame_idx, int) and kf_dir):
            return None
        img_dir = os.path.join(self.root_keyframes, kf_dir, "keyframes", video)
        if not os.path.isdir(img_dir):
            return None
        jpgs = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])
        if 0 <= frame_idx < len(jpgs):
            return os.path.join(img_dir, jpgs[frame_idx])
        return None

    def search(self, query: str, topk: int = 5) -> list[dict]:
        qv = self._encode_text(query)
        res = self.qdrant.query_points(
            collection_name=self.collection,
            query=qv.tolist(),
            limit=topk,
            with_payload=True
        )
        out = []
        for p in res.points:
            payload = p.payload or {}
            out.append({
                "id": p.id,
                "score": float(p.score),
                "video": payload.get("video"),
                "frame_idx": payload.get("frame_idx"),
                "keyframes": payload.get("keyframes") or self.video2folder.get(payload.get("video")),
                "feature_path": payload.get("feature_path"),
                "image": self._image_path_from_payload(payload)
            })
        return out
