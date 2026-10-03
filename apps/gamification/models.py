from django.conf import settings
from django.db import models


class Badge(models.Model):
    class BadgeCode(models.TextChoices):
        FIRST_COURSE = 'first_course', 'First Course Completed'
        QUIZ_MASTER = 'quiz_master', 'Quiz Master'
        STREAK_7 = 'streak_7', '7-Day Learning Streak'
        PYTHON_BEGINNER = 'python_beginner', 'Python Beginner'
        CONSISTENT_LEARNER = 'consistent_learner', 'Consistent Learner'
        FIVE_COURSES = 'five_courses', 'Five Courses Completed'
        PERFECT_SCORE = 'perfect_score', 'Perfect Score'

    code = models.CharField(max_length=30, choices=BadgeCode.choices, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon = models.CharField(max_length=10, default='star', help_text='Short glyph/label shown on the badge')
    points_reward = models.PositiveIntegerField(default=10)

    def __str__(self):
        return self.name


class StudentBadge(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='awarded_to')
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')
        ordering = ['-awarded_at']

    def __str__(self):
        return f'{self.student.username} — {self.badge.name}'


class Achievement(models.Model):
    """A logged, timestamped event feed entry (course completion, streak milestone, etc.)."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    description = models.CharField(max_length=255)
    points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.description
