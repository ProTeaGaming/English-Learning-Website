import re

import dns.exception
import dns.resolver
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

DNS_LIFETIME = 3.0  # seconds — keep signup snappy even when DNS is slow


def email_domain_accepts_mail(domain):
    """DNS-only deliverability check: can this domain receive mail at all?

    Catches typos ("gmial.com") and unregistered/parked custom domains at
    signup instead of letting the verification email silently bounce while
    the user stares at the check-your-email screen. Deliberately fails OPEN
    on resolver trouble (timeout, SERVFAIL, no network) so DNS hiccups never
    block signups, and never probes mailboxes — SMTP callouts are unreliable
    (catch-all servers) and get the sending IP blacklisted.
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX', lifetime=DNS_LIFETIME)
        # RFC 7505 "null MX" (single '.') explicitly means no mail accepted.
        return any(str(record.exchange) != '.' for record in answers)
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        pass  # domain exists but has no MX — RFC 5321 falls back to A/AAAA
    except dns.exception.DNSException:
        return True
    for rtype in ('A', 'AAAA'):
        try:
            dns.resolver.resolve(domain, rtype, lifetime=DNS_LIFETIME)
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            continue
        except dns.exception.DNSException:
            return True
    return False


class AccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        domain = email.rsplit('@', 1)[-1]
        if not email_domain_accepts_mail(domain):
            raise ValidationError(
                'This email domain cannot receive mail. '
                'Please check the address for typos.'
            )
        return email

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
