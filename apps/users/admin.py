from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, StudentProfile, InstructorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_instructor_approved', 'is_active')
    list_filter = ('role', 'is_instructor_approved', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Lodestar role', {'fields': ('role', 'phone_number', 'is_instructor_approved')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Lodestar role', {'fields': ('role', 'email')}),
    )

    actions = ['approve_instructors']

    @admin.action(description='Approve selected instructor accounts')
    def approve_instructors(self, request, queryset):
        updated = queryset.filter(role=User.Role.INSTRUCTOR).update(is_instructor_approved=True)
        self.message_user(request, f'{updated} instructor account(s) approved.')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_level', 'points', 'daily_streak')
    list_filter = ('current_level',)
    search_fields = ('user__username', 'user__email')


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'years_of_experience')
    search_fields = ('user__username', 'user__email')
