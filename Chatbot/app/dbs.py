from pymongo import MongoClient
import gridfs
from config import MONGODB_URI

client = MongoClient(MONGODB_URI)

try:
    client.admin.command("ping")
    print("MongoDB connected succesfully")
except Exception as e:
    print('MongoDB connection failed:',e)

db = client["vqa_project"]
fs = gridfs.GridFS(db)