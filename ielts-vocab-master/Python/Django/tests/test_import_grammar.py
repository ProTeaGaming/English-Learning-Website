import json
import pytest
from django.core.management import call_command
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion

TOPIC = {
    'slug': 'articles', 'stage': 'beginner', 'title': 'Articles (a/an/the)',
    'tag': 'Determiners', 'cefr': 'A1–A2', 'blurb': 'When to use a, an and the.',
    'lesson': [
        {'type': 'intro', 'body': '<p>Articles come before nouns.</p>'},
        {'type': 'table', 'title': 'Forms', 'data': {'head': ['Article'], 'rows': [['a']]}},
    ],
    'quiz': [
        {'qtype': 'mcq', 'prompt': 'She is ___ engineer.',
         'options': ['a', 'an', 'the', '(no article)'], 'answers': [1],
         'why': '"Engineer" starts with a vowel sound.'},
        {'qtype': 'gap', 'prompt': 'I saw ___ moon last night.', 'answers': ['the'],
         'why': 'There is only one moon — unique things take "the".'},
    ],
}


@pytest.fixture
def seed_file(tmp_path):
    path = tmp_path / 'grammar.json'
    path.write_text(json.dumps([TOPIC]), encoding='utf-8')
    return path


@pytest.mark.django_db
def test_import_creates_topic_blocks_questions(seed_file):
    call_command('import_grammar', file=str(seed_file))
    t = GrammarTopic.objects.get(slug='articles')
    assert t.stage == 'beginner'
    assert t.cefr_label == 'A1–A2'
    assert t.blocks.count() == 2
    assert t.questions.count() == 2
    assert t.questions.last().answers == ['the']


@pytest.mark.django_db
def test_import_is_idempotent_and_replaces_children(seed_file, tmp_path):
    call_command('import_grammar', file=str(seed_file))
    call_command('import_grammar', file=str(seed_file))
    assert GrammarTopic.objects.count() == 1
    assert GrammarLessonBlock.objects.count() == 2
    assert GrammarQuestion.objects.count() == 2

    changed = dict(TOPIC, title='Articles!', quiz=TOPIC['quiz'][:1])
    path2 = tmp_path / 'grammar2.json'
    path2.write_text(json.dumps([changed]), encoding='utf-8')
    call_command('import_grammar', file=str(path2))
    t = GrammarTopic.objects.get(slug='articles')
    assert t.title == 'Articles!'
    assert t.questions.count() == 1
