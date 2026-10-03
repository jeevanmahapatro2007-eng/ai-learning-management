from django.contrib import admin
from .models import StudentProgress


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'minutes_learned', 'lessons_completed', 'quizzes_taken')
