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


from vocab.models import GrammarTopic, GrammarSection


@pytest.fixture
def topic_ui_fixture(db):
    section = GrammarSection.objects.create(
        slug='tenses-section', name='Tenses', icon='i-tenses', order=0
    )
    return GrammarTopic.objects.create(
        slug='present-perfect', title='Present Perfect', tag='Tenses',
        cefr_label='B1', blurb='Using the present perfect.', stage='independent', order=0,
        section=section,
    )


@pytest.mark.django_db
def test_topic_dbg_ctl_visible_for_staff_on_grammar_browse(client, staff_user, topic_ui_fixture):
    client.force_login(staff_user)
    r = client.get('/grammar/category/')
    assert b'data-dbg-topic' in r.content
    assert f'data-id="{topic_ui_fixture.pk}"'.encode() in r.content
    assert b'data-dbg-add-topic' in r.content


@pytest.mark.django_db
def test_topic_dbg_ctl_absent_for_regular_user_on_grammar_browse(client, regular_user, topic_ui_fixture):
    client.force_login(regular_user)
    r = client.get('/grammar/category/')
    assert b'data-dbg-topic' not in r.content


from django.template import Template, Context


def test_json_attr_filter_escapes_for_html_attribute():
    tmpl = Template('{% load vocab_extras %}<div data-x="{{ value|json_attr }}"></div>')
    rendered = tmpl.render(Context({'value': {'head': ['A', 'B'], 'rows': [['1', '"2"']]}}))
    assert '&quot;' in rendered
    assert rendered.count('"') == 2  # only the attribute's own opening/closing quotes stay literal


from vocab.models import GrammarLessonBlock


@pytest.fixture
def block_ui_fixture(db, topic_ui_fixture):
    return GrammarLessonBlock.objects.create(
        topic=topic_ui_fixture, type='intro', title='Intro',
        body='<p>We use the present perfect for...</p>', data={}, order=0,
    )


@pytest.mark.django_db
def test_block_dbg_ctl_visible_for_staff_on_topic_detail(client, staff_user, block_ui_fixture):
    client.force_login(staff_user)
    r = client.get(f'/grammar/category/{block_ui_fixture.topic.slug}/')
    assert b'data-dbg-block' in r.content
    assert f'data-id="{block_ui_fixture.pk}"'.encode() in r.content
    assert b'data-dbg-add-block' in r.content


@pytest.mark.django_db
def test_block_dbg_ctl_absent_for_regular_user_on_topic_detail(client, regular_user, block_ui_fixture):
    client.force_login(regular_user)
    r = client.get(f'/grammar/category/{block_ui_fixture.topic.slug}/')
    assert b'data-dbg-block' not in r.content
