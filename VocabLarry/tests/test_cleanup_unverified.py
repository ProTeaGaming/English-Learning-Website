from datetime import timedelta
from io import StringIO

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone


def make_user(email, username, days_old, verified=None, **kwargs):
    """Create a user joined `days_old` days ago; verified=None means no
    allauth EmailAddress record at all (account created outside signup)."""
    U = get_user_model()
    user = U.objects.create_user(email=email, username=username,
                                 password='testpass123', **kwargs)
    U.objects.filter(pk=user.pk).update(
        date_joined=timezone.now() - timedelta(days=days_old))
    if verified is not None:
        EmailAddress.objects.create(user=user, email=email,
                                    verified=verified, primary=True)
    return user


def cleanup(*args):
    out = StringIO()
    call_command('cleanup_unverified_accounts', *args, stdout=out)
    return out.getvalue()


def exists(user):
    return get_user_model().objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_deletes_old_unverified_account():
    user = make_user('stale@example.com', 'staleuser', days_old=8, verified=False)
    cleanup()
    assert not exists(user)


@pytest.mark.django_db
def test_keeps_old_verified_account():
    user = make_user('ok@example.com', 'okuser', days_old=30, verified=True)
    cleanup()
    assert exists(user)


@pytest.mark.django_db
def test_keeps_recent_unverified_account():
    user = make_user('new@example.com', 'newuser', days_old=3, verified=False)
    cleanup()
    assert exists(user)


@pytest.mark.django_db
def test_keeps_account_without_emailaddress_record():
    # Accounts created outside the signup flow (shell, fixtures) have no
    # allauth EmailAddress row — never touch them.
    user = make_user('shell@example.com', 'shelluser', days_old=30, verified=None)
    cleanup()
    assert exists(user)


@pytest.mark.django_db
def test_keeps_staff_and_superuser():
    staff = make_user('staff2@example.com', 'staffuser2', days_old=30,
                      verified=False, is_staff=True)
    admin = make_user('super@example.com', 'superuser2', days_old=30,
                      verified=False, is_superuser=True)
    cleanup()
    assert exists(staff)
    assert exists(admin)


@pytest.mark.django_db
def test_keeps_account_that_has_logged_in():
    user = make_user('active@example.com', 'activeuser', days_old=30, verified=False)
    get_user_model().objects.filter(pk=user.pk).update(last_login=timezone.now())
    cleanup()
    assert exists(user)


@pytest.mark.django_db
def test_dry_run_deletes_nothing():
    user = make_user('stale2@example.com', 'staleuser2', days_old=8, verified=False)
    out = cleanup('--dry-run')
    assert exists(user)
    assert 'stale2@example.com' in out


@pytest.mark.django_db
def test_custom_days_cutoff():
    user = make_user('mid@example.com', 'miduser', days_old=15, verified=False)
    cleanup('--days', '30')
    assert exists(user)
    cleanup('--days', '14')
    assert not exists(user)
