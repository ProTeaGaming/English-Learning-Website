from django.shortcuts import render

from vocab.models import Category, Word
from vocab.services import learned_word_stats

# Production's home-page CEFR Breakdown groups the full 12-value CEFR scale
# (A1/A1+/A2/A2+/.../C2+) down into these 6 base levels — a "+" variant folds
# into its own base level's bucket (e.g. C1+ counts toward C1), matching
# vocablarry.html's updateHome() (cefrLevels.forEach + w.cefr.startsWith(lvl)).
CEFR_BASE_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']


def home(request):
    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    started_ids = [int(k) for k in learn_map.keys()]
    learned_ids, total_words, words_learned = learned_word_stats(request.user)
    pct_complete = round(words_learned / total_words * 100) if total_words else 0
    categories_started = Category.objects.filter(words__id__in=started_ids).distinct().count()

    cefr_breakdown = []
    for base in CEFR_BASE_LEVELS:
        level_words = Word.objects.filter(cefr_level__code__startswith=base)
        total_level = level_words.count()
        learned_in_level = level_words.filter(id__in=learned_ids).count() if total_level else 0
        pct = round(learned_in_level / total_level * 100) if total_level else 0
        cefr_breakdown.append({'code': base, 'pct': pct})

    return render(request, 'home.html', {
        'words_learned': words_learned,
        'categories_started': categories_started,
        'pct_complete': pct_complete,
        'cefr_breakdown': cefr_breakdown,
    })


def reading(request):
    return render(request, 'reading.html')


def writing(request):
    return render(request, 'writing.html')


def listening(request):
    return render(request, 'listening.html')


def speaking(request):
    return render(request, 'speaking.html')


def verify_email(request, key):
    return render(request, 'auth_deep_link.html')


def reset_password(request, key):
    return render(request, 'auth_deep_link.html')
