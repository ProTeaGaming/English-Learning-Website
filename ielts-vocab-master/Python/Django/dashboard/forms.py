from django import forms
from vocab.models import Word, Category, Color, CEFRLevel
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
