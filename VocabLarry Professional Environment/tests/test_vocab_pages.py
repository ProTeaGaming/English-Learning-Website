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
def test_vocabulary_category_list_renders():
    c = Client()
    r = c.get('/vocabulary/category/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_search_filters_by_name(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/?q=Animal')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_cefr_filter(cefr_a1, cefr_b1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='business-basics', name='Business Basics', order=2, cefr_level=cefr_b1)
    c = Client()
    r = c.get('/vocabulary/category/?cefr=B1')
    body = r.content.decode()
    assert 'Business Basics' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_home():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    assert 'href="/vocabulary/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body


@pytest.mark.django_db
def test_vocabulary_category_detail_renders_words(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small pet.', category=category, order=1)
    Word.objects.create(word='Dog', definition='A loyal pet.', category=category, order=2)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'Dog' in body


@pytest.mark.django_db
def test_vocabulary_category_detail_unknown_slug_404():
    c = Client()
    r = c.get('/vocabulary/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocabulary_category_detail_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r1 = c.get('/vocabulary/category/animals/')
    body1 = r1.content.decode()
    assert 'Word00' in body1
    assert 'Word29' not in body1  # page 2 content shouldn't leak onto page 1
    r2 = c.get('/vocabulary/category/animals/?page=2')
    body2 = r2.content.decode()
    assert 'Word29' in body2
    assert 'Word00' not in body2


@pytest.mark.django_db
def test_vocabulary_word_detail_renders(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(
        word='Cat', pos='noun', definition='A small domesticated pet.',
        example='The cat slept all day.', synonyms=['feline'], antonyms=[],
        category=category, order=1,
    )
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'A small domesticated pet.' in body
    assert 'The cat slept all day.' in body
    assert 'feline' in body


@pytest.mark.django_db
def test_vocabulary_word_detail_unknown_id_404():
    c = Client()
    r = c.get('/vocabulary/word/999999/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocabulary_word_detail_shows_progress_toggle_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'learn-state-btn' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_word_detail_hides_progress_toggle_when_anonymous(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'learn-state-btn' not in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_word_detail_reflects_existing_progress(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
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
def test_vocabulary_word_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocabulary_word_detail_loads_toggle_script_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'vocab-word.js' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_renders():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_cefr_levels(cefr_a1):
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert '>A1<' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_family_toggle():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'name="family"' in html
    assert 'value="quiz"' in html
    assert 'value="gap"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_gap_submodes():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="gap-context"' in html
    assert 'value="gap-nuance"' in html
    assert 'value="gap-collocation"' in html
    assert 'value="gap-connotation"' in html
    assert 'value="gap-mixed"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_quiz_modes_still_present():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="definition"' in html
    assert 'value="word"' in html
    assert 'value="synonym"' in html
    assert 'value="antonym"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_challenge_family_radio():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="challenge" id="familyChallenge"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_challenge_mode_input():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="challengeModeInput"' in html
    assert 'name="mode" value="challenge"' in html


@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_quiz():
    c = Client()
    r = c.get('/')
    # The Quiz link lives inside the collapsed dropdown markup — still
    # present in the raw HTML even though CSS hides it until opened.
    assert 'href="/vocabulary/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_renders():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_has_mount_point():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert 'id="quizPlayRoot"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_loads_script():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert 'vocab-quiz.js' in r.content.decode()


@pytest.mark.django_db
def test_old_vocab_urls_are_gone():
    c = Client()
    assert c.get('/vocab/').status_code == 404
    assert c.get('/vocab/category/animals/').status_code == 404
    assert c.get('/vocab/word/1/').status_code == 404
    assert c.get('/vocab/quiz/').status_code == 404
    assert c.get('/vocab/quiz/play/').status_code == 404


@pytest.mark.django_db
def test_vocabulary_word_list_stub_renders():
    c = Client()
    r = c.get('/vocabulary/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'Section 01 / Vocabulary' in html
    assert '<h1>Word</h1>' in html
    assert 'Coming soon.' in html


@pytest.mark.django_db
def test_vocabulary_home_renders():
    c = Client()
    r = c.get('/vocabulary/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'href="/vocabulary/category/"' in html
    assert 'href="/vocabulary/word/"' in html
    assert 'href="/vocabulary/quiz/"' in html
    assert 'data-i18n="vocabHome.title1"' in html


@pytest.mark.django_db
def test_mobile_page_switcher_present_on_vocabulary_landing_pages(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    for url in ('/vocabulary/category/', '/vocabulary/word/', '/vocabulary/quiz/', '/vocabulary/quiz/play/'):
        r = c.get(url)
        assert 'mobile-page-switcher' in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_absent_on_vocabulary_drill_in_pages(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    for url in ('/vocabulary/', f'/vocabulary/category/{category.slug}/', f'/vocabulary/word/{word.pk}/'):
        r = c.get(url)
        assert 'mobile-page-switcher' not in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_marks_active_chip():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="chip active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_vocabulary_category_list_shows_progress_bar_for_authenticated_user(cefr_a1, regular_user):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=category, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-pfill' in html
    assert 'cat-medal' not in html  # not 100% complete


@pytest.mark.django_db
def test_vocabulary_category_list_shows_medal_at_100_percent(cefr_a1, regular_user):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-medal' in html


@pytest.mark.django_db
def test_vocabulary_category_list_no_progress_bar_for_guest(cefr_a1):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-pfill' not in html
    assert 'cat-medal' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_renders_resolved_icon(cefr_a1):
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1, icon='📚',
    )
    c = Client()
    r = c.get('/vocabulary/category/')
    assert '#i-book' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_progress_filter_narrows_results(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/?progress=learned')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_progress_filter_not_started(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/?progress=not_started')
    body = r.content.decode()
    assert 'Food' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_chip_filter_bar_present(cefr_a1, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'data-browse-cefr="A1"' in html
    assert 'data-browse-status="completed"' in html
    assert 'data-browse-status="inProgress"' in html
    assert 'data-browse-status="notStarted"' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_renders_hover_reveal_cards(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(
        word='Cat', pos='noun', definition='A small pet.', example='I have a cat.',
        synonyms=['feline'], antonyms=['dog'], category=category, order=1, cefr_level=cefr_a1,
    )
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'word-card' in html
    assert 'A small pet.' in html
    assert 'feline' in html
    assert 'I have a cat.' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_shows_per_word_state(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    assert 'data-state="learned"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_detail_numbered_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(60):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'page-btn' in html
    assert '<a class="page-btn active"' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocabulary_category_detail_bulk_actions_present_for_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'cat-bulk-btn' in html
    assert 'catCompleteAllBtn' in html
    assert 'catResetAllBtn' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_bulk_actions_absent_for_guest(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    assert 'cat-bulk-btn' not in r.content.decode()


@pytest.mark.django_db
def test_bulk_mark_all_completed_round_trip_preserves_other_categories(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    other_word = Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(other_word.pk): 'little'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what vocabBulkSetCategory("learned") does: GET, set every
    # word ID in this category to "learned", POST the full map back.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    for w in (w1, w2):
        learn_map[str(w.pk)] = 'learned'
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {
        str(w1.pk): 'learned', str(w2.pk): 'learned', str(other_word.pk): 'little',
    }


@pytest.mark.django_db
def test_bulk_reset_all_deletes_keys_not_sets_none(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    other_word = Word.objects.create(word='Bread', definition='x', category=category, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned', str(other_word.pk): 'little'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what vocabBulkSetCategory("reset") does: delete every word
    # ID in this category from the map entirely.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    del learn_map[str(w1.pk)]
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert str(w1.pk) not in regular_user.learn_map
    assert regular_user.learn_map == {str(other_word.pk): 'little'}
