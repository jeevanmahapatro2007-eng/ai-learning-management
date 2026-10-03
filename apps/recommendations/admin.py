from django.contrib import admin
from .models import StudentSkill, Recommendation, LearningPath, LearningPathStep


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ('student', 'skill', 'proficiency_percent', 'level', 'attempts')
    list_filter = ('level',)
    search_fields = ('student__username', 'skill__name')


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'reason', 'score', 'is_dismissed', 'created_at')
    list_filter = ('reason', 'is_dismissed')


class LearningPathStepInline(admin.TabularInline):
    model = LearningPathStep
    extra = 0


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('student', 'domain', 'updated_at')
    inlines = [LearningPathStepInline]
