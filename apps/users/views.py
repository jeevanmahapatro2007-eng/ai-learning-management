from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect

from .forms import RegistrationForm, StudentProfileForm, InstructorProfileForm
from .models import User, StudentProfile, InstructorProfile
from apps.notifications.services import notify


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:redirect')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data['role']
            user.save()

            if user.role == User.Role.STUDENT:
                StudentProfile.objects.create(user=user)
            elif user.role == User.Role.INSTRUCTOR:
                InstructorProfile.objects.create(user=user)

            auth_login(request, user)
            notify(
                user,
                title='Welcome to Lodestar',
                message='Complete your profile and take a skill assessment to get personalized recommendations.',
                category='system',
            )
            if user.role == User.Role.STUDENT:
                messages.success(request, 'Account created. Let\'s build your learning profile next.')
                return redirect('users:edit_profile')
            messages.success(
                request,
                'Instructor account created. An admin will review and approve your account before you can publish courses.'
            )
            return redirect('dashboard:redirect')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


class LodestarLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


@login_required
def edit_profile(request):
    user = request.user

    if user.is_student:
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        FormClass = StudentProfileForm
        template = 'users/edit_student_profile.html'
    elif user.is_instructor:
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        FormClass = InstructorProfileForm
        template = 'users/edit_instructor_profile.html'
    else:
        messages.info(request, 'Admin accounts are managed from the platform admin console.')
        return redirect('dashboard:redirect')

    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('dashboard:redirect')
    else:
        form = FormClass(instance=profile, user=user)

    return render(request, template, {'form': form})


@login_required
def view_profile(request):
    user = request.user
    # get_or_create: accounts made via /admin/ have a role but no profile row yet
    if user.is_student:
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        return render(request, 'users/student_profile.html', {'profile': profile})
    elif user.is_instructor:
        profile, _ = InstructorProfile.objects.get_or_create(user=user)
        return render(request, 'users/instructor_profile.html', {'profile': profile})
    return redirect('dashboard:redirect')
