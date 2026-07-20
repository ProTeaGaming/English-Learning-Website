from collections import Counter

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import CEFRLevel, Category, Word


def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()
    categories = Category.objects.select_related('cefr_level', 'color').order_by('order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    categories = list(categories)

    word_category = dict(Word.objects.values_list('id', 'category_id'))
    word_counts = Counter(word_category.values())

    for category in categories:
        category.word_count = word_counts[category.id]

    if request.user.is_authenticated:
        learn_map = request.user.learn_map
        progress_by_category = {}
        for word_id_str, state in learn_map.items():
            try:
                word_id = int(word_id_str)
            except (TypeError, ValueError):
                continue
            category_id = word_category.get(word_id)
            if category_id is None:
                continue
            bucket = progress_by_category.setdefault(category_id, {'learned': 0, 'little': 0})
            if state == 'learned':
                bucket['learned'] += 1
            elif state == 'little':
                bucket['little'] += 1

        for category in categories:
            total = category.word_count
            bucket = progress_by_category.get(category.id, {'learned': 0, 'little': 0})
            learned = bucket['learned']
            little = bucket['little']
            category.progress = {
                'learned': learned,
                'little': little,
                'total': total,
                'learned_pct': round(learned / total * 100) if total else 0,
                'little_pct': round(little / total * 100) if total else 0,
                'complete': total > 0 and learned == total,
            }

        if progress_filter == 'learned':
            categories = [c for c in categories if c.progress['complete']]
        elif progress_filter == 'in_progress':
            categories = [
                c for c in categories
                if not c.progress['complete'] and (c.progress['learned'] or c.progress['little'])
            ]
        elif progress_filter == 'not_started':
            categories = [
                c for c in categories
                if not c.progress['learned'] and not c.progress['little']
            ]
    else:
        for category in categories:
            category.progress = None

    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
        'progress_filter': progress_filter,
    })


def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
    })


@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    return render(request, 'vocab/word_detail.html', {
        'word': word,
        'learn_state': learn_state,
    })


def vocab_quiz_setup(request):
    categories = Category.objects.order_by('order')
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/quiz_setup.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
    })


def vocab_quiz_play(request):
    return render(request, 'vocab/quiz_play.html')


def vocabulary_home(request):
    return render(request, 'vocab/home.html')


def vocabulary_word_list(request):
    return render(request, 'vocab/word_list.html')
