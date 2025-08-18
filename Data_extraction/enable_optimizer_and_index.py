from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
import os, time

COLL = "siglip2_384_v2"  # đổi nếu bạn dùng tên khác
URL  = os.environ.get("QDRANT_URL", "http://localhost:6333")

c = QdrantClient(url=URL)

# 1) Bật optimizer (2 threads là hợp lý; tùy CPU bạn có thể tăng)
c.update_collection(
    collection_name=COLL,
    optimizer_config=rest.OptimizersConfigDiff(
        max_optimization_threads=2
    )
)
print("Optimizer enabled.")

# 2) (khuyến nghị) Tạo index cho payload để filter nhanh
try:
    c.create_payload_index(COLL, "folder",   rest.PayloadSchemaType.KEYWORD)
    c.create_payload_index(COLL, "filename", rest.PayloadSchemaType.KEYWORD)
    print("Payload indexes created.")
except Exception as e:
    print("Payload index note:", e)

# 3) Poll tiến độ build HNSW
for _ in range(120):  # ~ 10 phút nếu sleep 5s
    info = c.get_collection(COLL)
    print(f"status={info.status} indexed={info.indexed_vectors_count} points={info.points_count} segments={info.segments_count}")
    if str(info.status).endswith("GREEN") and (info.indexed_vectors_count or 0) >= (info.points_count or 0):
        print("Index ready.")
        break
    time.sleep(5)
