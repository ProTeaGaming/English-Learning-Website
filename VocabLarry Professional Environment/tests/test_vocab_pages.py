import json

import pytest
from django.test import Client
from vocab.models import CEFRLevel, Category, Word


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


@pytest.mark.django_db
def test_vocab_category_renders_words(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small pet.', category=category, order=1)
    Word.objects.create(word='Dog', definition='A loyal pet.', category=category, order=2)
    c = Client()
    r = c.get('/vocab/category/animals/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'Dog' in body


@pytest.mark.django_db
def test_vocab_category_unknown_slug_404():
    c = Client()
    r = c.get('/vocab/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocab_category_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r1 = c.get('/vocab/category/animals/')
    body1 = r1.content.decode()
    assert 'Word00' in body1
    assert 'Word29' not in body1  # page 2 content shouldn't leak onto page 1
    r2 = c.get('/vocab/category/animals/?page=2')
    body2 = r2.content.decode()
    assert 'Word29' in body2
    assert 'Word00' not in body2


@pytest.mark.django_db
def test_vocab_word_detail_renders(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(
        word='Cat', pos='noun', definition='A small domesticated pet.',
        example='The cat slept all day.', synonyms=['feline'], antonyms=[],
        category=category, order=1,
    )
    c = Client()
    r = c.get(f'/vocab/word/{word.pk}/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'A small domesticated pet.' in body
    assert 'The cat slept all day.' in body
    assert 'feline' in body


@pytest.mark.django_db
def test_vocab_word_detail_unknown_id_404():
    c = Client()
    r = c.get('/vocab/word/999999/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocab_word_detail_shows_progress_toggle_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'learn-state-btn' in r.content.decode()


@pytest.mark.django_db
def test_vocab_word_detail_hides_progress_toggle_when_anonymous(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'learn-state-btn' not in r.content.decode()


@pytest.mark.django_db
def test_vocab_word_detail_reflects_existing_progress(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'data-state="learned"' in r.content.decode()


@pytest.mark.django_db
def test_progress_toggle_round_trip_preserves_other_words(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {'999': 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what static/js/vocab-word.js does on click: GET the current
    # map, mutate only this word's key, POST the full map back.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    learn_map[str(word.pk)] = 'little'
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {'999': 'learned', str(word.pk): 'little'}


@pytest.mark.django_db
def test_vocab_word_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocab_word_detail_loads_toggle_script_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'vocab-word.js' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_renders():
    c = Client()
    r = c.get('/vocab/quiz/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/quiz/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_cefr_levels(cefr_a1):
    c = Client()
    r = c.get('/vocab/quiz/')
    assert '>A1<' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_has_family_toggle():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'name="family"' in html
    assert 'value="quiz"' in html
    assert 'value="gap"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_gap_submodes():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="gap-context"' in html
    assert 'value="gap-nuance"' in html
    assert 'value="gap-collocation"' in html
    assert 'value="gap-connotation"' in html
    assert 'value="gap-mixed"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_quiz_modes_still_present():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="definition"' in html
    assert 'value="word"' in html
    assert 'value="synonym"' in html
    assert 'value="antonym"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_has_challenge_family_radio():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="challenge" id="familyChallenge"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_has_challenge_mode_input():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'id="challengeModeInput"' in html
    assert 'name="mode" value="challenge"' in html


@pytest.mark.django_db
def test_home_nav_links_to_vocab_quiz():
    c = Client()
    r = c.get('/')
    assert 'href="/vocab/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_play_renders():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_play_has_mount_point():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert 'id="quizPlayRoot"' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_play_loads_script():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert 'vocab-quiz.js' in r.content.decode()
