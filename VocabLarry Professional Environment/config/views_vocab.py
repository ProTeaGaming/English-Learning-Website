import itertools
from collections import Counter

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import CEFRLevel, Category, Word


def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()
    tier_filter = request.GET.get('tier', '').strip()

    categories = Category.objects.select_related('cefr_level', 'color', 'section').order_by('section__order', 'order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    categories = list(categories)

    word_category = dict(
        Word.objects.filter(category_id__in=[c.id for c in categories]).values_list('id', 'category_id')
    )
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

    sections = []
    for section_id, group in itertools.groupby(categories, key=lambda c: c.section_id):
        if section_id is None:
            continue
        group = list(group)
        section = group[0].section
        if tier_filter and section.tier != tier_filter:
            continue
        total_words = sum(c.word_count for c in group)
        entry = {'section': section, 'categories': group, 'word_count': total_words}
        if request.user.is_authenticated:
            learned_total = sum(c.progress['learned'] for c in group)
            entry['progress_pct'] = round(learned_total / total_words * 100) if total_words else 0
        else:
            entry['progress_pct'] = None
        sections.append(entry)

    paginator = Paginator(sections, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
        'progress_filter': progress_filter,
        'tier_filter': tier_filter,
    })


def _pagination_window(current, total, delta=2):
    """Page numbers to display, with None marking an ellipsis gap.
    Mirrors production's own windowed-pagination shape."""
    pages = []
    for p in range(1, total + 1):
        if p == 1 or p == total or (current - delta <= p <= current + delta):
            pages.append(p)
        elif pages and pages[-1] is not None:
            pages.append(None)
    return pages


@ensure_csrf_cookie
def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    for word in page_obj:
        word.learn_state = learn_map.get(str(word.pk))

    all_word_ids = list(words.values_list('id', flat=True))

    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'all_word_ids': all_word_ids,
    })


def _resolve_word_refs(strings):
    resolved = []
    for text in strings:
        match = Word.objects.filter(word__iexact=text).first()
        resolved.append({'text': text, 'word': match})
    return resolved


@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    context = {
        'word': word,
        'learn_state': learn_state,
        'synonym_refs': _resolve_word_refs(word.synonyms),
        'antonym_refs': _resolve_word_refs(word.antonyms),
    }
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'vocab/partials/word_detail_card.html', context)
    return render(request, 'vocab/word_detail.html', context)


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


WORD_STAGES = [
    ('basic', 'Basic', ['A1', 'A1+', 'A2', 'A2+']),
    ('intermediate', 'Intermediate', ['B1', 'B1+', 'B2', 'B2+']),
    ('advanced', 'Advanced', ['C1', 'C1+', 'C2', 'C2+']),
]


@ensure_csrf_cookie
def vocabulary_word_list(request):
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()

    words = Word.objects.select_related('category', 'cefr_level').order_by('word')

    if category_filter:
        words = words.filter(category__slug=category_filter)

    stage_codes = next((codes for sid, _, codes in WORD_STAGES if sid == stage_filter), None)
    if stage_codes:
        words = words.filter(cefr_level__code__in=stage_codes)
    if cefr_filter:
        words = words.filter(cefr_level__code=cefr_filter)

    if query:
        q_lower = query.lower()
        words = [
            w for w in words
            if q_lower in w.word.lower()
            or q_lower in w.definition.lower()
            or any(q_lower in s.lower() for s in w.synonyms)
            or any(q_lower in a.lower() for a in w.antonyms)
        ]
    else:
        words = list(words)

    if request.user.is_authenticated and progress_filter in ('learned', 'little', 'none'):
        learn_map = request.user.learn_map

        def _matches_progress(w):
            state = learn_map.get(str(w.pk))
            if progress_filter == 'none':
                return state not in ('learned', 'little')
            return state == progress_filter

        words = [w for w in words if _matches_progress(w)]

    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    if request.user.is_authenticated:
        learn_map = request.user.learn_map
        for word in page_obj:
            word.learn_state = learn_map.get(str(word.pk))
    else:
        for word in page_obj:
            word.learn_state = None

    return render(request, 'vocab/word_list.html', {
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'categories': Category.objects.order_by('name'),
        'cefr_levels': CEFRLevel.objects.order_by('order'),
        'stages': WORD_STAGES,
        'query': query,
        'category_filter': category_filter,
        'stage_filter': stage_filter,
        'cefr_filter': cefr_filter,
        'progress_filter': progress_filter,
    })
