import pytest
from django.test import Client

from vocab.models import CEFRLevel, GrammarTopic


@pytest.fixture(autouse=True)
def _setup_cefr_levels(db):
    """Automatically create CEFR levels for grammar tests."""
    if CEFRLevel.objects.exists():
        return
    cefr_data = [
        ('A1', 'Beginner', 1),
        ('A2', 'Elementary', 2),
        ('B1', 'Intermediate', 3),
        ('B2', 'Upper-Intermediate', 4),
        ('C1', 'Advanced', 5),
        ('C2+', 'Mastery', 6),
    ]
    for code, name, order in cefr_data:
        CEFRLevel.objects.create(code=code, name=name, order=order)


@pytest.fixture
def grammar_section(db):
    from vocab.models import GrammarSection
    return GrammarSection.objects.create(
        slug='nouns-pronouns-determiners', name='Nouns, Pronouns & Determiners',
        icon='i-type', order=2, image_ids=['1507842217343-583bb7270b66', '1524995997946-a1c2e315a42f'],
    )


@pytest.fixture
def topic_articles(db, grammar_section):
    return GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1', blurb='When to use a, an and the.',
        stage='beginner', order=0, section=grammar_section,
    )


@pytest.mark.django_db
def test_grammar_category_list_renders():
    c = Client()
    r = c.get('/grammar/category/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_lists_topics(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'Articles (a/an/the)' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_has_headline_bar(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert 'class="headline-bar"' in html
    assert 'data-grammar-stage="beginner"' in html
    assert 'data-grammar-stage="independent"' in html
    assert 'data-grammar-stage="expert"' in html


@pytest.mark.django_db
def test_grammar_category_list_has_accordion_section(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert 'class="section-block"' in html
    assert 'Nouns, Pronouns &amp; Determiners' in html
    assert 'section-block-pct' in html


@pytest.mark.django_db
def test_grammar_category_list_has_cefr_chips(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert 'data-grammar-cefr="A1"' in html
    assert 'data-grammar-cefr="C2+"' in html


@pytest.mark.django_db
def test_grammar_category_list_has_status_chips_for_authenticated_user(topic_articles, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert 'data-grammar-status="completed"' in html
    assert 'data-grammar-status="inProgress"' in html
    assert 'data-grammar-status="notStarted"' in html


@pytest.mark.django_db
def test_grammar_category_list_no_status_chips_for_guest(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'data-grammar-status' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_cefr_filter(topic_articles, grammar_section):
    GrammarTopic.objects.create(
        slug='future-forms', title='Future Forms', tag='Tenses',
        cefr_label='B2', blurb='will vs going to.', stage='beginner', order=1,
        section=grammar_section,
    )
    c = Client()
    r = c.get('/grammar/category/?cefr=A1')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Future Forms' not in html


@pytest.mark.django_db
def test_grammar_category_list_status_filter(topic_articles, regular_user):
    regular_user.grammar_map = {'articles': {'best': 95, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/?status=notStarted')
    html = r.content.decode()
    assert 'Articles (a/an/the)' not in html


@pytest.mark.django_db
def test_grammar_category_list_section_filter(topic_articles, grammar_section):
    from vocab.models import GrammarSection
    other_section = GrammarSection.objects.create(slug='voice', name='Voice', icon='i-megaphone', order=6)
    GrammarTopic.objects.create(
        slug='passive-voice', title='Passive Voice', tag='Voice',
        cefr_label='B1', blurb='x', stage='independent', order=1,
        section=other_section,
    )
    c = Client()
    r = c.get(f'/grammar/category/?section={grammar_section.slug}')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Passive Voice' not in html


@pytest.mark.django_db
def test_grammar_category_list_topics_have_theme_class(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'cat-card t-t' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_topics_yet_message():
    c = Client()
    r = c.get('/grammar/category/')
    assert 'No grammar topics yet.' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_topics_match_message(topic_articles):
    c = Client()
    r = c.get('/grammar/category/?q=zzz-no-match')
    assert 'No topics match these filters' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_search_filters_by_title(topic_articles, grammar_section):
    GrammarTopic.objects.create(
        slug='future-forms', title='Future Forms', tag='Tenses',
        cefr_label='A1+', blurb='will vs going to.', stage='beginner', order=1,
        section=grammar_section,
    )
    c = Client()
    r = c.get('/grammar/category/?q=Articles')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Future Forms' not in html


@pytest.mark.django_db
def test_grammar_category_list_stage_filter(topic_articles, grammar_section):
    GrammarTopic.objects.create(
        slug='conditionals', title='Conditionals', tag='Conditionals',
        cefr_label='B2', blurb='If clauses.', stage='expert', order=1,
        section=grammar_section,
    )
    c = Client()
    r = c.get('/grammar/category/?stage=expert')
    html = r.content.decode()
    assert 'Conditionals' in html
    assert 'Articles (a/an/the)' not in html


@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/"' in html
    assert 'nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_home_hero_grammar_cta_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'hero.grammar">Practice Grammar</a>' in html


from vocab.models import GrammarLessonBlock


@pytest.fixture
def topic_with_blocks(db):
    from vocab.models import GrammarSection
    section = GrammarSection.objects.get_or_create(
        slug='tenses', defaults=dict(
            name='Tenses', icon='i-clock', order=0,
            image_ids=['1501139083538-0139583c060f', '1456513080510-7bf3a84b82f8'],
        ),
    )[0]
    topic = GrammarTopic.objects.create(
        slug='present-simple-continuous', title='Present Simple & Continuous',
        tag='Tenses', cefr_label='A1', blurb='Know when to use which.',
        stage='beginner', order=0, section=section,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='intro',
        body='<p>The present simple describes <b>facts</b>.</p>', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='rule', title='Present Simple',
        body='<p>Form: base verb (+ <b>-s</b>).</p>', order=1,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='table', title='Quick map',
        data={'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}, order=2,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='examples',
        data={'items': [
            {'en': 'The sun rises in the east.', 'note': 'General fact.'},
            {'en': 'Prices are rising.'},
        ]}, order=3,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='tip', body='<p>Use present simple for charts.</p>', order=4,
    )
    return topic


@pytest.mark.django_db
def test_grammar_category_detail_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert r.status_code == 200
    assert 'Present Simple &amp; Continuous' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_category_detail_renders_intro_html_unescaped(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert '<b>facts</b>' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_renders_rule_title(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'Present Simple' in html
    assert '<b>-s</b>' in html


@pytest.mark.django_db
def test_grammar_category_detail_renders_table(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert '<th>Use</th>' in html
    assert '<td>Fact</td>' in html


@pytest.mark.django_db
def test_grammar_category_detail_renders_examples(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'The sun rises in the east.' in html
    assert 'General fact.' in html
    assert 'Prices are rising.' in html


@pytest.mark.django_db
def test_grammar_category_quiz_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-topic-slug="present-simple-continuous"' in html


@pytest.mark.django_db
def test_grammar_category_quiz_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/category/does-not-exist/quiz/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_category_detail_has_practice_link(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'href="/grammar/category/present-simple-continuous/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_quiz_authenticated_flag_set(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert 'data-authenticated="1"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_quiz_authenticated_flag_unset_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert 'data-authenticated="0"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_not_started_for_authenticated_user(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Not started yet' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_shows_best_score(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 60, 'done': False}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Best score: 60%' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_shows_mastered(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 90, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Mastered' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_no_status_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'Not started yet' not in html
    assert 'grammar-topic-detail-status' not in html


@pytest.mark.django_db
def test_grammar_category_list_badge_shows_mastered(topic_articles, regular_user):
    regular_user.grammar_map = {'articles': {'best': 95, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/')
    assert 'cat-medal' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_medal_for_untouched_topic(topic_articles, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/')
    assert 'cat-medal' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_medal_for_guest(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'cat-medal' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_quiz_play_renders():
    c = Client()
    r = c.get('/grammar/quiz/play/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-mode="test"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_renders():
    c = Client()
    r = c.get('/grammar/quiz/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'name="stage"' in html
    assert 'name="qtype"' in html
    assert 'name="count"' in html
    assert 'action="/grammar/quiz/play/"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_stage_options_match_model():
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<option value="beginner">Basic</option>' in html
    assert '<option value="independent">Intermediate</option>' in html
    assert '<option value="expert">Advanced</option>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_link_present():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/quiz/"' in html
    assert 'nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_old_grammar_urls_are_gone():
    c = Client()
    assert c.get('/grammar/').status_code == 200  # now the intro page, not 404
    assert c.get('/grammar/topic/articles/').status_code == 404
    assert c.get('/grammar/topic/articles/quiz/').status_code == 404
    assert c.get('/grammar/test/').status_code == 404
    assert c.get('/grammar/test/play/').status_code == 404


@pytest.mark.django_db
def test_grammar_word_stub_renders():
    c = Client()
    r = c.get('/grammar/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'Section 02 / Grammar' in html
    assert '<h1>Word</h1>' in html
    assert 'Coming soon.' in html


@pytest.mark.django_db
def test_grammar_home_renders():
    c = Client()
    r = c.get('/grammar/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'href="/grammar/category/"' in html
    assert 'href="/grammar/word/"' in html
    assert 'href="/grammar/quiz/"' in html
    assert 'data-i18n="grammarHome.title1"' in html


@pytest.mark.django_db
def test_mobile_page_switcher_present_on_grammar_landing_pages(topic_articles):
    c = Client()
    for url in ('/grammar/category/', '/grammar/word/', '/grammar/quiz/', '/grammar/quiz/play/'):
        r = c.get(url)
        assert 'mobile-page-switcher' in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_absent_on_grammar_drill_in_pages(topic_with_blocks):
    c = Client()
    for url in ('/grammar/', f'/grammar/category/{topic_with_blocks.slug}/', f'/grammar/category/{topic_with_blocks.slug}/quiz/'):
        r = c.get(url)
        assert 'mobile-page-switcher' not in r.content.decode(), url
