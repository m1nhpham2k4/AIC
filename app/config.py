import os
from dotenv import load_dotenv, find_dotenv

# Tự tìm .env dù bạn chạy uvicorn ở đâu
load_dotenv(find_dotenv())

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME       = os.getenv("AWS_BUCKET_NAME")
AWS_REGION            = os.getenv("AWS_REGION", "ap-southeast-1")

ROOT_PREFIX           = os.getenv("S3_ROOT_PREFIX")
VIDEOS_ROOT_PREFIX = os.getenv("S3_VIDEOS_ROOT_PREFIX", "Videos_test/")  

print(f"Using S3 root prefix config: {ROOT_PREFIX}")
# FE dev URL để redirect "/" khi phát triển
FRONTEND_URL          = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Validate sớm cho rõ lỗi
_required = {
    "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
    "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
    "AWS_BUCKET_NAME": AWS_BUCKET_NAME,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise RuntimeError(f"Missing env: {', '.join(_missing)}. Check your .env")
