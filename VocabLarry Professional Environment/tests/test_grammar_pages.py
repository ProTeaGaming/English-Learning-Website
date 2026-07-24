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
def test_grammar_category_list_groupby_contiguity_with_duplicate_section_orders():
    """Regression test: itertools.groupby requires input contiguous by grouping key.
    This test verifies that even if two GrammarSection rows have the SAME order value,
    their topics still render in separate, correctly-grouped section blocks (not split/interleaved).
    This tests the fix: order_by('section__order', 'section_id', ...) breaks ties on section_id
    to ensure groupby's contiguity precondition is always satisfied.
    """
    from vocab.models import GrammarSection

    # Create two sections with the SAME order value (both 0)
    section1 = GrammarSection.objects.create(
        slug='section-one', name='Section One', icon='i-test', order=0,
    )
    section2 = GrammarSection.objects.create(
        slug='section-two', name='Section Two', icon='i-test', order=0,
    )

    # Create multiple topics in each section to increase chance of interleaving
    # if the ordering doesn't guarantee contiguity by section_id
    for i in range(3):
        GrammarTopic.objects.create(
            slug=f'topic-one-{i}', title=f'Topic One-{i}', tag='Test',
            cefr_label='A1', blurb='Test topic.',
            stage='beginner', order=i, section=section1,
        )
    for i in range(3):
        GrammarTopic.objects.create(
            slug=f'topic-two-{i}', title=f'Topic Two-{i}', tag='Test',
            cefr_label='A1', blurb='Test topic.',
            stage='beginner', order=i, section=section2,
        )

    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()

    # All topics should be present
    for i in range(3):
        assert f'Topic One-{i}' in html
        assert f'Topic Two-{i}' in html

    # Both sections should be present (rendered as separate section blocks)
    assert 'Section One' in html
    assert 'Section Two' in html

    # Critical assertion: count section blocks — should be exactly 2 (one for each section)
    # Without the section_id fix, if topics interleave by section_id in the query results,
    # groupby would create MORE than 2 groups (e.g. 4 or 6), splitting what should be
    # one section's block into multiple blocks
    section_block_count = html.count('class="section-block"')
    assert section_block_count == 2, f"Expected exactly 2 section blocks, got {section_block_count}. Topics may have interleaved due to missing section_id in order_by."


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
def test_home_quick_test_cta_present():
    # Practice Grammar (a direct shortcut) was replaced by Quick Test (opens
    # the mode picker) per FIXES-NEEDED item 20 — this test replaces the
    # older direct-link version.
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-i18n="home.quickTest">Quick Test' in html


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


@pytest.fixture
def gramword_topics(db):
    from vocab.models import GrammarLessonBlock

    verbs_topic = GrammarTopic.objects.create(
        slug='irregular-verbs', title='Irregular Verbs',
        tag='Verbs', cefr_label='A2', blurb='Common irregular verb forms.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=verbs_topic, type='table', title='Irregular Verbs',
        data={
            'head': ['Base (V1)', 'Past simple (V2)', 'Past participle (V3)'],
            'rows': [
                ['cut', 'cut', 'cut'],
                ['buy', 'bought', 'bought'],
                ['come', 'came', 'come'],
                ['go', 'went', 'gone'],
            ],
        },
        order=0,
    )

    comparisons_topic = GrammarTopic.objects.create(
        slug='comparison-structures', title='Comparison Structures',
        tag='Adjectives', cefr_label='A2', blurb='Irregular comparative/superlative forms.',
        stage='beginner', order=1,
    )
    GrammarLessonBlock.objects.create(
        topic=comparisons_topic, type='table', title='Irregular Comparisons',
        data={
            'head': ['Base', 'Comparative', 'Superlative'],
            'rows': [
                ['good / well', 'better', 'best'],
                ['bad / badly', 'worse', 'worst'],
                ['far', 'further / farther', 'furthest / farthest'],
            ],
        },
        order=0,
    )
    return {'verbs': verbs_topic, 'comparisons': comparisons_topic}


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
    assert 'class="gram-stage' in html
    assert 'Rule 01' in html


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
def test_grammar_category_detail_has_themed_header(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'class="cat-view-title-row"' in html
    assert 'cat-view-icon t-t' in html
    assert 'i-clock' in html


@pytest.mark.django_db
def test_grammar_category_detail_rule_card_has_image(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'gram-stage-panel' in html
    assert 'images.unsplash.com/photo-' in html


@pytest.mark.django_db
def test_grammar_category_detail_loads_topic_js(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'grammar-topic.js' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_has_back_link(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'class="back-btn"' in html
    assert 'href="/grammar/category/"' in html


@pytest.mark.django_db
def test_grammar_category_detail_gram_block_types_render(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'gram-intro' in html
    assert 'gram-table-wrap' in html
    assert 'gram-examples' in html


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
    from vocab.models import GrammarQuestion
    GrammarQuestion.objects.create(
        topic=topic_with_blocks, qtype='mcq', prompt='Test question?',
        options=['a', 'b'], answers=[0], why='because', order=0,
    )
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'href="/grammar/category/present-simple-continuous/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_no_practice_link_when_no_questions(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'href="/grammar/category/present-simple-continuous/quiz/"' not in r.content.decode()


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
def test_grammar_topic_quiz_uses_q_card_classes(topic_with_blocks):
    from vocab.models import GrammarQuestion
    GrammarQuestion.objects.create(
        topic=topic_with_blocks, qtype='mcq', prompt='Test?',
        options=['a', 'b'], answers=[0], why='because', order=0,
    )
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert 'grammar-quiz.js' in r.content.decode()


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
    assert 'cat-view-name' in r.content.decode()


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
    assert 'id="gramtestModes"' in html
    assert 'id="gramtestCounts"' in html
    assert 'id="gramtestStart"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_has_cefr_chips():
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert 'data-gramtest-cefr="A1"' in html
    assert 'data-gramtest-cefr="C2+"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_has_no_stage_filter():
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert 'name="stage"' not in html


@pytest.mark.django_db
def test_grammar_quiz_setup_has_topic_picker_containers():
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert 'id="gramtestSectionChips"' in html
    assert 'id="gramtestTopicChips"' in html
    assert 'id="gramtestPoolCount"' in html
    assert 'id="gramtestSearch"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_loads_quiz_js():
    c = Client()
    r = c.get('/grammar/quiz/')
    assert 'grammar-quiz.js' in r.content.decode()


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
def test_mobile_page_switcher_present_on_grammar_landing_pages(topic_articles, gramword_topics):
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


def test_grammar_quiz_js_has_no_stale_urls():
    import pathlib
    js_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'js' / 'grammar-quiz.js'
    content = js_path.read_text(encoding='utf-8')
    assert '/grammar/topic/' not in content
    assert '/grammar/test/' not in content
    assert content.count('/grammar/category/') >= 1
    assert content.count('/grammar/quiz/') >= 1


@pytest.mark.django_db
def test_grammar_quiz_play_has_back_btn_not_breadcrumb():
    c = Client()
    r = c.get('/grammar/quiz/play/')
    html = r.content.decode()
    assert 'class="back-btn"' in html
    assert 'grammar-breadcrumb' not in html


@pytest.mark.django_db
def test_grammar_topic_quiz_has_back_btn_not_breadcrumb(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    html = r.content.decode()
    assert 'class="back-btn"' in html
    assert 'grammar-breadcrumb' not in html


def test_grammar_quiz_js_normalizes_smart_quotes():
    import pathlib
    js_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'js' / 'grammar-quiz.js'
    content = js_path.read_text(encoding='utf-8')
    # Check for U+2019 (right single quotation mark) and U+2018 (left single quotation mark)
    right_quote = chr(0x2019)  # '''
    left_quote = chr(0x2018)   # '''
    assert right_quote in content and left_quote in content, (
        "grammarNorm's smart-quote character class must contain the actual "
        "curly-quote Unicode characters (U+2019, U+2018), not their ASCII "
        "apostrophe look-alikes, or typed answers with autocorrected quotes "
        "will be silently marked wrong"
    )


def test_classify_verb_pattern_all_four_branches():
    from config.views_grammar import _classify_verb_pattern
    assert _classify_verb_pattern('cut', 'cut', 'cut') == 'AAA'
    assert _classify_verb_pattern('buy', 'bought', 'bought') == 'ABB'
    assert _classify_verb_pattern('come', 'came', 'come') == 'ABA'
    assert _classify_verb_pattern('go', 'went', 'gone') == 'ABC'


@pytest.mark.django_db
def test_grammar_word_default_set_is_verbs(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert '>cut<' in html
    assert 'class="headline-btn active" href="?set=verbs"' in html


@pytest.mark.django_db
def test_grammar_word_verbs_table_has_pattern_column(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/')
    html = r.content.decode()
    assert 'class="pattern-badge AAA">AAA</span>' in html
    assert 'class="pattern-badge ABB">ABB</span>' in html
    assert 'class="pattern-badge ABA">ABA</span>' in html
    assert 'class="pattern-badge ABC">ABC</span>' in html


@pytest.mark.django_db
def test_grammar_word_comparisons_set(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'set': 'comparisons'})
    html = r.content.decode()
    assert '>better<' in html
    assert '>worse<' in html
    assert 'pattern-badge' not in html
    assert 'class="filter-label">Pattern</span>' not in html


@pytest.mark.django_db
def test_grammar_word_search_matches_any_column(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'q': 'went'})
    html = r.content.decode()
    assert '>go<' in html and '>cut<' not in html and '>buy<' not in html


@pytest.mark.django_db
def test_grammar_word_pattern_filter(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'pattern': 'ABB'})
    html = r.content.decode()
    assert '>buy<' in html
    assert '>cut<' not in html and '>come<' not in html and '>go<' not in html


@pytest.mark.django_db
def test_grammar_word_pattern_filter_ignored_on_comparisons(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'set': 'comparisons', 'pattern': 'AAA'})
    html = r.content.decode()
    assert '>better<' in html
    assert '>worse<' in html


@pytest.mark.django_db
def test_grammar_word_clear_filters_link_present(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'q': 'cut', 'pattern': 'AAA'})
    html = r.content.decode()
    assert 'class="clear-btn" href="/grammar/word/"' in html


@pytest.mark.django_db
def test_grammar_word_invalid_pattern_filter_shows_no_active_chip(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'set': 'verbs', 'pattern': 'XYZ'})
    html = r.content.decode()
    assert 'class="chip active" href="?set=verbs"' in html
    assert 'class="chip active" href="?set=verbs&pattern=AAA"' not in html
    assert 'class="chip active" href="?set=verbs&pattern=ABA"' not in html
    assert 'class="chip active" href="?set=verbs&pattern=ABB"' not in html
    assert 'class="chip active" href="?set=verbs&pattern=ABC"' not in html
