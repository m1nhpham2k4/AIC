import os
from typing import List, Dict, Optional
import boto3
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, AWS_REGION, ROOT_PREFIX
print(f"Using S3 root prefix_load: {ROOT_PREFIX}")
router = APIRouter(tags=["keyframes"])

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def _list_common_prefixes(prefix: str) -> List[str]:
    """Liệt kê 'folder' con (common prefixes) dưới prefix."""
    prefixes: List[str] = []
    token: Optional[str] = None
    while True:
        kw = dict(Bucket=AWS_BUCKET_NAME, Prefix=prefix, Delimiter="/")
        if token:
            kw["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kw)
        for p in resp.get("CommonPrefixes", []):
            prefixes.append(p["Prefix"])
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
    return prefixes

def _list_objects(prefix: str, suffixes=(".jpg", ".jpeg", ".png")) -> List[str]:
    """Liệt kê tất cả object keys dưới prefix (lọc theo đuôi file)."""
    keys: List[str] = []
    token: Optional[str] = None
    while True:
        kw = dict(Bucket=AWS_BUCKET_NAME, Prefix=prefix)
        if token:
            kw["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kw)
        for obj in resp.get("Contents", []):
            k = obj["Key"]
            if k.lower().endswith(suffixes):
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

@router.get("/keyframes/folders")
def list_folders():
    """
    Trả về danh sách folder cấp Lxx, ví dụ: Keyframes_L01, Keyframes_L02...
    """
    try:
        prefixes = _list_common_prefixes(ROOT_PREFIX)
        # lọc những prefix có dạng ".../Keyframes_Lxx/"
        folders = [
            p[len(ROOT_PREFIX):].strip("/")       # chỉ giữ phần 'Keyframes_L01'
            for p in prefixes
            if p.startswith(ROOT_PREFIX + "Keyframes_L")
        ]
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/keyframes/images")
def list_images(
    folder: str = Query(..., description="Ví dụ: Keyframes_L01"),
    seq: Optional[str] = Query(None, description="Ví dụ: L01_V001; nếu bỏ trống trả về theo từng seq"),
    ttl: int = Query(3600, description="Thời gian sống của presigned URL (giây)"),
):
    """
    - Nếu truyền seq: trả list ảnh cho đúng sequence đó.
    - Nếu không: trả group {seq: [urls...]} cho toàn bộ sequence trong folder.
    Cấu trúc S3 giả định: ROOT/Keyframes_Lxx/keyframes/Lxx_Vyyy/*.jpg
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
        # không có seq -> group theo từng sequence
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
