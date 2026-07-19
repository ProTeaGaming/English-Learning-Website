import pytest
from django.test import Client

from vocab.models import GrammarTopic


@pytest.fixture
def topic_articles(db):
    return GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )


@pytest.mark.django_db
def test_grammar_browse_renders():
    c = Client()
    r = c.get('/grammar/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_lists_topics(topic_articles):
    c = Client()
    r = c.get('/grammar/')
    assert 'Articles (a/an/the)' in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_search_filters_by_title(topic_articles):
    GrammarTopic.objects.create(
        slug='future-forms', title='Future Forms', tag='Tenses',
        cefr_label='A1+', blurb='will vs going to.', stage='beginner', order=1,
    )
    c = Client()
    r = c.get('/grammar/?q=Articles')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Future Forms' not in html


@pytest.mark.django_db
def test_grammar_browse_stage_filter(topic_articles):
    GrammarTopic.objects.create(
        slug='conditionals', title='Conditionals', tag='Conditionals',
        cefr_label='B2', blurb='If clauses.', stage='expert', order=1,
    )
    c = Client()
    r = c.get('/grammar/?stage=expert')
    html = r.content.decode()
    assert 'Conditionals' in html
    assert 'Articles (a/an/the)' not in html


@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/"' in html
    assert 'nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_home_hero_grammar_cta_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'hero.grammar">Practice Grammar</a>' in html


from vocab.models import GrammarLessonBlock


@pytest.fixture
def topic_with_blocks(db):
    topic = GrammarTopic.objects.create(
        slug='present-simple-continuous', title='Present Simple & Continuous',
        tag='Tenses', cefr_label='A1', blurb='Know when to use which.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='intro',
        body='<p>The present simple describes <b>facts</b>.</p>', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='rule', title='Present Simple',
        body='<p>Form: base verb (+ <b>-s</b>).</p>', order=1,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='table', title='Quick map',
        data={'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}, order=2,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='examples',
        data={'items': [
            {'en': 'The sun rises in the east.', 'note': 'General fact.'},
            {'en': 'Prices are rising.'},
        ]}, order=3,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='tip', body='<p>Use present simple for charts.</p>', order=4,
    )
    return topic


@pytest.mark.django_db
def test_grammar_topic_detail_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert r.status_code == 200
    assert 'Present Simple & Continuous' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/topic/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_topic_detail_renders_intro_html_unescaped(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert '<b>facts</b>' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_renders_rule_title(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert 'Present Simple' in html
    assert '<b>-s</b>' in html


@pytest.mark.django_db
def test_grammar_topic_detail_renders_table(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert '<th>Use</th>' in html
    assert '<td>Fact</td>' in html


@pytest.mark.django_db
def test_grammar_topic_detail_renders_examples(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert 'The sun rises in the east.' in html
    assert 'General fact.' in html
    assert 'Prices are rising.' in html
