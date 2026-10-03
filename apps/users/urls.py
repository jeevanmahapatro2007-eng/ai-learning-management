from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.LodestarLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', views.view_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('password-reset/', PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]
