# core/admin.py

from django.contrib import admin
from .models import User, EssayTopic, Submission, Semester, Schedule

# Admin panel sarlavhasini o'zgartirish
admin.site.site_header = "AI University Boshqaruv Paneli"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Tizim Boshqaruvchisi"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'role', 'group_name', 'hemis_id')
    list_filter = ('role', 'group_name')
    search_fields = ('username', 'full_name')

@admin.register(EssayTopic)
class EssayTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'deadline', 'submission_type', 'created_at')
    search_fields = ('title',)
    list_filter = ('submission_type', 'created_at')

    fields = ('title', 'description', 'topic_file', 'deadline', 'submission_type')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'status', 'final_grade_display', 'submitted_at')
    list_filter = ('status', 'topic', 'submitted_at')
    search_fields = ('user__full_name', 'user__username', 'topic__title')
    readonly_fields = ('ai_grade', 'ai_feedback') 

    def final_grade_display(self, obj):
        return obj.final_grade
    final_grade_display.short_description = "Yakuniy Baho"

admin.site.register(Semester)
admin.site.register(Schedule)