from django.contrib import admin
from .models import Quiz, Question, Answer, QuizResult, QuestionResponse


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'quiz_type', 'course', 'pass_mark_percent', 'created_by')
    list_filter = ('quiz_type',)
    inlines = [QuestionInline]
    filter_horizontal = ('skills',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'skill', 'points')
    inlines = [AnswerInline]


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'percent', 'passed', 'taken_at')
    list_filter = ('passed',)
    search_fields = ('student__username', 'quiz__title')
