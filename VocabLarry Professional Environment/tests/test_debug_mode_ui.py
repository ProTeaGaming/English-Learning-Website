import pytest


@pytest.mark.django_db
def test_debug_toggle_visible_for_staff(client, staff_user):
    client.force_login(staff_user)
    r = client.get('/')
    assert r.status_code == 200
    assert b'id="debugToggle"' in r.content


@pytest.mark.django_db
def test_debug_toggle_visible_for_admin(client, admin_user):
    client.force_login(admin_user)
    r = client.get('/')
    assert b'id="debugToggle"' in r.content


@pytest.mark.django_db
def test_debug_toggle_absent_for_regular_user(client, regular_user):
    client.force_login(regular_user)
    r = client.get('/')
    assert b'id="debugToggle"' not in r.content


@pytest.mark.django_db
def test_debug_toggle_absent_for_anonymous(client):
    r = client.get('/')
    assert b'id="debugToggle"' not in r.content
