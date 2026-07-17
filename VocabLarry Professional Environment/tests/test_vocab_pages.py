import pytest
from django.test import Client
from vocab.models import CEFRLevel, Category


@pytest.fixture
def cefr_a1(db):
    return CEFRLevel.objects.create(code='A1', name='Beginner', order=1)


@pytest.fixture
def cefr_b1(db):
    return CEFRLevel.objects.create(code='B1', name='Intermediate', order=2)


@pytest.mark.django_db
def test_vocab_browse_renders():
    c = Client()
    r = c.get('/vocab/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_browse_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocab_browse_search_filters_by_name(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/?q=Animal')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocab_browse_cefr_filter(cefr_a1, cefr_b1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='business-basics', name='Business Basics', order=2, cefr_level=cefr_b1)
    c = Client()
    r = c.get('/vocab/?cefr=B1')
    body = r.content.decode()
    assert 'Business Basics' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_home_nav_links_to_vocab_browse():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    # Vocabulary becomes a real link. Grammar stays disabled/coming-soon
    # on this same page (separate future sub-project) - don't assert
    # "coming soon" is gone entirely, only that Vocabulary now links out.
    assert 'href="/vocab/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body
