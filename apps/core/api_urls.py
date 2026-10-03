from django.urls import path
from . import api

app_name = 'api'

urlpatterns = [
    path('courses/', api.api_course_list, name='course_list'),
    path('courses/<slug:slug>/', api.api_course_detail, name='course_detail'),
    path('courses/<slug:slug>/enroll/', api.api_enroll, name='enroll'),
    path('me/progress/', api.api_my_progress, name='my_progress'),
    path('me/recommendations/', api.api_recommendations, name='recommendations'),
    path('me/notifications/', api.api_notifications, name='notifications'),
]
