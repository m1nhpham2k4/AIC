import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

# Lấy các biến
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD")

# In ra kiểm tra
# print("GEMINI_API_KEY:", GEMINI_API_KEY)
# print("MONGODB_USERNAME:", MONGODB_USERNAME)
# print("MONGODB_PASSWORD:", MONGODB_PASSWORD)

# Tạo URI
MONGODB_URI = f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.s84nghm.mongodb.net/'
# print("MONGODB_URI:", MONGODB_URI)
