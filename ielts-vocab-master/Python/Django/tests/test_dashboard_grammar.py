import pytest
from django.test import Client
from vocab.models import GrammarTopic, GrammarQuestion


@pytest.fixture
def staff_client(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    return c


@pytest.fixture
def topic(db):
    return GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )


@pytest.mark.django_db
def test_grammar_list_requires_staff(regular_user):
    c = Client()
    c.force_login(regular_user)
    assert c.get('/dashboard/grammar/').status_code == 403


@pytest.mark.django_db
def test_grammar_list_shows_topics_and_stage_filter(staff_client, topic):
    r = staff_client.get('/dashboard/grammar/')
    assert r.status_code == 200
    assert b'Articles (a/an/the)' in r.content
    r = staff_client.get('/dashboard/grammar/?stage=expert')
    assert b'Articles (a/an/the)' not in r.content


@pytest.mark.django_db
def test_topic_add_and_delete(staff_client):
    r = staff_client.post('/dashboard/grammar/add/', {
        'slug': 'passive-voice', 'title': 'Passive & Active Voice', 'tag': 'Voice',
        'cefr_label': 'B1–B2', 'blurb': 'Focus on the action, not the doer.',
        'stage': 'independent', 'order': 13,
    })
    assert r.status_code == 302
    t = GrammarTopic.objects.get(slug='passive-voice')
    r = staff_client.post(f'/dashboard/grammar/{t.pk}/delete/')
    assert r.status_code == 302
    assert not GrammarTopic.objects.filter(slug='passive-voice').exists()


@pytest.mark.django_db
def test_question_add_valid_mcq(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'She is ___ engineer.',
        'options': '["a", "an", "the", "(no article)"]',
        'answers': '[1]', 'why': 'Vowel sound.', 'order': 0,
    })
    assert r.status_code == 302
    q = GrammarQuestion.objects.get(topic=topic)
    assert q.answers == [1]


@pytest.mark.django_db
def test_question_add_rejects_mcq_with_three_options(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'x', 'options': '["a", "b", "c"]',
        'answers': '[0]', 'why': 'x', 'order': 0,
    })
    assert r.status_code == 200  # re-rendered with errors
    assert b'exactly 4 options' in r.content
    assert GrammarQuestion.objects.count() == 0


@pytest.mark.django_db
def test_question_add_rejects_gap_without_string_answers(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'gap', 'prompt': 'I saw ___ moon.', 'options': '[]',
        'answers': '[1]', 'why': 'x', 'order': 0,
    })
    assert r.status_code == 200
    assert b'non-empty strings' in r.content


@pytest.mark.django_db
def test_block_add_rejects_table_without_head_rows(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/blocks/add/', {
        'type': 'table', 'title': 'Forms', 'body': '', 'data': '{}', 'order': 0,
    })
    assert r.status_code == 200
    assert b'head' in r.content


@pytest.mark.django_db
def test_index_shows_grammar_count(staff_client, topic):
    r = staff_client.get('/dashboard/')
    assert b'Grammar topics' in r.content
