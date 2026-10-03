from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.users.models import User
from apps.courses.models import Course, Category
from apps.analytics.services import admin_overview
from apps.notifications.services import notify


def _is_admin(user):
    return user.is_authenticated and user.is_platform_admin


@login_required
@user_passes_test(_is_admin)
def console_home(request):
    return render(request, 'administration/console_home.html', {'overview': admin_overview()})


@login_required
@user_passes_test(_is_admin)
def manage_students(request):
    students = User.objects.filter(role=User.Role.STUDENT).select_related('student_profile')
    return render(request, 'administration/manage_students.html', {'students': students})


@login_required
@user_passes_test(_is_admin)
def manage_instructors(request):
    instructors = User.objects.filter(role=User.Role.INSTRUCTOR).select_related('instructor_profile')
    return render(request, 'administration/manage_instructors.html', {'instructors': instructors})


@login_required
@user_passes_test(_is_admin)
@require_POST
def approve_instructor(request, pk):
    instructor = get_object_or_404(User, pk=pk, role=User.Role.INSTRUCTOR)
    instructor.is_instructor_approved = True
    instructor.save(update_fields=['is_instructor_approved'])
    notify(instructor, title='Instructor account approved', message='You can now publish courses on Lodestar.', category='system')
    messages.success(request, f'{instructor.get_full_name() or instructor.username} approved.')
    return redirect('administration:manage_instructors')


@login_required
@user_passes_test(_is_admin)
@require_POST
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('administration:console_home')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f'{user.username} is now {"active" if user.is_active else "deactivated"}.')
    back = request.META.get('HTTP_REFERER', '')
    if back and url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
        return redirect(back)
    return redirect('administration:console_home')


@login_required
@user_passes_test(_is_admin)
def manage_courses(request):
    courses = Course.objects.select_related('instructor', 'category')
    return render(request, 'administration/manage_courses.html', {'courses': courses})


@login_required
@user_passes_test(_is_admin)
def manage_categories(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.get_or_create(name=name)
            messages.success(request, f'Category "{name}" added.')
        return redirect('administration:manage_categories')
    return render(request, 'administration/manage_categories.html', {'categories': categories})
