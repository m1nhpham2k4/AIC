import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs

# Load biến môi trường từ .env
load_dotenv()
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

# Kết nối MongoDB
MONGODB_URI = f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.s84nghm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGODB_URI)

# ✅ Thư mục mới: Data_extraction/output_videos (tính từ cùng cấp với script)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Data_extraction", "output_videos"))
print("📂 Đang duyệt thư mục:", BASE_DIR)

# Ping thử MongoDB
try:
    client.admin.command("ping")
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Chuẩn bị DB và GridFS
db = client["vqa_project"]
fs = gridfs.GridFS(db)
json_collection = db["keyframes_json"]

def import_images_and_build_structure(base_dir):
    result = {"output_video": []}  # 🟢 Đổi key gốc từ "Keyframes" → "output_video"

    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        image_filenames = []

        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(folder_path, filename)

                # Upload vào GridFS nếu chưa tồn tại
                if not fs.find_one({
                    "filename": filename,
                    "metadata.level2": folder
                }):
                    with open(full_path, "rb") as f:
                        fs.put(
                            f.read(),
                            filename=filename,
                            content_type="image/jpeg",
                            metadata={
                                "level1": "output_video",
                                "level2": folder
                            }
                        )
                image_filenames.append(filename)

        if image_filenames:
            result["output_video"].append({folder: image_filenames})

    return result

if __name__ == "__main__":
    data = import_images_and_build_structure(BASE_DIR)

    # Ghi metadata ra JSON
    with open("keyframes_structure.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Ghi vào MongoDB
    json_collection.delete_many({})
    json_collection.insert_one(data)

    print("✅ Ảnh đã được upload vào GridFS và metadata lưu vào MongoDB!")
