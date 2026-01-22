from django.urls import path
from . import views

urlpatterns = [
    # 1. Landing Page (Kirish sahifasi)
    path('exams/', views.exam_landing_page, name='exam_list'),
    
    # 2. Random Start (Tugma bosilganda ishlaydi)
    path('exams/start-random/', views.start_random_exam, name='start_random_exam'),
    
    # 3. Jarayon (Har bir bo'limni ishlash)
    path('exams/session/<int:result_id>/<int:section_id>/', views.take_section_view, name='take_section'),
    
    # 4. Natija (Imtihon tugagach)
    path('exams/result/<int:result_id>/', views.exam_result_view, name='exam_result'),
]