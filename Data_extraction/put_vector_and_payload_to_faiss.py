import torch
import open_clip
from PIL import Image
import numpy as np
import os
import faiss
import json

device = "cuda" if torch.cuda.is_available() else "cpu"
# Chọn model mạnh hơn: ViT-g-14 (huấn luyện trên LAION-2B)cái 
model_name = "ViT-SO400M-16-SigLIP2-384"
pretrained = "webli"
dim = 1152

def load_model(model_name,pretrained,device):
    # Load model + preprocess
    global model
    global preprocess
    global tokenizer
    model, _, preprocess = open_clip.create_model_and_transforms(
        model_name=model_name,
        pretrained=pretrained,
        device=device
    )
    # Load tokenizer cho text
    tokenizer = open_clip.get_tokenizer(model_name)


## Lấy đặc trưng ảnh ->embeddings
def extract_image_features(image_path):
    """ Trả về 1 vector 1152 chiều"""
    image = Image.open(image_path).convert("RGB")
    
    image_input = preprocess(image).to(device).unsqueeze(0)
    
    with torch.no_grad():
        image_features = model.encode_image(image_input)
    
    image_features /= image_features.norm(dim=-1, keepdim=True)
    
    return image_features.cpu().detach().numpy()

## Lấy đặc trưng text -> embeddings
## đẩy vector lên faiss
def put_vector_into_faiss():
    root_keyfrm = r"D:\GIT\AIC\Data_extraction\features"
    ## đọc đường dẫn file .npy
    npy_directory = [root_keyfrm+txt for txt in os.listdir(r"D:\GIT\AIC\Data_extraction\features") if txt.find(".npy")!=-1]
    all_vectors = []
    for file in npy_directory:
        arr = np.load(file).astype("float32")
        all_vectors.append(arr)
    ## Stack các vector lại
        
    vectors = np.vstack(all_vectors)
    d = vectors.shape[1]          # số chiều vector
    index = faiss.IndexFlatL2(d)  # index theo L2
    index = faiss.IndexIDMap(index)
    ids = np.arange(vectors.shape[0]).astype("int64")
    # Thêm vào FAISS
    index.add_with_ids(vectors, ids)
    print("Số vector trong FAISS:", index.ntotal)
    faiss.write_index(index, "Faiss/aic_2025_vectors.faiss")


import os
import json
import glob

def sort_tags_by_paths(tag_file, paths_file, output_file=None):
    with open(tag_file, "r", encoding="utf-8") as f:
        tags_json = json.load(f)

    tag_map = {os.path.basename(item["dict"]): item["Tags"] for item in tags_json}

    with open(paths_file, "r", encoding="utf-8") as f:
        paths = [line.strip() for line in f.readlines()]

    new_tags = []
    for p in paths:
        key = os.path.basename(p)
        new_tags.append({
            "dict": p,
            "Tags": tag_map.get(key, [])
        })

    if output_file is None:
        output_file = tag_file

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_tags, f, ensure_ascii=False, indent=2)

    print(f"✅ Sorted {tag_file}")


def create_payload(paths_file, captions_file, tags_file, output_file, start_id=0):
    with open(paths_file, "r", encoding="utf-8") as f:
        paths = [line.strip() for line in f.readlines()]

    with open(captions_file, "r", encoding="utf-8") as f:
        captions = [line.strip() for line in f.readlines()]

    with open(tags_file, "r", encoding="utf-8") as f:
        tags_data = json.load(f)

    payloads = {}
    for i, (path, caption, tag_item) in enumerate(zip(paths, captions, tags_data)):
        # lấy tên video từ path, vd: Keyframes_L21/keyframes/L21_V001/001.jpg
        video_name = path.split("/")[-2]  # => "L21_V001"
        video_link = f"{video_name}.mp4"

        payloads[start_id + i] = {
            "path": path,
            "video_link": video_link,  # ✅ thêm video_link
            "caption": caption,
            "tags": tag_item["Tags"]
        }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payloads, f, ensure_ascii=False, indent=2)

    print(f"✅ Created payload {output_file}, total {len(payloads)} items")
    return payloads



def process_all(root_dir):
    # lấy đường dẫn cha của tags
    tag_dir = os.path.join(root_dir, "metadata", "Tag")
    # lấy đường dẫn cha của captions
    caption_dir = os.path.join(root_dir, "metadata", "Caption") # ⚠️ caption nằm ở đây
    # lấy đường dẫn cha của feature
    feature_dir = os.path.join(root_dir, "metadata", "features")
    payload_dir = os.path.join(root_dir, "payloads")
    os.makedirs(payload_dir, exist_ok=True)

    all_tag_files = glob.glob(os.path.join(tag_dir, "*", "*.json"))
    all_payloads = {}
    next_id = 0

    for tag_file in all_tag_files:
        base = os.path.splitext(os.path.basename(tag_file))[0]  # L21_V001
        folder = os.path.basename(os.path.dirname(tag_file))    # L21
        video_name = base  # ví dụ: L21_V001

        paths_file = os.path.join(feature_dir, f"{video_name}.paths.txt")
        captions_file = os.path.join(caption_dir, folder, f"{video_name.split('_')[1]}.txt")  
        # => metadata/Caption/L21/V001.txt

        if not (os.path.exists(paths_file) and os.path.exists(captions_file)):
            print(f"⚠️ Missing paths/captions for {video_name}, skip.")
            continue

        # sort lại tags.json
        sort_tags_by_paths(tag_file, paths_file)

        # tạo payload nhỏ
        output_file = os.path.join(payload_dir, f"{video_name}_payload.json")
        payloads = create_payload(paths_file, captions_file, tag_file, output_file, start_id=next_id)

        all_payloads.update(payloads)
        next_id += len(payloads)

    # merge tất cả thành all_payload.json
    merged_file = os.path.join(payload_dir, "all_payload.json")
    with open(merged_file, "w", encoding="utf-8") as f:
        json.dump(all_payloads, f, ensure_ascii=False, indent=2)

    print(f"🎉 Done! Merged payload saved to {merged_file} with {len(all_payloads)} entries")


if __name__ == "__main__":
    ROOT_DIR = r"D:\GIT\AIC\Data_extraction"
    process_all(ROOT_DIR)
    ##put_vector_into_faiss()

