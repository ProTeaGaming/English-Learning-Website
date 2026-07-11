from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added


@receiver(social_account_added)
def flag_social_account_connected(sender, request, sociallogin, **kwargs):
    # A "connect" round trip is a full-page redirect through the provider
    # and back, same as login/signup — this one-time flag (consumed via
    # session.pop() in accounts/views.py:session()) lets the frontend
    # reopen the profile modal showing the new connection once landed
    # back on '/', instead of silently updating nothing the user can see.
    request.session['social_account_connected'] = True
