from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

from .forms import CourseForm, LessonForm, LearningMaterialForm, CourseSearchForm
from .models import Course, Lesson, Enrollment, Category
from apps.notifications.services import notify
from apps.gamification.services import award_first_course_badge, check_completion_badges, update_streak


def course_list(request):
    form = CourseSearchForm(request.GET or None)
    courses = Course.objects.filter(status=Course.Status.PUBLISHED).select_related('category', 'instructor')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        difficulty = form.cleaned_data.get('difficulty')
        duration = form.cleaned_data.get('duration')

        if q:
            courses = courses.filter(
                Q(title__icontains=q) | Q(skills_covered__name__icontains=q) | Q(description__icontains=q)
            ).distinct()
        if category:
            courses = courses.filter(category=category)
        if difficulty:
            courses = courses.filter(difficulty=difficulty)
        if duration == 'short':
            courses = courses.filter(duration_hours__lt=5)
        elif duration == 'medium':
            courses = courses.filter(duration_hours__gte=5, duration_hours__lte=15)
        elif duration == 'long':
            courses = courses.filter(duration_hours__gt=15)

    # distinct=True: the skills_covered join above would otherwise multiply the enrollment count
    courses = courses.annotate(enrolled_count=Count('enrollments', distinct=True))
    paginator = Paginator(courses, 9)
    page = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'courses/course_list.html', {
        'form': form, 'page_obj': page, 'querystring': params.urlencode(),
    })


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
    lessons = course.lessons.all()
    enrollment = None
    if request.user.is_authenticated and request.user.is_student:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    return render(request, 'courses/course_detail.html', {
        'course': course, 'lessons': lessons, 'enrollment': enrollment,
        'via': request.GET.get('via', ''),
    })


@login_required
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)
    if not request.user.is_student:
        messages.error(request, 'Only student accounts can enroll in courses.')
        return redirect('courses:detail', slug=slug)

    was_recommended = request.GET.get('via') == 'recommendation'
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user, course=course, defaults={'was_recommended': was_recommended}
    )
    if created:
        messages.success(request, f'Enrolled in "{course.title}". Happy learning!')
        notify(request.user, title='Enrollment confirmed', message=f'You enrolled in {course.title}.', category='course')
    else:
        messages.info(request, 'You are already enrolled in this course.')
    return redirect('courses:learn', slug=slug)


@login_required
def learn(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lessons = course.lessons.prefetch_related('materials')

    lesson_id = request.GET.get('lesson')
    current_lesson = None
    if lesson_id and lesson_id.isdigit():
        current_lesson = lessons.filter(id=int(lesson_id)).first()
    if current_lesson is None:
        current_lesson = lessons.first()

    if current_lesson:
        enrollment.last_accessed_lesson = current_lesson
        enrollment.last_accessed_at = timezone.now()
        enrollment.save(update_fields=['last_accessed_lesson', 'last_accessed_at'])

    return render(request, 'courses/learn.html', {
        'course': course, 'lessons': lessons, 'enrollment': enrollment, 'current_lesson': current_lesson,
        'completed_ids': set(enrollment.completed_lessons.values_list('id', flat=True)),
    })


@login_required
@require_POST
def mark_lesson_complete(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    already_done = enrollment.completed_lessons.filter(pk=lesson.pk).exists()
    enrollment.completed_lessons.add(lesson)
    if not already_done:
        # feeds the "learning hours" stat on the dashboard (previously never updated)
        profile = getattr(request.user, 'student_profile', None)
        if profile:
            profile.total_learning_minutes += lesson.estimated_minutes
            profile.save(update_fields=['total_learning_minutes'])
        update_streak(request.user)

    if enrollment.progress_percent >= 100 and enrollment.status != Enrollment.Status.COMPLETED:
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=['status', 'completed_at'])
        messages.success(request, f'Course completed! "{course.title}" is now marked complete.')
        notify(request.user, title='Course completed', message=f'You finished {course.title}. Great work!', category='achievement')
        award_first_course_badge(request.user)
        check_completion_badges(request.user)
    # completed_lessons.add() above already persists the M2M change directly;
    # no further save() is needed unless the course was just marked complete.

    messages.success(request, f'Marked "{lesson.title}" as complete.')
    learn_url = reverse('courses:learn', kwargs={'slug': slug})
    return redirect(f'{learn_url}?lesson={lesson.id}')


# ---------------------------------------------------------------------------
# Instructor course management
# ---------------------------------------------------------------------------

def _require_instructor(request):
    return request.user.is_authenticated and request.user.is_instructor


def _enforce_publish_rule(request, course):
    """Instructors must be admin-approved before a course can go live."""
    if course.status == Course.Status.PUBLISHED and not request.user.is_instructor_approved:
        course.status = Course.Status.DRAFT
        messages.warning(request, 'Saved as draft — your instructor account must be approved before you can publish.')


@login_required
def instructor_course_list(request):
    if not _require_instructor(request):
        return HttpResponseForbidden('Instructor access only.')
    courses = Course.objects.filter(instructor=request.user).annotate(
        enrolled_count=Count('enrollments')
    ).select_related('category')
    return render(request, 'courses/instructor_course_list.html', {'courses': courses})


@login_required
def course_create(request):
    if not _require_instructor(request):
        return HttpResponseForbidden('Instructor access only.')
    if not request.user.is_instructor_approved:
        messages.warning(request, 'Your instructor account is pending admin approval. You can still draft courses.')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            _enforce_publish_rule(request, course)
            course.save()
            form.save_m2m()
            messages.success(request, 'Course created. Now add lessons and materials.')
            return redirect('courses:instructor_lessons', slug=course.slug)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'mode': 'create'})


@login_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user:
        return HttpResponseForbidden('You do not own this course.')
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            course = form.save(commit=False)
            _enforce_publish_rule(request, course)
            course.save()
            form.save_m2m()
            messages.success(request, 'Course updated.')
            return redirect('courses:instructor_courses')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'mode': 'edit', 'course': course})


@login_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user:
        return HttpResponseForbidden('You do not own this course.')
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted.')
        return redirect('courses:instructor_courses')
    return render(request, 'courses/course_confirm_delete.html', {'course': course})


@login_required
def instructor_lessons(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user:
        return HttpResponseForbidden('You do not own this course.')

    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            form.save_m2m()
            messages.success(request, 'Lesson added.')
            return redirect('courses:instructor_lessons', slug=slug)
    else:
        form = LessonForm()

    return render(request, 'courses/instructor_lessons.html', {
        'course': course, 'lessons': course.lessons.all(), 'form': form,
    })


@login_required
def instructor_materials(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    if course.instructor != request.user:
        return HttpResponseForbidden('You do not own this course.')
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

    if request.method == 'POST':
        form = LearningMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.lesson = lesson
            material.save()
            messages.success(request, 'Material added.')
            return redirect('courses:instructor_materials', slug=slug, lesson_id=lesson_id)
    else:
        form = LearningMaterialForm()

    return render(request, 'courses/instructor_materials.html', {
        'course': course, 'lesson': lesson, 'materials': lesson.materials.all(), 'form': form,
    })
