import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY= os.getenv("GEMINI_API_KEY")
MONGODB_USERNAME=os.getenv("MONGODB_USERNAME")
MONGODB_PASSWORD=os.getenv("MONGODB_PASSWORD")

MONGODB_URI = f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.s84nghm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'