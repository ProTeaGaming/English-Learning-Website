import pytest
from django.test import Client


@pytest.fixture
def logged_in(mocker):
    """Client factory: log a user in with allauth MFA check stubbed out."""
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    def _login(user):
        c = Client()
        c.force_login(user)
        return c
    return _login


@pytest.mark.django_db
def test_session_reports_is_staff_false_for_regular_user(logged_in, regular_user):
    r = logged_in(regular_user).get('/auth/session/')
    assert r.status_code == 200
    assert r.json()['isStaff'] is False


@pytest.mark.django_db
def test_session_reports_is_staff_true_for_staff_and_admin(logged_in, staff_user, admin_user):
    assert logged_in(staff_user).get('/auth/session/').json()['isStaff'] is True
    assert logged_in(admin_user).get('/auth/session/').json()['isStaff'] is True


@pytest.mark.django_db
def test_session_anonymous_has_no_is_staff_key():
    r = Client().get('/auth/session/')
    assert r.json() == {'loggedIn': False}
