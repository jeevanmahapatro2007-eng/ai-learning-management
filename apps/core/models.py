from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question
