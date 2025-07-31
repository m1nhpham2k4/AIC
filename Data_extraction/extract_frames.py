import os
import cv2
import numpy as np
from TransNetV2.inference.transnetv2 import TransNetV2

def extract_keyframes_from_video(video_path, output_root):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n🟢 Đang xử lý: {video_name}")

    # Load model (nên load 1 lần bên ngoài nếu xử lý nhiều video)
    model = TransNetV2()
    _, single_frame_predictions, _ = model.predict_video(video_path)

    # Dự đoán danh sách scene
    scenes = model.predictions_to_scenes(single_frame_predictions)
    print(f"🔹 Số cảnh phát hiện: {len(scenes)}")

    # Tính index của keyframe (ở giữa mỗi cảnh)
    key_frms_idx = (scenes[:, 0] + scenes[:, 1]) // 2
    print(f"🔹 Keyframe indices: {key_frms_idx}")

    # Mở video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Tạo folder output riêng cho video
    output_dir = os.path.join(output_root, video_name)
    os.makedirs(output_dir, exist_ok=True)

    count_saved = 0
    for i, frm_idx in enumerate(key_frms_idx):
        if frm_idx >= total_frames:
            print(f"⚠️ Bỏ qua frame {frm_idx} (vượt quá số frame)")
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, frm_idx)
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Không thể đọc frame tại {frm_idx}")
            continue

        out_path = os.path.join(output_dir, f"scene_{i:03d}.jpg")
        cv2.imwrite(out_path, frame)
        print(f"✅ Đã lưu: {out_path}")
        count_saved += 1

    cap.release()
    print(f"🟡 Tổng số keyframe đã lưu: {count_saved}")

def process_all_videos_in_folder(input_folder, output_root="output_videos"):
    os.makedirs(output_root, exist_ok=True)

    video_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    print(f"📁 Đã tìm thấy {len(video_files)} video trong '{input_folder}'")

    for video_file in video_files:
        video_path = os.path.join(input_folder, video_file)
        extract_keyframes_from_video(video_path, output_root)

if __name__ == "__main__":
    input_folder = "videos"  # thư mục chứa các video gốc
    output_root = "output_videos"  # nơi chứa các thư mục theo video
    process_all_videos_in_folder(input_folder, output_root)
