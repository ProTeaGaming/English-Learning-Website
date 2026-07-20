import pytest
from django.test import Client

from config.context_processors import nav_active_section


class _FakeMatch:
    def __init__(self, url_name):
        self.url_name = url_name


class _FakeRequest:
    def __init__(self, resolver_match):
        self.resolver_match = resolver_match


def test_nav_active_section_matches_vocabulary_prefix():
    request = _FakeRequest(_FakeMatch('vocabulary_quiz_setup'))
    assert nav_active_section(request) == {'nav_active_section': 'vocabulary'}


def test_nav_active_section_matches_grammar_prefix():
    request = _FakeRequest(_FakeMatch('grammar_category_detail'))
    assert nav_active_section(request) == {'nav_active_section': 'grammar'}


def test_nav_active_section_matches_flat_section_names():
    for name in ('home', 'reading', 'writing', 'listening', 'speaking'):
        request = _FakeRequest(_FakeMatch(name))
        assert nav_active_section(request) == {'nav_active_section': name}


def test_nav_active_section_none_for_unmatched_url_name():
    request = _FakeRequest(_FakeMatch('account_login'))
    assert nav_active_section(request) == {'nav_active_section': None}


def test_nav_active_section_none_when_resolver_match_is_none():
    request = _FakeRequest(None)
    assert nav_active_section(request) == {'nav_active_section': None}


@pytest.mark.django_db
def test_context_processor_is_wired_into_templates():
    # If config.context_processors.nav_active_section weren't correctly
    # registered in TEMPLATES, this dotted-path lookup would raise
    # ImproperlyConfigured the first time any page renders.
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
