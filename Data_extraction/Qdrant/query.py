import torch, open_clip
import numpy as np
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Kết nối Qdrant
client = QdrantClient(host="localhost", port=6333, prefer_grpc=False)
CACHE_DIR = r"D:Models\open_clip_cache"

# 2. Load model encode query
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-g-14', device=device, pretrained='laion2b_s34b_b88k', cache_dir=CACHE_DIR
)

tokenizer = open_clip.get_tokenizer('ViT-g-14')

def encode_image(path):
    img = Image.open(path).convert("RGB")
    x = preprocess(img).unsqueeze(0).to(device)
    with torch.no_grad():
        f = model.encode_image(x)
        f = f / f.norm(dim=-1, keepdim=True)
    return f.cpu().numpy().astype(np.float32).squeeze()

def encode_text(text):
    tok = tokenizer([text]).to(device)
    with torch.no_grad():
        f = model.encode_text(tok)
        f = f / f.norm(dim=-1, keepdim=True)
    return f.cpu().numpy().astype(np.float32).squeeze()

query_vec = encode_text("a man riding a motorcycle on a highway")

# hits = client.search(
#     collection_name="clip_keyframes",
#     query_vector=query_vec.tolist(),
#     limit=5,
#     with_payload=True,
# )

# for h in hits:
#     print(f"ID: {h.id}, Score: {h.score:.4f}, Payload: {h.payload}")
info = client.get_collection("clip_keyframes")
print(info.vectors_count, info.config.params.vectors)
