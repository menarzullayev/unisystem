import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env yuklash (agar kerak bo'lsa)
try:
    load_dotenv()
except:
    pass

# Agent turlari (Konstantalar)
AGENT_STUDENT = 'student'
AGENT_EDUCATION = 'education'
AGENT_ESSAY = 'essay'
AGENT_EXAM = 'exam'
AGENT_GENERAL = 'general'

def get_api_key(agent_type):
    """Har bir agent uchun alohida yoki umumiy API kalitni qaytaradi."""
    keys = {
        AGENT_STUDENT: os.getenv('GEMINI_KEY_STUDENT'),
        AGENT_EDUCATION: os.getenv('GEMINI_KEY_EDUCATION'),
        AGENT_ESSAY: os.getenv('GEMINI_KEY_ESSAY'),
        AGENT_EXAM: os.getenv('GEMINI_KEY_EXAM'),
        AGENT_GENERAL: os.getenv('GEMINI_KEY_GENERAL'),
    }
    # Agar maxsus kalit bo'lmasa, STUDENT kalitini yoki eng asosiysini qaytaradi
    return keys.get(agent_type) or keys.get(AGENT_STUDENT)

def get_available_model():
    """Mavjud modellarni tekshirib, eng yaxshisini qaytaradi."""
    try:
        # Tizimdagi barcha modellarni olamiz
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Bizga kerakli modellar ketma-ketligi (ustuvorlik bo'yicha)
        priority_list = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        
        for model in priority_list:
            if model in available_models:
                return model
                
        # Agar ro'yxatdan topilmasa, birinchisini yoki standartni qaytaradi
        return available_models[0] if available_models else 'gemini-pro'
    except:
        # Agar list_models ishlamasa, eng ishonchli variantni qaytaradi
        return 'gemini-pro'