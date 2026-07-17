import pytest


@pytest.mark.django_db
def test_home_page_renders():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
    assert 'text/html' in r['Content-Type']


@pytest.mark.django_db
def test_home_page_has_nav_and_hero():
    from django.test import Client
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body
    assert 'hero' in body


@pytest.mark.django_db
def test_login_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/login/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body


@pytest.mark.django_db
def test_signup_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/signup/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_google_login_redirects_to_google():
    from django.test import Client
    c = Client()
    c.get('/accounts/google/login/')  # loads the CSRF-protected confirm page
    r = c.post('/accounts/google/login/')
    assert r.status_code == 302
    assert 'accounts.google.com' in r['Location']


@pytest.mark.django_db
def test_logout_confirm_page_uses_site_layout(regular_user):
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/accounts/logout/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_password_reset_request_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/password/reset/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_email_verification_sent_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/confirm-email/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()
