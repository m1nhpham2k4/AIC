# pip install faiss-cpu natsort numpy
import os
import json
import numpy as np
from natsort import natsorted
import faiss

# ------------ Cấu hình ------------
EMB_NPY = "D:/Summer_2025/AIC/Data_extraction/feature_new/L21_V001.npy"  # file .npy có shape (N, D)
IMG_DIR  = "D:/Summer_2025/AIC/Data_extraction/Keyframes_2025/Keyframes_L21/keyframes/L21_V001"  # thư mục chứa 001.jpg ... 012.jpg
# INDEX_OUT = "faiss_index_ip.cos"
# MAPPING_OUT = "image_id_mapping.json"  # id (int) -> path

# ------------ Helper ------------
def list_images_sorted(img_dir, exts={".jpg", ".jpeg", ".png"}):
    files = [f for f in os.listdir(img_dir) if os.path.splitext(f.lower())[1] in exts]
    files = natsorted(files)  # sort theo thứ tự tự nhiên: 1,2,10 thay vì 1,10,2
    return [os.path.join(img_dir, f) for f in files]

def load_embeddings(npy_path, mmap=False):
    if mmap:
        return np.load(npy_path, mmap_mode='r')
    return np.load(npy_path)

def ensure_2d(a):
    a = np.asarray(a)
    if a.ndim == 1:
        a = a.reshape(1, -1)
    return a

# ------------ 1) Đọc ảnh & embedding ------------
image_paths = list_images_sorted(IMG_DIR)
emb = load_embeddings(EMB_NPY, mmap=True)   # đọc full .npy (memory-mapped)

emb = np.asarray(emb, dtype="float32")
N, D = emb.shape
print(f"Embeddings: N={N}, D={D}")
print(f"Images    : {len(image_paths)}")

# Kiểm tra khớp số lượng (rất quan trọng)
if len(image_paths) != N:
    raise ValueError(f"Số ảnh ({len(image_paths)}) không khớp số vector ({N}). "
                     f"Hãy đảm bảo thứ tự ảnh chính là thứ tự embed khi tạo .npy.")

faiss.normalize_L2(emb)

index = faiss.IndexFlatIP(D)             # IP cho cosine (đã normalize)
index = faiss.IndexIDMap2(index)         # để add kèm ID tuỳ ý
