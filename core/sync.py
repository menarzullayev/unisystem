# core/sync.py
import requests
from django.conf import settings
from .models import Semester, Week, Schedule, Attendance, Task, Subject
from .services import get_auth_token  # Yordamchi funksiya kerak bo'ladi

API_BASE = "https://student.samdu.uz/rest/v1"

def sync_student_data(user):

    if not user.hemis_login or not user.hemis_password:
        print(f"❌ {user.username}: Login yoki parol saqlanmagan.")
        return False

    headers = {'Authorization': f'Bearer {user.hemis_token}'}

    try:
        test_resp = requests.get(f"{API_BASE}/education/semester", headers=headers, timeout=5)
        
        if test_resp.status_code == 401:
            print(f"🔄 {user.username}: Token eskirgan. Yangilanmoqda...")
            
            auth_data = get_auth_token(user.hemis_login, user.hemis_password)
            
            if auth_data['success']:
                new_token = auth_data['token']
                user.hemis_token = new_token
                user.save()
                
                # Headerni yangilaymiz
                headers = {'Authorization': f'Bearer {new_token}'}
                print(f"✅ {user.username}: Token muvaffaqiyatli yangilandi.")
            else:
                print(f"❌ {user.username}: Tokenni yangilab bo'lmadi. Parol o'zgargan bo'lishi mumkin.")
                return False

    except Exception as e:
        print(f"Internet xatosi: {e}")
        return False

    # ---------------------------------------------------------
    # AGAR TOKEN ISHLASA, MA'LUMOTLARNI YUKLASHNI BOSHLAYMIZ
    # ---------------------------------------------------------
    
    try:
        # 1. SEMESTRLARNI YUKLASH
        sem_resp = requests.get(f"{API_BASE}/education/semester", headers=headers)
        if sem_resp.status_code == 200:
            sem_data = sem_resp.json().get('data', [])
            for s in sem_data:
                Semester.objects.update_or_create(
                    code=str(s['code']),
                    defaults={'name': s['name'], 'current': s.get('current', False)}
                )

        # Joriy semestrni aniqlaymiz
        current_sem = Semester.objects.filter(current=True).first()
        if not current_sem:
            current_sem = Semester.objects.order_by('-code').first()
        
        if not current_sem:
            return True 
        week_resp = requests.get(f"{API_BASE}/education/week", headers=headers)
        if week_resp.status_code == 200:
            week_data = week_resp.json().get('data', [])
            for w in week_data:
                Week.objects.update_or_create(
                    week_id=str(w['id']),
                    defaults={
                        'name': w['name'],
                        'start_date': w['startDate'],
                        'end_date': w['endDate']
                    }
                )

        sched_resp = requests.get(f"{API_BASE}/education/schedule", headers=headers, params={'semester': current_sem.code})
        
        if sched_resp.status_code == 200:
            sched_data = sched_resp.json().get('data', [])
            Schedule.objects.filter(user=user, semester=current_sem).delete()
            
            for item in sched_data:
                subject_name = item.get('subject', {}).get('name', 'Noma\'lum fan')
                subject, _ = Subject.objects.get_or_create(name=subject_name)
                
                week_data = item.get('week', {})
                week_obj = None
                if week_data:
                    try:
                        week_obj, _ = Week.objects.get_or_create(
                            week_id=str(week_data.get('id')),
                            defaults={
                                'name': week_data.get('name', ''),
                                'start_date': datetime.fromtimestamp(week_data.get('startDate')),
                                'end_date': datetime.fromtimestamp(week_data.get('endDate'))
                            }
                        )
                    except:
                        pass 

                Schedule.objects.create(
                    user=user,
                    semester=current_sem,
                    week_id=str(week_data.get('id')) if week_data else None,
                    day_name=item.get('weekDay', {}).get('name', ''),
                    subject=subject,
                    lesson_time=f"{item.get('lessonPair', {}).get('startTime', '')} - {item.get('lessonPair', {}).get('endTime', '')}",
                    teacher=item.get('employee', {}).get('name', ''),
                    room=item.get('auditorium', {}).get('name', ''),
                    training_type=item.get('trainingType', {}).get('name', '')
                )

        # 4. DAVOMAT (ATTENDANCE)
        att_resp = requests.get(f"{API_BASE}/education/attendance", headers=headers, params={'semester': current_sem.code})
        if att_resp.status_code == 200:
            att_data = att_resp.json().get('data', [])
            Attendance.objects.filter(user=user, semester=current_sem).delete()
            
            for item in att_data:
                subject_name = item.get('subject', {}).get('name', 'Noma\'lum fan')
                subject, _ = Subject.objects.get_or_create(name=subject_name)
                
                Attendance.objects.create(
                    user=user,
                    semester=current_sem,
                    subject=subject,
                    date=item.get('date', '2024-01-01'),
                    hours=item.get('length', 2),
                    type=item.get('attendanceType', {}).get('name', 'Sababsiz'),
                    teacher=item.get('employee', {}).get('name', ''),
                    training_type=item.get('trainingType', {}).get('name', '')
                )

        task_resp = requests.get(f"{API_BASE}/education/performance", headers=headers, params={'semester': current_sem.code})
        if task_resp.status_code == 200:
            task_data = task_resp.json().get('data', [])
            Task.objects.filter(user=user, semester=current_sem).delete()
            
            for item in task_data:
                subject_name = item.get('subject', {}).get('name', 'Fan')
                subject, _ = Subject.objects.get_or_create(name=subject_name)
                
                Task.objects.create(
                    user=user,
                    semester=current_sem,
                    subject=subject,
                    name=item.get('name', 'Nazorat ishi'),
                    deadline=item.get('deadline', ''),
                    status=item.get('studentStatus', {}).get('name', 'Topshirilmagan'),
                    grade=str(item.get('grade', {}).get('score', 0)),
                    grade_val=float(item.get('grade', {}).get('score', 0) or 0),
                    max_ball=float(item.get('maxScore', 0) or 0)
                )

        return True

    except Exception as e:
        print(f"Sync jarayonida xatolik: {e}")
        return False