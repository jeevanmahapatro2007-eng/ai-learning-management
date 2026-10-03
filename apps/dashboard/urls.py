from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.redirect_to_dashboard, name='redirect'),
    path('student/', views.student_dashboard, name='student'),
    path('instructor/', views.instructor_dashboard, name='instructor'),
    path('admin/', views.admin_dashboard, name='admin'),
]
