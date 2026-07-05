from django.http import JsonResponse
from django.views.decorators.http import require_GET
from vocab.models import CEFRLevel, Category, Word, GrammarTopic


@require_GET
def words(request):
    qs = Word.objects.select_related('cefr_level', 'category').order_by('category__order', 'order')
    data = [
        {
            'id':          w.id,
            'word':        w.word,
            'pos':         w.pos,
            'definition':  w.definition,
            'synonyms':    w.synonyms,
            'antonyms':    w.antonyms,
            'example':     w.example,
            'gap':         w.gap,
            'category_id': w.category_id,
            'cefr_code':   w.cefr_level.code if w.cefr_level else None,
            'order':       w.order,
        }
        for w in qs
    ]
    return JsonResponse(data, safe=False)


@require_GET
def categories(request):
    qs = Category.objects.select_related('cefr_level', 'color').order_by('order')
    data = [
        {
            'id':       c.id,
            'slug':     c.slug,
            'name':     c.name,
            'icon':     c.icon,
            'cefr_code': c.cefr_level.code if c.cefr_level else None,
            'bg_hex':   c.color.bg_hex if c.color else None,
            'text_hex': c.color.text_hex if c.color else None,
            'order':    c.order,
        }
        for c in qs
    ]
    return JsonResponse(data, safe=False)


@require_GET
def cefr_levels(request):
    qs = CEFRLevel.objects.order_by('order')
    data = [{'id': l.id, 'code': l.code, 'name': l.name, 'order': l.order} for l in qs]
    return JsonResponse(data, safe=False)


GRAMMAR_STAGES = [
    ('beginner', 'Beginner', 'A1–A2'),
    ('independent', 'Independent', 'B1–B2'),
    ('expert', 'Expert', 'C1–C2'),
]


@require_GET
def grammar(request):
    topics = GrammarTopic.objects.prefetch_related('blocks', 'questions').order_by('order')
    by_stage = {}
    for t in topics:
        by_stage.setdefault(t.stage, []).append({
            'slug':  t.slug,
            'title': t.title,
            'tag':   t.tag,
            'cefr':  t.cefr_label,
            'blurb': t.blurb,
            'lesson': [
                {'type': b.type, 'title': b.title, 'body': b.body, 'data': b.data}
                for b in t.blocks.all()
            ],
            'quiz': [
                {'qtype': q.qtype, 'prompt': q.prompt, 'options': q.options,
                 'answers': q.answers, 'why': q.why}
                for q in t.questions.all()
            ],
        })
    data = [
        {'id': sid, 'name': name, 'cefr': cefr, 'topics': by_stage.get(sid, [])}
        for sid, name, cefr in GRAMMAR_STAGES
    ]
    return JsonResponse(data, safe=False)
