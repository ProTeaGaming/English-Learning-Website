from vocab.models import Category
from vocab.services import categories_started_count, learned_word_stats

_VOCABULARY_PREFIX = 'vocabulary_'
_GRAMMAR_PREFIX = 'grammar_'
_FLAT_SECTIONS = {'home', 'reading', 'writing', 'listening', 'speaking'}


def nav_active_section(request):
    """Which top-level nav section the current page belongs to.

    Derived from the URL name's prefix rather than hand-listed per view,
    so adding a new vocabulary_*/grammar_* page never requires touching
    this function or nav.html's active-state logic.
    """
    match = request.resolver_match
    url_name = match.url_name if match else None
    if url_name is None:
        section = None
    elif url_name in _FLAT_SECTIONS:
        section = url_name
    elif url_name.startswith(_VOCABULARY_PREFIX):
        section = 'vocabulary'
    elif url_name.startswith(_GRAMMAR_PREFIX):
        section = 'grammar'
    else:
        section = None
    return {'nav_active_section': section}


def user_progress_stats(request):
    """Live 'Learned: X / Y' + 'N to review' stats shown in the nav —
    mirrors production's client-side saveLearned()/updateHome() counters
    (vocablarry.html), computed server-side instead since VLPE is
    server-rendered.
    """
    if not request.user.is_authenticated:
        return {}
    _, total_words, words_learned = learned_word_stats(request.user)
    little_count = sum(1 for v in request.user.learn_map.values() if v == 'little')
    return {
        'words_learned': words_learned,
        'total_words': total_words,
        'little_count': little_count,
    }


def site_footer_stats(request):
    """Stats for the sitewide footer (every page, authenticated or not) —
    mirrors production's <footer class="site-footer"> dashboard (total
    words, learned %, categories started), computed server-side. The
    day-streak widget is deliberately not built (see FIXES-NEEDED.md item
    17) since VLPE has no activity-tracking data to back it.
    """
    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    started_ids = [int(k) for k in learn_map.keys()]
    _, total_words, words_learned = learned_word_stats(request.user)
    pct_complete = round(words_learned / total_words * 100) if total_words else 0
    return {
        'footer_total_words': total_words,
        'footer_words_learned': words_learned,
        'footer_pct_complete': pct_complete,
        'footer_categories_started': categories_started_count(started_ids),
        'footer_total_categories': Category.objects.count(),
    }
