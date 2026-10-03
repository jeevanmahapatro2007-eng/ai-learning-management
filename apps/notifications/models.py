from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        SYSTEM = 'system', 'System'
        COURSE = 'course', 'Course'
        QUIZ = 'quiz', 'Quiz'
        RECOMMENDATION = 'recommendation', 'Recommendation'
        ACHIEVEMENT = 'achievement', 'Achievement'
        REMINDER = 'reminder', 'Reminder'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.title}'
