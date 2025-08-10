import os
import json
from yt_dlp import YoutubeDL

# Danh sách video (bạn có thể load từ file json nếu cần)
video_data = {
    "0": {"video_path": "L02_V001", "watch_url": "https://youtube.com/watch?v=lGfBEHpCpT4"},
    "1": {"video_path": "L02_V002", "watch_url": "https://youtube.com/watch?v=OvouNlTdHHw"},
    "2": {"video_path": "L02_V003", "watch_url": "https://youtube.com/watch?v=m7hc_dNufeE"},
    "3": {"video_path": "L02_V004", "watch_url": "https://youtube.com/watch?v=CXi4sAnmKFA"},
    "4": {"video_path": "L02_V005", "watch_url": "https://youtube.com/watch?v=dFpwaGPKXhg"},
    "5": {"video_path": "L03_V001", "watch_url": "https://youtube.com/watch?v=gK2opN8WW74"},
    "6": {"video_path": "L03_V002", "watch_url": "https://youtube.com/watch?v=ekx2YIGmu2Y"},
    "7": {"video_path": "L03_V003", "watch_url": "https://youtube.com/watch?v=jU_yT1t7Cs8"},
    "8": {"video_path": "L03_V004", "watch_url": "https://youtube.com/watch?v=Dq92C09gcEc"},
    "9": {"video_path": "L03_V005", "watch_url": "https://youtube.com/watch?v=g4V9V9fEnzM"},
    "10": {"video_path": "L04_V001", "watch_url": "https://youtube.com/watch?v=aJLgbg8X1GY"},
    "11": {"video_path": "L04_V002", "watch_url": "https://youtube.com/watch?v=xuWygNAkqH4"},
    "12": {"video_path": "L04_V003", "watch_url": "https://youtube.com/watch?v=YXE60FF30BY"},
    "13": {"video_path": "L04_V004", "watch_url": "https://youtube.com/watch?v=xKfaba_QTug"},
    "14": {"video_path": "L04_V005", "watch_url": "https://youtube.com/watch?v=XReJhqnOu_4"},
    "15": {"video_path": "L05_V001", "watch_url": "https://youtube.com/watch?v=cR7-ohh5IEQ"},
    "16": {"video_path": "L05_V002", "watch_url": "https://youtube.com/watch?v=vjfXl07RWH0"},
    "17": {"video_path": "L05_V003", "watch_url": "https://youtube.com/watch?v=INZIJAvcClg"},
    "18": {"video_path": "L05_V004", "watch_url": "https://youtube.com/watch?v=lycHmBwSr58"},
    "19": {"video_path": "L05_V005", "watch_url": "https://youtube.com/watch?v=UPbl5uzBlzw"}
}

# Thư mục gốc để lưu video
base_output_dir = "Data_extraction/Videos_L02/video"
os.makedirs(base_output_dir, exist_ok=True)

# Tải từng video
for _, item in video_data.items():
    url = item["watch_url"]
    filename = item["video_path"] + ".mp4"
    output_path = os.path.join(base_output_dir, filename)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': False,
    }

    print(f"⬇️  Đang tải: {url} ➜ {filename}")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"❌ Lỗi khi tải {url}: {e}")

print("✅ Hoàn tất tải toàn bộ video.")
