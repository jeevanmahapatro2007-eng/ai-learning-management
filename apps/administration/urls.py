from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.console_home, name='console_home'),
    path('students/', views.manage_students, name='manage_students'),
    path('instructors/', views.manage_instructors, name='manage_instructors'),
    path('instructors/<int:pk>/approve/', views.approve_instructor, name='approve_instructor'),
    path('users/<int:pk>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
    path('courses/', views.manage_courses, name='manage_courses'),
    path('categories/', views.manage_categories, name='manage_categories'),
]
