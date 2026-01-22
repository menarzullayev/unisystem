import google.generativeai as genai
from .ai import get_api_key, get_available_model, AGENT_EDUCATION

def ask_education_ai(user_message):
    """
    Faqat ta'limga oid savollarga javob beruvchi maxsus AI agenti.
    GEMINI_KEY_EDUCATION kalitidan foydalanadi.
    """
    # 1. Maxsus Education API Kalitni olish
    api_key = get_api_key(AGENT_EDUCATION)
    
    if not api_key:
        return "Tizim xatoligi: Education API kalit topilmadi (.env faylni tekshiring)."

    try:
        # 2. Sozlash
        genai.configure(api_key=api_key)
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)

        # 3. QAT'IY YO'RIQNOMA (System Prompt)
        system_instruction = """
        Sen "Education Support AI"san - Ta'lim bo'yicha maxsus yordamchisan.
        
        VAZIFANG:
        Foydalanuvchining savollariga javob berish, LEKIN faqat quyidagi mavzular doirasida:
        - Fanlar (Matematika, Fizika, Dasturlash, Tarix va h.k.)
        - Universitet va o'qish jarayonlari.
        - Ilmiy tadqiqotlar, maqolalar yozish.
        - Til o'rganish va tarjima (faqat o'quv maqsadida).
        - Kod yozish va tushuntirish.

        TAQIQ (FILTER):
        Agar foydalanuvchi ta'limga aloqasi bo'lmagan mavzuda (masalan: kino, siyosat, shou-biznes, kundalik gap-so'zlar, sevgi-muhabbat, o'yin-kulgi) savol bersa, qat'iy rad et.
        
        Rad etish javobi shunday bo'lsin: 
        "Uzr, men faqat ta'lim va ilm-fan mavzularidagi savollarga javob bera olaman."

        JAVOB USLUBI:
        - O'zbek tilida javob ber.
        - Aniq, ilmiy va tushunarli bo'lsin.
        """

        full_prompt = f"{system_instruction}\n\nFOYDALANUVCHI SAVOLI: {user_message}"

        # 4. Javob olish
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        return f"Education AI xatosi: {str(e)}"