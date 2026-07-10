import json
import pytest
from django.contrib.auth import get_user_model
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


@pytest.mark.django_db
def test_session_reports_has_password(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/session/')
    assert json.loads(r.content)['hasPassword'] is True


@pytest.mark.django_db
def test_session_reports_no_password_for_social_only_account(regular_user):
    regular_user.set_unusable_password()
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/session/')
    assert json.loads(r.content)['hasPassword'] is False


@pytest.mark.django_db
def test_session_reports_just_signed_up_social_when_flagged(regular_user):
    c = Client()
    c.force_login(regular_user)
    session = c.session
    session['social_signup_needs_profile'] = True
    session.save()
    r = c.get('/auth/session/')
    assert json.loads(r.content)['justSignedUpSocial'] is True


@pytest.mark.django_db
def test_session_just_signed_up_social_is_one_time_only(regular_user):
    c = Client()
    c.force_login(regular_user)
    session = c.session
    session['social_signup_needs_profile'] = True
    session.save()
    c.get('/auth/session/')
    r = c.get('/auth/session/')
    assert json.loads(r.content)['justSignedUpSocial'] is False


@pytest.mark.django_db
def test_session_just_signed_up_social_false_for_normal_login(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/session/')
    assert json.loads(r.content)['justSignedUpSocial'] is False


@pytest.mark.django_db
def test_social_account_adapter_flags_first_time_signup(regular_user, rf):
    from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
    from accounts.adapters import SocialAccountAdapter

    request = rf.get('/')
    request.session = {}

    class FakeSocialLogin:
        user = regular_user
        account = None

        def save(self, request):
            pass

    adapter = SocialAccountAdapter()
    import unittest.mock as mock
    with mock.patch.object(DefaultSocialAccountAdapter, 'save_user', return_value=regular_user):
        adapter.save_user(request, FakeSocialLogin())
    assert request.session.get('social_signup_needs_profile') is True


@pytest.mark.django_db
def test_session_reports_social_account_connected_when_flagged(regular_user):
    c = Client()
    c.force_login(regular_user)
    session = c.session
    session['social_account_connected'] = True
    session.save()
    r = c.get('/auth/session/')
    assert json.loads(r.content)['socialAccountConnected'] is True


@pytest.mark.django_db
def test_session_social_account_connected_is_one_time_only(regular_user):
    c = Client()
    c.force_login(regular_user)
    session = c.session
    session['social_account_connected'] = True
    session.save()
    c.get('/auth/session/')
    r = c.get('/auth/session/')
    assert json.loads(r.content)['socialAccountConnected'] is False


@pytest.mark.django_db
def test_social_account_added_signal_flags_session(regular_user, rf):
    from allauth.socialaccount.signals import social_account_added

    request = rf.get('/')
    request.session = {}
    social_account_added.send(sender=object, request=request, sociallogin=None)
    assert request.session.get('social_account_connected') is True


@pytest.mark.django_db
def test_connected_providers_list_and_disconnect(regular_user):
    from allauth.account.models import EmailAddress
    from allauth.socialaccount.models import SocialAccount

    # Disconnecting your only SocialAccount also requires a verified email
    # on file (so a password reset stays possible) — the regular_user
    # fixture doesn't create one by default.
    EmailAddress.objects.create(user=regular_user, email=regular_user.email, verified=True, primary=True)
    SocialAccount.objects.create(user=regular_user, provider='google', uid='test-uid-1', extra_data={})
    c = Client()
    c.force_login(regular_user)

    r = c.get('/_allauth/browser/v1/account/providers')
    assert r.status_code == 200
    data = json.loads(r.content)['data']
    assert len(data) == 1
    assert data[0]['provider']['id'] == 'google'
    assert data[0]['uid'] == 'test-uid-1'

    r = c.delete(
        '/_allauth/browser/v1/account/providers',
        data=json.dumps({'provider': 'google', 'account': 'test-uid-1'}),
        content_type='application/json',
    )
    assert r.status_code == 200
    assert not SocialAccount.objects.filter(user=regular_user, provider='google').exists()


@pytest.mark.django_db
def test_cannot_disconnect_only_login_method_without_password(regular_user):
    from allauth.socialaccount.models import SocialAccount

    regular_user.set_unusable_password()
    regular_user.save()
    SocialAccount.objects.create(user=regular_user, provider='google', uid='test-uid-2', extra_data={})
    c = Client()
    c.force_login(regular_user)

    r = c.delete(
        '/_allauth/browser/v1/account/providers',
        data=json.dumps({'provider': 'google', 'account': 'test-uid-2'}),
        content_type='application/json',
    )
    assert r.status_code == 400
    assert SocialAccount.objects.filter(user=regular_user, provider='google').exists()


@pytest.mark.django_db
def test_delete_account_wrong_password_rejected(regular_user):
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'password': 'wrong'})
    r = c.post('/auth/delete-account/', payload, content_type='application/json')
    assert r.status_code == 401
    assert get_user_model().objects.filter(pk=regular_user.pk).exists()


@pytest.mark.django_db
def test_delete_account_correct_password_succeeds(regular_user):
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'password': 'testpass123'})
    r = c.post('/auth/delete-account/', payload, content_type='application/json')
    assert r.status_code == 200
    assert not get_user_model().objects.filter(pk=regular_user.pk).exists()


@pytest.mark.django_db
def test_delete_account_without_usable_password_succeeds_without_password(regular_user):
    # Social-login-only accounts (e.g. Google) have no usable password —
    # check_password() rejects any input for them, so the password check
    # must be skipped entirely rather than permanently blocking deletion.
    regular_user.set_unusable_password()
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'password': ''})
    r = c.post('/auth/delete-account/', payload, content_type='application/json')
    assert r.status_code == 200
    assert not get_user_model().objects.filter(pk=regular_user.pk).exists()
