from typing import Dict, List, Optional
import boto3
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_REGION, ROOT_PREFIX, VIDEOS_ROOT_PREFIX
from botocore.exceptions import ClientError
import csv, io


router = APIRouter(prefix="/keyframes", tags=["keyframes"])
print(f"Using S3 root prefix hehe: {ROOT_PREFIX}")
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def _list_common_prefixes(prefix: str) -> List[str]:
    """Liệt kê folder con (S3 common prefixes) dưới prefix"""
    prefixes, token = [], None
    while True:
        params = dict(Bucket=AWS_BUCKET_NAME, Prefix=prefix, Delimiter="/")
        if token:
            params["ContinuationToken"] = token
        resp = s3.list_objects_v2(**params)
        for p in resp.get("CommonPrefixes", []):
            pr = p.get("Prefix")
            if pr:
                prefixes.append(pr)
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return prefixes

def _list_objects(prefix: str, suffixes=(".jpg", ".jpeg", ".png")) -> List[str]:
    """Liệt kê mọi object (lọc ảnh) dưới prefix"""
    keys, token = [], None
    while True:
        params = dict(Bucket=AWS_BUCKET_NAME, Prefix=prefix)
        if token:
            params["ContinuationToken"] = token
        resp = s3.list_objects_v2(**params)
        for obj in resp.get("Contents", []):
            k = obj.get("Key")
            if k and k.lower().endswith(suffixes):
                keys.append(k)
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return keys

def _sign(key: str, ttl: int = 3600) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_BUCKET_NAME, "Key": key},
        ExpiresIn=ttl,
    )

@router.get("/folders")
def list_folders():
    """Trả về danh sách 'Keyframes_Lxx' ở cấp đầu"""
    try:
        lvl_prefixes = _list_common_prefixes(ROOT_PREFIX)
        folders = [
            p[len(ROOT_PREFIX):].strip("/")
            for p in lvl_prefixes
            if p.startswith(ROOT_PREFIX + "Keyframes_L")
        ]
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/images")
def list_images(
    folder: str = Query(..., description="VD: Keyframes_L01"),
    seq: Optional[str] = Query(None, description="VD: L01_V001"),
    ttl: int = Query(3600, description="Presigned URL TTL (s)"),
):
    """
    - Nếu truyền seq => trả ảnh cho đúng sequence đó.
    - Nếu không => trả groups { seq: [ {key,url} ] } cho toàn bộ sequence trong folder.
    S3 layout giả định: ROOT/Keyframes_Lxx/keyframes/Lxx_Vyyy/*.jpg
    """
    try:
        base = f"{ROOT_PREFIX}{folder}/keyframes/"
        if seq:
            keys = _list_objects(base + f"{seq}/")
            return {
                "folder": folder,
                "seq": seq,
                "count": len(keys),
                "items": [{"key": k, "url": _sign(k, ttl)} for k in keys],
            }
        # nhóm theo mọi sequence
        seq_prefixes = _list_common_prefixes(base)
        result: Dict[str, List[Dict[str, str]]] = {}
        for sp in seq_prefixes:
            seq_name = sp[len(base):].strip("/")
            keys = _list_objects(sp)
            if not keys:
                continue
            result[seq_name] = [{"key": k, "url": _sign(k, ttl)} for k in keys]
        return {"folder": folder, "groups": result}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/manifest")
def build_manifest(ttl: int = Query(3600, description="Presigned URL TTL (s)")):
    """
    Trả về manifest dạng:
    {
      "Keyframes_L01/keyframes/L01_V001": [<url1>, <url2>, ...],
      ...
    }
    => Khớp 100% format FE của bạn đang dùng.
    """
    try:
        manifest: Dict[str, List[str]] = {}
        # liệt kê các mức Lxx
        for folder_prefix in _list_common_prefixes(ROOT_PREFIX):
            folder_name = folder_prefix[len(ROOT_PREFIX):].strip("/")  # Keyframes_Lxx
            if not folder_name.startswith("Keyframes_L"):
                continue
            # liệt kê seq dưới '.../keyframes/'
            base = f"{folder_prefix}keyframes/"
            for seq_prefix in _list_common_prefixes(base):
                seq_name = seq_prefix[len(base):].strip("/")  # Lxx_Vyyy
                keys = _list_objects(seq_prefix)
                if not keys:
                    continue
                urls = [_sign(k, ttl) for k in keys]
                # KHỚP đường dẫn leaf FE đang hiển thị (không có ROOT_PREFIX, có "Keyframes_Lxx/keyframes/Seq")
                leaf = f"{folder_name}/keyframes/{seq_name}"
                manifest[leaf] = urls
        return JSONResponse(content=manifest)
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/video")
def get_video(
    level: str = Query(..., description="VD: L01"),
    clip: str  = Query(...,  description="VD: L01_V001"),
    ttl:  int  = Query(3600, description="Presigned URL TTL (s)"),
):
    """
    Trả về danh sách URL video khả dụng tương ứng với clip (đã presign nếu nằm trên S3).
    Hỗ trợ 2 layout:
      - Videos_test/Videos_L01/video/L01_V001.mp4
      - Videos_test/Videos_L01 video/video/L01_V001.mp4
    """
    try:
        # các key ứng viên trong S3
        s3_keys = [
            f"{VIDEOS_ROOT_PREFIX}Videos_{level} video/video/{clip}.mp4",
            f"{VIDEOS_ROOT_PREFIX}Videos_{level}/video/{clip}.mp4",
        ]

        urls: list[str] = []
        for key in s3_keys:
            try:
                s3.head_object(Bucket=AWS_BUCKET_NAME, Key=key)  # tồn tại?
                urls.append(_sign(key, ttl))
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code")
                if code in ("404", "NoSuchKey"):
                    continue
                # lỗi khác thì ném ra
                raise

        return {"level": level, "clip": clip, "urls": urls}
    except Exception as e:
        raise HTTPException(500, str(e))
    
@router.get("/map")
def get_map(
    clip: str = Query(..., description="VD: L01_V001"),
    level: Optional[str] = Query(None, description="VD: L01 (tuỳ chọn, fallback)"),
):
    """
    Trả JSON rows [{n, pts_time, fps, frame_idx}, ...] đọc từ S3.
    Ưu tiên: map-keyframes/{clip}.csv
    Fallback cũ: map-keyframes/Keyframes_{level}/keyframes/{clip}.csv
    """
    candidates = [f"map-keyframes/{clip}.csv"]
    if level:
        candidates.append(f"map-keyframes/Keyframes_{level}/keyframes/{clip}.csv")

    last_err = None
    for key in candidates:
        try:
            obj = s3.get_object(Bucket=AWS_BUCKET_NAME, Key=key)
            body = obj["Body"].read().decode("utf-8")
            rows = []
            rdr = csv.DictReader(io.StringIO(body))
            for r in rdr:
                rows.append({
                    "n": int(float(r.get("n", 0) or 0)),
                    "pts_time": float(r.get("pts_time", 0) or 0),
                    "fps": int(float(r.get("fps", 0) or 0)),
                    "frame_idx": int(float(r.get("frame_idx", 0) or 0)),
                })
            # chuẩn hoá và sort để khớp thứ tự thumbnails
            rows.sort(key=lambda x: (x["n"], x["pts_time"]))
            return {"clip": clip, "level": level, "key": key, "count": len(rows), "rows": rows}
        except ClientError as e:
            last_err = e
            continue

    # không tìm thấy ở cả 2 layout
    msg = f"Không tìm thấy CSV map cho clip={clip}"
    if level: msg += f" (đã thử với level={level})"
    raise HTTPException(404, msg)

def _join(*parts: str) -> str:
    return "/".join(p.strip("/").replace("\\", "/") for p in parts if p is not None and p != "")

def _exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=AWS_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchKey"):
            return False
        raise

def _list(prefix: str):
    keys, token = [], None
    while True:
        params = dict(Bucket=AWS_BUCKET_NAME, Prefix=prefix)
        if token:
            params["ContinuationToken"] = token
        resp = s3.list_objects_v2(**params)
        for obj in resp.get("Contents", []):
            k = obj.get("Key")
            if k:
                keys.append(k)
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return keys

def _find_map_key(clip: str, level: Optional[str]) -> Optional[str]:
    """
    Trả về key CSV đầu tiên tìm thấy cho clip. Thử theo các layout:
      1) ROOT_PREFIX/Map_keyframes/{clip}.csv
      2) Map_keyframes/{clip}.csv
      3) ROOT_PREFIX/Map_keyframes/Keyframes_{level}/keyframes/{clip}.csv
      4) Map_keyframes/Keyframes_{level}/keyframes/{clip}.csv
    Nếu vẫn không thấy: cuối cùng list(prefix='.../Map_keyframes/') và tìm gần đúng.
    """
    bases = []
    if ROOT_PREFIX:
        bases.append(_join(ROOT_PREFIX, "map-keyframes"))
    bases.append("map-keyframes")

    candidates = []
    for base in bases:
        candidates.append(_join(base, f"{clip}.csv"))
        if level:
            candidates.append(_join(base, f"Keyframes_{level}", "keyframes", f"{clip}.csv"))

    # thử head_object trước
    for k in candidates:
        if _exists(k):
            return k

    # fallback: liệt kê và tìm gần đúng (phòng khi khác hoa/thường)
    for base in bases:
        all_keys = _list(_join(base) + "/")
        # ưu tiên khớp đuôi .../{clip}.csv
        for k in all_keys:
            if k.lower().endswith(f"/{clip.lower()}.csv") or k.lower().endswith(f"{clip.lower()}.csv"):
                return k
    return None

@router.get("/map")
def get_map(
    clip: str = Query(..., description="VD: L01_V001"),
    level: Optional[str] = Query(None, description="VD: L01 (tuỳ chọn)"),
):
    key = _find_map_key(clip, level)
    if not key:
        raise HTTPException(404, f"Không tìm thấy CSV map cho clip={clip}. Kiểm tra Map_keyframes/ trên S3.")

    try:
        obj = s3.get_object(Bucket=AWS_BUCKET_NAME, Key=key)
        body = obj["Body"].read().decode("utf-8", errors="ignore")
        rows = []
        rdr = csv.DictReader(io.StringIO(body))
        for r in rdr:
            rows.append({
                "n": int(float(r.get("n", 0) or 0)),
                "pts_time": float(r.get("pts_time", 0) or 0),
                "fps": int(float(r.get("fps", 0) or 0)),
                "frame_idx": int(float(r.get("frame_idx", 0) or 0)),
            })
        rows.sort(key=lambda x: (x["n"], x["pts_time"]))
        return {"clip": clip, "level": level, "s3_key": key, "count": len(rows), "rows": rows}
    except ClientError as e:
        raise HTTPException(500, f"S3 error: {e}")

@router.get("/debug/map-list")
def debug_map_list():
    bases = []
    if ROOT_PREFIX:
        bases.append(_join(ROOT_PREFIX, "map-keyframes"))
    bases.append("map-keyframes")
    out = {}
    for b in bases:
        out[b] = _list(_join(b) + "/")
    return out