import google.generativeai as genai
from deep_translator import GoogleTranslator
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def translate_text_GoogleTranslate(text, target_language="en"):
    """
    Translates the input text from the source language to the target language.

    :param text: The text to be translated
    :param to_lang: The language code of the target language (default is English 'en')
    :return: The translated text or error message.
    """
    translation = GoogleTranslator(source='auto', target='en').translate(text)
    print("✅ Translation by Google Translate Library")
    return translation

def translate_text_GoogleGenerativeAI(text, target_language="en"):
    """
    Dịch văn bản bằng Google Generative AI (Gemini).

    :param text: Văn bản cần dịch.
    :param target_language: Mã ngôn ngữ đích (ví dụ: 'en' cho tiếng Anh).
    :return: Văn bản đã được dịch hoặc thông báo lỗi.
    """
    try:
        # Ensure model is initialized
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Call the model
        response = model.generate_content(
            f"Translate the following text to {target_language}:\n{text}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1000,
            )
        )

        translation = response.text.strip()
        print("✅ Translation by Google Generative AI")
        return translation

    except Exception as e:
        print(f"❌ Error in Google Generative AI translation: {e}")
        return f"Error: {e}"

    
def translate_text_OpenAI(text, target_language="en"):
    """
    Translates the input text using OpenAI's GPT model.

    :param text: The text to be translated
    :param target_language: The language code of the target language (default is English 'en')
    :return: The translated text or error message.
    """
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[ {"role": "user", "content": f"Translate the following text to {target_language}: {text}"}],
            temperature=0.2,
            max_tokens=1000
        )
        translation = response.choices[0].message.content.strip()
        print("✅ Translation by OpenAI")
        return translation
    except Exception as e:
        print(f"❌ Error in OpenAI translation: {e}")
        return f"Error: {e}"
    

    
