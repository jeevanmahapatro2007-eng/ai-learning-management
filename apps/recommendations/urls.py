from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommendations_view, name='list'),
    path('<int:pk>/dismiss/', views.dismiss_recommendation, name='dismiss'),
    path('learning-path/', views.learning_path_view, name='learning_path'),
]
