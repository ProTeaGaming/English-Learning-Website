import pytest
from django.test import Client


@pytest.mark.django_db
def test_dashboard_anonymous_redirects_to_login():
    c = Client()
    r = c.get('/dashboard/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_dashboard_regular_user_forbidden(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_staff_user_forbidden_without_2fa(staff_user):
    # MFA not configured → middleware blocks it
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_index_accessible_to_staff_with_2fa(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    assert b'Dashboard' in r.content
