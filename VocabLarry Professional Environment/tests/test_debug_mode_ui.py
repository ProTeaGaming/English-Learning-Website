import pytest


@pytest.mark.django_db
def test_debug_toggle_visible_for_staff(client, staff_user):
    client.force_login(staff_user)
    r = client.get('/')
    assert r.status_code == 200
    assert b'id="debugToggle"' in r.content


@pytest.mark.django_db
def test_debug_toggle_visible_for_admin(client, admin_user):
    client.force_login(admin_user)
    r = client.get('/')
    assert b'id="debugToggle"' in r.content


@pytest.mark.django_db
def test_debug_toggle_absent_for_regular_user(client, regular_user):
    client.force_login(regular_user)
    r = client.get('/')
    assert b'id="debugToggle"' not in r.content


@pytest.mark.django_db
def test_debug_toggle_absent_for_anonymous(client):
    r = client.get('/')
    assert b'id="debugToggle"' not in r.content


from vocab.models import CEFRLevel, Color, Category, Word, VocabSection


@pytest.fixture
def word_ui_fixture(db):
    cefr = CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)
    color = Color.objects.create(name='Violet', bg_hex='#7c3aed', text_hex='#ffffff')
    section = VocabSection.objects.create(slug='travel-section', name='Travel', tier='intermediate', order=0)
    category = Category.objects.create(
        slug='travel', name='Travel', icon='plane', cefr_level=cefr, color=color, section=section, order=0,
    )
    word = Word.objects.create(
        word='journey', pos='noun', definition='a trip', example='A long journey.',
        gap='A long ___.', category=category, cefr_level=cefr, order=0,
        synonyms=['trip'], antonyms=[],
    )
    return category, word


@pytest.mark.django_db
def test_word_dbg_ctl_visible_for_staff_on_category_word_list(client, staff_user, word_ui_fixture):
    category, word = word_ui_fixture
    client.force_login(staff_user)
    r = client.get(f'/vocabulary/category/{category.slug}/')
    assert b'data-dbg-word' in r.content
    assert f'data-id="{word.pk}"'.encode() in r.content


@pytest.mark.django_db
def test_word_dbg_ctl_absent_for_regular_user_on_category_word_list(client, regular_user, word_ui_fixture):
    category, word = word_ui_fixture
    client.force_login(regular_user)
    r = client.get(f'/vocabulary/category/{category.slug}/')
    assert b'data-dbg-word' not in r.content


@pytest.mark.django_db
def test_word_add_button_visible_for_staff_on_word_list(client, staff_user, word_ui_fixture):
    client.force_login(staff_user)
    r = client.get('/vocabulary/word/')
    assert b'dbgAddWordBtn' in r.content


@pytest.mark.django_db
def test_word_add_button_absent_for_regular_user_on_word_list(client, regular_user, word_ui_fixture):
    client.force_login(regular_user)
    r = client.get('/vocabulary/word/')
    assert b'dbgAddWordBtn' not in r.content


@pytest.mark.django_db
def test_word_dbg_ctl_visible_for_staff_on_word_detail(client, staff_user, word_ui_fixture):
    category, word = word_ui_fixture
    client.force_login(staff_user)
    r = client.get(f'/vocabulary/word/{word.pk}/')
    assert b'data-dbg-word' in r.content


@pytest.mark.django_db
def test_category_dbg_ctl_visible_for_staff_on_browse(client, staff_user, word_ui_fixture):
    category, word = word_ui_fixture
    client.force_login(staff_user)
    r = client.get('/vocabulary/category/')
    assert b'data-dbg-category' in r.content
    assert f'data-id="{category.pk}"'.encode() in r.content
    assert b'data-dbg-add-category' in r.content


@pytest.mark.django_db
def test_category_dbg_ctl_absent_for_regular_user_on_browse(client, regular_user, word_ui_fixture):
    client.force_login(regular_user)
    r = client.get('/vocabulary/category/')
    assert b'data-dbg-category' not in r.content
    assert b'data-dbg-add-category' not in r.content
