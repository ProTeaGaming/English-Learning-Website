import pytest


@pytest.mark.django_db
def test_home_page_renders():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
    assert 'text/html' in r['Content-Type']
