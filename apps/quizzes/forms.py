from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from apps.courses.models import Course, Lesson
from .models import Quiz, Question, Answer


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'quiz_type', 'description', 'course', 'lesson', 'skills', 'pass_mark_percent']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = 'ls-multiselect' if name == 'skills' else 'ls-input'
            field.widget.attrs['class'] = css
        if user is not None:  # instructors should only attach quizzes to their own courses/lessons
            self.fields['course'].queryset = Course.objects.filter(instructor=user)
            self.fields['lesson'].queryset = Lesson.objects.filter(course__instructor=user)


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'skill', 'points', 'order']
        widgets = {'text': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'ls-input'


class BaseAnswerFormSet(BaseInlineFormSet):
    """A question needs at least two options and at least one correct one, otherwise it can never be scored."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return
        kept = [
            f for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('text')
        ]
        if len(kept) < 2:
            raise ValidationError('Add at least two answer options.')
        if not any(f.cleaned_data.get('is_correct') for f in kept):
            raise ValidationError('Mark at least one option as correct.')


AnswerFormSet = inlineformset_factory(
    Question, Answer, formset=BaseAnswerFormSet,
    fields=['text', 'is_correct'], extra=4, can_delete=True,
    widgets={'text': forms.TextInput(attrs={'class': 'ls-input', 'placeholder': 'Answer option'})}
)
