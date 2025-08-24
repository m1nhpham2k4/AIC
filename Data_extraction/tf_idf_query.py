from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from tqdm import tqdm
import os
import pickle
import glob
import boto3
import requests
from PIL import Image
from IPython import display
import io
from dotenv import load_dotenv
import nltk
nltk.download("punkt_tab")
nltk.download("stopwords")
nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from deep_translator import GoogleTranslator
load_dotenv()

def connectS3():
# Lấy thông tin AWS từ .env
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "ap-southeast-1")  # region của bạn

    # Kết nối S3
    global s3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )
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
def preprocessing_eng_query(text: str):
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

def load_tf_idf():
    pass 
from sklearn.metrics.pairwise import cosine_similarity

def search_video(query, model_path, top_k=5):
    """
    Tìm kiếm văn bản gần nhất với câu query dựa trên TF-IDF + cosine similarity
    
    Args:
        query (str): câu truy vấn
        model_path (str): đường dẫn file đã lưu (vectorizer, X, docs)
        top_k (int): số kết quả trả về
    
    Returns:
        List[Tuple[str, float]]: danh sách (tài liệu, độ tương đồng)
    """
    # Load TF-IDF model đã lưu
    with open(model_path, "rb") as f:
        obj = pickle.load(f)
        vectorizer = obj["vectorizer"]
        X = obj["X"]
        docs = obj["docs"]

    # Biến query thành vector
    q_vec = vectorizer.transform([query])

    # Tính cosine similarity
    cos_sim = cosine_similarity(q_vec, X)[0]

    # Sắp xếp kết quả theo độ tương đồng giảm dần
    ranking = cos_sim.argsort()[::-1]

    # Lấy top_k
    results = [(docs[idx], float(cos_sim[idx])) for idx in ranking[:top_k]]

    return results
def translate_text_GoogleTranslate(text,translation):
    """
    Translates the input text from the source language to the target language.

    :param text: The text to be translated
    :param to_lang: The language code of the target language (default is English 'en')
    :return: The translated text or error message.
    """
    txt = translation.translate(text)
    return txt
def getTranslated(vi_txt,translation):
    res_translate = translate_text_GoogleTranslate(vi_txt,translation) 
    return res_translate

def search_frames_by_caption(query, model_path, top_k=10):
    """
    Tìm kiếm văn bản gần nhất với câu query dựa trên TF-IDF + cosine similarity
    
    Args:
        query (str): câu truy vấn
        model_path (str): đường dẫn file đã lưu (vectorizer, X, docs)
        top_k (int): số kết quả trả về
    
    Returns:
        List[Tuple[str, float]]: danh sách (tài liệu, độ tương đồng)
    """
    # Load TF-IDF model đã lưu
    with open(model_path, "rb") as f:
        obj = pickle.load(f)
        vectorizer = obj["vectorizer"]
        X = obj["X"]
        docs = obj["docs"]

    # Biến query thành vector
    q_vec = vectorizer.transform([query])

    # Tính cosine similarity
    cos_sim = cosine_similarity(q_vec, X)[0]

    # Sắp xếp kết quả theo độ tương đồng giảm dần
    ranking = cos_sim.argsort()[::-1]

    # Lấy top_k
    results = [(docs[idx], float(cos_sim[idx])) for idx in ranking[:top_k]]

    return results
# ================== DEMO ==================
if __name__ == "__main__":
    ## nếu là asr thì khỏi dịch
    ## nếu là caption thì vi -> eng
    ## nếu là tags thì vi -> eng
    # file bạn đã lưu khi fit TF-IDF
    types ="tags"
    if types == 'asr':
        query = "Đoạn video được thể hiện bằng một loạt tranh vẽ màu liên tiếp. Nội dung của các bức tranh là trong một phiên xét xử tại tòa án. Có cờ nước Mỹ trong một trong số các bức tranh."
        print(query)
        query = preprocess_text(query)
        model_path = r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-asr.pkl"
        results = search_frames_by_caption(query, model_path, top_k=5)
        for doc, score in results:
            print(f"{score:.4f} --> {doc}")
    elif types == 'caption':
        translation = GoogleTranslator(source='auto', target='en')
        connectS3()
        query = "Đoạn video được thể hiện bằng một loạt tranh vẽ màu liên tiếp. Nội dung của các bức tranh là trong một phiên xét xử tại tòa án. Có cờ nước Mỹ trong một trong số các bức tranh."
        query = getTranslated(query,translation)
        print(query)
        processed_query = preprocessing_eng_query(query)
        model_path = r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-caption.pkl"
        # Thông tin bucket và file
        results = search_frames_by_caption(processed_query, model_path, top_k=5)
        bucket_name = "aic2025data"
        for doc, score in results:
        # Lấy ảnh từ S3
            response = s3.get_object(Bucket=bucket_name, Key='Keyframes_2025/'+doc)
            img_data = response["Body"].read()
                # Hiển thị ảnh
            image = Image.open(io.BytesIO(img_data))
            image.show()
            print(f"{score:.4f} --> {doc}")
    elif types == 'tags':
        translation = GoogleTranslator(source='auto', target='en')
        connectS3()
        query = "Đoạn video được thể hiện bằng một loạt tranh vẽ màu liên tiếp. Nội dung của các bức tranh là trong một phiên xét xử tại tòa án. Có cờ nước Mỹ trong một trong số các bức tranh."
        query = getTranslated(query,translation)
        print(query)
        processed_query = preprocessing_eng_query(query)
        model_path = r"D:\GIT\AIC\Data_extraction\tf-idf-save-path\tf-idf-tags.pkl"
        # Thông tin bucket và file
        results = search_frames_by_caption(processed_query, model_path, top_k=10)
        bucket_name = "aic2025data"
        for doc, score in results:
        # Lấy ảnh từ S3
            response = s3.get_object(Bucket=bucket_name, Key='Keyframes_2025/'+doc)
            img_data = response["Body"].read()
                # Hiển thị ảnh
            image = Image.open(io.BytesIO(img_data))
            image.show()
            print(f"{score:.4f} --> {doc}")
    elif types == 'tags + caption':
        pass
