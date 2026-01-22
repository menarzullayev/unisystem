from django.contrib import admin
from .models import (
    Section, Question, StudentResult, SectionResult,
    ReadingSection, WritingSection
)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('order', 'question_type', 'question_text', 'correct_option', 'correct_text')

@admin.register(ReadingSection)
class ReadingAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    fields = ('title', 'is_active', 'duration', 'content_text')
    list_display = ('title', 'duration', 'is_active', 'question_count')
    list_filter = ('is_active',)

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = "Savollar soni"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(section_type='reading')

    def save_model(self, request, obj, form, change):
        obj.section_type = 'reading'
        obj.order = 1
        super().save_model(request, obj, form, change)

@admin.register(WritingSection)
class WritingAdmin(admin.ModelAdmin):
    list_display = ('title', 'duration', 'is_active')
    list_filter = ('is_active',)

    fieldsets = (
        ('Umumiy Sozlamalar', {
            'fields': ('title', 'duration', 'is_active')
        }),
        ('Writing Task 1', {
            'fields': ('writing_task1_instruction', 'writing_task1_content'),
        }),
        ('Writing Task 2', {
            'fields': ('writing_task2_instruction', 'writing_task2_content'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(section_type='writing')

    def save_model(self, request, obj, form, change):
        obj.section_type = 'writing'
        obj.order = 2
        super().save_model(request, obj, form, change)

@admin.register(StudentResult)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'overall_score', 'start_time', 'is_completed')
    list_filter = ('is_completed', 'start_time')

@admin.register(SectionResult)
class SectionResultAdmin(admin.ModelAdmin):
    list_display = ('student_result', 'section', 'score', 'completed_at')