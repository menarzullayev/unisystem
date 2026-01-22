import os
import google.generativeai as genai
import json
import re

# API kalitni olish (.env faylidan)
API_KEY = os.getenv('GEMINI_KEY_EXAM') or os.getenv('GEMINI_KEY_STUDENT')

def configure_genai():
    """Gemini API ni sozlash"""
    if not API_KEY:
        return False
    try:
        # Stable API versiyasini ko'rsatamiz
        genai.configure(api_key=API_KEY)
        return True
    except Exception as e:
        print(f"❌ API Config Error: {e}")
        return False

def grade_writing_full_exam(t1_prompt, t1_resp, t2_prompt, t2_resp):
    """
    Qat'iy IELTS standartlari asosida Writing tahlili.
    Model nomi xatoliklarni oldini olish uchun prefiksiz ishlatiladi.
    """
    if not configure_genai():
        return 0, "Texnik xatolik: API kalit sozlanmagan."
    
    # MUHIM: Model nomi shunchaki 'gemini-1.5-flash' bo'lishi kerak
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Kuchli prompt (Strict IELTS Examiner)
    prompt = f"""
    Act as a professional IELTS Academic Writing Examiner. Be extremely strict.
    
    EVALUATION RULES:
    1. WORD COUNT: Task 1 must be >= 150 words. Task 2 must be >= 250 words. If less, deduct band score.
    2. RELEVANCE: Ensure the student stays on topic.
    3. COHESION: Proper use of linking words and paragraphing.

    --- TASK 1 ---
    Topic: {t1_prompt}
    Response: {t1_resp}

    --- TASK 2 ---
    Topic: {t2_prompt}
    Response: {t2_resp}

    RETURN ONLY JSON:
    {{
        "overall_score": 6.5,
        "feedback": "### Task 1 Analysis:\\n- Word Count: [X]\\n- Weaknesses: [Analysis]\\n\\n### Task 2 Analysis:\\n- Word Count: [Y]\\n- Quality: [Analysis]\\n\\n### Advice: [Tips]"
    }}
    """
    
    try:
        # Sun'iy intellektga yuborish
        response = model.generate_content(prompt)
        text_data = response.text.strip()
        
        # JSONni Markdown bloklaridan tozalab olish (Xavfsiz tahlil)
        json_match = re.search(r'\{.*\}', text_data, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return float(data.get('overall_score', 0)), data.get('feedback', "Tahlil yakunlandi.")
        else:
            raise ValueError("AI invalid format")
            
    except Exception as e:
        print(f"🚨 Writing AI Error: {str(e)}")
        # Zaxira sifatida muqobil modelni sinab ko'rish
        try:
            fallback_model = genai.GenerativeModel('gemini-pro')
            res = fallback_model.generate_content(prompt)
            match = re.search(r'\{.*\}', res.text, re.DOTALL)
            if match:
                d = json.loads(match.group())
                return float(d.get('overall_score', 0)), d.get('feedback', "")
        except:
            pass
        return 0, f"AI hozirda xizmat ko'rsata olmayapti. Iltimos, bir necha daqiqadan so'ng qayta urinib ko'ring."