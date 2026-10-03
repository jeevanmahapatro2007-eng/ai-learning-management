from django.contrib import admin
from .models import Badge, StudentBadge, Achievement


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'points_reward')


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'awarded_at')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'description', 'points', 'created_at')
