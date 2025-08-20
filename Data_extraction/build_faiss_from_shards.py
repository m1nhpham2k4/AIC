# build_faiss_from_shards.py
import argparse, os, math, glob, sqlite3, ujson
import numpy as np
import faiss
from tqdm import tqdm

def list_shards(data_dir):
    npys = sorted(glob.glob(os.path.join(data_dir, "*.npy")))
    shards = []
    for f in npys:
        stem = os.path.splitext(os.path.basename(f))[0]
        ptxt = os.path.join(data_dir, stem + ".paths.txt")
        if not os.path.isfile(ptxt):
            raise FileNotFoundError(f"Thiếu paths cho {f}: {ptxt}")
        shards.append((f, ptxt, stem))
    if not shards:
        raise FileNotFoundError("Không tìm thấy *.npy trong thư mục.")
    return shards

def shard_sizes(shards):
    sizes = []
    D = None
    for npy, _, _ in shards:
        X = np.load(npy, mmap_mode="r")
        if X.ndim != 2:
            raise ValueError(f"{npy} không phải ma trận [n, d]")
        if D is None: D = X.shape[1]
        elif D != X.shape[1]:
            raise ValueError(f"Chiều D không khớp: {npy} có D={X.shape[1]}, expected {D}")
        sizes.append(X.shape[0])
    N = int(sum(sizes))
    return N, D, sizes

def choose_params(N, D, ivf_flat: bool):
    nlist = int(max(4096, min(65536, round(math.sqrt(N)))))
    if ivf_flat:
        return {"type": "ivf_flat", "nlist": nlist}
    # PQ params
    m = 64
    for cand in [96, 80, 72, 64, 56, 48, 40, 32, 24, 16, 8]:
        if cand <= D:
            m = cand
            break
    return {"type": "ivf_pq", "nlist": nlist, "m": m, "nbits": 8}

def build_index(args):
    shards = list_shards(args.data_dir)
    N, D, sizes = shard_sizes(shards)
    print(f"Found {len(shards)} shards | Total N={N:,} | D={D}")

    # kiểm tra paths khớp số dòng
    for (_, ptxt, stem), n in zip(shards, sizes):
        with open(ptxt, "r", encoding="utf-8") as f:
            lines = sum(1 for _ in f)
        if lines != n:
            raise ValueError(f"{stem}.paths.txt có {lines} dòng nhưng {stem}.npy có {n} vectors")

    params = choose_params(N, D, args.ivf_flat)
    print("Index params:", params)

    # tạo index
    metric = faiss.METRIC_INNER_PRODUCT if args.use_cosine else faiss.METRIC_L2
    quantizer = faiss.IndexFlatIP(D) if args.use_cosine else faiss.IndexFlatL2(D)

    if params["type"] == "ivf_flat":
        base = faiss.IndexIVFFlat(quantizer, D, params["nlist"], metric)
    else:
        base = faiss.IndexIVFPQ(quantizer, D, params["nlist"], params["m"], params["nbits"], metric)
        opq = faiss.OPQMatrix(D, params["m"])
        base = faiss.IndexPreTransform(opq, base)

    index = faiss.IndexIDMap2(base)

    # ===== Train (chuẩn hoá tại đây nếu dùng cosine) =====
    train_sz = min(200_000, N)
    print(f"Sampling {train_sz} vectors for training…")
    # lấy mẫu đều từ các shard
    need = train_sz
    sample = np.empty((0, D), dtype="float16")
    for npy, _, _ in shards:
        if need <= 0: break
        X = np.load(npy, mmap_mode="r")
        step = max(1, X.shape[0] // max(1, min(need, X.shape[0])))
        take_idx = np.arange(0, X.shape[0], step, dtype=int)
        if take_idx.size > need:
            take_idx = take_idx[:need]
        blk = np.asarray(X[take_idx], dtype="float16", order="C")
        sample = np.vstack([sample, blk])
        need -= blk.shape[0]

    if args.use_cosine:
        faiss.normalize_L2(sample)

    print("Training index…")
    index.train(sample)

    # ===== Add theo batch (chuẩn hoá từng batch) =====
    print("Adding vectors in batches…")
    id_offset = 0
    batch = args.batch
    for npy, _, _ in shards:
        X = np.load(npy, mmap_mode="r")
        n = X.shape[0]
        ids = np.arange(id_offset, id_offset + n, dtype=np.int64)
        for s in tqdm(range(0, n, batch), desc=os.path.basename(npy)):
            e = min(s + batch, n)
            xb = np.asarray(X[s:e], dtype="float16", order="C")
            if args.use_cosine:
                faiss.normalize_L2(xb)
            index.add_with_ids(xb, ids[s:e])
        id_offset += n

    # lưu index
    faiss.write_index(index, args.index_out)
    print("Saved index to", args.index_out)

    # lưu metadata
    print("Writing SQLite metadata…")
    conn = sqlite3.connect(args.sqlite_db)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS docs(
      id INTEGER PRIMARY KEY,
      path TEXT,
      payload TEXT
    )""")
    rows, id_base = [], 0
    for _, ptxt, _ in shards:
        with open(ptxt, "r", encoding="utf-8") as f:
            for line in f:
                rows.append((id_base, line.strip(), ujson.dumps({})))
                id_base += 1
        if len(rows) >= 200000:
            conn.executemany("INSERT OR REPLACE INTO docs(id, path, payload) VALUES(?,?,?)", rows)
            conn.commit()
            rows = []
    if rows:
        conn.executemany("INSERT OR REPLACE INTO docs(id, path, payload) VALUES(?,?,?)", rows)
        conn.commit()
    conn.close()
    print("Saved metadata to", args.sqlite_db)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="Thư mục chứa *.npy và *.paths.txt")
    ap.add_argument("--index-out", default="index.faiss")
    ap.add_argument("--sqlite-db", default="meta.db")
    ap.add_argument("--batch", type=int, default=100_000)
    ap.add_argument("--use-cosine", action="store_true", help="Dùng cosine (normalize + Inner Product)")
    ap.add_argument("--ivf-flat", action="store_true", help="Dùng IVF-Flat (không PQ)")
    args = ap.parse_args()
    build_index(args)
