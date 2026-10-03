from django import forms
from .models import Course, Lesson, LearningMaterial, Category, Skill


class StyledMixin:
    def _style(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ls-input').strip()


class CourseForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'category', 'short_description', 'description', 'difficulty',
            'duration_hours', 'thumbnail', 'learning_objectives', 'skills_covered', 'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'learning_objectives': forms.Textarea(attrs={'rows': 4, 'placeholder': 'One objective per line'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['skills_covered'].widget.attrs['class'] = 'ls-multiselect'


class LessonForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content', 'video_url', 'order', 'estimated_minutes', 'skills']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
        self.fields['skills'].widget.attrs['class'] = 'ls-multiselect'


class LearningMaterialForm(StyledMixin, forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = ['title', 'material_type', 'file', 'external_url', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()


class CourseSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'class': 'ls-input', 'placeholder': 'Search courses by title or skill...'}
    ))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False, empty_label='All categories')
    difficulty = forms.ChoiceField(
    choices=(('', 'All levels'),) + tuple(Course.Difficulty.choices),
    )
    duration = forms.ChoiceField(
        choices=(
            ('', 'Any duration'),
            ('short', 'Under 5 hours'),
            ('medium', '5–15 hours'),
            ('long', '15+ hours'),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('category', 'difficulty', 'duration'):
            self.fields[name].widget.attrs['class'] = 'ls-select'
