import os
import google.generativeai as genai
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Q, Min, Max
from core.models import Schedule, Attendance, Task, Semester, User, Week
from dotenv import load_dotenv
import pathlib

# Markaziy utilitlardan import qilamiz
from .ai import get_api_key, get_available_model, AGENT_STUDENT

# .env yuklash
CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(ENV_PATH)

# DIPPAT: get_best_model funksiyasi O'CHIRILDI, o'rniga ai.py dagi ishlatiladi.

def get_hemis_context(user: User):
    """Talabaning to'liq akademik tarixi va jadvali bo'yicha kontekst yaratadi."""
    # ... (Bu funksiyaning ichki kodi o'zgarishsiz qoladi, chunki u mukammal ishlaydi)
    now = timezone.now()
    today_str = now.strftime("%d.%m.%Y (%A)")
    
    address_info = user.address if user.address else "Kiritilmagan"
    phone_info = user.phone if user.phone else "Kiritilmagan"
    birth_info = user.birth_date if user.birth_date else "Kiritilmagan"

    context = f"""
    BUGUNGI SANA: {today_str}
    
    TALABA PROFILI:
    - Ism: {user.full_name}
    - ID: {user.hemis_id}
    - Fakultet: {user.faculty}
    - Kurs: {user.level}
    - Guruh: {user.group_name}
    - Telefon: {phone_info}
    - Manzil: {address_info}
    - Tug'ilgan sana: {birth_info}
    """
    context += "\n--- O'QISH DAVRLARI VA JADVALLAR ---\n"
    
    sem_ids = Schedule.objects.filter(user=user).values_list('semester', flat=True)
    unique_sem_ids = list(set(sem_ids))
    sched_semesters = Semester.objects.filter(id__in=unique_sem_ids).order_by('-code')
    
    days_order = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]
    
    if sched_semesters.exists():
        for sem in sched_semesters:
            related_schedules = Schedule.objects.filter(user=user, semester=sem)
            week_ids = related_schedules.values_list('week_id', flat=True)
            
            # Semestr sanalarini aniqlash
            date_range = Week.objects.filter(week_id__in=list(set(week_ids))).aggregate(
                start=Min('start_date'),
                end=Max('end_date')
            )
            
            start_date = date_range['start'].strftime('%d.%m.%Y') if date_range['start'] else "Noma'lum"
            end_date = date_range['end'].strftime('%d.%m.%Y') if date_range['end'] else "Noma'lum"
            
            sem_header = f"{sem.name} (Davri: {start_date} dan {end_date} gacha)"
            if sem.current: sem_header += " [JORIY SEMESTR]"
            
            context += f"\n>>> {sem_header}:\n"
            
            has_lesson = False
            for day in days_order:
                lessons = related_schedules.filter(day_name__iexact=day).order_by('lesson_time')
                
                if lessons.exists():
                    has_lesson = True
                    context += f"  {day}:\n"
                    
                    time_map = {} 
                    for s in lessons:
                        time_key = s.lesson_time
                        if time_key not in time_map: time_map[time_key] = []
                        
                        teacher_str = s.teacher if s.teacher else "Noma'lum"
                        subject_entry = f"Fan: {s.subject.name} || Xona: {s.room} || O'qituvchi: {teacher_str}"
                        
                        if subject_entry not in time_map[time_key]: 
                            time_map[time_key].append(subject_entry)
                    
                    for time, subjects in time_map.items():
                        subjects_str = " / ".join(subjects)
                        context += f"    - {time} | {subjects_str}\n"

            if not has_lesson:
                context += "  (Bu semestr uchun jadval yo'q)\n"
    else:
        context += "Jadval ma'lumotlari topilmadi.\n"

    context += "\n--- DAVOMAT STATISTIKASI ---\n"
    all_semesters = Semester.objects.all().order_by('code')
    for sem in all_semesters:
        stats = Attendance.objects.filter(user=user, semester=sem).aggregate(
            total=Sum('hours'),
            sababli=Sum('hours', filter=Q(type__icontains='Sababli')),
            sababsiz=Sum('hours', filter=Q(type__icontains='Sababsiz'))
        )
        if stats['total'] and stats['total'] > 0:
            context += f"{sem.name}: Jami {stats['total']} soat (Sababli: {stats['sababli'] or 0}, Sababsiz: {stats['sababsiz'] or 0})\n"

    context += "\n--- SO'NGGI BAHOLAR ---\n"
    tasks = Task.objects.filter(user=user).exclude(grade_val=0).order_by('-semester__code', '-id')[:20]
    if tasks.exists():
        for t in tasks:
            context += f"{t.semester.name}: {t.subject.name} - {t.grade} ball ({t.name})\n"
    else:
        context += "Baholar yo'q.\n"

    return context

def ask_hemis_ai(user, user_message):
    """
    Hemis AI ning asosiy interfeysi.
    Faqat Hemis ma'lumotlariga asoslangan javob qaytaradi.
    """
    # 1. API Kalitni olish (Markaziy funksiyadan)
    api_key = get_api_key(AGENT_STUDENT)
    
    if not api_key: return "Tizim xatoligi: API kalit topilmadi."

    try:
        genai.configure(api_key=api_key)
        
        # 2. Model tanlash (Markaziy funksiyadan)
        model_name = get_available_model()
        model = genai.GenerativeModel(model_name)
        
        context_data = get_hemis_context(user)
        
        # --- QAT'IY YO'RIQNOMA (PROMPT) ---
        system_instruction = f"""
        Sen "Hemis AI"san - talabaning shaxsiy akademik assistenti.
        
        CONTEXT (MA'LUMOTLAR):
        {context_data}
        
        QAT'IY QOIDALAR:
        1. **Faqat HEMIS Mavzusi:** Sen faqat talabaning o'qish jarayoni, dars jadvallari, baholari, davomati va akademik qarzdorliklari haqida gapira olasan.
        2. **Taqiq:** Agar savol sport, siyosat, kino, kod yozish yoki shaxsiy maslahat haqida bo'lsa, "Men faqat Hemis ma'lumotlari bo'yicha javob bera olaman" deb javobni qisqa qil.
        
        3. **Jadval va Sanalar:**
           - Agar talaba jadval so'rasa, javobni albatta **4 ustunli Markdown Jadval** ko'rinishida ber.
           - Jadval ustunlari aniq shunday bo'lsin: **| Vaqt | Fan | Xona | O'qituvchi |**
           
        4. **Guruhlash:** Agar bir vaqtda 2 ta fan bo'lsa, ularni jadval ichida chiroyli qilib (masalan tagma-tag) yoz.
        
        5. **Manzil va Davomat:** Agar so'ralsa, profildagi aniq raqamlarni olib ber.
        
        6. O'zbek tilida, samimiy va aniq javob ber.
        """
        
        response = model.generate_content(f"{system_instruction}\n\nSAVOL: {user_message}")
        return response.text

    except Exception as e:
        return f"Xatolik ({model_name if 'model_name' in locals() else '?'}) {str(e)}"