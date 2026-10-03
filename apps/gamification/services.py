from django.utils import timezone

from .models import Badge, StudentBadge, Achievement
from apps.notifications.services import notify


def award_badge(student, code):
    try:
        badge = Badge.objects.get(code=code)
    except Badge.DoesNotExist:
        return None

    student_badge, created = StudentBadge.objects.get_or_create(student=student, badge=badge)
    if created:
        profile = getattr(student, 'student_profile', None)
        if profile:
            profile.points += badge.points_reward
            profile.save(update_fields=['points'])
        Achievement.objects.create(
            student=student, description=f'Earned the "{badge.name}" badge', points=badge.points_reward,
        )
        notify(
            student, title='New badge earned!',
            message=f'You earned "{badge.name}" — {badge.description}',
            category='achievement',
        )
    return student_badge


def award_first_course_badge(student):
    completed = student.enrollments.filter(status='completed').count()
    if completed >= 1:
        award_badge(student, Badge.BadgeCode.FIRST_COURSE)


def check_completion_badges(student):
    completed = student.enrollments.filter(status='completed').count()
    if completed >= 1:
        award_badge(student, Badge.BadgeCode.FIRST_COURSE)
    if completed >= 5:
        award_badge(student, Badge.BadgeCode.FIVE_COURSES)


def check_quiz_badges(student):
    from apps.quizzes.models import QuizResult

    results = student.quiz_results.all()
    if results.filter(percent=100).exists():
        award_badge(student, Badge.BadgeCode.PERFECT_SCORE)

    high_scorers = results.filter(percent__gte=80).count()
    if high_scorers >= 5:
        award_badge(student, Badge.BadgeCode.QUIZ_MASTER)


def update_streak(student):
    """Call once per day the student is active (e.g. on dashboard visit / lesson completion)."""
    profile = getattr(student, 'student_profile', None)
    if not profile:
        return
    today = timezone.localdate()
    if profile.last_active_date == today:
        return  # already counted today

    if profile.last_active_date and (today - profile.last_active_date).days == 1:
        profile.daily_streak += 1
    else:
        profile.daily_streak = 1

    profile.longest_streak = max(profile.longest_streak, profile.daily_streak)
    profile.last_active_date = today
    profile.save(update_fields=['daily_streak', 'longest_streak', 'last_active_date'])

    if profile.daily_streak == 7:
        award_badge(student, Badge.BadgeCode.STREAK_7)


def leaderboard(limit=10):
    from apps.users.models import StudentProfile
    return StudentProfile.objects.select_related('user').order_by('-points')[:limit]
