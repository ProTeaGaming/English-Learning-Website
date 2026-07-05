import json
import pytest
from django.test import Client
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.fixture
def grammar_data(db):
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(topic=t, type='intro', body='<p>Articles come before nouns.</p>', order=0)
    GrammarLessonBlock.objects.create(
        topic=t, type='table', title='Forms',
        data={'head': ['Article', 'Use'], 'rows': [['a', 'consonant sound']]}, order=1,
    )
    GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She studies at ___ university in London.',
        options=['a', 'an', 'the', '(no article)'], answers=[0],
        why='"University" starts with a /j/ (consonant) sound, so we use "a".', order=0,
    )
    return t


@pytest.mark.django_db
def test_grammar_endpoint_nests_stages_topics_blocks_questions(grammar_data):
    r = Client().get('/api/grammar/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert [s['id'] for s in data] == ['beginner', 'independent', 'expert']
    beginner = data[0]
    assert beginner['name'] == 'Beginner'
    assert beginner['cefr'] == 'A1–A2'
    topic = beginner['topics'][0]
    assert topic['slug'] == 'articles'
    assert topic['cefr'] == 'A1–A2'
    assert topic['lesson'][0]['type'] == 'intro'
    assert topic['lesson'][1]['data']['head'] == ['Article', 'Use']
    assert topic['quiz'][0]['options'] == ['a', 'an', 'the', '(no article)']
    assert topic['quiz'][0]['answers'] == [0]
    assert data[1]['topics'] == []
    assert data[2]['topics'] == []


@pytest.mark.django_db
def test_grammar_endpoint_avoids_n_plus_one(grammar_data, django_assert_num_queries):
    with django_assert_num_queries(3):  # topics + prefetched blocks + prefetched questions
        Client().get('/api/grammar/')


@pytest.mark.django_db
def test_grammar_endpoint_rejects_post(grammar_data):
    r = Client().post('/api/grammar/')
    assert r.status_code == 405
