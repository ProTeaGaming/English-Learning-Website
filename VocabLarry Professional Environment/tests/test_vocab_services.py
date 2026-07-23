import pytest
from django.contrib.auth.models import AnonymousUser

from vocab.models import Category, Word
from vocab.services import learned_word_stats


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
