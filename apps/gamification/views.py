from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Badge, StudentBadge, Achievement
from .services import leaderboard


@login_required
def badges_view(request):
    earned_ids = set(StudentBadge.objects.filter(student=request.user).values_list('badge_id', flat=True))
    all_badges = Badge.objects.all()
    achievements = Achievement.objects.filter(student=request.user)[:20]
    return render(request, 'gamification/badges.html', {
        'all_badges': all_badges, 'earned_ids': earned_ids, 'achievements': achievements,
    })


def leaderboard_view(request):
    top_students = leaderboard(20)
    return render(request, 'gamification/leaderboard.html', {'top_students': top_students})
