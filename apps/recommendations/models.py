from django.conf import settings
from django.db import models

from apps.courses.models import Skill, Course


class StudentSkill(models.Model):
    """Tracks a student's measured proficiency in a given skill, updated after every quiz attempt."""

    class Level(models.TextChoices):
        WEAK = 'weak', 'Weak'
        DEVELOPING = 'developing', 'Developing'
        STRONG = 'strong', 'Strong'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_records')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='student_records')
    proficiency_percent = models.FloatField(default=0)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.WEAK)
    attempts = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'skill')
        ordering = ['-proficiency_percent']

    def recompute_level(self):
        if self.proficiency_percent >= 75:
            self.level = self.Level.STRONG
        elif self.proficiency_percent >= 50:
            self.level = self.Level.DEVELOPING
        else:
            self.level = self.Level.WEAK

    def __str__(self):
        return f'{self.student.username} — {self.skill.name}: {self.proficiency_percent:.0f}%'


class Recommendation(models.Model):
    """A single AI-generated recommendation surfaced to a student."""

    class SourceType(models.TextChoices):
        COURSE = 'course', 'Course'
        LESSON = 'lesson', 'Lesson/Topic'
        QUIZ = 'quiz', 'Quiz'

    class Reason(models.TextChoices):
        WEAK_SKILL = 'weak_skill', 'Targets a weak skill'
        INTEREST_MATCH = 'interest_match', 'Matches your interests'
        NEXT_IN_PATH = 'next_in_path', 'Next step in your learning path'
        POPULAR_IN_DOMAIN = 'popular_in_domain', 'Popular in your preferred domain'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='recommended_to')
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.COURSE)
    reason = models.CharField(max_length=30, choices=Reason.choices, default=Reason.INTEREST_MATCH)
    score = models.FloatField(default=0, help_text='Internal ranking score, higher = more relevant')
    explanation = models.CharField(max_length=255, blank=True)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-created_at']
        unique_together = ('student', 'course')

    def __str__(self):
        return f'Recommend {self.course.title} to {self.student.username} ({self.score:.1f})'


class LearningPath(models.Model):
    """An ordered, auto-generated sequence of topics/courses for a student within a domain."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_paths')
    domain = models.CharField(max_length=150, help_text='e.g. Python, Web Development')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'domain')

    def __str__(self):
        return f'{self.student.username} — {self.domain} path'


class LearningPathStep(models.Model):
    class StepStatus(models.TextChoices):
        LOCKED = 'locked', 'Locked'
        AVAILABLE = 'available', 'Available'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'

    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name='steps')
    topic = models.CharField(max_length=150)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=StepStatus.choices, default=StepStatus.LOCKED)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.path.domain}: {self.order}. {self.topic}'
