from pymongo import MongoClient
import gridfs
import certifi
from config import MONGODB_URI

# Bổ sung các đối số tls=True và tlsCAFile để dùng chứng chỉ đáng tin cậy
client = MongoClient(MONGODB_URI, tls=True, tlsCAFile=certifi.where())

try:
    client.admin.command("ping")
    print("MongoDB connected successfully")
except Exception as e:
    print('MongoDB connection failed:', e)

db = client["vqa_project"]
fs = gridfs.GridFS(db)
