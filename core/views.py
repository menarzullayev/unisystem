from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.db.models import Sum
from django.core.files.storage import default_storage

# Modellar
from .models import (
    User, Semester, Week, Schedule, Attendance, Task, 
    EssayTopic, Submission
)

from .services import get_auth_token
from .sync import sync_student_data
from chat.essay_agent import grade_essay_ai

# -----------------------------------------------------------------------------
# 1. AUTHENTICATION (KIRISH/CHIQISH)
# -----------------------------------------------------------------------------

def login_view(request):

    if request.user.is_authenticated:
        if request.user.is_teacher or request.user.is_superuser:
            return redirect('teacher_dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        login_input = request.POST.get('login')
        password = request.POST.get('password')
        
        # A) Django Admin/Teacher tekshiruvi
        user = authenticate(request, username=login_input, password=password)
        if user is not None:
            login(request, user)
            if user.is_teacher or user.is_superuser:
                return redirect('teacher_dashboard')
            return redirect('dashboard')
        
        # B) Hemis API tekshiruvi (Talabalar uchun)
        auth_resp = get_auth_token(login_input, password)
        
        if auth_resp['success']:
            token = auth_resp['token']
            user, created = User.objects.get_or_create(username=login_input)
            
            user.hemis_login = login_input
            user.hemis_password = password
            user.hemis_token = token
            if created:
                user.role = 'student'
                user.full_name = login_input 
            user.save()
            
            login(request, user)
            
            messages.info(request, "Ma'lumotlar bazasi yangilanmoqda...")
            try:
                if sync_student_data(user):
                    messages.success(request, "Xush kelibsiz! Ma'lumotlar muvaffaqiyatli yuklandi.")
                else:
                    messages.warning(request, "Tizimga kirildi, lekin ma'lumotlarni to'liq yuklab bo'lmadi.")
            except Exception as e:
                print(f"Sync Error: {e}")
                messages.warning(request, "Ma'lumotlarni yuklashda xatolik yuz berdi.")

            return redirect('dashboard')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')


# -----------------------------------------------------------------------------
# 2. TALABA DASHBOARD & HEMIS LOGIKASI
# -----------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    if request.user.is_teacher and not request.user.is_superuser:
        return redirect('teacher_dashboard')
        
    return render(request, 'dashboard.html', {
        'student': request.user, 
        'group': request.user.group_name
    })

@login_required
def force_update_view(request):
    user = request.user
    if not user.hemis_login or not user.hemis_password:
        messages.error(request, "Sinxronizatsiya uchun qaytadan tizimga kirishingiz kerak.")
        logout(request) 
        return redirect('login')

    try:
        success = sync_student_data(user)
        if success:
            messages.success(request, "Ma'lumotlar Hemis tizimidan muvaffaqiyatli yangilandi!")
        else:
            messages.warning(request, "Yangilashda xatolik: Hemis bilan bog'lanib bo'lmadi.")
    except Exception as e:
        messages.error(request, f"Tizim xatoligi: {e}")
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def hemis_view(request):
    if request.user.is_teacher and not request.user.is_superuser:
        return redirect('teacher_dashboard')

    user = request.user
    all_semesters = Semester.objects.all().order_by('-code')
    selected_sem_id = request.GET.get('semester')
    
    current_sem = None
    if selected_sem_id:
        current_sem = all_semesters.filter(code=selected_sem_id).first()
    if not current_sem:
        current_sem = all_semesters.filter(current=True).first() or all_semesters.first()
            
    if not current_sem:
        messages.warning(request, "Semestrlar topilmadi. 'Yangilash' tugmasini bosing.")
        return render(request, 'hemis/main.html', {'all_semesters': [], 'schedule': []})

    user_schedules = Schedule.objects.filter(user=user, semester=current_sem)
    week_ids = user_schedules.values_list('week_id', flat=True).distinct()
    all_weeks = Week.objects.filter(week_id__in=week_ids).order_by('start_date')
    
    today = datetime.now().date()
    selected_week_id = request.GET.get('week')
    active_week = None
    
    weeks_display = []
    for w in all_weeks:
        is_current = (w.start_date <= today <= w.end_date)
        w.current = is_current
        weeks_display.append(w)
        if not selected_week_id and is_current: active_week = w
            
    if selected_week_id: active_week = all_weeks.filter(week_id=selected_week_id).first()
    if not active_week and all_weeks.exists(): active_week = all_weeks.first()

    schedule_list = []
    if active_week:
        weekly_scheds = user_schedules.filter(week_id=active_week.week_id).order_by('lesson_time')
        days_order = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]
        grouped = {day: [] for day in days_order}
        for s in weekly_scheds:
            if s.day_name in grouped: grouped[s.day_name].append(s)
        for day in days_order:
            if grouped[day]: schedule_list.append({'day_name': day, 'lessons': grouped[day]})

    attendances = Attendance.objects.filter(user=user, semester=current_sem).order_by('-date')
    att_stats = {
        'total': sum(a.hours for a in attendances),
        'sababli': sum(a.hours for a in attendances if 'ababl' in a.type),
        'sababsiz': sum(a.hours for a in attendances if 'ababs' in a.type),
        'list': attendances
    }
    tasks = Task.objects.filter(user=user, semester=current_sem).order_by('deadline')

    context = {
        'all_semesters': all_semesters,
        'selected_sem_id': current_sem.code,
        'all_weeks': weeks_display,
        'selected_week_id': active_week.week_id if active_week else None,
        'schedule': schedule_list,
        'attendance': att_stats,
        'tasks': tasks
    }
    return render(request, 'hemis/main.html', context)

@login_required
def profile_view(request):
    if request.user.is_teacher and not request.user.is_superuser:
        return redirect('teacher_dashboard')
    return render(request, 'hemis/profile.html', {'active_tab': 'profile', 'student_info': request.user})


# -----------------------------------------------------------------------------
# 3. YOZMA ISHLAR (ESSAY) & AI ASSESSMENT
# -----------------------------------------------------------------------------

@login_required
def student_essay_list(request):
    """Talaba uchun mavzular ro'yxati"""
    if request.user.is_teacher and not request.user.is_superuser:
        return redirect('teacher_dashboard')

    topics = EssayTopic.objects.all().order_by('-deadline')
    my_submissions = Submission.objects.filter(user=request.user)
    submitted_ids = list(my_submissions.values_list('topic_id', flat=True))
    
    return render(request, 'education/essay_list.html', {
        'topics': topics,
        'submitted_ids': submitted_ids,
        'active_tab': 'essays'
    })

@login_required
def essay_detail_view(request, topic_id):
    """
    Yozma ish topshirish (Matn yoki Rasm) va natijani ko'rish.
    """
    topic = get_object_or_404(EssayTopic, id=topic_id)
    submission = Submission.objects.filter(user=request.user, topic=topic).first()
    
    # 1. Yangi ish topshirish yoki Qayta topshirish (POST)
    if request.method == 'POST' and 'submit_essay' in request.POST:
        
        # Agar oldin topshirgan bo'lsa va qayta topshirishga ruxsati bo'lmasa
        # (submission.can_resubmit propertysi modelda bo'lishi kerak)
        if submission and not getattr(submission, 'can_resubmit', False) and submission.status != 'ai_graded':
             messages.warning(request, "Siz allaqachon bu ishni topshirgansiz. Qayta topshirish uchun o'qituvchi ruxsati kerak.")
        else:
            text_content = request.POST.get('content')
            uploaded_file = request.FILES.get('file') # FAYLNI OLISH
            
            # Agar bo'sh bo'lsa
            if not text_content and not uploaded_file:
                messages.error(request, "Iltimos, matn yozing yoki rasm/fayl yuklang.")
                return redirect('essay_detail', topic_id=topic.id)

            # --- SUBMISSION YARATISH YOKI YANGILASH ---
            if submission:
                # Qayta topshirish: Eski ma'lumotlarni tozalaymiz va yangilaymiz
                sub = submission
                sub.status = 'pending'
                sub.ai_grade = None
                sub.ai_feedback = None
                sub.teacher_grade = None
                sub.teacher_feedback = None
            else:
                # Yangi topshirish
                sub = Submission(
                    user=request.user,
                    topic=topic,
                    status='pending'
                )
            
            # Yangi kontentni yozamiz
            if text_content: sub.content = text_content
            if uploaded_file: sub.file = uploaded_file
            
            sub.save()
            
            # --- AI TEKSHIRUVI (Vision) ---
            topic_file_path = topic.topic_file.path if topic.topic_file else None
            student_file_path = sub.file.path if sub.file else None
            
            # Agentni chaqiramiz
            grade, feedback = grade_essay_ai(
                topic_title=topic.title, 
                topic_desc=topic.description, 
                topic_file_path=topic_file_path,
                student_text=text_content, 
                student_file_path=student_file_path 
            )
            
            # Natijani yangilash
            sub.ai_grade = grade
            sub.ai_feedback = feedback
            sub.status = 'ai_graded' # AI baholadi, talaba natijani ko'radi va xohlasa qayta topshiradi
            sub.save()
            
            messages.success(request, f"Ishingiz qabul qilindi! AI Bahosi: {grade}")
            return redirect('essay_detail', topic_id=topic.id)

    # 2. Appellatsiya berish (POST)
    if request.method == 'POST' and 'appeal' in request.POST:
        if submission and submission.status == 'ai_graded':
            submission.status = 'appeal'
            submission.save()
            messages.warning(request, "Sizning ishingiz qayta ko'rib chiqish uchun o'qituvchiga yuborildi.")
            return redirect('essay_detail', topic_id=topic.id)

    return render(request, 'education/essay_detail.html', {
        'topic': topic,
        'submission': submission,
        'active_tab': 'essays'
    })

@login_required
def student_grades_view(request):
    """Talabaning baholari ro'yxati (Gradebook)"""
    if request.user.is_teacher and not request.user.is_superuser:
        return redirect('teacher_dashboard')
        
    submissions = Submission.objects.filter(user=request.user).order_by('-submitted_at')
    
    # O'rtacha ball
    total_score = 0
    count = 0
    for sub in submissions:
        if sub.final_grade is not None:
            total_score += sub.final_grade
            count += 1
    
    average = round(total_score / count, 1) if count > 0 else 0

    return render(request, 'education/student_grades.html', {
        'submissions': submissions,
        'average': average,
        'active_tab': 'grades'
    })


# -----------------------------------------------------------------------------
# 4. O'QITUVCHI (TEACHER) DASHBOARD
# -----------------------------------------------------------------------------

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher and not request.user.is_superuser:
        messages.error(request, "Sizda o'qituvchi huquqi yo'q!")
        return redirect('dashboard')
    
    # Apellatsiya yoki qayta ko'rishdagilar
    pending_reviews = Submission.objects.filter(
        status__in=['appeal', 'teacher_review']
    ).order_by('submitted_at')
    
    stats = {
        'pending_count': pending_reviews.count(),
        'total_graded': Submission.objects.filter(status='done', teacher_grade__isnull=False).count(),
        'total_ai_graded': Submission.objects.filter(status='ai_graded').count()
    }

    return render(request, 'teacher/dashboard.html', {
        'user': request.user,
        'reviews': pending_reviews,
        'stats': stats,
        'active_tab': 'teacher_dash'
    })

@login_required
def teacher_essay_topics(request):
    """
    Mavzu yaratish sahifasi.
    O'qituvchi rasm/fayl yuklashi mumkin.
    """
    if not request.user.is_teacher and not request.user.is_superuser:
        return redirect('dashboard')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        sub_type = request.POST.get('submission_type', 'both')
        topic_file = request.FILES.get('topic_file') # <-- Admin yuklagan fayl
        
        EssayTopic.objects.create(
            title=title,
            description=description,
            deadline=deadline,
            submission_type=sub_type,
            topic_file=topic_file 
        )
        messages.success(request, "Yangi yozma ish mavzusi muvaffaqiyatli yaratildi!")
        return redirect('teacher_topics')
    
    topics = EssayTopic.objects.all().order_by('-created_at')
    return render(request, 'teacher/essay_topics.html', {
        'topics': topics,
        'active_tab': 'teacher_topics'
    })

@login_required
def teacher_grade_submission(request, sub_id):
    if not request.user.is_teacher and not request.user.is_superuser:
        return redirect('dashboard')
        
    submission = get_object_or_404(Submission, id=sub_id)
    
    if request.method == 'POST':
        # YANGI: Qayta topshirishga ruxsat berish
        if 'allow_resubmit' in request.POST:
            submission.status = 'resubmit'
            submission.teacher_grade = None
            submission.teacher_feedback = "O'qituvchi qayta topshirishga ruxsat berdi."
            submission.save()
            messages.info(request, f"{submission.user.full_name} ga qayta topshirishga ruxsat berildi.")
            return redirect('teacher_dashboard')

        # Baholash
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback')
        
        submission.teacher_grade = grade
        submission.teacher_feedback = feedback
        submission.status = 'done'
        submission.save()
        
        messages.success(request, f"{submission.user.full_name}ning ishi baholandi!")
        return redirect('teacher_dashboard')
        
    return render(request, 'teacher/grade_form.html', {'submission': submission})


# -----------------------------------------------------------------------------
# 5. BOShQA
# -----------------------------------------------------------------------------

def mock_exam_view(request):
    return render(request, 'education/exams.html', {'active_tab': 'exams'})

def ai_assessment_view(request):
    return render(request, 'education/assessment.html', {'active_tab': 'assessment'})