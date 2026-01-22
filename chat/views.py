import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# --- AGENTLAR IMPORTI ---
from .hemis_agent import ask_hemis_ai          # Hemis AI
from .universal_agent import ask_universal_ai  # Universal AI
from .education_agent import ask_education_ai  # Education AI (YANGI)

# ---------------------------------------------------------
# 1. HEMIS AI (Faqat o'qish va jadval uchun)
# ---------------------------------------------------------
@login_required
def chat_view(request):
    """Hemis AI sahifasi"""
    return render(request, 'chat.html', {'active_tab': 'chat'})

@csrf_exempt
@login_required
def chat_api(request):
    """Hemis AI APIsi"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # 1. Hemis Agentini chaqiramiz
            ai_reply = ask_hemis_ai(request.user, user_message)
            
            return JsonResponse({'status': 'success', 'reply': ai_reply})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ---------------------------------------------------------
# 2. UNIVERSAL AI (Smart Assistant - Barcha savollar uchun)
# ---------------------------------------------------------
@login_required
def universal_chat_view(request):
    """Universal AI sahifasi"""
    return render(request, 'universal_chat.html', {'active_tab': 'universal_ai'})

@csrf_exempt
@login_required
def universal_chat_api(request):
    """Universal AI APIsi"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # 2. Universal Agentni chaqiramiz
            ai_reply = ask_universal_ai(user_message)
            
            return JsonResponse({'status': 'success', 'reply': ai_reply})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ---------------------------------------------------------
# 3. EDUCATION SUPPORT AI (Faqat Ta'lim) - YANGI
# ---------------------------------------------------------
@login_required
def education_chat_view(request):
    """Education AI sahifasi"""
    # Universal chat shablonidan foydalanamiz, lekin kontekstni o'zgartiramiz
    # Frontendda (HTML) 'active_tab' ga qarab API manzilini o'zgartirish kerak bo'ladi.
    return render(request, 'universal_chat.html', {
        'active_tab': 'education_ai',
        'bot_title': "Ta'lim Assistenti",
        'bot_description': "Faqat fan va ta'limga oid savollaringizni bering."
    })

@csrf_exempt
@login_required
def education_chat_api(request):
    """Education AI APIsi"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # 3. Education Agentni chaqiramiz
            ai_reply = ask_education_ai(user_message)
            
            return JsonResponse({'status': 'success', 'reply': ai_reply})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})