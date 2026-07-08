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
