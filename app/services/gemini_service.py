import google.generativeai as genai
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-pro")

def get_gemini_response(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Đã xảy ra lỗi khi gọi Gemini API."