from .models import Category, Word


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


def categories_started_count(started_ids):
    """Count of distinct categories containing any word in started_ids.

    Shared between config/views.py's home() and the sitewide footer's
    site_footer_stats context processor.
    """
    return Category.objects.filter(words__id__in=started_ids).distinct().count()
