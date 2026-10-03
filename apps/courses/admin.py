from django.contrib import admin
from .models import Category, Skill, Course, Lesson, LearningMaterial, Enrollment


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'difficulty', 'status', 'duration_hours', 'created_at')
    list_filter = ('status', 'difficulty', 'category')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]
    filter_horizontal = ('skills_covered',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'lesson_type', 'order', 'estimated_minutes')
    list_filter = ('lesson_type',)


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'material_type')
    list_filter = ('material_type',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'enrolled_at', 'progress_percent')
    list_filter = ('status',)
    search_fields = ('student__username', 'course__title')
