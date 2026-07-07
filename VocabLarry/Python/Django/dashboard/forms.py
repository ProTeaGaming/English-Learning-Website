from django import forms
from vocab.models import Word, Category, Color, CEFRLevel, GrammarTopic, GrammarLessonBlock, GrammarQuestion
from django.contrib.auth import get_user_model


class WordForm(forms.ModelForm):
    synonyms_text = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'comma-separated'}),
        required=False, label='Synonyms',
    )
    antonyms_text = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'comma-separated'}),
        required=False, label='Antonyms',
    )

    class Meta:
        model = Word
        fields = ['word', 'pos', 'definition', 'example', 'gap', 'category', 'cefr_level', 'order']
        widgets = {
            'definition': forms.Textarea(attrs={'rows': 3}),
            'example':    forms.Textarea(attrs={'rows': 2}),
            'gap':        forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['synonyms_text'].initial = ', '.join(self.instance.synonyms or [])
            self.fields['antonyms_text'].initial = ', '.join(self.instance.antonyms or [])

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.synonyms = [s.strip() for s in self.cleaned_data['synonyms_text'].split(',') if s.strip()]
        instance.antonyms = [s.strip() for s in self.cleaned_data['antonyms_text'].split(',') if s.strip()]
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['slug', 'name', 'icon', 'cefr_level', 'color', 'order']


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'bg_hex', 'text_hex']
        widgets = {
            'bg_hex':   forms.TextInput(attrs={'type': 'color'}),
            'text_hex': forms.TextInput(attrs={'type': 'color'}),
        }


class CEFRForm(forms.ModelForm):
    class Meta:
        model = CEFRLevel
        fields = ['code', 'name', 'order']


class UserRoleForm(forms.Form):
    ROLE_CHOICES = [('user', 'User'), ('staff', 'Staff'), ('admin', 'Admin')]
    role        = forms.ChoiceField(choices=ROLE_CHOICES)
    is_active   = forms.BooleanField(required=False, label='Active')


class GrammarTopicForm(forms.ModelForm):
    class Meta:
        model = GrammarTopic
        fields = ['slug', 'title', 'tag', 'cefr_label', 'blurb', 'stage', 'order']
        widgets = {'blurb': forms.Textarea(attrs={'rows': 2})}


class GrammarLessonBlockForm(forms.ModelForm):
    class Meta:
        model = GrammarLessonBlock
        fields = ['type', 'title', 'body', 'data', 'order']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
            'data': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'table: {"head": [...], "rows": [[...]]} — examples: {"items": [{"en": "...", "note": "..."}]}',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        btype = cleaned.get('type')
        data  = cleaned.get('data') or {}
        if btype == 'table':
            if not isinstance(data.get('head'), list) or not isinstance(data.get('rows'), list):
                raise forms.ValidationError('Table blocks need data with "head" and "rows" lists.')
        elif btype == 'examples':
            items = data.get('items')
            if not isinstance(items, list) or not items:
                raise forms.ValidationError('Examples blocks need data {"items": [...]} with at least one item.')
        elif not cleaned.get('body'):
            raise forms.ValidationError('Intro, rule and tip blocks need body text.')
        return cleaned


class GrammarQuestionForm(forms.ModelForm):
    class Meta:
        model = GrammarQuestion
        fields = ['qtype', 'prompt', 'options', 'answers', 'why', 'order']
        widgets = {
            'prompt':  forms.Textarea(attrs={'rows': 2}),
            'why':     forms.Textarea(attrs={'rows': 2}),
            'options': forms.Textarea(attrs={'rows': 2, 'placeholder': '["opt A", "opt B", "opt C", "opt D"] (mcq only)'}),
            'answers': forms.Textarea(attrs={'rows': 2, 'placeholder': 'mcq: [1] (correct index) — gap/transform: ["accepted", "answers"]'}),
        }

    def clean(self):
        cleaned = super().clean()
        qtype   = cleaned.get('qtype')
        options = cleaned.get('options') or []
        answers = cleaned.get('answers')
        if qtype == 'mcq':
            if not isinstance(options, list) or len(options) != 4:
                self.add_error('options', 'MCQ questions need exactly 4 options.')
            elif (not isinstance(answers, list) or len(answers) != 1
                    or not isinstance(answers[0], int) or not 0 <= answers[0] <= 3):
                self.add_error('answers', 'MCQ answers must be [index] with index 0–3.')
        else:
            if (not isinstance(answers, list) or not answers
                    or not all(isinstance(a, str) and a.strip() for a in answers)):
                self.add_error('answers', 'Gap/transform answers must be a list of non-empty strings.')
        return cleaned
