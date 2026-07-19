import pytest


@pytest.mark.django_db
def test_home_page_renders():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
    assert 'text/html' in r['Content-Type']


@pytest.mark.django_db
def test_home_page_has_nav_and_hero():
    from django.test import Client
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body
    assert 'hero' in body


@pytest.mark.django_db
def test_login_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/login/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body


@pytest.mark.django_db
def test_signup_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/signup/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_google_login_redirects_to_google():
    from django.test import Client
    c = Client()
    c.get('/accounts/google/login/')  # loads the CSRF-protected confirm page
    r = c.post('/accounts/google/login/')
    assert r.status_code == 302
    assert 'accounts.google.com' in r['Location']


@pytest.mark.django_db
def test_logout_confirm_page_uses_site_layout(regular_user):
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/accounts/logout/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_password_reset_request_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/password/reset/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_email_verification_sent_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/confirm-email/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_base_includes_fonts_and_icon_sprite():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'fonts.googleapis.com' in html
    assert 'Fraunces' in html
    assert 'id="i-mark"' in html


@pytest.mark.django_db
def test_nav_theme_and_lang_toggles_are_icon_only():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-theme-toggle' in html
    assert 'data-lang-toggle' in html
    assert '#i-moon' in html
    assert '#i-globe' in html


@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocab_browse():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="tab" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_quiz_tab_active_on_vocab_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
    assert '<a class="tab" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_browse():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/" data-i18n="nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_nav_grammar_test_tab_active_on_grammar_test_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/test/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/test/" data-i18n="nav.grammarTest">Grammar Test</a>' in html


@pytest.mark.django_db
def test_home_stats_zero_for_guest():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<div class="home-stat-val">0</div>' in html
    assert '<div class="home-stat-val">0%</div>' in html


@pytest.mark.django_db
def test_home_stats_computed_for_authenticated_user(regular_user):
    from django.test import Client
    from vocab.models import Category, Word

    cat1 = Category.objects.create(slug='animals', name='Animals', order=1)
    cat2 = Category.objects.create(slug='colors', name='Colors', order=2)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    w3 = Word.objects.create(word='Red', definition='x', category=cat2, order=1)

    # w1 fully learned, w2 only "little" (counts toward categories-started
    # but NOT words-learned), w3 untouched.
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])

    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()

    from vocab.models import Word as WordModel
    total = WordModel.objects.count()
    expected_pct = round(1 / total * 100)

    assert '<div class="home-stat-val">1</div>' in html
    assert f'<div class="home-stat-val">{expected_pct}%</div>' in html
    # Both cat1 (via w1 AND w2) and cat2 (untouched) exist, but only cat1
    # has any learn_map entry — categories_started must be 1, not 2.
    assert '<div class="home-stat-val">2</div>' not in html


@pytest.mark.django_db
def test_home_badge_and_progress_heading_render():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'home.badge">IELTS Preparation' in html
    assert 'home.yourProgress">Your Progress' in html
