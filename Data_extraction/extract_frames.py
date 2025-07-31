import os
import sys
import cv2
import numpy as np

# Thêm đường dẫn để import TransNetV2
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "TransNetV2", "inference"))

from transnetv2 import TransNetV2


def extract_scenes_from_video(video_path, output_root, threshold=0.5):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(output_root, video_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"🟢 Processing: {video_name}")

    # Load model và dự đoán
    model = TransNetV2()
    single_frame_predictions, _, _ = model.predict_video(video_path)

    # Xác định các frame là điểm scene boundary
    boundaries = np.where(single_frame_predictions > threshold)[0]
    print(f"✂️  Detected {len(boundaries)} scene boundaries")

    # Mở video để trích xuất frame
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for i, frame_idx in enumerate(boundaries):
        if frame_idx >= total_frames:
            continue
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if ret:
            scene_folder = os.path.join(output_dir, f"scene_{i:03d}")
            os.makedirs(scene_folder, exist_ok=True)
            out_path = os.path.join(scene_folder, f"frame_{frame_idx:05d}.jpg")
            cv2.imwrite(out_path, frame)

    cap.release()
    print(f"✅ Done: {video_name} ({len(boundaries)} scenes)\n")


def batch_process_folder(video_folder, output_folder="output_frames", threshold=0.5):
    os.makedirs(output_folder, exist_ok=True)

    video_files = [f for f in os.listdir(video_folder)
                   if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

    if not video_files:
        print("⚠️ Không tìm thấy file video nào trong thư mục:", video_folder)
        return

    for video_file in video_files:
        video_path = os.path.join(video_folder, video_file)
        extract_scenes_from_video(video_path, output_folder, threshold)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract scene boundary frames using TransNetV2")
    parser.add_argument("--video_folder", default="videos", help="Thư mục chứa video")
    parser.add_argument("--output_folder", default="output_frames", help="Thư mục lưu ảnh output")
    parser.add_argument("--threshold", type=float, default=0.5, help="Ngưỡng phân tách scene (0-1)")

    args = parser.parse_args()
    batch_process_folder(args.video_folder, args.output_folder, args.threshold)
