from urllib.parse import quote
from app.config import KEYFRAMES_BASE_URL

def attach_image_url(item: dict) -> dict:
    leaf = item.get("leaf")
    filename = item.get("filename")
    if not leaf or not filename:
        item["image_url"] = None
        return item
    rel = "/".join(quote(seg) for seg in str(leaf).split("/"))
    file = quote(str(filename))
    item["image_url"] = f"{KEYFRAMES_BASE_URL.rstrip('/')}/{rel}/{file}"
    return item
