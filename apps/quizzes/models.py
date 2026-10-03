from django.conf import settings
from django.db import models

from apps.courses.models import Course, Lesson, Skill


class Quiz(models.Model):
    class QuizType(models.TextChoices):
        SKILL_ASSESSMENT = 'assessment', 'Skill Assessment'
        LESSON_QUIZ = 'lesson_quiz', 'Lesson Quiz'
        COURSE_QUIZ = 'course_quiz', 'Course Quiz'

    title = models.CharField(max_length=200)
    quiz_type = models.CharField(max_length=20, choices=QuizType.choices, default=QuizType.LESSON_QUIZ)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name='quizzes')
    pass_mark_percent = models.PositiveIntegerField(default=60)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quizzes_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Quizzes'
        ordering = ['-created_at']

    def question_count(self):
        return self.questions.count()

    def total_points(self):
        return sum(q.points for q in self.questions.all())

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizResult(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_results')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='results')
    score_points = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)
    percent = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)
    taken_at = models.DateTimeField(auto_now_add=True)
    # per-skill breakdown stored as JSON-ish text for lightweight storage without extra deps
    skill_breakdown = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-taken_at']

    def __str__(self):
        return f'{self.student.username} — {self.quiz.title}: {self.percent:.0f}%'


class QuestionResponse(models.Model):
    """Stores which answer a student picked for a given attempt, for review screens."""
    quiz_result = models.ForeignKey(QuizResult, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='+')
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, related_name='+')
    is_correct = models.BooleanField(default=False)
