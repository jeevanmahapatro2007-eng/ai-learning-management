from django.conf import settings
from django.db import models

from apps.courses.models import Course


class StudentProgress(models.Model):
    """A daily/periodic snapshot of a student's overall learning activity,
    used to power streaks, learning-hours totals and progress charts."""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_logs')
    date = models.DateField(auto_now_add=True)
    minutes_learned = models.PositiveIntegerField(default=0)
    lessons_completed = models.PositiveIntegerField(default=0)
    quizzes_taken = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student.username} — {self.date}'
