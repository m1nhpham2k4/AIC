import os, open_clip

tag = 'laion2b_s34b_b88k'

# Lấy URL tương ứng với tag pretrained
url = open_clip.get_pretrained_url(tag)

# Trả về đường dẫn file .pt / .bin trong cache (nếu đã có sẽ dùng lại)
ckpt_path = open_clip.download_pretrained_from_url(url)
print("Checkpoint path:", ckpt_path)
