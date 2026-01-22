# chat/essay_agent.py

import os
import google.generativeai as genai
import json
from dotenv import load_dotenv
import pathlib
from PIL import Image
import time

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(ENV_PATH)

def grade_essay_ai(topic_title, topic_desc, topic_file_path=None, student_text=None, student_file_path=None):
    api_key = os.getenv('GEMINI_KEY_ESSAY') or os.getenv('GEMINI_KEY_STUDENT')
    
    if not api_key:
        return 0, "Tizim xatoligi: API kalit topilmadi."

    MODELS_TO_TRY = [
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-flash-latest',
        'gemini-2.0-flash-lite',
    ]

    genai.configure(api_key=api_key)

    base_prompt = f"""
    Sen Oliy Ta'lim muassasasining o'qituvchisisan.
    
    MAVZU: {topic_title}
    TAVSIF: {topic_desc}
    
    VAZIFANG:
    1. Talabaning javobini (matn yoki rasmda) diqqat bilan tekshir.
    2. Mavzuga mosligini va to'g'riligini aniqla.
    3. 100 balli tizimda baho qo'y.
    4. Qisqa va foydali izoh yoz.
    
    JAVOB FORMATI (Faqat JSON):
    {{
        "grade": 85,
        "feedback": "Javob to'g'ri, lekin 2-qismda xatolik bor..."
    }}
    """

    content_parts = [base_prompt]

    if topic_file_path:
        try:
            img = Image.open(topic_file_path)
            content_parts.append("---O'QITUVCHI BERGAN SAVOL (RASM)---")
            content_parts.append(img)
        except: pass 

    content_parts.append("---TALABA JAVOBI---")
    
    if student_file_path:
        try:
            img = Image.open(student_file_path)
            content_parts.append("(Talaba javobni rasmda yukladi):")
            content_parts.append(img)
        except:
            content_parts.append("(Talaba fayl yukladi, lekin tizim ocha olmadi).")
    
    if student_text:
        content_parts.append(f"(Talaba matn yozdi): {student_text}")

    last_error = ""
    
    for model_name in MODELS_TO_TRY:
        try:
            print(f"🔄 AI urinmoqda: {model_name}...")
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content(content_parts)
            
            text_resp = response.text
            if not text_resp: raise ValueError("Bo'sh javob keldi")
                
            cleaned_text = text_resp.replace('```json', '').replace('```', '').strip()
            
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}')
            if start != -1 and end != -1:
                cleaned_text = cleaned_text[start : end + 1]

            data = json.loads(cleaned_text)
            
            print(f"✅ Muvaffaqiyatli: {model_name}")
            return data.get('grade', 0), data.get('feedback', "Izoh yo'q")

        except Exception as e:
            print(f"❌ {model_name} xatosi: {e}")
            last_error = str(e)
            time.sleep(1)
            continue

    return 0, f"Texnik xatolik: AI modellari javob bermadi. ({last_error})"