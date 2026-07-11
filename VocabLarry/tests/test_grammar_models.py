import pytest
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


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
