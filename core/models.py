from django.db import models
from django.contrib.auth.models import AbstractUser

# -----------------------------------------------------------------------------
# 1. FOYDALANUVCHI MODELI (USER)
# -----------------------------------------------------------------------------

class User(AbstractUser):
    # ROLLAR
    ROLE_CHOICES = (
        ('student', 'Talaba'),
        ('teacher', 'O\'qituvchi'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Rol")

    # TIZIMGA KIRISH (HEMIS)
    hemis_id = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Hemis ID")
    hemis_login = models.CharField(max_length=50, null=True, blank=True, verbose_name="Hemis Login")
    hemis_password = models.CharField(max_length=100, null=True, blank=True, verbose_name="Hemis Parol")
    hemis_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="Token")
    
    # TELEGRAM INTEGRATSIYASI
    telegram_chat_id = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="Telegram ID")

    # PROFIL MA'LUMOTLARI
    full_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="F.I.Sh")
    image = models.URLField(null=True, blank=True, verbose_name="Rasm URL")
    group_name = models.CharField(max_length=50, null=True, blank=True, verbose_name="Guruh")
    faculty = models.CharField(max_length=100, null=True, blank=True, verbose_name="Fakultet")
    specialty = models.CharField(max_length=100, null=True, blank=True, verbose_name="Mutaxassislik")
    level = models.CharField(max_length=20, null=True, blank=True, verbose_name="Kurs/Bosqich")
    gpa = models.CharField(max_length=10, null=True, blank=True, verbose_name="GPA")
    
    # QO'SHIMCHA MA'LUMOTLAR
    phone = models.CharField(max_length=50, null=True, blank=True, verbose_name="Telefon")
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Manzil")
    birth_date = models.CharField(max_length=30, null=True, blank=True, verbose_name="Tug'ilgan sana")
    
    def __str__(self):
        return self.full_name if self.full_name else self.username

    @property
    def is_teacher(self):
        return self.role == 'teacher' or self.is_staff

    @property
    def is_student(self):
        return self.role == 'student'

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"


# -----------------------------------------------------------------------------
# 2. HEMIS TIZIMI MODELLARI
# -----------------------------------------------------------------------------

class Semester(models.Model):
    code = models.CharField(max_length=20, unique=True) 
    name = models.CharField(max_length=50) 
    current = models.BooleanField(default=False)
    def __str__(self): return self.name
    class Meta: verbose_name = "Semestr"; verbose_name_plural = "Semestrlar"

class Subject(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self): return self.name
    class Meta: verbose_name = "Fan"; verbose_name_plural = "Fanlar"

class Week(models.Model):
    week_id = models.CharField(max_length=20) 
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    class Meta: verbose_name = "Hafta"; verbose_name_plural = "Haftalar"

class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    week_id = models.CharField(max_length=20, null=True)
    day_name = models.CharField(max_length=20)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    lesson_time = models.CharField(max_length=50)
    teacher = models.CharField(max_length=100, null=True)
    room = models.CharField(max_length=50, null=True)
    training_type = models.CharField(max_length=50, null=True)
    class Meta:
        ordering = ['week_id', 'day_name', 'lesson_time']
        verbose_name = "Dars Jadvali"
        verbose_name_plural = "Dars Jadvallari"

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    hours = models.IntegerField()
    type = models.CharField(max_length=20)
    teacher = models.CharField(max_length=100, null=True)
    training_type = models.CharField(max_length=50, null=True)
    time_str = models.CharField(max_length=50, null=True)
    class Meta: verbose_name = "Davomat"; verbose_name_plural = "Davomatlar"

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    deadline = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    grade = models.CharField(max_length=10, default="-")
    grade_val = models.FloatField(default=0)
    max_ball = models.FloatField(default=0)
    percentage = models.IntegerField(default=0)
    def __str__(self): return f"{self.subject.name} - {self.name}"
    class Meta: verbose_name = "Topshiriq/Baho"; verbose_name_plural = "Topshiriqlar va Baholar"


# -----------------------------------------------------------------------------
# 3. YOZMA ISH (ESSAY) VA AI BAHOLASH MODELLARI
# -----------------------------------------------------------------------------

class EssayTopic(models.Model):
    SUBMISSION_TYPES = (
        ('text', 'Faqat Matn'),
        ('file', 'Faqat Fayl/Rasm'),
        ('both', 'Ixtiyoriy (Matn yoki Fayl)'),
    )

    title = models.CharField(max_length=255, verbose_name="Mavzu nomi")
    description = models.TextField(verbose_name="Tavsif (Matn ko'rinishida)", blank=True, null=True)
    
    topic_file = models.FileField(
        upload_to='topic_files/', 
        verbose_name="Savol Fayli (Rasm/PDF)", 
        blank=True, null=True,
        help_text="Agar savol rasmda bo'lsa, shu yerga yuklang."
    )
    
    deadline = models.DateTimeField(verbose_name="Topshirish muddati")
    
    submission_type = models.CharField(
        max_length=10, 
        choices=SUBMISSION_TYPES, 
        default='both', 
        verbose_name="Topshirish turi"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    def __str__(self): return self.title

    class Meta:
        verbose_name = "Yozma Ish Mavzusi"
        verbose_name_plural = "✍️ Yozma Ish Mavzulari"

class Submission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Tekshirilmoqda (AI)'),
        ('ai_graded', 'AI Baholadi (Qayta topshirish mumkin)'),
        ('appeal', 'Apellatsiya (Domlaga)'),
        ('teacher_review', 'Domla Tekshiruvida'),
        ('done', 'Baholandi'),
        ('resubmit', 'Qayta topshirishga ruxsat berildi'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', verbose_name="Talaba")
    topic = models.ForeignKey(EssayTopic, on_delete=models.CASCADE, related_name='submissions', verbose_name="Mavzu")
    
    # Talaba javobi: Matn va/yoki Fayl
    content = models.TextField(verbose_name="Javob matni", blank=True, null=True)
    file = models.FileField(upload_to='essays/', verbose_name="Yuklangan fayl (Rasm)", blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Holat")
    
    # AI Bahosi
    ai_grade = models.IntegerField(null=True, blank=True, verbose_name="AI Bahosi")
    ai_feedback = models.TextField(null=True, blank=True, verbose_name="AI Izohi")
    
    # O'qituvchi Bahosi
    teacher_grade = models.IntegerField(null=True, blank=True, verbose_name="O'qituvchi Bahosi")
    teacher_feedback = models.TextField(null=True, blank=True, verbose_name="O'qituvchi Izohi")
    
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Topshirilgan vaqt")

    def __str__(self):
        return f"{self.user.full_name} - {self.topic.title}"

    @property
    def final_grade(self):
        return self.teacher_grade if self.teacher_grade is not None else self.ai_grade
    
    @property
    def can_resubmit(self):
        return self.status in ['ai_graded', 'resubmit']

    class Meta:
        verbose_name = "Topshirilgan Ish"
        verbose_name_plural = "📥 Topshirilgan Ishlar"


# -----------------------------------------------------------------------------
# 4. BOT XABARNOMALARI TARIXI (YANGI)
# -----------------------------------------------------------------------------

class NotificationLog(models.Model):
    """
    Bu model bot orqali yuborilgan xabarlarni saqlab boradi.
    Maqsad: Qayta-qayta (duplicate) xabar yuborishni oldini olish.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Unikal kalit: masalan "topic_15_1day" yoki "subject_3_nb_5"
    notification_key = models.CharField(max_length=255, verbose_name="Bildirishnoma Kaliti")
    
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    def __str__(self):
        return f"{self.user.username} - {self.notification_key}"

    class Meta:
        # Bir xil kalitli xabar bir userga faqat bir marta yozilishi mumkin
        unique_together = ('user', 'notification_key') 
        verbose_name = "Bot Tarixi"
        verbose_name_plural = "🤖 Bot Bildirishnomalari"