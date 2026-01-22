# hemis_ai/edu/views.py

import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Section, SectionResult, StudentResult
from .ai_examiner import grade_writing_full_exam

@login_required
def exam_landing_page(request):
    history = StudentResult.objects.filter(user=request.user, is_completed=True).order_by('-start_time')
    return render(request, 'edu/exam_landing.html', {'history': history})

@login_required
def start_random_exam(request):
    section_types = ['reading', 'writing']
    selected_sections = []

    for s_type in section_types:
        available_ids = list(Section.objects.filter(section_type=s_type, is_active=True).values_list('id', flat=True))
        if not available_ids:
            messages.error(request, f"Tizimda '{s_type}' bo'limi uchun ma'lumotlar yetarli emas.")
            return redirect('exam_list')
        
        random_id = random.choice(available_ids)
        selected_sections.append(Section.objects.get(id=random_id))

    result = StudentResult.objects.create(user=request.user)
    for section in selected_sections:
        SectionResult.objects.create(student_result=result, section=section)

    first_section = min(selected_sections, key=lambda x: x.order)
    return redirect('take_section', result_id=result.id, section_id=first_section.id)

@login_required
def take_section_view(request, result_id, section_id):
    result = get_object_or_404(StudentResult, id=result_id, user=request.user)
    section = get_object_or_404(Section, id=section_id)
    
    if result.is_completed:
        return redirect('exam_result', result_id=result.id)

    if request.method == 'POST':
        sec_res = get_object_or_404(SectionResult, student_result=result, section=section)
        
        if section.section_type == 'reading':
            user_answers = {}
            correct_count = 0
            questions = section.questions.all()
            total_q = questions.count()
            
            for q in questions:
                ans = request.POST.get(f'question_{q.id}')
                if ans:
                    user_answers[str(q.id)] = ans
                    if q.question_type == 'tfng':
                        if ans.strip().upper() == (q.correct_option or "").strip().upper():
                            correct_count += 1
                    elif q.question_type == 'gap_fill':
                        if ans.strip().lower() == (q.correct_text or "").strip().lower():
                            correct_count += 1
            
            sec_res.user_answers = user_answers
            sec_res.correct_count = correct_count
            sec_res.score = round((correct_count / total_q) * 9, 1) if total_q > 0 else 0.0
            sec_res.save()

        elif section.section_type == 'writing':
            task1_text = request.POST.get('task1_text', '')
            task2_text = request.POST.get('task2_text', '')
            sec_res.writing_task1_response = task1_text
            sec_res.writing_task2_response = task2_text
            sec_res.save()
            
            try:
                grade, feedback = grade_writing_full_exam(
                    section.writing_task1_content, task1_text,
                    section.writing_task2_content, task2_text
                )
                sec_res.score = grade
                sec_res.ai_feedback = feedback
            except Exception as e:
                sec_res.score = 0
                sec_res.ai_feedback = f"Xatolik: {str(e)}"
            sec_res.save()

        # Keyingi bo'limga o'tish
        all_results = result.section_results.all().order_by('section__order')
        next_sec = None
        found = False
        for sr in all_results:
            if found:
                next_sec = sr.section
                break
            if sr.section.id == section.id:
                found = True
        
        if next_sec:
            return redirect('take_section', result_id=result.id, section_id=next_sec.id)
        else:
            finish_exam(result)
            return redirect('exam_result', result_id=result.id)

    # --- INPUTLARNI O'ZGARTIRISH LOGIKASI ---
    # 1. Asosiy matnni o'zgartirish
    final_content = section.content_text.replace('[input]', '________________') if section.content_text else ""

    # 2. Savollar ichidagi [input] ni o'zgartirish
    questions = section.questions.all()
    for q in questions:
        if q.question_text:
            q.question_text = q.question_text.replace('[input]', '________________')

    return render(request, 'edu/exam_session.html', {
        'section': section,
        'result': result,
        'questions': questions,
        'displayed_content': final_content
    })

def finish_exam(result):
    results = result.section_results.all()
    if results.exists():
        total = sum([r.score for r in results])
        result.overall_score = round(total / results.count(), 1)
    result.is_completed = True
    result.end_time = timezone.now()
    result.save()

@login_required
def exam_result_view(request, result_id):
    result = get_object_or_404(StudentResult, id=result_id, user=request.user)
    return render(request, 'edu/exam_result.html', {'result': result})