from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.quiz_list, name='list'),
    path('history/', views.quiz_history, name='history'),
    path('mine/', views.instructor_quiz_list, name='instructor_quizzes'),
    path('new/', views.quiz_create, name='create'),
    path('<int:pk>/take/', views.take_quiz, name='take'),
    path('<int:pk>/result/', views.quiz_result, name='result'),
    path('<int:pk>/questions/', views.instructor_questions, name='instructor_questions'),
    path('<int:quiz_pk>/questions/<int:question_pk>/answers/', views.instructor_answers, name='instructor_answers'),
]
