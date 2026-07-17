import json
from types import SimpleNamespace

import dns.exception
import dns.resolver
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client

from accounts.adapters import AccountAdapter, email_domain_accepts_mail


def _mx(exchange):
    return SimpleNamespace(exchange=exchange)


def test_domain_with_mx_accepts_mail(mocker):
    mocker.patch('accounts.adapters.dns.resolver.resolve',
                 return_value=[_mx('mail.example.com.')])
    assert email_domain_accepts_mail('example.com') is True


def test_nonexistent_domain_rejected(mocker):
    mocker.patch('accounts.adapters.dns.resolver.resolve',
                 side_effect=dns.resolver.NXDOMAIN)
    assert email_domain_accepts_mail('no-such-brand-9f2x.com') is False


def test_null_mx_rejected(mocker):
    # RFC 7505: a single "." MX means the domain explicitly refuses mail.
    mocker.patch('accounts.adapters.dns.resolver.resolve',
                 return_value=[_mx('.')])
    assert email_domain_accepts_mail('no-mail.example') is False


def test_no_mx_falls_back_to_a_record(mocker):
    def fake_resolve(domain, rtype, lifetime=None):
        if rtype == 'MX':
            raise dns.resolver.NoAnswer
        return [SimpleNamespace()]
    mocker.patch('accounts.adapters.dns.resolver.resolve', side_effect=fake_resolve)
    assert email_domain_accepts_mail('a-record-only.example') is True


def test_no_mx_and_no_address_records_rejected(mocker):
    def fake_resolve(domain, rtype, lifetime=None):
        raise dns.resolver.NoAnswer
    mocker.patch('accounts.adapters.dns.resolver.resolve', side_effect=fake_resolve)
    assert email_domain_accepts_mail('parked.example') is False


def test_dns_timeout_fails_open(mocker):
    # A resolver hiccup must never block signups.
    mocker.patch('accounts.adapters.dns.resolver.resolve',
                 side_effect=dns.exception.Timeout)
    assert email_domain_accepts_mail('example.com') is True


def test_clean_email_rejects_undeliverable_domain(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=False)
    with pytest.raises(ValidationError):
        AccountAdapter().clean_email('me@unpurchased-brand.com')


def test_clean_email_accepts_deliverable_domain(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=True)
    assert AccountAdapter().clean_email('me@example.com') == 'me@example.com'


@pytest.mark.django_db
def test_signup_rejects_undeliverable_email_domain(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=False)
    c = Client()
    r = c.post('/accounts/signup/', {
        'email': 'me@unpurchased-brand.com', 'username': 'branduser',
        'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
    })
    assert r.status_code == 200  # re-renders the form with an error
    assert 'This email domain cannot receive mail' in r.content.decode()
    assert not get_user_model().objects.filter(email='me@unpurchased-brand.com').exists()


@pytest.mark.django_db
def test_signup_with_deliverable_domain_still_works(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=True)
    c = Client()
    r = c.post('/accounts/signup/', {
        'email': 'me@example.com', 'username': 'newuser',
        'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
    })
    # Mandatory verification: account is created, redirected to the
    # "check your inbox" page rather than logged straight in.
    assert r.status_code == 302
    assert r['Location'] == '/accounts/confirm-email/'
    assert get_user_model().objects.filter(email='me@example.com').exists()
