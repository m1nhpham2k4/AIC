# save thành file: check_count.py
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import os

client = QdrantClient(url=os.environ.get("QDRANT_URL","http://localhost:6333"))
print(client.get_collection("siglip2_384_v2 "))
print("points:", client.count(collection_name="siglip2_384", count_filter=None, exact=True).count)
