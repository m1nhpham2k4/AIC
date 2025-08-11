# app/services/clip_search_service.py
import os
from pathlib import Path
import argparse
import time

# Import engine CLIP
# Đảm bảo đường dẫn Data_extraction nằm cùng cấp với thư mục app/
ROOT_DIR = Path(__file__).resolve().parents[1]  # .../AIC
ENGINE_PATH = ROOT_DIR / "Data_extraction" / "search"
if str(ROOT_DIR) not in os.sys.path:
    os.sys.path.append(str(ROOT_DIR))
if str(ENGINE_PATH) not in os.sys.path:
    os.sys.path.append(str(ENGINE_PATH))

from Data_extraction.search.clip_engine import ClipSearchEngine  # noqa: E402

# Singleton lười khởi tạo (lazy init) để tránh block lúc import
_engine = None

def get_engine() -> ClipSearchEngine:
    """Khởi tạo engine lần đầu tiên khi cần."""
    global _engine
    if _engine is None:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        collection = os.getenv("CLIP_COLLECTION", "clip_ViT_g_14_cosine")
        model_name = os.getenv("CLIP_MODEL_NAME", "ViT-g-14")
        pretrained = os.getenv("CLIP_PRETRAINED", "laion2b_s34b_b88k")
        device = os.getenv("CLIP_DEVICE")  # "cuda" / "cpu" / None -> auto

        # Mặc định trỏ về Data_extraction/Keyframes_test
        root_keyframes = os.getenv(
            "ROOT_KEYFRAMES",
            str(ROOT_DIR / "Data_extraction" / "Keyframes_test")
        )
        video2folder_json = os.getenv(
            "VIDEO2FOLDER_JSON",
            str(ROOT_DIR / "Data_extraction" / "video2folder.json")
        )

        # TIP: nếu chỉ test nhanh, dùng model nhẹ để load nhanh:
        # model_name = os.getenv("CLIP_MODEL_NAME", "ViT-B-32")
        # pretrained = os.getenv("CLIP_PRETRAINED", "openai")

        _engine = ClipSearchEngine(
            qdrant_url=qdrant_url,
            collection=collection,
            model_name=model_name,
            pretrained=pretrained,
            device=device,
            root_keyframes=root_keyframes,
            video2folder_json=video2folder_json,
        )
    return _engine

def search_clip(query: str, topk: int = 12):
    """API mỏng để routes gọi."""
    return get_engine().search(query, topk=topk)

def _diagnose_collection_and_model():
    """
    In ra thông tin Qdrant collection (size, distance) và số chiều vector của model,
    để phát hiện mismatch (nguồn gây lỗi OutputTooSmall/500).
    """
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
        coll = os.getenv("CLIP_COLLECTION", "clip_ViT_g_14_cosine")
        info = client.get_collection(coll)
        size = info.config.params.vectors.size
        dist = info.config.params.vectors.distance
        print(f"[Qdrant] collection={coll}, vectors.size={size}, distance={dist}, vectors_count={info.vectors_count}")
    except Exception as e:
        print(f"[Qdrant] Không đọc được thông tin collection: {e}")
        size = None

    try:
        eng = get_engine()
        # ép encode thử để biết dim
        import open_clip, torch
        tok = open_clip.get_tokenizer(os.getenv("CLIP_MODEL_NAME", "ViT-g-14"))(["test"])
        with torch.no_grad():
            feat = eng.model.encode_text(tok.to(eng.device)).float()
            feat = feat / feat.norm(dim=-1, keepdim=True)
        qdim = int(feat.shape[-1])
        print(f"[Model] name={os.getenv('CLIP_MODEL_NAME','ViT-g-14')}, pretrained={os.getenv('CLIP_PRETRAINED','laion2b_s34b_b88k')}, query_dim={qdim}")
    except Exception as e:
        print(f"[Model] Không kiểm tra được số chiều: {e}")
        qdim = None

    if size is not None and qdim is not None and size != qdim:
        print(f"[WARN] MISMATCH: Qdrant size={size} khác query_dim={qdim}. Cần đổi model hoặc recreate collection!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Self-test CLIP search engine (no server).")
    parser.add_argument("--q", "--query", dest="query", default="a man riding a motorcycle on a highway", help="Câu query để test")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    print("== Warmup engine ==")
    t0 = time.time()
    eng = get_engine()
    print(f"Engine ready in {(time.time()-t0):.2f}s, device={eng.device}")

    _diagnose_collection_and_model()

    print(f"\n== Search: {args.query!r}, topk={args.topk} ==")
    t1 = time.time()
    try:
        results = eng.search(args.query, topk=args.topk)
        dt = time.time()-t1
        print(f"Returned {len(results)} results in {dt:.2f}s")
        for i, r in enumerate(results, 1):
            img = r.get("image")
            exists = os.path.exists(img) if img else False
            print(f"{i:02d}. score={r.get('score'):.4f} video={r.get('video')} frame={r.get('frame_idx')} image={img} exists={exists}")
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        print("→ Gợi ý: kiểm tra Qdrant URL, collection name, và MISMATCH số chiều (xem phần [WARN] ở trên).")
