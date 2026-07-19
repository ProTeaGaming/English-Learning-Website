import json
import pytest
from django.test import Client
from vocab.models import Word, Category, CEFRLevel, GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.mark.django_db
def test_dashboard_index_requires_login():
    c = Client()
    r = c.get('/dashboard/')
    assert r.status_code == 302
    assert '/accounts/login/' in r.url


@pytest.mark.django_db
def test_dashboard_index_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_index_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    assert 'Dashboard' in r.content.decode()


@pytest.mark.django_db
def test_dashboard_word_list_forbidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_word_list_allowed_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/words/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_users_forbidden_for_staff_non_admin(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_users_allowed_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_staff(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_visible_for_admin(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/')
    assert 'href="/dashboard/"' in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_regular_user(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()


@pytest.mark.django_db
def test_nav_dashboard_link_hidden_for_guest():
    c = Client()
    r = c.get('/')
    assert 'href="/dashboard/"' not in r.content.decode()


@pytest.fixture
def cefr_a1(db):
    return CEFRLevel.objects.create(code='A1', name='Beginner', order=1)


@pytest.fixture
def category_animals(db, cefr_a1):
    return Category.objects.create(slug='animals', name='Animals', cefr_level=cefr_a1, order=1)


@pytest.mark.django_db
def test_dashboard_word_add_creates_word(staff_user, category_animals):
    c = Client()
    c.force_login(staff_user)
    r = c.post('/dashboard/words/add/', {
        'word': 'Cat', 'pos': 'noun', 'definition': 'A small domesticated feline.',
        'example': '', 'gap': '', 'category': category_animals.pk, 'cefr_level': '',
        'order': 0, 'synonyms_text': 'feline, kitty', 'antonyms_text': '',
    })
    assert r.status_code == 302
    word = Word.objects.get(word='Cat')
    assert word.definition == 'A small domesticated feline.'
    assert word.synonyms == ['feline', 'kitty']


@pytest.mark.django_db
def test_dashboard_word_edit_updates_word(staff_user, category_animals):
    word = Word.objects.create(word='Dog', definition='A domesticated canine.', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/words/{word.pk}/edit/', {
        'word': 'Dog', 'pos': 'noun', 'definition': 'A loyal domesticated canine.',
        'example': '', 'gap': '', 'category': category_animals.pk, 'cefr_level': '',
        'order': 0, 'synonyms_text': '', 'antonyms_text': '',
    })
    assert r.status_code == 302
    word.refresh_from_db()
    assert word.definition == 'A loyal domesticated canine.'


@pytest.mark.django_db
def test_dashboard_word_delete_removes_word(staff_user, category_animals):
    word = Word.objects.create(word='Bird', definition='x', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/words/{word.pk}/delete/')
    assert r.status_code == 302
    assert not Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_dashboard_category_delete_blocked_when_words_exist(staff_user, category_animals):
    Word.objects.create(word='Cat', definition='x', category=category_animals)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/categories/{category_animals.pk}/delete/')
    assert r.status_code == 302
    assert Category.objects.filter(pk=category_animals.pk).exists()


@pytest.mark.django_db
def test_dashboard_grammar_topic_add_creates_topic(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.post('/dashboard/grammar/add/', {
        'slug': 'test-topic', 'title': 'Test Topic', 'tag': 'Testing',
        'cefr_label': 'A1', 'blurb': 'A topic for testing.', 'stage': 'beginner', 'order': 0,
    })
    assert r.status_code == 302
    assert GrammarTopic.objects.filter(slug='test-topic').exists()


@pytest.mark.django_db
def test_dashboard_grammar_topic_delete_cascades_blocks_and_questions(staff_user):
    topic = GrammarTopic.objects.create(slug='t0', title='T0', tag='X', cefr_label='A1', stage='beginner')
    GrammarLessonBlock.objects.create(topic=topic, type='intro', body='<p>x</p>', order=0)
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/delete/')
    assert r.status_code == 302
    assert not GrammarTopic.objects.filter(pk=topic.pk).exists()
    assert not GrammarLessonBlock.objects.filter(topic_id=topic.pk).exists()


@pytest.mark.django_db
def test_dashboard_grammar_block_add_with_table_data(staff_user):
    topic = GrammarTopic.objects.create(slug='t1', title='T1', tag='X', cefr_label='A1', stage='beginner')
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/blocks/add/', {
        'type': 'table', 'title': 'Quick map', 'body': '',
        'data': json.dumps({'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}),
        'order': 0,
    })
    assert r.status_code == 302
    block = GrammarLessonBlock.objects.get(topic=topic)
    assert block.data == {'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}


@pytest.mark.django_db
def test_dashboard_grammar_question_add_mcq(staff_user):
    topic = GrammarTopic.objects.create(slug='t2', title='T2', tag='X', cefr_label='A1', stage='beginner')
    c = Client()
    c.force_login(staff_user)
    r = c.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'Water ___ at 100C.',
        'options': json.dumps(['boils', 'boil', 'is boiling', 'boiled']),
        'answers': json.dumps([0]), 'why': 'Scientific fact takes present simple.', 'order': 0,
    })
    assert r.status_code == 302
    q = GrammarQuestion.objects.get(topic=topic)
    assert q.answers == [0]


@pytest.mark.django_db
def test_dashboard_category_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/categories/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_color_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/colors/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_cefr_list_smoke(staff_user):
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/cefr-levels/')
    assert r.status_code == 200


@pytest.mark.django_db
def test_dashboard_user_list_smoke(admin_user):
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200
