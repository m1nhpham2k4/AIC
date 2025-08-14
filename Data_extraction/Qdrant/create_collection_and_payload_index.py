from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance, VectorParams, OptimizersConfigDiff, HnswConfigDiff,
    ScalarQuantization, ScalarQuantizationConfig, CompressionRatio
)

client = QdrantClient(url="https://6333-m1nhpham2k4-aic-76zktre511o.ws-us121.gitpod.io/")

VECTOR_SIZE_VISUAL = 1152
VECTOR_SIZE_TEXT = 1152

client.recreate_collection(
    collection_name="frames",
    vectors_config={
        "visual": VectorParams(size=VECTOR_SIZE_VISUAL, distance=Distance.COSINE),
        "text_asr": VectorParams(size=VECTOR_SIZE_TEXT, distance=Distance.COSINE),
        "text_ocr": VectorParams(size=VECTOR_SIZE_TEXT, distance=Distance.COSINE),
        "text_tags": VectorParams(size=VECTOR_SIZE_TEXT, distance=Distance.COSINE),
    },
    hnsw_config=HnswConfigDiff(m=32, ef_construct=256),  # tốc độ/gtr nhớ vs độ chính xác
    optimizers_config=OptimizersConfigDiff(memmap_threshold=20000),
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(always_ram=True, compression=CompressionRatio.x4)
    )
)