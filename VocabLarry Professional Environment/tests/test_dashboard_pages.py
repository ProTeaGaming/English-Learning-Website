import pytest
from django.test import Client


@pytest.mark.django_db
def test_dashboard_index_requires_login():
    c = Client()
    r = c.get('/dashboard/')
    assert r.status_code == 302
    assert '/accounts/login/' in r.url


@pytest.mark.django_db
def test_dashboard_index_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_index_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    assert 'Dashboard' in r.content.decode()


@pytest.mark.django_db
def test_dashboard_word_list_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_word_list_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_users_forbidden_for_staff_non_admin(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_users_allowed_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_guest():
    c = Client()
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()
