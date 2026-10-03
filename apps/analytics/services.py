"""Aggregation helpers for the student, instructor and admin dashboards (sections 10-13)."""
from django.db.models import Avg, Count, Q

from apps.courses.models import Course, Enrollment
from apps.quizzes.models import QuizResult
from apps.recommendations.models import StudentSkill


def student_overview(student):
    enrollments = Enrollment.objects.filter(student=student)
    results = QuizResult.objects.filter(student=student)
    profile = getattr(student, 'student_profile', None)

    return {
        'courses_enrolled': enrollments.count(),
        'courses_completed': enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
        'courses_in_progress': enrollments.filter(status=Enrollment.Status.IN_PROGRESS).count(),
        'quiz_average': round(results.aggregate(avg=Avg('percent'))['avg'] or 0, 1),
        'learning_hours': round((profile.total_learning_minutes if profile else 0) / 60, 1),
        'current_streak': profile.daily_streak if profile else 0,
        'points': profile.points if profile else 0,
        'weak_skills': StudentSkill.objects.filter(student=student, proficiency_percent__lt=50).select_related('skill')[:5],
        'strong_skills': StudentSkill.objects.filter(student=student, proficiency_percent__gte=75).select_related('skill')[:5],
    }


def instructor_overview(instructor):
    courses = Course.objects.filter(instructor=instructor)
    enrollments = Enrollment.objects.filter(course__instructor=instructor)
    results = QuizResult.objects.filter(quiz__course__instructor=instructor)

    total_students = enrollments.values('student').distinct().count()
    completion_rate = 0
    if enrollments.count():
        completion_rate = round(
            enrollments.filter(status=Enrollment.Status.COMPLETED).count() / enrollments.count() * 100, 1
        )

    return {
        'total_courses': courses.count(),
        'total_students': total_students,
        'completion_rate': completion_rate,
        'average_quiz_score': round(results.aggregate(avg=Avg('percent'))['avg'] or 0, 1),
        'courses': courses.annotate(
            enrolled_count=Count('enrollments'),
            completed_count=Count('enrollments', filter=Q(enrollments__status=Enrollment.Status.COMPLETED)),
        ),
    }


def admin_overview():
    from apps.users.models import User

    return {
        'total_students': User.objects.filter(role=User.Role.STUDENT).count(),
        'total_instructors': User.objects.filter(role=User.Role.INSTRUCTOR).count(),
        'pending_instructors': User.objects.filter(role=User.Role.INSTRUCTOR, is_instructor_approved=False).count(),
        'total_courses': Course.objects.count(),
        'published_courses': Course.objects.filter(status=Course.Status.PUBLISHED).count(),
        'total_enrollments': Enrollment.objects.count(),
        'total_quizzes_taken': QuizResult.objects.count(),
        'avg_completion_rate': _platform_completion_rate(),
    }


def _platform_completion_rate():
    total = Enrollment.objects.count()
    if not total:
        return 0
    completed = Enrollment.objects.filter(status=Enrollment.Status.COMPLETED).count()
    return round(completed / total * 100, 1)
