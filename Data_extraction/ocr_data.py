import os
import cv2
import glob
import json
import torch
import easyocr
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

keyframes_dir = 'Keyframes_test'
all_keyframe_paths = dict()
for part in sorted(os.listdir(keyframes_dir)):
    part_path = os.path.join(keyframes_dir, part)
    keyframes_subdir = os.path.join(part_path, 'keyframes')

    if not os.path.exists(keyframes_subdir):
        print(f"[⚠️] Bỏ qua vì không có keyframes/: {part}")
        continue

    all_keyframe_paths[part] = dict()

    # Lặp qua từng thư mục như L01_V001, L01_V002,...
    for frame_dir in sorted(os.listdir(keyframes_subdir)):
        frame_id = frame_dir  # dùng luôn tên như L01_V001
        frame_path = os.path.join(keyframes_subdir, frame_dir)
        keyframe_paths = sorted(glob.glob(os.path.join(frame_path, '*.jpg')))

        all_keyframe_paths[part][frame_id] = keyframe_paths

reader = easyocr.Reader(['vi'], gpu=True)

bs = 16
save_dir = 'Keyframes_test/ocr_results/'

if not os.path.exists(save_dir):
    os.mkdir(save_dir)

keys = sorted(all_keyframe_paths.keys())
for key in tqdm(keys):
    video_keyframe_paths = all_keyframe_paths[key]
    video_ids = sorted(video_keyframe_paths.keys())

    if not os.path.exists(os.path.join(save_dir, key)):
        os.mkdir(os.path.join(save_dir, key))

    for video_id in tqdm(video_ids):
        video_keyframe_path = video_keyframe_paths[video_id]
        video_ocr_results = []
        video_ocr_results_path = []
        for i in range(0, len(video_keyframe_path), bs):
            # Support batchsize inferencing
            image_paths = video_keyframe_path[i:i+bs]

            results = reader.readtext_batched(image_paths, batch_size=len(image_paths))
            for result in results:
                refined_result = []
                for item in result: 
                    if item[2] > 0.5:
                        refined_result.append(item)   
                refined_result = easyocr.utils.get_paragraph(refined_result)
                text_detected = [item[1] for item in refined_result]
                video_ocr_results.append(text_detected)
                video_ocr_results_path.append(image_paths)

        with open(f'{save_dir}/{key}/{video_id}.json',"w", encoding='utf-8') as jsonfile:
            json.dump(video_ocr_results, jsonfile, ensure_ascii=False)