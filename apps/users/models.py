from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """Custom user with three roles: student, instructor, admin."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        INSTRUCTOR = 'instructor', 'Instructor'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone_number = models.CharField(max_length=20, blank=True)
    is_instructor_approved = models.BooleanField(
        default=False,
        help_text='Instructors must be approved by an admin before they can publish courses.'
    )
    date_joined_platform = models.DateTimeField(auto_now_add=True)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'


class StudentProfile(models.Model):
    """Extended profile for students, feeds the recommendation engine."""

    class LearningLevel(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    education = models.CharField(max_length=255, blank=True, help_text='e.g. B.Tech CSE, 3rd year')
    interests = models.CharField(max_length=500, blank=True, help_text='Comma-separated interests')
    preferred_domains = models.CharField(max_length=500, blank=True, help_text='Comma-separated domains, e.g. Python, Web Development')
    current_level = models.CharField(max_length=20, choices=LearningLevel.choices, default=LearningLevel.BEGINNER)
    learning_goals = models.TextField(blank=True)
    daily_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_learning_minutes = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    def interests_list(self):
        return [i.strip() for i in self.interests.split(',') if i.strip()]

    def preferred_domains_list(self):
        return [d.strip() for d in self.preferred_domains.split(',') if d.strip()]

    def get_absolute_url(self):
        return reverse('users:profile')

    def __str__(self):
        return f'Student profile: {self.user.username}'


class InstructorProfile(models.Model):
    """Extended profile for instructors."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True)
    expertise = models.CharField(max_length=500, blank=True, help_text='Comma-separated areas of expertise')
    years_of_experience = models.PositiveIntegerField(default=0)
    linkedin_url = models.URLField(blank=True)

    def expertise_list(self):
        return [e.strip() for e in self.expertise.split(',') if e.strip()]

    def __str__(self):
        return f'Instructor profile: {self.user.username}'
