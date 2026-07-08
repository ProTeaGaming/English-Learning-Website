import json
import pytest
from django.test import Client


@pytest.mark.django_db
def test_sync_get_requires_login():
    c = Client()
    r = c.get('/auth/sync/')
    assert r.status_code == 401


@pytest.mark.django_db
def test_sync_get_returns_learn_map(regular_user):
    regular_user.learn_map = {'42': 1700000000}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/sync/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert data['learn_map'] == {'42': 1700000000}


@pytest.mark.django_db
def test_sync_post_updates_learn_map(regular_user):
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'learn_map': {'7': 1700000001}})
    r = c.post('/auth/sync/', payload, content_type='application/json')
    assert r.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {'7': 1700000001}


@pytest.mark.django_db
def test_sync_get_returns_grammar_map(regular_user):
    regular_user.grammar_map = {'articles': {'best': 90, 'done': True}}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/sync/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert data['grammar_map'] == {'articles': {'best': 90, 'done': True}}


@pytest.mark.django_db
def test_sync_post_updates_grammar_map(regular_user):
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'learn_map': {}, 'grammar_map': {'articles': {'best': 70, 'done': False}}})
    r = c.post('/auth/sync/', payload, content_type='application/json')
    assert r.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.grammar_map == {'articles': {'best': 70, 'done': False}}


@pytest.mark.django_db
def test_sync_post_without_grammar_map_leaves_it_untouched(regular_user):
    regular_user.grammar_map = {'articles': {'best': 90, 'done': True}}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'learn_map': {'7': 'learned'}})
    r = c.post('/auth/sync/', payload, content_type='application/json')
    assert r.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.grammar_map == {'articles': {'best': 90, 'done': True}}


@pytest.mark.django_db
def test_check_email_returns_false_for_unknown():
    c = Client()
    payload = json.dumps({'email': 'nobody@example.com'})
    r = c.post('/auth/check-email/', payload, content_type='application/json',
               HTTP_X_CSRFTOKEN='test', enforce_csrf_checks=False)
    assert r.status_code == 200
    assert json.loads(r.content) == {'exists': False}


@pytest.mark.django_db
def test_check_email_returns_true_for_existing(regular_user):
    c = Client()
    payload = json.dumps({'email': regular_user.email})
    r = c.post('/auth/check-email/', payload, content_type='application/json',
               enforce_csrf_checks=False)
    assert r.status_code == 200
    assert json.loads(r.content) == {'exists': True}
