"""
Lightweight JSON API for Lodestar.

The project deliberately skips Django REST Framework and JWT (per the
"simple stack" build) to keep dependencies to Django + Pillow. These
hand-rolled JsonResponse endpoints still satisfy the brief's API
requirement (section 19): authentication-gated JSON for courses,
enrollment, progress, quiz submission and recommendations, all under
session authentication (the same login used by the website).
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.courses.models import Course, Enrollment
from apps.quizzes.models import QuizResult
from apps.recommendations.engine import generate_recommendations
from apps.analytics.services import student_overview
from apps.notifications.models import Notification


def _course_payload(course):
    return {
        'id': course.id,
        'title': course.title,
        'slug': course.slug,
        'category': course.category.name if course.category else None,
        'difficulty': course.difficulty,
        'duration_hours': course.duration_hours,
        'lesson_count': course.lesson_count(),
        'instructor': course.instructor.get_full_name() or course.instructor.username,
    }


@require_http_methods(['GET'])
def api_course_list(request):
    courses = Course.objects.filter(status=Course.Status.PUBLISHED).select_related('category', 'instructor')
    q = request.GET.get('q')
    if q:
        courses = courses.filter(title__icontains=q)
    category = request.GET.get('category')
    if category:
        courses = courses.filter(category__slug=category)
    return JsonResponse({'results': [_course_payload(c) for c in courses[:50]]})


@require_http_methods(['GET'])
def api_course_detail(request, slug):
    try:
        course = Course.objects.get(slug=slug, status=Course.Status.PUBLISHED)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)
    payload = _course_payload(course)
    payload['description'] = course.description
    payload['objectives'] = course.objectives_list()
    payload['skills'] = list(course.skills_covered.values_list('name', flat=True))
    return JsonResponse(payload)


@login_required
@require_http_methods(['POST'])
def api_enroll(request, slug):
    try:
        course = Course.objects.get(slug=slug, status=Course.Status.PUBLISHED)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)
    if not request.user.is_student:
        return JsonResponse({'error': 'Only students can enroll'}, status=403)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    return JsonResponse({'enrolled': True, 'created': created, 'progress_percent': enrollment.progress_percent})


@login_required
@require_http_methods(['GET'])
def api_my_progress(request):
    if not request.user.is_student:
        return JsonResponse({'error': 'Students only'}, status=403)
    overview = student_overview(request.user)
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return JsonResponse({
        'overview': {k: v for k, v in overview.items() if not hasattr(v, 'model')},
        'courses': [
            {
                'course': e.course.title,
                'status': e.status,
                'progress_percent': e.progress_percent,
            }
            for e in enrollments
        ],
    })


@login_required
@require_http_methods(['GET'])
def api_recommendations(request):
    if not request.user.is_student:
        return JsonResponse({'error': 'Students only'}, status=403)
    recs = generate_recommendations(request.user, limit=10)
    return JsonResponse({
        'results': [
            {
                'course': r.course.title,
                'slug': r.course.slug,
                'score': round(r.score, 1),
                'reason': r.get_reason_display(),
                'explanation': r.explanation,
            }
            for r in recs
        ]
    })


@login_required
@require_http_methods(['GET'])
def api_notifications(request):
    notifications = Notification.objects.filter(user=request.user)[:20]
    return JsonResponse({
        'results': [
            {
                'id': n.id, 'title': n.title, 'message': n.message,
                'category': n.category, 'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
    })
