import itertools

from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import GrammarLessonBlock, GrammarSection, GrammarTopic

GRAMMAR_CARD_THEMES = [
    't-tb', 't-tv', 't-tp', 't-tr', 't-te', 't-ta', 't-tc', 't-tg', 't-ti',
    't-to', 't-tro', 't-tfg', 't-tpurp', 't-ts', 't-tnavy',
]
GRAMMAR_IMG_FALLBACK = ['1456513080510-7bf3a84b82f8', '1488190211105-8b0e65b80b4e', '1516979187457-637abb4f9353']
GRAMMAR_CEFR_LEVELS = ['A1', 'A1+', 'A2', 'A2+', 'B1', 'B1+', 'B2', 'B2+', 'C1', 'C1+', 'C2', 'C2+']

GRAMWORD_SETS = {
    'verbs': {'topic_slug': 'irregular-verbs', 'label': 'Irregular Verbs'},
    'comparisons': {'topic_slug': 'comparison-structures', 'label': 'Comparisons'},
}


def _classify_verb_pattern(v1, v2, v3):
    if v1 == v2 == v3:
        return 'AAA'
    if v2 == v3:
        return 'ABB'
    if v1 == v3:
        return 'ABA'
    return 'ABC'


def _pagination_window(current, total, delta=2):
    """Page numbers to display, with None marking an ellipsis gap.
    Duplicated from views_vocab.py's identical helper rather than
    cross-imported, keeping the vocab/grammar view modules independent."""
    pages = []
    for p in range(1, total + 1):
        if p == 1 or p == total or (current - delta <= p <= current + delta):
            pages.append(p)
        elif pages and pages[-1] is not None:
            pages.append(None)
    return pages


def _stage_ranked_topics():
    return GrammarTopic.objects.select_related('section').annotate(
        stage_rank=Case(
            When(stage='beginner', then=Value(0)),
            When(stage='independent', then=Value(1)),
            When(stage='expert', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
    ).order_by('section__order', 'section_id', 'stage_rank', 'order')


def _assign_themes(topics):
    for idx, topic in enumerate(topics):
        topic.theme = GRAMMAR_CARD_THEMES[idx % len(GRAMMAR_CARD_THEMES)]
    return topics


def _annotate_progress(topics, grammar_map):
    for topic in topics:
        record = grammar_map.get(topic.slug) or {}
        topic.best = record.get('best', 0)
        topic.done = bool(record.get('done'))
        if topic.done:
            topic.status = 'completed'
        elif topic.best > 0:
            topic.status = 'inProgress'
        else:
            topic.status = 'notStarted'
    return topics


def grammar_img_url(image_id):
    return f'https://images.unsplash.com/photo-{image_id}?auto=format&fit=crop&w=900&q=80'


def grammar_browse(request):
    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    status_filter = request.GET.get('status', '').strip()
    section_filter = request.GET.get('section', '').strip()

    has_any_topics = GrammarTopic.objects.exists()
    grammar_map = request.user.grammar_map if request.user.is_authenticated else {}

    all_topics = list(_stage_ranked_topics())
    _assign_themes(all_topics)
    _annotate_progress(all_topics, grammar_map)

    q_lower = query.lower()
    sections = []
    for section_id, group in itertools.groupby(all_topics, key=lambda t: t.section_id):
        if section_id is None:
            continue
        group = list(group)
        section = group[0].section
        if section_filter and section.slug != section_filter:
            continue
        filtered = [
            t for t in group
            if (not stage_filter or t.stage == stage_filter)
            and (not cefr_filter or t.cefr_label == cefr_filter)
            and (not status_filter or t.status == status_filter)
            and (not q_lower or q_lower in t.title.lower())
        ]
        if not filtered:
            continue
        done_count = sum(1 for t in filtered if t.done)
        progress_pct = round(done_count / len(filtered) * 100) if filtered else 0
        sections.append({'section': section, 'topics': filtered, 'progress_pct': progress_pct})

    return render(request, 'grammar/browse.html', {
        'sections': sections,
        'all_sections': GrammarSection.objects.order_by('order'),
        'stages': GrammarTopic.STAGES,
        'cefr_levels': GRAMMAR_CEFR_LEVELS,
        'query': query,
        'stage_filter': stage_filter,
        'cefr_filter': cefr_filter,
        'status_filter': status_filter,
        'section_filter': section_filter,
        'has_any_topics': has_any_topics,
    })


def grammar_topic_detail(request, slug):
    topic = get_object_or_404(GrammarTopic.objects.select_related('section'), slug=slug)
    themed_topics = _assign_themes(list(_stage_ranked_topics()))
    theme = next((t.theme for t in themed_topics if t.slug == slug), 't-tv')

    blocks = list(topic.blocks.order_by('order'))
    pool = list(dict.fromkeys(
        (topic.section.image_ids if topic.section else []) + GRAMMAR_IMG_FALLBACK
    ))
    lesson_items = []
    stack = []
    rule_idx = 0
    for block in blocks:
        if block.type == 'rule':
            image_url = grammar_img_url(pool[rule_idx % len(pool)]) if pool else ''
            stack.append({
                'block': block,
                'num': str(rule_idx + 1).zfill(2),
                'accent': f'gram-ac-{rule_idx % 4}',
                'flip': bool(rule_idx % 2),
                'image_url': image_url,
            })
            rule_idx += 1
        else:
            if stack:
                lesson_items.append({'kind': 'stack', 'cards': stack})
                stack = []
            lesson_items.append({'kind': 'block', 'block': block})
    if stack:
        lesson_items.append({'kind': 'stack', 'cards': stack})

    grammar_status = None
    if request.user.is_authenticated:
        grammar_status = request.user.grammar_map.get(topic.slug)

    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'theme': theme,
        'lesson_items': lesson_items,
        'grammar_status': grammar_status,
    })


@ensure_csrf_cookie
def grammar_topic_quiz(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    return render(request, 'grammar/topic_quiz.html', {'topic': topic})


def grammar_test_setup(request):
    return render(request, 'grammar/quiz_setup.html')


def grammar_test_play(request):
    return render(request, 'grammar/quiz_play.html')


def grammar_home(request):
    return render(request, 'grammar/home.html')


def grammar_word(request):
    active_set = request.GET.get('set', 'verbs')
    if active_set not in GRAMWORD_SETS:
        active_set = 'verbs'
    query = request.GET.get('q', '').strip()
    pattern_filter = request.GET.get('pattern', '').strip()

    topic_slug = GRAMWORD_SETS[active_set]['topic_slug']
    block = get_object_or_404(GrammarLessonBlock, topic__slug=topic_slug, type='table')
    head = block.data.get('head', [])
    rows = block.data.get('rows', [])

    if active_set == 'verbs':
        entries = [
            {'cells': row, 'pattern': _classify_verb_pattern(*row)}
            for row in rows
        ]
        if pattern_filter in ('AAA', 'ABA', 'ABB', 'ABC'):
            entries = [e for e in entries if e['pattern'] == pattern_filter]
    else:
        entries = [{'cells': row, 'pattern': None} for row in rows]
        pattern_filter = ''

    if query:
        q_lower = query.lower()
        entries = [
            e for e in entries
            if any(q_lower in str(cell).lower() for cell in e['cells'])
        ]

    paginator = Paginator(entries, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'grammar/word.html', {
        'active_set': active_set,
        'head': head,
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'query': query,
        'pattern_filter': pattern_filter,
    })
