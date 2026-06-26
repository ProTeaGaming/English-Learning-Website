import re
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.role = 'user'
        if commit:
            user.save()
        return user

    def populate_username(self, request, user):
        email = user.email or ''
        base = re.sub(r'[^a-z0-9_]', '_', email.split('@')[0].lower())[:18]
        base = base or 'user'
        username = base
        User = get_user_model()
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user.username = username
