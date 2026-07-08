import pytest
from django.test import Client


@pytest.fixture
def logged_in(mocker):
    """Client factory: log a user in with allauth MFA check stubbed out."""
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    def _login(user):
        c = Client()
        c.force_login(user)
        return c
    return _login


@pytest.mark.django_db
def test_session_reports_is_staff_false_for_regular_user(logged_in, regular_user):
    r = logged_in(regular_user).get('/auth/session/')
    assert r.status_code == 200
    assert r.json()['isStaff'] is False


@pytest.mark.django_db
def test_session_reports_is_staff_true_for_staff_and_admin(logged_in, staff_user, admin_user):
    assert logged_in(staff_user).get('/auth/session/').json()['isStaff'] is True
    assert logged_in(admin_user).get('/auth/session/').json()['isStaff'] is True


@pytest.mark.django_db
def test_session_anonymous_has_no_is_staff_key():
    r = Client().get('/auth/session/')
    assert r.json() == {'loggedIn': False}


from vocab.models import CEFRLevel, Color, Category, Word


@pytest.fixture
def cefr_b1(db):
    return CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)


@pytest.fixture
def category(db, cefr_b1):
    color = Color.objects.create(name='Violet', bg_hex='#7c3aed', text_hex='#ffffff')
    return Category.objects.create(
        slug='travel', name='Travel', icon='✈️',
        cefr_level=cefr_b1, color=color, order=0,
    )


@pytest.fixture
def word(db, category, cefr_b1):
    return Word.objects.create(
        word='journey', pos='noun', definition='a trip', example='A long journey.',
        gap='A long ___.', category=category, cefr_level=cefr_b1, order=0,
        synonyms=['trip'], antonyms=[],
    )


def word_payload(category, cefr_b1, **over):
    p = {
        'word': 'voyage', 'pos': 'noun', 'definition': 'a long trip by sea',
        'example': 'The voyage took weeks.', 'gap': 'The ___ took weeks.',
        'category': category.pk, 'cefr_level': cefr_b1.pk, 'order': 1,
        'synonyms': ['journey', 'trip'], 'antonyms': [],
    }
    p.update(over)
    return p


@pytest.mark.django_db
def test_word_write_endpoints_reject_non_staff(logged_in, regular_user, word, category, cefr_b1):
    anon = Client()
    user = logged_in(regular_user)
    payload = word_payload(category, cefr_b1)
    for c in (anon, user):
        assert c.post('/api/words/', payload, content_type='application/json').status_code == 403
        assert c.patch(f'/api/words/{word.pk}/', payload, content_type='application/json').status_code == 403
        assert c.delete(f'/api/words/{word.pk}/').status_code == 403
    assert Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_staff_can_create_word(logged_in, staff_user, category, cefr_b1):
    r = logged_in(staff_user).post(
        '/api/words/', word_payload(category, cefr_b1), content_type='application/json')
    assert r.status_code == 200
    body = r.json()
    assert body['word'] == 'voyage'
    assert body['synonyms'] == ['journey', 'trip']
    assert Word.objects.filter(word='voyage').exists()


@pytest.mark.django_db
def test_staff_can_update_word(logged_in, staff_user, word, category, cefr_b1):
    payload = word_payload(category, cefr_b1, word='journey', definition='an act of travelling')
    r = logged_in(staff_user).patch(
        f'/api/words/{word.pk}/', payload, content_type='application/json')
    assert r.status_code == 200
    word.refresh_from_db()
    assert word.definition == 'an act of travelling'


@pytest.mark.django_db
def test_staff_can_delete_word(logged_in, staff_user, word):
    r = logged_in(staff_user).delete(f'/api/words/{word.pk}/')
    assert r.status_code == 200 and r.json() == {'ok': True}
    assert not Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_word_create_missing_field_returns_400_with_errors(logged_in, staff_user, category, cefr_b1):
    payload = word_payload(category, cefr_b1, word='')
    r = logged_in(staff_user).post('/api/words/', payload, content_type='application/json')
    assert r.status_code == 400
    assert 'word' in r.json()['errors']


@pytest.mark.django_db
def test_word_create_bad_json_returns_400(logged_in, staff_user):
    r = logged_in(staff_user).post('/api/words/', 'not json', content_type='application/json')
    assert r.status_code == 400


@pytest.mark.django_db
def test_category_write_endpoints_reject_non_staff(logged_in, regular_user, category):
    c = logged_in(regular_user)
    assert c.post('/api/categories/', {}, content_type='application/json').status_code == 403
    assert c.patch(f'/api/categories/{category.pk}/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/categories/{category.pk}/').status_code == 403


@pytest.mark.django_db
def test_staff_can_create_update_delete_category(logged_in, staff_user, category, cefr_b1):
    c = logged_in(staff_user)
    payload = {'slug': 'work', 'name': 'Work', 'icon': '💼',
               'cefr_level': cefr_b1.pk, 'color': category.color.pk, 'order': 5}
    r = c.post('/api/categories/', payload, content_type='application/json')
    assert r.status_code == 200 and r.json()['slug'] == 'work'
    new_pk = r.json()['id']

    payload['name'] = 'Work & Career'
    r = c.patch(f'/api/categories/{new_pk}/', payload, content_type='application/json')
    assert r.status_code == 200 and r.json()['name'] == 'Work & Career'

    r = c.delete(f'/api/categories/{new_pk}/')
    assert r.status_code == 200
    assert not Category.objects.filter(pk=new_pk).exists()


@pytest.mark.django_db
def test_category_create_duplicate_slug_returns_400(logged_in, staff_user, category, cefr_b1):
    payload = {'slug': 'travel', 'name': 'Travel 2', 'icon': 'x',
               'cefr_level': cefr_b1.pk, 'color': category.color.pk, 'order': 9}
    r = logged_in(staff_user).post('/api/categories/', payload, content_type='application/json')
    assert r.status_code == 400 and 'slug' in r.json()['errors']


from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.fixture
def topic(db):
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles', tag='Determiners',
        cefr_label='A1', blurb='a/an/the', stage='beginner', order=0)
    GrammarLessonBlock.objects.create(topic=t, type='intro', body='Intro text.', order=0)
    GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She is ___ engineer.',
        options=['a', 'an', 'the', '(none)'], answers=[1], why='Vowel sound.', order=0)
    return t


@pytest.mark.django_db
def test_grammar_api_includes_ids_and_order(topic):
    r = Client().get('/api/grammar/')
    beginner = next(s for s in r.json() if s['id'] == 'beginner')
    t = beginner['topics'][0]
    assert t['id'] == topic.pk and t['order'] == 0
    assert t['lesson'][0]['id'] and t['lesson'][0]['order'] == 0
    assert t['quiz'][0]['id'] and t['quiz'][0]['order'] == 0


def topic_payload(**over):
    p = {'slug': 'passive-voice', 'title': 'Passive Voice', 'tag': 'Voice',
         'cefr_label': 'B1', 'blurb': 'Focus on the action.',
         'stage': 'independent', 'order': 13}
    p.update(over)
    return p


@pytest.mark.django_db
def test_grammar_topic_writes_reject_non_staff(logged_in, regular_user, topic):
    c = logged_in(regular_user)
    assert c.post('/api/grammar/topics/', topic_payload(), content_type='application/json').status_code == 403
    assert c.patch(f'/api/grammar/topics/{topic.pk}/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/topics/{topic.pk}/').status_code == 403


@pytest.mark.django_db
def test_staff_can_create_update_topic(logged_in, staff_user):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/topics/', topic_payload(), content_type='application/json')
    assert r.status_code == 200 and r.json()['slug'] == 'passive-voice'
    pk = r.json()['id']
    r = c.patch(f'/api/grammar/topics/{pk}/',
                topic_payload(title='Passive & Active Voice'), content_type='application/json')
    assert r.status_code == 200 and r.json()['title'] == 'Passive & Active Voice'


@pytest.mark.django_db
def test_topic_delete_cascades_blocks_and_questions(logged_in, staff_user, topic):
    r = logged_in(staff_user).delete(f'/api/grammar/topics/{topic.pk}/')
    assert r.status_code == 200
    assert not GrammarTopic.objects.filter(pk=topic.pk).exists()
    assert GrammarLessonBlock.objects.count() == 0
    assert GrammarQuestion.objects.count() == 0


@pytest.mark.django_db
def test_topic_create_invalid_stage_returns_400(logged_in, staff_user):
    r = logged_in(staff_user).post('/api/grammar/topics/',
                                   topic_payload(stage='wizard'), content_type='application/json')
    assert r.status_code == 400 and 'stage' in r.json()['errors']


@pytest.mark.django_db
def test_staff_can_create_update_delete_block(logged_in, staff_user, topic):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/blocks/', {
        'topic': topic.pk, 'type': 'rule', 'title': 'Use "an" before vowels',
        'body': 'Use an before vowel sounds.', 'data': {}, 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200
    pk = r.json()['id']
    r = c.patch(f'/api/grammar/blocks/{pk}/', {
        'type': 'rule', 'title': 'Use "an" before vowel SOUNDS',
        'body': 'an hour, an MP.', 'data': {}, 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200 and 'SOUNDS' in r.json()['title']
    assert c.delete(f'/api/grammar/blocks/{pk}/').status_code == 200


@pytest.mark.django_db
def test_block_create_table_without_head_returns_400(logged_in, staff_user, topic):
    r = logged_in(staff_user).post('/api/grammar/blocks/', {
        'topic': topic.pk, 'type': 'table', 'title': 'T', 'body': '',
        'data': {'rows': [['a']]}, 'order': 2,
    }, content_type='application/json')
    assert r.status_code == 400


@pytest.mark.django_db
def test_staff_can_create_question_and_bad_mcq_rejected(logged_in, staff_user, topic):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/questions/', {
        'topic': topic.pk, 'qtype': 'mcq', 'prompt': 'He bought ___ umbrella.',
        'options': ['a', 'an', 'the', '(none)'], 'answers': [1], 'why': 'Vowel.', 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200
    r = c.post('/api/grammar/questions/', {
        'topic': topic.pk, 'qtype': 'mcq', 'prompt': 'x',
        'options': ['a', 'b', 'c'], 'answers': [0], 'why': 'x', 'order': 2,
    }, content_type='application/json')
    assert r.status_code == 400 and 'options' in r.json()['errors']


@pytest.mark.django_db
def test_gap_question_with_empty_options_saves_cleanly(logged_in, staff_user, topic):
    r = logged_in(staff_user).post('/api/grammar/questions/', {
        'topic': topic.pk, 'qtype': 'gap', 'prompt': 'She ___ (go) home.',
        'options': [], 'answers': ['went'], 'why': 'Past simple.', 'order': 3,
    }, content_type='application/json')
    assert r.status_code == 200
    assert r.json()['options'] == []


@pytest.mark.django_db
def test_block_and_question_writes_reject_non_staff(logged_in, regular_user, topic):
    c = logged_in(regular_user)
    block = topic.blocks.first()
    q = topic.questions.first()
    assert c.post('/api/grammar/blocks/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/blocks/{block.pk}/').status_code == 403
    assert c.post('/api/grammar/questions/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/questions/{q.pk}/').status_code == 403


@pytest.mark.django_db
def test_word_detail_nonexistent_pk_returns_404(logged_in, staff_user):
    c = logged_in(staff_user)
    assert c.patch('/api/words/99999/', {}, content_type='application/json').status_code == 404
    assert c.delete('/api/words/99999/').status_code == 404


@pytest.mark.django_db
def test_block_patch_cannot_move_to_another_topic(logged_in, staff_user, topic):
    other = GrammarTopic.objects.create(
        slug='other-topic', title='Other', tag='Voice',
        cefr_label='B1', blurb='x', stage='independent', order=9)
    block = topic.blocks.first()
    r = logged_in(staff_user).patch(f'/api/grammar/blocks/{block.pk}/', {
        'topic': other.pk, 'type': block.type, 'title': block.title,
        'body': block.body, 'data': block.data, 'order': block.order,
    }, content_type='application/json')
    assert r.status_code == 200
    block.refresh_from_db()
    assert block.topic_id == topic.pk


@pytest.mark.django_db
def test_word_create_non_dict_json_returns_400(logged_in, staff_user):
    r = logged_in(staff_user).post('/api/words/', '[1, 2]', content_type='application/json')
    assert r.status_code == 400
