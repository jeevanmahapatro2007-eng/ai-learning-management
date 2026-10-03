from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('badges/', views.badges_view, name='badges'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]
