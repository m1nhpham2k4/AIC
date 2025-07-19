from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import google.generativeai as genai
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI()
username = os.getenv('MONGODB_USERNAME')
password = os.getenv('MONGODB_PASSWORD')
uri = f'mongodb+srv://{username}:{password}@cluster0.s84nghm.mongodb.net/'
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print('Pinged your deployment. You successfully connected to MongoDB')
except Exception as e:
    print(e)

model = genai.GenerativeModel(model_name="gemini-2.5-pro")

# Mount static folder
app.mount('/static', StaticFiles(directory='static'), name="static")

# Load templates
templates = Jinja2Templates(directory='templates')

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        response = model.generate_content(message)
        reply = response.text
    except Exception as e:
        reply = "Đã xảy ra lỗi khi gọi Gemini API."
    
    return JSONResponse(content={"reply": reply})