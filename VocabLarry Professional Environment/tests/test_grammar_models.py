import pytest
import importlib
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion, GrammarSection


@pytest.fixture(autouse=True)
def seed_grammar_sections(db):
    """
    Auto-seed GrammarSection objects from migration data.

    With pytest's --no-migrations flag, RunPython operations in migrations
    don't execute during test DB setup. This fixture seeds the sections
    before each test that touches GrammarSection, using the migration's
    SECTIONS data as the source of truth.
    """
    from vocab.models import GrammarSection

    # If sections already exist (shouldn't happen in test isolation), skip
    if GrammarSection.objects.exists():
        return

    # Import the migration module to get the authoritative SECTIONS data
    migration = importlib.import_module('vocab.migrations.0009_grammarsection')

    # Seed sections using the migration's data
    for order, (slug, name, icon, image_ids) in enumerate(migration.SECTIONS):
        GrammarSection.objects.create(
            slug=slug, name=name, icon=icon, order=order, image_ids=image_ids,
        )


@pytest.mark.django_db
def test_topic_str_and_ordering():
    t2 = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=1,
    )
    t1 = GrammarTopic.objects.create(
        slug='word-forms', title='Word Forms', tag='Word Building',
        cefr_label='A1–A2', blurb='Noun, verb, adjective, adverb.',
        stage='beginner', order=0,
    )
    assert str(t2) == 'Articles (a/an/the)'
    assert list(GrammarTopic.objects.all()) == [t1, t2]


@pytest.mark.django_db
def test_blocks_and_questions_cascade_and_order():
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='x', stage='beginner', order=0,
    )
    b2 = GrammarLessonBlock.objects.create(topic=t, type='rule', title='Form', body='<p>a + consonant sound</p>', order=1)
    b1 = GrammarLessonBlock.objects.create(topic=t, type='intro', body='<p>Articles come before nouns.</p>', order=0)
    q = GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She is ___ engineer.',
        options=['a', 'an', 'the', '(no article)'], answers=[1],
        why='"Engineer" starts with a vowel sound.', order=0,
    )
    assert list(t.blocks.all()) == [b1, b2]
    assert list(t.questions.all()) == [q]
    assert q.options[1] == 'an'
    assert q.answers == [1]
    t.delete()
    assert GrammarLessonBlock.objects.count() == 0
    assert GrammarQuestion.objects.count() == 0


@pytest.mark.django_db
def test_grammar_sections_seeded_by_migration():
    assert GrammarSection.objects.count() == 12
    tenses = GrammarSection.objects.get(slug='tenses')
    assert tenses.name == 'Tenses'
    assert tenses.icon == 'i-clock'
    assert tenses.order == 0
    assert tenses.image_ids == ['1501139083538-0139583c060f', '1456513080510-7bf3a84b82f8']
    idioms = GrammarSection.objects.get(slug='idioms')
    assert idioms.name == 'Idioms'
    assert idioms.order == 11


@pytest.mark.django_db
def test_grammar_sections_ordered_correctly():
    names = list(GrammarSection.objects.order_by('order').values_list('name', flat=True))
    assert names == [
        'Tenses', 'Questions & Reported Speech', 'Nouns, Pronouns & Determiners',
        'Adjectives & Adverbs', 'Word Forms & Prepositions', 'Verb Patterns & Modals',
        'Voice', 'Conditionals & Unreal Forms', 'Clauses', 'Emphasis & Sentence Focus',
        'Cohesion & Academic Style', 'Idioms',
    ]


@pytest.mark.django_db
def test_grammar_topic_can_be_assigned_a_section():
    section = GrammarSection.objects.get(slug='tenses')
    topic = GrammarTopic.objects.create(
        slug='present-simple-continuous', title='Present Simple & Continuous',
        tag='Tenses', cefr_label='A1', blurb='x', stage='beginner', order=0,
        section=section,
    )
    assert topic.section == section
    assert section.topics.first() == topic


@pytest.mark.django_db
def test_grammar_topic_section_survives_section_deletion():
    section = GrammarSection.objects.get(slug='tenses')
    topic = GrammarTopic.objects.create(
        slug='present-simple-continuous', title='Present Simple & Continuous',
        tag='Tenses', cefr_label='A1', blurb='x', stage='beginner', order=0,
        section=section,
    )
    section.delete()
    topic.refresh_from_db()
    assert topic.section is None
