from qdrant_client import QdrantClient
import numpy as np
import open_clip, torch

COLLECTION = "clip_ViT_g_14_cosine"
client = QdrantClient(url="http://localhost:6333")

# 1) Xem schema collection (size & distance)
info = client.get_collection(COLLECTION)
print("vectors_count=", info.vectors_count)
print("size=", info.config.params.vectors.size)        # <-- số chiều trong Qdrant
print("distance=", info.config.params.vectors.distance)

# 2) Encode thử 1 query để xem chiều của model bạn đang dùng
model, _, _ = open_clip.create_model_and_transforms("ViT-g-14", pretrained="laion2b_s34b_b88k", device="cpu")
tok = open_clip.get_tokenizer("ViT-g-14")(["test"])
with torch.no_grad():
    feat = model.encode_text(tok).float()
    feat = feat / feat.norm(dim=-1, keepdim=True)
print("query_dim=", feat.shape[-1])                    # <-- số chiều của vector query
