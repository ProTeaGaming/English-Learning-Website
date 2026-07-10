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
def test_dashboard_accessible_to_superuser_with_default_role(regular_user, mocker):
    # createsuperuser sets is_staff/is_superuser but leaves the custom `role`
    # field at its 'user' default — role_required() must still grant access
    # (previously it only checked `role`, locking out every fresh superuser).
    regular_user.is_staff = True
    regular_user.is_superuser = True
    regular_user.save(update_fields=['is_staff', 'is_superuser'])
    assert regular_user.role == 'user'
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    # Admin-only view too, since is_superuser should count as admin-level.
    r = c.get('/dashboard/users/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_superuser_still_subject_to_mfa_gate(regular_user, mocker):
    regular_user.is_staff = True
    regular_user.is_superuser = True
    regular_user.save(update_fields=['is_staff', 'is_superuser'])
    c = Client()
    c.force_login(regular_user)
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


@pytest.mark.django_db
def test_users_list_forbidden_for_staff(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_users_list_accessible_to_admin(admin_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200


def _admin_client(admin_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(admin_user)
    return c


@pytest.mark.django_db
def test_admin_cannot_demote_self(admin_user, mocker):
    c = _admin_client(admin_user, mocker)
    r = c.post(f'/dashboard/users/{admin_user.pk}/', {'role': 'user', 'is_active': 'on'})
    assert r.status_code == 302
    admin_user.refresh_from_db()
    assert admin_user.role == 'admin'


@pytest.mark.django_db
def test_admin_cannot_deactivate_self(admin_user, mocker):
    c = _admin_client(admin_user, mocker)
    r = c.post(f'/dashboard/users/{admin_user.pk}/', {'role': 'admin'})  # is_active unchecked
    assert r.status_code == 302
    admin_user.refresh_from_db()
    assert admin_user.is_active is True


@pytest.mark.django_db
def test_cannot_demote_last_admin(admin_user, regular_user, mocker):
    # Promote regular_user to admin so admin_user can act on a *different* admin,
    # then demote admin_user down to that single remaining admin.
    second_admin = regular_user
    second_admin.role = 'admin'
    second_admin.save(update_fields=['role'])
    c = _admin_client(second_admin, mocker)
    # Deactivate the other admin first, leaving second_admin as the only active admin.
    c.post(f'/dashboard/users/{admin_user.pk}/', {'role': 'admin'})  # deactivate other admin
    admin_user.refresh_from_db()
    assert admin_user.is_active is False
    # Now demoting the last remaining active admin (self) is blocked.
    r = c.post(f'/dashboard/users/{second_admin.pk}/', {'role': 'user', 'is_active': 'on'})
    assert r.status_code == 302
    second_admin.refresh_from_db()
    assert second_admin.role == 'admin'


@pytest.mark.django_db
def test_admin_can_change_other_user_role(admin_user, regular_user, mocker):
    c = _admin_client(admin_user, mocker)
    r = c.post(f'/dashboard/users/{regular_user.pk}/', {'role': 'staff', 'is_active': 'on'})
    assert r.status_code == 302
    regular_user.refresh_from_db()
    assert regular_user.role == 'staff'
