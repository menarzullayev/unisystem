from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Views importi
from core.views import (
    login_view, logout_view, dashboard_view, hemis_view, 
    profile_view, force_update_view,
    # Talaba (Essay & Grades)
    student_essay_list, essay_detail_view, student_grades_view,
    # O'qituvchi
    teacher_dashboard, teacher_essay_topics, teacher_grade_submission
)

# AI Chat importi
from chat.views import (
    chat_view, chat_api,                       # 1. Hemis AI
    universal_chat_view, universal_chat_api,   # 2. Universal AI
    education_chat_view, education_chat_api    # 3. Education AI (YANGI)
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- AUTHENTICATION ---
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
    
    # --- HEMIS ASOSIY ---
    path('hemis/', hemis_view, name='hemis_data'),
    path('hemis/profile/', profile_view, name='student_profile'),
    path('hemis/update/', force_update_view, name='update_data'),
    
    # --- 1. HEMIS AI (Shaxsiy Ma'lumotlar Bo'yicha) ---
    path('ai-chat/', chat_view, name='ai_chat'),
    path('ai-chat/api/', chat_api, name='chat_api'),

    # --- 2. UNIVERSAL AI (Smart Assistant) ---
    path('smart-assistant/', universal_chat_view, name='universal_chat'),
    path('smart-assistant/api/', universal_chat_api, name='universal_chat_api'),

    # --- 3. EDUCATION SUPPORT AI (Ta'lim Bo'yicha Savol-Javob) - YANGI ---
    path('education-support/', education_chat_view, name='education_chat'),
    path('education-support/api/', education_chat_api, name='education_chat_api'),
    
    # --- YOZMA ISHLAR (TALABA) ---
    path('essays/', student_essay_list, name='essay_list'),
    path('essays/<int:topic_id>/', essay_detail_view, name='essay_detail'),
    path('grades/', student_grades_view, name='student_grades'), 
    
    # --- O'QITUVCHI ---
    path('teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('teacher/topics/', teacher_essay_topics, name='teacher_topics'),
    path('teacher/grade/<int:sub_id>/', teacher_grade_submission, name='teacher_grade'),

    # --- MOCK EXAM (Imtihonlar) ---
    path('edu/', include('edu.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)