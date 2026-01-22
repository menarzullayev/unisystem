from django.db import models
from django.conf import settings

class Section(models.Model):
    SECTION_TYPES = (
        ('reading', '📖 Reading (O\'qish)'),
        ('writing', '✍️ Writing (Yozish)'),
    )

    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    title = models.CharField(max_length=100, default="Section")
    order = models.PositiveIntegerField(default=1, verbose_name="Bosqich")
    duration = models.PositiveIntegerField(default=60, verbose_name="Umumiy vaqt (daqiqada)")
    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")
    
    content_text = models.TextField(null=True, blank=True, verbose_name="Reading: Matn (Passage)")
    
    writing_task1_instruction = models.TextField(null=True, blank=True, verbose_name="Task 1: Yo'riqnoma")
    writing_task1_content = models.TextField(null=True, blank=True, verbose_name="Task 1: Savol Matni")
    
    writing_task2_instruction = models.TextField(null=True, blank=True, verbose_name="Task 2: Yo'riqnoma")
    writing_task2_content = models.TextField(null=True, blank=True, verbose_name="Task 2: Savol Matni")

    def __str__(self):
        return f"{self.get_section_type_display()} - {self.title}"

    class Meta:
        ordering = ['section_type', 'title']
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar (Hovuz)"

class ReadingSection(Section):
    class Meta:
        proxy = True
        verbose_name = "📖 Reading (Matn)"
        verbose_name_plural = "1. Reading Bazasi"

class WritingSection(Section):
    class Meta:
        proxy = True
        verbose_name = "✍️ Writing (Mavzu)"
        verbose_name_plural = "2. Writing Bazasi"

class Question(models.Model):
    TYPE_CHOICES = (
        ('tfng', '⚪ True / False / Not Given'),
        ('gap_fill', '📝 Gap Filling (So\'z kiritish)'),
    )
    
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='tfng', verbose_name="Savol Turi")
    question_text = models.TextField(verbose_name="Savol matni")
    
    correct_option = models.CharField(
        max_length=20, 
        choices=[('TRUE', 'TRUE'), ('FALSE', 'FALSE'), ('NOT GIVEN', 'NOT GIVEN')],
        blank=True, null=True,
        verbose_name="To'g'ri Javob (TFNG)"
    )
    
    correct_text = models.CharField(
        max_length=255, 
        blank=True, null=True, 
        verbose_name="To'g'ri Javob (Gap Fill)"
    )
    
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.question_text[:50]}"

    class Meta:
        ordering = ['order']
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"

class StudentResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_results')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    overall_score = models.FloatField(default=0.0)

    @property
    def title(self):
        return f"Mock Exam ({self.start_time.strftime('%d.%m.%Y %H:%M')})"

    def __str__(self):
        return f"{self.user} - {self.title}"

    class Meta:
        verbose_name = "Imtihon Natijasi"
        verbose_name_plural = "3. Natijalar"

class SectionResult(models.Model):
    student_result = models.ForeignKey(StudentResult, on_delete=models.CASCADE, related_name='section_results')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    user_answers = models.JSONField(null=True, blank=True)
    correct_count = models.IntegerField(default=0)
    writing_task1_response = models.TextField(null=True, blank=True, verbose_name="Task 1 Javobi")
    writing_task2_response = models.TextField(null=True, blank=True, verbose_name="Task 2 Javobi")
    ai_feedback = models.TextField(null=True, blank=True, verbose_name="AI Izohi")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bo'lim Natijasi"
        ordering = ['section__order']