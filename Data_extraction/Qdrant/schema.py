import qdrant_client
from qdrant_client import QdrantClient

print("qdrant-client version:", qdrant_client.__version__)

client = QdrantClient(host="localhost", port=6333, prefer_grpc=False)  # dùng HTTP để thấy lỗi rõ
print("Server version:", client.get_version())

info = client.get_collection("clip_keyframes")
print("== COLLECTION INFO ==")
print(info)

# In vector schema để biết single hay named vectors
try:
    vectors_schema = info.config.params.vectors  # client mới
except AttributeError:
    vectors_schema = info.result.config.params.vectors  # client cũ
print("== VECTOR SCHEMA ==", vectors_schema)
