from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='list'),
    path('mine/', views.instructor_course_list, name='instructor_courses'),
    path('new/', views.course_create, name='create'),
    path('<slug:slug>/', views.course_detail, name='detail'),
    path('<slug:slug>/edit/', views.course_edit, name='edit'),
    path('<slug:slug>/delete/', views.course_delete, name='delete'),
    path('<slug:slug>/enroll/', views.enroll, name='enroll'),
    path('<slug:slug>/learn/', views.learn, name='learn'),
    path('<slug:slug>/learn/<int:lesson_id>/complete/', views.mark_lesson_complete, name='complete_lesson'),
    path('<slug:slug>/lessons/', views.instructor_lessons, name='instructor_lessons'),
    path('<slug:slug>/lessons/<int:lesson_id>/materials/', views.instructor_materials, name='instructor_materials'),
]
