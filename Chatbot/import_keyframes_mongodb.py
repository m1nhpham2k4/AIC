import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs

# Load env
load_dotenv()
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

MONGODB_URI = f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.s84nghm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'

client = MongoClient(MONGODB_URI)
BASE_DIR = "Keyframes"

try:
    client.admin.command("ping")
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

db = client["vqa_project"]
fs = gridfs.GridFS(db)
json_collection = db["keyframes_json"]

def import_images_and_build_structure(base_dir):
    result = {"Keyframes": []}

    for level2 in sorted(os.listdir(base_dir)):
        level2_path = os.path.join(base_dir, level2)
        if not os.path.isdir(level2_path):
            continue

        level2_entry = []

        for level3 in sorted(os.listdir(level2_path)):
            level3_path = os.path.join(level2_path, level3)
            if not os.path.isdir(level3_path):
                continue

            image_filenames = []

            for filename in sorted(os.listdir(level3_path)):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    full_path = os.path.join(level3_path, filename)

                    # Upload vào GridFS nếu chưa tồn tại
                    if not fs.find_one({
                        "filename": filename,
                        "metadata.level2": level2,
                        "metadata.level3": level3
                    }):
                        with open(full_path, "rb") as f:
                            fs.put(
                                f.read(),
                                filename=filename,
                                content_type="image/png",
                                metadata={
                                    "level1": "Keyframes",
                                    "level2": level2,
                                    "level3": level3
                                }
                            )
                    image_filenames.append(filename)

            if image_filenames:
                level2_entry.append({level3: image_filenames})

        result["Keyframes"].append({level2: level2_entry})

    return result

if __name__ == "__main__":
    data = import_images_and_build_structure(BASE_DIR)

    with open("keyframes_structure.json", "w") as f:
        json.dump(data, f, indent=2)

    json_collection.delete_many({})
    json_collection.insert_one(data)

    print("✅ Ảnh đã được upload vào GridFS và metadata lưu vào MongoDB!")
