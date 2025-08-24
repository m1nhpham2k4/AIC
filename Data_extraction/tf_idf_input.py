from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from tqdm import tqdm
import os
import pickle
import glob
import nltk
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Khởi tạo TF-IDF
vectorizer = TfidfVectorizer()

def preprocess_text(text: str):
    '''
    Processes the input text by converting it to lowercase and removing special characters, 
    allowing only alphanumeric characters and Vietnamese diacritics.
    
    Parameters:
        text (str): The input text string.
    
    Returns:
        output (str): Cleaned and lowercased text string with special characters removed.
    '''
    text = text.lower()
    reg_pattern = r'[^a-z0-9A-Z_ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂưăạảấầẩẫậắằẳẵặẹẻẽềềểỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪễếệỉịọỏốồổỗộớờởỡợụủứừỬỮỰỲỴÝỶỸửữựỳỵỷỹ\s]'

    output = re.sub(reg_pattern, '', text)
    output = output.strip()
    return output

from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet



def preprocessing_eng_text(text: str):
    # lowercase
    text = text.lower()

    # remove special characters (chỉ giữ chữ và số)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # tokenize
    words = word_tokenize(text)

    # remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words]

    # stemming
    lemma = WordNetLemmatizer()
    words = [lemma.lemmatize(word) for word in words]

    # join lại thành 1 string
    return " ".join(words)



import json

def load_documents(data_path, meta_datatype):
    """Mỗi file JSON/TXT = 1 hoặc nhiều document"""

    documents = []
    mapping = []

    if meta_datatype == 'ASR':
        path_jsons = glob.glob(data_path)
        path_jsons.sort()

        for pj in tqdm(path_jsons):
            with open(pj, "r", encoding="utf-8") as f:
                content = json.load(f)  # list câu
                # preprocess từng câu
                cleaned_sentences = [preprocess_text(sent) for sent in content]
                # ghép thành 1 đoạn văn duy nhất
                doc = " ".join(cleaned_sentences)
                documents.append(doc)
                mapping.append(pj[-16:-8])

    elif meta_datatype == 'Caption':
        path_txts = glob.glob(data_path)
        path_txts.sort()

        for pt in tqdm(path_txts):
            with open(pt, "r",encoding="utf-8") as f:
                lines = f.readlines()

            # Lấy thư mục cha (vd: L21, L27)
            parent_dir = os.path.basename(os.path.dirname(pt))
            # Lấy tên file (vd: V001.txt -> V001)
            video_id = os.path.splitext(os.path.basename(pt))[0]

            for idx, line in enumerate(lines, start=1):
                preprocessed_caption = preprocessing_eng_text(line)
                caption = preprocessed_caption.strip()
                if caption:
                    documents.append(caption)
                    # mapping: Keyframes_L21/keyframes/L21_V001/001.jpg
                    mapping.append(
                        f"Keyframes_{parent_dir}/keyframes/{parent_dir}_{video_id}/{idx:03d}.jpg"
                    )
    elif meta_datatype == 'Tags':
        path_jsons = glob.glob(data_path)
        path_jsons.sort()

        for pj in tqdm(path_jsons):
            with open(pj, "r", encoding="utf-8") as f:
                content = json.load(f)  # list các object {"dict": "...", "Tags": [...]}

            for obj in content:
                tags = obj.get("Tags", [])
                # ghép các tag thành 1 document duy nhất
                doc = " ".join(preprocessing_eng_text(tag) for tag in tags if tag)
                if doc:
                    documents.append(doc)
                    mapping.append(obj["dict"])  # mapping chính là đường dẫn ảnh
    elif meta_datatype == 'tags + caption':
        path_txts = glob.glob(data_path[1], recursive=True)  # caption files
        path_jsons = glob.glob(data_path[0], recursive=True)   # tags files
        path_txts.sort()
        path_jsons.sort()

        # Đảm bảo caption và tags cùng thứ tự (theo L21_V001, L21_V002,...)
        for pt, pj in tqdm(zip(path_txts, path_jsons), total=len(path_txts)):
            # ---- Load captions ----
            with open(pt, "r", encoding="utf-8") as f:
                captions = [preprocessing_eng_text(line).strip() for line in f.readlines()]

            # ---- Load tags ----
            with open(pj, "r", encoding="utf-8") as f:
                tags_data = json.load(f)

            # ---- Ghép caption + tags ----
            for caption, tag_item in zip(captions, tags_data):
                tags_text = " ".join(preprocessing_eng_text(tag) for tag in tag_item.get("Tags", []))
                combined = f"{caption} {tags_text}".strip()

                if combined:
                    documents.append(combined)
                    mapping.append(tag_item["dict"])  # mapping lấy từ tags
    return documents, mapping

def create_payload(data_path):
    pass


def tf_idf_transform(data_path, save_tfids_object_path, update=False, meta_datatype=""):
    docs,mapp = load_documents(data_path, meta_datatype)
    print("okokok 1")
    if update and os.path.exists(save_tfids_object_path):
        # Load TF-IDF đã lưu
        with open(save_tfids_object_path, "rb") as f:
            obj = pickle.load(f)
            vectorizer = obj["vectorizer"]
            X_old = obj["X"]
            docs_old = obj["docs"]

        # Ghép thêm dữ liệu mới
        all_docs = docs_old + docs
    else:
        # Train mới
        vectorizer = TfidfVectorizer(ngram_range=(1,2))
        all_docs = docs

    # Fit lại TF-IDF trên toàn bộ dữ liệu
    X = vectorizer.fit_transform(all_docs)
    print("okokok 2")
    # Lưu lại
    with open(save_tfids_object_path, "wb") as f:
        pickle.dump({
            "vectorizer": vectorizer,
            "X": X,
            "docs": mapp
        }, f)

    return X, vectorizer

if __name__ == "__main__":
    data_path = {"ASR":r'D:\GIT\AIC\Data_extraction\metadata\ASR\**\*vi.json',
                 "Tags":r'D:\GIT\AIC\Data_extraction\metadata\Tag\**\*.json',
                 "Caption":r"D:\GIT\AIC\Data_extraction\metadata\Caption\**\*.txt"}
    
    save_tf_idf_path = {"ASR":r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-asr.pkl",
                        "Tags":r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-tags.pkl",
                        "Caption":r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-caption.pkl",
                        "Tags_Caption":r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-caption-tags.pkl"}
    X, vector = tf_idf_transform((data_path["Tags"],data_path["Caption"]), save_tf_idf_path["Tags_Caption"], update=False, meta_datatype="tags + caption")
    # X1, vector1 = tf_idf_transform(data_path["Caption"], save_tf_idf_path["Caption"], update=False,meta_datatype="Caption")
    print(X.shape)
    # X1, vector1 = tf_idf_transform(data_path["Tags"], save_tf_idf_path["Tags"], update=False,meta_datatype="Tags")
    # print(X1.shape)

