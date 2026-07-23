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


@pytest.mark.django_db
def test_user_progress_stats_empty_for_anonymous():
    from django.contrib.auth.models import AnonymousUser

    from config.context_processors import user_progress_stats

    class _Req:
        user = AnonymousUser()

    assert user_progress_stats(_Req()) == {}


@pytest.mark.django_db
def test_user_progress_stats_computed_for_authenticated_user(regular_user):
    from config.context_processors import user_progress_stats
    from vocab.models import Category, Word

    cat = Category.objects.create(slug='animals', name='Animals', order=1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])

    class _Req:
        user = regular_user

    assert user_progress_stats(_Req()) == {
        'words_learned': 1, 'total_words': 2, 'little_count': 1,
    }


@pytest.mark.django_db
def test_user_progress_stats_wired_into_templates(regular_user):
    # If config.context_processors.user_progress_stats weren't correctly
    # registered in TEMPLATES, this would raise ImproperlyConfigured the
    # first time any page renders for a logged-in user.
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_site_footer_stats_computed_for_anonymous_user():
    from config.context_processors import site_footer_stats
    from django.contrib.auth.models import AnonymousUser
    from vocab.models import Category, Word

    cat = Category.objects.create(slug='animals', name='Animals', order=1)
    Word.objects.create(word='Cat', definition='x', category=cat, order=1)

    class _Req:
        user = AnonymousUser()

    assert site_footer_stats(_Req()) == {
        'footer_total_words': 1,
        'footer_words_learned': 0,
        'footer_pct_complete': 0,
        'footer_categories_started': 0,
        'footer_total_categories': 1,
    }


@pytest.mark.django_db
def test_site_footer_stats_computed_for_authenticated_user(regular_user):
    from config.context_processors import site_footer_stats
    from vocab.models import Category, Word

    cat1 = Category.objects.create(slug='animals', name='Animals', order=1)
    cat2 = Category.objects.create(slug='colors', name='Colors', order=2)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    Word.objects.create(word='Red', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])

    class _Req:
        user = regular_user

    assert site_footer_stats(_Req()) == {
        'footer_total_words': 3,
        'footer_words_learned': 1,
        'footer_pct_complete': 33,
        'footer_categories_started': 1,
        'footer_total_categories': 2,
    }


@pytest.mark.django_db
def test_site_footer_stats_wired_into_templates():
    # Guards against an ImproperlyConfigured typo in TEMPLATES, same as
    # the user_progress_stats guard above.
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
