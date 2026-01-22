import requests
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

BASE_URL = "https://student.samtuit.uz/rest/v1"
TIMEOUT = 10

def get_auth_token(login, password):
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={'login': login, 'password': password}, timeout=TIMEOUT)
        data = resp.json()
        if data.get('success'):
            return {'success': True, 'token': data['data']['token']}
        return {'success': False, 'error': data.get('error', 'Login xato')}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_student_profile(token):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        resp = requests.get(f"{BASE_URL}/account/me", headers=headers, timeout=TIMEOUT)
        data = resp.json()
        
        doc_resp = requests.get(f"{BASE_URL}/student/document-all", headers=headers, timeout=TIMEOUT)
        doc_data = doc_resp.json()
        diploma = None
        if doc_data.get('success'):
            for d in doc_data.get('data', []):
                if d.get('type') == 'diploma':
                    diploma = {
                        'number': next((a['value'] for a in d['attributes'] if a['label'] == 'Diplom raqami'), '-'),
                        'date': next((a['value'] for a in d['attributes'] if a['label'] == 'Qayd sanasi'), '-')
                    }
                    break

        if data.get('success'):
            info = data['data']
            b_date = '-'
            if info.get('birth_date'):
                try: 
                    b_date = datetime.fromtimestamp(info['birth_date']).strftime('%d.%m.%Y')
                except: 
                    b_date = str(info['birth_date'])

            full_address = info.get('address')
            if not full_address:
                region = info.get('province', {}).get('name', '') if isinstance(info.get('province'), dict) else ''
                district = info.get('district', {}).get('name', '') if isinstance(info.get('district'), dict) else ''
                full_address = f"{region}, {district}".strip(", ")

            return {
                'success': True,
                'name': info.get('full_name', 'Talaba'),
                'id': info.get('student_id_number'),
                'group_id': info.get('group', {}).get('id'),
                'group_name': info.get('group', {}).get('name'),
                'level': info.get('level', {}).get('name'),
                'faculty': info.get('faculty', {}).get('name'),
                'specialty': info.get('specialty', {}).get('name'),
                'image': info.get('image'), 
                'phone': info.get('phone', 'Kiritilmagan'),
                'address': full_address or 'Manzil kiritilmagan',
                'birth_date': b_date,
                'gpa': info.get('avg_gpa', '0'),
                'passport': "Himoyalangan (AD*******)",
                'diploma': diploma
            }
        return {'success': False, 'error': 'Profil topilmadi'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_semester_list(token):
    headers = {'Authorization': f'Bearer {token}'}
    try:
        resp = requests.get(f"{BASE_URL}/education/semesters", headers=headers, timeout=TIMEOUT)
        data = resp.json()
        semesters = []
        if data.get('success'):
            for item in data['data']:
                sem_code = item.get('code')
                val = str(sem_code) if sem_code else str(item['id'])
                semesters.append({
                    'id': val, 
                    'name': item.get('name'),
                    'current': item.get('current', False)
                })
            semesters.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 0, reverse=True)
        return semesters
    except:
        return []

def get_attendance(token, semester_id):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'semester': semester_id} if semester_id else {}
    try:
        resp = requests.get(f"{BASE_URL}/education/attendance", headers=headers, params=params, timeout=TIMEOUT)
        data = resp.json()
        stats = {'total': 0, 'sababli': 0, 'sababsiz': 0, 'list': []}
        
        if data.get('success'):
            items = data['data'] if isinstance(data['data'], list) else data['data'].get('items', [])
            for i in items:
                off = i.get('absent_off', 0) or 0
                on = i.get('absent_on', 0) or 0
                h = off + on
                is_excused = i.get('explicable', False)
                
                stats['total'] += h
                if is_excused: stats['sababli'] += h
                else: stats['sababsiz'] += h
                
                d_str = datetime.fromtimestamp(i['lesson_date']).strftime('%d.%m.%Y') if i.get('lesson_date') else '-'
                
                teacher = i.get('employee', {}).get('name', 'Aniqlanmagan')
                training_type = i.get('trainingType', {}).get('name', '-')
                
                l_pair = i.get('lessonPair', {})
                start = l_pair.get('start_time', '')
                end = l_pair.get('end_time', '')
                time_str = f"{start} - {end}" if start and end else '-'

                stats['list'].append({
                    'subject': i.get('subject', {}).get('name'),
                    'date': d_str,
                    'type': "Sababli" if is_excused else "Sababsiz",
                    'hours': h,
                    'teacher': teacher,
                    'time': time_str,
                    'training_type': training_type
                })
        return stats
    except Exception as e:
        logger.error(f"Attendance error: {e}")
        return {'total': 0}

def get_schedule_with_weeks(token, semester_id, selected_week_id=None):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'semester': semester_id} if semester_id else {}

    result = {
        'weeks': [],
        'schedule': [],
        'active_week_id': None
    }

    try:
        resp = requests.get(f"{BASE_URL}/education/schedule", headers=headers, params=params, timeout=TIMEOUT)
        data = resp.json()
        
        items = []
        if data.get('success'):
            items = data['data'] if isinstance(data['data'], list) else data['data'].get('items', [])

        if not items:
            return result

        weeks_map = {}
        valid_week_ids = set()

        for item in items:
            w_id = item.get('_week')
            start = item.get('weekStartTime')
            end = item.get('weekEndTime')
            
            if w_id:
                valid_week_ids.add(int(w_id)) 
                if w_id not in weeks_map:
                    weeks_map[w_id] = {
                        'id': w_id,
                        'start': start,
                        'end': end
                    }
        
        if selected_week_id:
            try:
                if int(selected_week_id) not in valid_week_ids:
                    selected_week_id = None
            except:
                selected_week_id = None

        sorted_weeks = sorted(weeks_map.values(), key=lambda x: x['start'])
        current_ts = int(time.time())
        final_weeks = []
        for idx, w in enumerate(sorted_weeks):
            s_date = datetime.fromtimestamp(w['start']).strftime('%d.%m')
            e_date = datetime.fromtimestamp(w['end']).strftime('%d.%m')
            is_current = (w['start'] <= current_ts <= w['end'])
            final_weeks.append({
                'id': w['id'],
                'name': f"{idx + 1}-hafta ({s_date} - {e_date})",
                'current': is_current
            })
            if not selected_week_id and is_current:
                selected_week_id = w['id']

        if not selected_week_id and final_weeks:
            selected_week_id = final_weeks[0]['id']

        result['weeks'] = final_weeks
        result['active_week_id'] = selected_week_id

        week_days_order = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]
        grouped_schedule = {day: [] for day in week_days_order}
        
        try:
            target_week = int(selected_week_id) if selected_week_id else 0
        except:
            target_week = 0

        for item in items:
            if item.get('_week') != target_week: continue
            if item.get('lesson_date'):
                dt = datetime.fromtimestamp(item['lesson_date'])
                day_index = dt.weekday()
                if day_index > 5: continue 
                day_name = week_days_order[day_index]
            else:
                continue

            subj = item.get('subject', {}).get('name')
            start = item.get('lessonPair', {}).get('start_time')
            end = item.get('lessonPair', {}).get('end_time')
            
            existing = False
            for lesson in grouped_schedule[day_name]:
                if lesson['time'] == f"{start} - {end}" and lesson['subject'] == subj:
                    existing = True
                    break
            
            if not existing:
                grouped_schedule[day_name].append({
                    'subject': subj,
                    'time': f"{start} - {end}",
                    'teacher': item.get('employee', {}).get('name'),
                    'room': item.get('auditorium', {}).get('name', 'Onlayn'),
                    'type': item.get('trainingType', {}).get('name')
                })

        final_list = []
        for day in week_days_order:
            if grouped_schedule[day]:
                grouped_schedule[day].sort(key=lambda x: x['time'])
                final_list.append({
                    'day_name': day,
                    'lessons': grouped_schedule[day]
                })
        
        result['schedule'] = final_list
        return result

    except Exception as e:
        logger.error(f"Schedule error: {e}")
        return result

def get_tasks(token, semester_id):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'semester': semester_id} if semester_id else {}
    
    try:
        resp = requests.get(f"{BASE_URL}/education/task-list", headers=headers, params=params, timeout=TIMEOUT)
        data = resp.json()
        tasks = []
        if data.get('success'):
            items = data['data'] if isinstance(data['data'], list) else data['data'].get('items', [])
            for t in items:
                deadline = datetime.fromtimestamp(t['deadline']).strftime('%d.%m.%Y') if t.get('deadline') else 'Muddatsiz'
                
                status_name = t.get('taskStatus', {}).get('name', 'Noma\'lum')
                
                grade_val = 0
                max_ball_val = 0
                percentage = 0
                grade_str = "-"

                if t.get('max_ball'):
                    try: max_ball_val = float(t['max_ball'])
                    except: max_ball_val = 0

                act = t.get('studentTaskActivity')
                if act and act.get('mark'):
                    grade_str = str(act['mark'])
                    try:
                        grade_val = float(act['mark'])
                        if max_ball_val > 0:
                            percentage = int((grade_val / max_ball_val) * 100)
                    except: pass
                
                tasks.append({
                    'subject': t.get('subject', {}).get('name'),
                    'name': t.get('name'),
                    'deadline': deadline,
                    'status': status_name,
                    'grade': grade_str,
                    'grade_val': grade_val,
                    'max_ball': max_ball_val,
                    'percentage': percentage
                })
        return tasks
    except Exception as e:
        logger.error(f"Tasks error: {e}")
        return []