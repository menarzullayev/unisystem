import google.generativeai as genai
from .ai import get_api_key, get_available_model, AGENT_GENERAL

def ask_universal_ai(user_message):
    """
    Universal AI (Smart Assistant) uchun mantiq.
    Bu agent Hemis ma'lumotlariga ega emas, faqat umumiy bilimlar bazasidan foydalanadi.
    """
    # 1. API Kalitni olish
    api_key = get_api_key(AGENT_GENERAL)
    
    if not api_key:
        return "Tizim xatoligi: Universal API kalit topilmadi."

    try:
        # 2. Sozlash
        genai.configure(api_key=api_key)
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)

        # 3. Prompt (Yo'riqnoma)
        system_instruction = """
        Sen "Smart Assistant" - Universal sun'iy intellektsan.
        Vazifang: Foydalanuvchining har qanday savoliga (kod yozish, tarjima, ilmiy savollar, maslahatlar) aniq va lo'nda javob berish.
        
        QOIDALAR:
        1. Javoblaring o'zbek tilida bo'lsin (agar foydalanuvchi boshqa tilni so'ramasa).
        2. Kod yozganda Markdown formatidan (```python kabi) foydalan.
        3. O'zingni Hemis tizimi deb tanishtirma, sen universal yordamchisan.
        4. Javoblar qisqa, mazmunli va foydali bo'lsin.
        """

        full_prompt = f"{system_instruction}\n\nFOYDALANUVCHI SAVOLI: {user_message}"

        # 4. Javob olish
        response = model.generate_content(full_prompt)
        return response.text

    except Exception as e:
        return f"Universal AI xatosi ({model_name}): {str(e)}"