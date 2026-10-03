from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from . import engine
from apps.users.models import StudentProfile
from .models import Recommendation


@login_required
def recommendations_view(request):
    if not request.user.is_student:
        return redirect('dashboard:redirect')
    engine.generate_recommendations(request.user)
    recs = Recommendation.objects.filter(student=request.user, is_dismissed=False).select_related('course')
    return render(request, 'recommendations/recommendations.html', {'recommendations': recs})


@login_required
def dismiss_recommendation(request, pk):
    rec = get_object_or_404(Recommendation, pk=pk, student=request.user)
    rec.is_dismissed = True
    rec.save(update_fields=['is_dismissed'])
    messages.info(request, 'Recommendation dismissed.')
    return redirect('recommendations:list')


@login_required
def learning_path_view(request):
    if not request.user.is_student:
        return redirect('dashboard:redirect')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    domains = profile.preferred_domains_list() or ['General']
    paths = []
    for domain in domains:
        paths.append(engine.generate_learning_path(request.user, domain))

    return render(request, 'recommendations/learning_path.html', {'paths': paths})
