from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Short label/emoji shown next to the category')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Skill(models.Model):
    """A discrete, taggable skill/topic used across courses, quizzes and recommendations."""
    name = models.CharField(max_length=120, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='skills')

    def __str__(self):
        return self.name


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_taught',
        limit_choices_to={'role': 'instructor'}
    )
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    duration_hours = models.PositiveIntegerField(default=1, help_text='Estimated total hours to complete')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    learning_objectives = models.TextField(blank=True, help_text='One objective per line')
    skills_covered = models.ManyToManyField(Skill, blank=True, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'course'
            if base in ('new', 'mine'):  # would collide with fixed URL routes
                base = f'{base}-course'
            slug = base
            n = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('courses:detail', kwargs={'slug': self.slug})

    def objectives_list(self):
        return [o.strip() for o in self.learning_objectives.splitlines() if o.strip()]

    def lesson_count(self):
        return self.lessons.count()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    class LessonType(models.TextChoices):
        VIDEO = 'video', 'Video Lesson'
        TEXT = 'text', 'Text Lesson'
        PROJECT = 'project', 'Mini Project'

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices, default=LessonType.TEXT)
    content = models.TextField(blank=True, help_text='Text content, or a video description/transcript summary')
    video_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    estimated_minutes = models.PositiveIntegerField(default=10)
    skills = models.ManyToManyField(Skill, blank=True, related_name='lessons')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.title} — {self.title}'


class LearningMaterial(models.Model):
    class MaterialType(models.TextChoices):
        PDF = 'pdf', 'PDF Notes'
        PRESENTATION = 'presentation', 'Presentation'
        EXAMPLE = 'example', 'Example'
        EXERCISE = 'exercise', 'Coding Exercise'

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices, default=MaterialType.EXAMPLE)
    file = models.FileField(upload_to='learning_materials/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        DROPPED = 'dropped', 'Dropped'

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_lessons = models.ManyToManyField(Lesson, blank=True, related_name='completed_by_enrollments')
    last_accessed_lesson = models.ForeignKey(
        Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    was_recommended = models.BooleanField(default=False, help_text='True if the student enrolled via a recommendation')

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    @property
    def progress_percent(self):
        total = self.course.lesson_count()
        if not total:
            return 0
        return round((self.completed_lessons.count() / total) * 100)

    def __str__(self):
        return f'{self.student.username} → {self.course.title}'
