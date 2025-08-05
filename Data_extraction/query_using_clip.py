import torch
import open_clip
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from encode_and_insert import model, preprocess, qdrant, collection_name

device = "cuda" if torch.cuda.is_available() else "cpu"

# 🔍 Truy vấn text
text_query = "ferry"
tokenizer = open_clip.get_tokenizer('ViT-B-32')
text = tokenizer([text_query]).to(device)

with torch.no_grad():
    text_vector = model.encode_text(text).cpu().numpy()[0]
    text_vector /= (text_vector**2).sum()**0.5  # Normalize (cosine)

# ✅ Sử dụng search() thay vì query_points()
hits = qdrant.search(
    collection_name=collection_name,
    query_vector=text_vector,
    limit=5
)

print(f"\n🔍 Kết quả cho truy vấn: \"{text_query}\"\n")
for hit in hits:
    print(f"{hit.payload['path']} (score={hit.score:.4f})")
