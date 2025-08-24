import os
import glob
import faiss
import numpy as np
from tqdm import tqdm

feature_shape = 1152
features_dir = './feature'
print(features_dir)
index = faiss.IndexFlatIP(feature_shape)

for feature_path in tqdm(sorted(glob.glob(os.path.join(features_dir) +'/*.npy'))):
        print(feature_path)
        feats = np.load(feature_path)
        for feat in feats:
            feat = feat.astype(np.float32).reshape(1,-1)
            index.add(feat)

faiss.write_index(index, f"./faiss_clip_14.bin")