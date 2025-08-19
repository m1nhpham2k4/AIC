import argparse, sqlite3, ujson
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
import faiss
import open_clip

# ==== cấu hình ====
INDEX_PATH = "index.faiss"
SQLITE_DB  = "meta.db"
MODEL_NAME = "ViT-SO400M-16-SigLIP2-384"
PRETRAINED = "webli"
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"
USE_COSINE = True  # SigLIP2 dùng cosine

# ==== load model + preprocess ====
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name=MODEL_NAME,
    pretrained=PRETRAINED,
    device=DEVICE
)
model.eval()

# Lấy context length ĐÚNG từ model SigLIP2 (thường = 64)
CTX_LEN = int(model.text.positional_embedding.shape[0])

# Lấy tokenizer phù hợp với model (open-clip tự chọn đúng loại)
tokenizer = open_clip.get_tokenizer(MODEL_NAME)

# Lấy context length thật từ model (SigLIP2 thường = 64)
CTX_LEN = int(model.text.positional_embedding.shape[0])

def tokenize_texts(texts):
    import torch, open_clip
    # Dùng trực tiếp open_clip.tokenize (chuẩn cho open-clip)
    try:
        toks = open_clip.tokenize(texts, context_length=CTX_LEN, truncate=True)
    except TypeError:
        # Fallback cho bản open-clip cũ không có 'truncate'
        toks = open_clip.tokenize(texts, context_length=CTX_LEN)
        # đảm bảo đúng [B, CTX_LEN]
        if toks.shape[1] > CTX_LEN:
            toks = toks[:, :CTX_LEN]
        elif toks.shape[1] < CTX_LEN:
            pad = torch.zeros((toks.shape[0], CTX_LEN - toks.shape[1]), dtype=toks.dtype)
            toks = torch.cat([toks, pad], dim=1)
    return toks



@torch.no_grad()
def embed_text(texts):
    toks = tokenize_texts(texts).to(DEVICE)
    feats = model.encode_text(toks).float()
    if USE_COSINE:
        feats = F.normalize(feats, dim=-1)
    return feats.cpu().numpy().astype("float32")

@torch.no_grad()
def embed_images(images):
    batch = torch.stack([preprocess(img) for img in images]).to(DEVICE)
    feats = model.encode_image(batch).float()
    if USE_COSINE:
        feats = F.normalize(feats, dim=-1)
    return feats.cpu().numpy().astype("float32")

# ==== load FAISS + DB ====
index = faiss.read_index(INDEX_PATH)
# tăng recall nếu cần
faiss.ParameterSpace().set_index_parameter(index, "nprobe", 32)

conn = sqlite3.connect(SQLITE_DB)

def search_vec(vec, k=10):
    D, I = index.search(vec, k)
    out = []
    for s, idx in zip(D[0].tolist(), I[0].tolist()):
        if idx == -1: continue
        row = conn.execute("SELECT path, payload FROM docs WHERE id=?", (int(idx),)).fetchone()
        if row:
            out.append({"id": int(idx), "score": float(s), "path": row[0], "payload": ujson.loads(row[1])})
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", type=str, help="truy vấn văn bản (text→image)")
    ap.add_argument("--image", type=str, help="đường dẫn ảnh (image→image)")
    ap.add_argument("-k", type=int, default=10)
    args = ap.parse_args()

    if args.text:
        qv = embed_text([args.text])
        res = search_vec(qv, k=args.k)
        print(f"\nTop-{args.k} cho TEXT: {args.text}")
        for r in res:
            print(f"{r['score']:.4f}\t{r['path']}")

    if args.image:
        img = Image.open(args.image).convert("RGB")
        qv = embed_images([img])
        res = search_vec(qv, k=args.k)
        print(f"\nTop-{args.k} cho IMAGE: {args.image}")
        for r in res:
            print(f"{r['score']:.4f}\t{r['path']}")
