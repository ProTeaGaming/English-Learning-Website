from .models import Word


def learned_word_stats(user):
    """Returns (learned_ids, total_words, words_learned) for a user's learn_map.

    Shared between config/views.py's home() (which also needs
    categories_started/pct_complete) and the nav's user_progress_stats
    context processor (which only needs the raw counts) so the
    learn_map-to-counts computation isn't duplicated.
    """
    learn_map = user.learn_map if user.is_authenticated else {}
    learned_ids = [int(k) for k, v in learn_map.items() if v == 'learned']
    total_words = Word.objects.count()
    words_learned = len(learned_ids)
    return learned_ids, total_words, words_learned
