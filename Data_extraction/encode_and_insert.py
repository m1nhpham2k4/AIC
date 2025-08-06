import os
import uuid
from PIL import Image
import torch
import open_clip
from torchvision import transforms
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from pathlib import Path

# 1️⃣ Load model CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', pretrained='laion2b_s34b_b79k', device=device
)

# 2️⃣ Kết nối Qdrant
qdrant = QdrantClient(host="localhost", port=6333)
collection_name = "clip_image_vectors"

# Tạo collection nếu chưa có
if not qdrant.collection_exists(collection_name):
    qdrant.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE)
    )

# 3️⃣ Load ảnh & encode
BASE_DIR = Path(__file__).resolve().parent / "output_videos"
points = []

for folder in sorted(os.listdir(BASE_DIR)):
    folder_path = os.path.join(BASE_DIR, folder)
    if not os.path.isdir(folder_path):
        continue

    for filename in sorted(os.listdir(folder_path)):
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        img_path = os.path.join(folder_path, filename)

        try:
            image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
            with torch.no_grad():
                vec = model.encode_image(image).cpu().numpy()[0]
                vec /= (vec**2).sum()**0.5  # Normalize

            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "folder": folder,
                    "filename": filename,
                    "path": img_path
                }
            )
            points.append(point)
            print(f"✅ Encoded: {img_path}")

        except Exception as e:
            print(f"❌ Lỗi ảnh {img_path}: {e}")

# 4️⃣ Lưu vào Qdrant
if points:
    qdrant.upsert(collection_name=collection_name, points=points)
    print(f"\n✅ Đã thêm {len(points)} vector vào Qdrant")
else:
    print("⚠️ Không có ảnh hợp lệ nào được xử lý")
