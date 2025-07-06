import cv2
import torch
import clip
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

# Thiết bị
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model CLIP
model, preprocess = clip.load("ViT-B/32", device=device)

# Đọc video
cap = cv2.VideoCapture("video.mp4")
frames, features = [], []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img)
    image_input = preprocess(pil_img).unsqueeze(0).to(device)

    with torch.no_grad():
        feat = model.encode_image(image_input).cpu().numpy().flatten()

    frames.append(frame)
    features.append(feat)

cap.release()

# KMeans clustering
features = np.array(features)
n_clusters = 10
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
kmeans.fit(features)

# Tìm frame gần nhất với mỗi tâm cụm
keyframe_indices = []
for center in kmeans.cluster_centers_:
    distances = np.linalg.norm(features - center, axis=1)
    closest_idx = np.argmin(distances)
    keyframe_indices.append(closest_idx)

# Lưu keyframes
for i, idx in enumerate(sorted(set(keyframe_indices))):
    cv2.imwrite(f"keyframe_{i}.jpg", frames[idx])
