import pytest
from django.contrib.auth.models import AnonymousUser

from vocab.models import Category, Word
from vocab.services import categories_started_count, learned_word_stats


@pytest.mark.django_db
def test_learned_word_stats_for_authenticated_user_with_learned_words(regular_user):
    cat = Category.objects.create(slug='animals', name='Animals', order=1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat, order=2)
    Word.objects.create(word='Red', definition='x', category=cat, order=3)
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])

    learned_ids, total_words, words_learned = learned_word_stats(regular_user)

    assert learned_ids == [w1.pk]
    assert total_words == 3
    assert words_learned == 1


@pytest.mark.django_db
def test_learned_word_stats_for_anonymous_user():
    Word.objects.create(
        word='Cat', definition='x',
        category=Category.objects.create(slug='animals', name='Animals', order=1),
        order=1,
    )

    learned_ids, total_words, words_learned = learned_word_stats(AnonymousUser())

    assert learned_ids == []
    assert total_words == 1
    assert words_learned == 0


@pytest.mark.django_db
def test_categories_started_count_counts_distinct_categories_with_any_started_word():
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1)
    cat2 = Category.objects.create(slug='colors', name='Colors', order=2)
    cat3 = Category.objects.create(slug='food', name='Food', order=3)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    w3 = Word.objects.create(word='Red', definition='x', category=cat2, order=1)
    Word.objects.create(word='Bread', definition='x', category=cat3, order=1)

    # w1 and w2 both started (cat1 counts once), w3 started (cat2 counts),
    # cat3's word untouched (cat3 doesn't count).
    count = categories_started_count([w1.pk, w2.pk, w3.pk])

    assert count == 2


@pytest.mark.django_db
def test_categories_started_count_zero_for_no_started_words():
    Category.objects.create(slug='animals', name='Animals', order=1)
    assert categories_started_count([]) == 0
