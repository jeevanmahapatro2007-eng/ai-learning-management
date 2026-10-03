from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from apps.analytics.services import student_overview, instructor_overview, admin_overview
from apps.courses.models import Enrollment
from apps.recommendations.engine import generate_recommendations, generate_insights
from apps.gamification.services import update_streak, leaderboard
from apps.notifications.models import Notification


@login_required
def redirect_to_dashboard(request):
    user = request.user
    if user.is_student:
        return redirect('dashboard:student')
    if user.is_instructor:
        return redirect('dashboard:instructor')
    if user.is_platform_admin:
        return redirect('dashboard:admin')
    return redirect('core:home')


@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('dashboard:redirect')

    update_streak(request.user)

    overview = student_overview(request.user)
    recommendations = generate_recommendations(request.user, limit=4)
    insights = generate_insights(request.user)
    recent_enrollments = Enrollment.objects.filter(student=request.user).select_related('course')[:5]
    notifications = request.user.notifications.filter(is_read=False)[:5]

    return render(request, 'dashboard/student_dashboard.html', {
        'overview': overview,
        'recommendations': recommendations,
        'insights': insights,
        'recent_enrollments': recent_enrollments,
        'notifications': notifications,
    })


@login_required
def instructor_dashboard(request):
    if not request.user.is_instructor:
        return redirect('dashboard:redirect')
    overview = instructor_overview(request.user)
    return render(request, 'dashboard/instructor_dashboard.html', {'overview': overview})


@login_required
def admin_dashboard(request):
    if not request.user.is_platform_admin:
        return redirect('dashboard:redirect')
    overview = admin_overview()
    top_students = leaderboard(5)
    return render(request, 'dashboard/admin_dashboard.html', {'overview': overview, 'top_students': top_students})
