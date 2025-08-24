import re
import os
import sqlite3
import ujson
import open_clip
import torch
import numpy as np
import faiss
# from app.utils.languages_translate import translate_text_GoogleTranslate


class FaissSearch:
    
    def __init__(self, load_file_path, is_open_clip=False, nprobe=256):
        """
        load_file_path = {
            "faiss_bin": "D:/.../faiss_clip.bin",
            "sqlite_db": "D:/.../meta.db"
        }
        """
        # --- FAISS ---
        self.faiss_bin = self.load_file_bin(load_file_path["faiss_bin"])
        # set nprobe nếu index là IVF (IndexFlat* sẽ không hỗ trợ, an toàn bỏ qua) 
        try:
            faiss.ParameterSpace().set_index_parameter(self.faiss_bin, "nprobe", nprobe)
        except Exception:
            pass

        # --- device / openclip ---
        print(0)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_open_clip = is_open_clip
        print(is_open_clip)
        if is_open_clip:
            print("((()))")
            self.open_clip_model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name="ViT-SO400M-16-SigLIP2-384",
                pretrained="webli",
                device=self.device
            )
            # self.open_clip_model.eval()
            print("*")
            self.open_clip_tokenizer = open_clip.get_tokenizer("ViT-SO400M-16-SigLIP2-384")

        # --- SQLite ---
        self.sqlite_path = load_file_path.get("sqlite_db")
        self.conn = None
        if self.sqlite_path and os.path.exists(self.sqlite_path):
            self.conn = sqlite3.connect(self.sqlite_path)
            self.conn.row_factory = sqlite3.Row

    def text_search_open_clip(self, text, k=5):
        """
        Encode text bằng OpenCLIP và search trên FAISS index đã nạp trong __init__.
        Trả về list dict {id, score, path, payload}.
        """
        # text = translate_text_GoogleTranslate(text, "en")
        tokens = self.open_clip_tokenizer(text).to(self.device)
        print(1)
        with torch.no_grad():
            text_features = self.open_clip_model.encode_text(tokens)

        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        vec = text_features.detach().cpu().numpy().astype(np.float32)

        index = self.faiss_bin
        D, I = index.search(vec, k)
        print(2)
        return self._lookup_rows(I[0].tolist(), D[0].tolist(), dbsqlite=self.sqlite_path)

    def _lookup_rows(self, indices, scores, dbsqlite=None):
        """
        Map FAISS indices -> rows trong bảng docs(id, path, payload).
        Nếu không có DB, trả về id/score thô.
        """
        conn = self.conn
        temp_conn = None
        if conn is None and dbsqlite:
            temp_conn = sqlite3.connect(dbsqlite)
            temp_conn.row_factory = sqlite3.Row
            conn = temp_conn

        out = []
        if conn is None:
            for s, idx in zip(scores, indices):
                if idx == -1:
                    continue
                out.append({"id": int(idx), "score": float(s), "path": None, "payload": None})
            return out

        try:
            for s, idx in zip(scores, indices):
                if idx == -1:
                    continue
                row = conn.execute(
                    "SELECT path, payload FROM docs WHERE id=?",
                    (int(idx),)
                ).fetchone()
                if row:
                    payload = row["payload"]
                    try:
                        if isinstance(payload, (bytes, bytearray)):
                            payload = payload.decode("utf-8", errors="ignore")
                        payload = ujson.loads(payload) if isinstance(payload, str) else payload
                    except Exception:
                        pass
                    out.append({
                        "id": int(idx),
                        "score": float(s),
                        "path": row["path"],
                        "payload": payload
                    })
        finally:
            if temp_conn is not None:
                temp_conn.close()

        return out
    
    def load_file_bin(self, bin_file):
        return faiss.read_index(bin_file)


# --------- run demo ----------
if __name__ == "__main__":
    path = {
        "faiss_bin": "D:/Summer_2025/AIC/Data_extraction/faiss_clip.bin",
        "sqlite_db": "D:/Summer_2025/AIC/Data_extraction/meta.db"
    }

    search = FaissSearch(path, is_open_clip=True)

    result = search.text_search_open_clip("a man sitting on a motorbike", k=5)
    
    for r in result:
        print(r["score"], r["path"])
