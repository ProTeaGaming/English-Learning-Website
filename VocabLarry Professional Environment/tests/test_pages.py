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
def test_nav_vocabulary_tab_active_on_vocabulary_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    # The li wrapper's "active" class is what nav.js reads (via
    # .closest(".nav-group")) to decide toggle-dropdown vs navigate —
    # check it explicitly, not just the inner <a>'s class.
    assert '<li class="nav-group active" data-section="vocabulary">' in html
    assert '<a class="tab active" href="/vocabulary/" data-nav-toggle data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="nav-dropdown-item active" href="/vocabulary/category/" data-i18n="nav.category">Category</a>' in html


@pytest.mark.django_db
def test_nav_quiz_dropdown_item_active_on_vocabulary_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/" data-nav-toggle data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="nav-dropdown-item active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/" data-nav-toggle data-i18n="nav.grammar">Grammar</a>' in html
    assert '<a class="nav-dropdown-item active" href="/grammar/category/" data-i18n="nav.category">Category</a>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_dropdown_item_active_on_grammar_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<a class="nav-dropdown-item active" href="/grammar/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_reading_writing_listening_speaking_tabs_present():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<a class="tab" href="/reading/" data-i18n="nav.reading">Reading</a>' in html
    assert '<a class="tab" href="/writing/" data-i18n="nav.writing">Writing</a>' in html
    assert '<a class="tab" href="/listening/" data-i18n="nav.listening">Listening</a>' in html
    assert '<a class="tab" href="/speaking/" data-i18n="nav.speaking">Speaking</a>' in html


@pytest.mark.django_db
def test_mobile_nav_menu_lists_all_7_sections():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'id="mobileNavMenu"' in html
    for href in ('/', '/vocabulary/', '/grammar/', '/reading/', '/writing/', '/listening/', '/speaking/'):
        assert f'<a class="mobile-nav-menu-item" href="{href}"' in html


@pytest.mark.django_db
def test_home_hero_ctas_bypass_intro_pages_and_link_to_category():
    # Regression guard: the nav's Vocabulary/Grammar links now point at the
    # intro pages (asserted above), but Home's own hero CTAs must keep
    # pointing directly at Category — this is the one deliberate exception
    # to "everything links to the intro page now".
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<a class="btn btn-primary" href="/vocabulary/category/" data-i18n="hero.start">Start Learning</a>' in html
    assert '<a class="home-btn-outline" href="/grammar/category/" data-i18n="hero.grammar">Practice Grammar</a>' in html


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


@pytest.mark.django_db
def test_reading_writing_listening_speaking_stub_pages_render():
    from django.test import Client
    c = Client()
    pages = [
        ('/reading/', 'Section 03 / Reading', 'Reading'),
        ('/writing/', 'Section 04 / Writing', 'Writing'),
        ('/listening/', 'Section 05 / Listening', 'Listening'),
        ('/speaking/', 'Section 06 / Speaking', 'Speaking'),
    ]
    for url, eyebrow, title in pages:
        r = c.get(url)
        assert r.status_code == 200, url
        html = r.content.decode()
        assert eyebrow in html, url
        assert f'<h1>{title}</h1>' in html, url
        assert 'Coming soon.' in html, url


@pytest.mark.django_db
def test_nav_has_single_signin_button_when_logged_out():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<button type="button" class="btn btn-primary" id="signInBtn" data-i18n="nav.signIn">Sign In</button>' in html


@pytest.mark.django_db
def test_nav_no_longer_links_directly_to_classic_login_signup():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/accounts/login/"' not in html
    assert 'href="/accounts/signup/"' not in html


@pytest.mark.django_db
def test_auth_modal_renders_on_home_page():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    for element_id in (
        'authOverlay', 'authClose', 'authTitle', 'authForm',
        'authEmailGroup', 'authEmail', 'authPasswordGroup', 'authPassword',
        'authPwToggle', 'authRememberMe', 'authForgotWrap', 'authForgotLink',
        'authSignupExtra', 'authName', 'authUsername', 'authPicture',
        'authMfaGroup', 'authMfaCode', 'authResetGroup', 'authResetPassword',
        'authResetPassword2', 'authSubmitBtn', 'authSwitch', 'authError', 'authInfo',
    ):
        assert f'id="{element_id}"' in html, element_id


@pytest.mark.django_db
def test_auth_modal_has_exactly_4_social_providers_no_github():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-provider="google"' in html
    assert 'data-provider="facebook"' in html
    assert 'data-provider="microsoft"' in html
    assert 'data-provider="apple"' in html
    assert 'data-provider="github"' not in html


@pytest.mark.django_db
def test_eye_icon_symbols_present_for_password_toggle():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'id="i-eye"' in html
    assert 'id="i-eye-off"' in html


@pytest.mark.django_db
def test_auth_modal_js_included_on_every_page():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert 'auth-modal.js' in r.content.decode()


@pytest.mark.django_db
def test_lang_dropdown_has_11_languages_two_active_nine_soon():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-lang-menu' in html
    assert '<button class="mode-picker-row" data-lang="en" type="button">' in html
    assert '<button class="mode-picker-row" data-lang="vi" type="button">' in html
    # Production's own current lang-menu markup (vocablarry.html) has 10
    # disabled rows, not the 9 FIXES-NEEDED.md's summary text describes —
    # trust the direct source-of-truth comparison per this file's ground
    # rule, not the checklist's own (here, slightly stale) prose.
    assert html.count('mode-picker-row-disabled') == 10
    for name in ('中文', '日本語', '한국어', 'العربية', 'Français', 'Nederlands', 'Deutsch', 'Español', 'Português', 'Русский'):
        assert name in html, name


@pytest.mark.django_db
def test_home_explore_sections_cards_have_live_and_soon_badges():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'home.exploreSections">Explore Sections' in html
    assert html.count('home-sec-status live') == 2
    assert html.count('home-sec-status soon') == 4
    assert '<a class="home-sec" href="/vocabulary/category/">' in html
    assert '<a class="home-sec" href="/grammar/category/">' in html
    assert '<a class="home-sec" href="/reading/">' in html
    assert '<a class="home-sec" href="/writing/">' in html
    assert '<a class="home-sec" href="/listening/">' in html
    assert '<a class="home-sec" href="/speaking/">' in html


@pytest.mark.django_db
def test_home_cefr_breakdown_renders_all_6_levels():
    from django.test import Client
    from vocab.models import CEFRLevel

    for i, code in enumerate(('A1', 'A2', 'B1', 'B2', 'C1', 'C2'), start=1):
        CEFRLevel.objects.create(code=code, name=code, order=i)

    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'home.cefrBreakdown">CEFR Breakdown' in html
    for code in ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'):
        assert f'<div class="home-cefr-badge">{code}</div>' in html, code
    assert html.count('home-cefr-row') >= 6


@pytest.mark.django_db
def test_home_cefr_breakdown_pct_reflects_learned_words(regular_user):
    from django.test import Client
    from vocab.models import Category, CEFRLevel, Word

    a1 = CEFRLevel.objects.create(code='A1', name='Beginner', order=1)
    cat = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat, cefr_level=a1, order=1)
    Word.objects.create(word='Dog', definition='x', category=cat, cefr_level=a1, order=2)

    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])

    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()
    assert '<div class="home-cefr-badge">A1</div>' in html
    assert 'width:50%' in html


@pytest.mark.django_db
def test_user_chip_and_stats_render_for_authenticated_user(regular_user):
    from django.test import Client
    from vocab.models import Category, Word

    cat = Category.objects.create(slug='animals', name='Animals', order=1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat, order=2)
    regular_user.name = 'Regular Tester'
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save()

    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()

    assert 'data-user-chip' in html
    assert '<span class="avatar-initials">R</span>' in html
    assert '<span class="user-name">Regular Tester</span>' in html
    assert '<span class="user-menu-username">@regularuser</span>' in html
    assert '<span class="user-menu-email">user@example.com</span>' in html
    assert '<b>1</b> / <b>2</b>' in html
    assert '?progress=little' in html
    assert '<b>1</b> <span data-i18n="header.toReview">to review</span>' in html
    assert 'data-open-edit-profile' in html
    assert 'data-open-reset-progress' in html
    assert 'data-open-delete-account' in html


@pytest.mark.django_db
def test_review_link_absent_when_no_little_bit_words(regular_user):
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()
    assert 'review-link' not in html


@pytest.mark.django_db
def test_user_chip_falls_back_to_email_when_name_blank(regular_user):
    from django.test import Client
    assert regular_user.name == ''
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()
    assert '<span class="avatar-initials">U</span>' in html
    assert '<span class="user-name">user@example.com</span>' in html


@pytest.mark.django_db
def test_user_chip_shows_uploaded_picture_instead_of_initials(regular_user, tmp_path, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.test import Client

    settings.MEDIA_ROOT = tmp_path
    regular_user.picture = SimpleUploadedFile('avatar.png', b'fake-image-bytes', content_type='image/png')
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()
    assert f'<img src="{regular_user.picture.url}" alt="">' in html
    assert 'avatar-initials' not in html


@pytest.mark.django_db
def test_anonymous_user_sees_no_stats_or_user_chip():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-user-chip' not in html
    assert 'class="stats"' not in html


@pytest.mark.django_db
def test_account_modals_render_for_authenticated_user(regular_user):
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/')
    html = r.content.decode()
    for element_id in (
        'profileOverlay', 'profileClose', 'profileError', 'profileAvatarPreviewWrap',
        'profileAvatarPreview', 'profilePicture', 'profileName', 'profileUsername',
        'profileForm', 'profileSubmitBtn', 'profileConnectionsError', 'profileConnectionsList',
        'deleteOverlay', 'deleteClose', 'deleteError', 'deleteWarning',
        'deletePasswordGroup', 'deletePassword', 'deleteForm', 'deleteSubmitBtn',
        'resetOverlay', 'resetClose', 'resetError', 'resetConfirmBtn', 'resetCancelBtn',
    ):
        assert f'id="{element_id}"' in html, element_id


@pytest.mark.django_db
def test_account_modals_absent_for_anonymous_user():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'id="profileOverlay"' not in html
    assert 'id="deleteOverlay"' not in html
    assert 'id="resetOverlay"' not in html
