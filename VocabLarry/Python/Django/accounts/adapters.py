import re
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
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


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        # For existing users, never overwrite their chosen username, name, or picture.
        if sociallogin.is_existing:
            User = get_user_model()
            try:
                saved = User.objects.get(pk=user.pk)
                user.username = saved.username
                user.name = saved.name
            except User.DoesNotExist:
                pass
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # First-time social signup only (save_user is never called for a
        # returning user — see DefaultSocialAccountAdapter's docstring).
        # They never got the name/username/picture step the email+password
        # signup form offers, so flag it for the frontend to prompt for
        # once, right after landing back from the provider. Consumed via
        # session.pop() in accounts/views.py:session() — a one-time signal.
        request.session['social_signup_needs_profile'] = True
        return user
