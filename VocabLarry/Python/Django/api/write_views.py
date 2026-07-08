import json
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from accounts.decorators import is_staff_user
from dashboard.forms import WordForm, CategoryForm, GrammarTopicForm, GrammarLessonBlockForm, GrammarQuestionForm
from vocab.models import Word, Category, GrammarTopic, GrammarLessonBlock, GrammarQuestion


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_staff_user(request.user):
            return JsonResponse({'error': 'staff only'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapped


def _json_body(request):
    try:
        return json.loads(request.body or b'{}'), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({'errors': {'__all__': ['Invalid JSON body.']}}, status=400)


def _word_json(w):
    return {
        'id': w.id, 'word': w.word, 'pos': w.pos, 'definition': w.definition,
        'synonyms': w.synonyms, 'antonyms': w.antonyms, 'example': w.example,
        'gap': w.gap, 'category_id': w.category_id,
        'cefr_code': w.cefr_level.code if w.cefr_level else None, 'order': w.order,
    }


def _word_form_data(payload):
    data = {k: payload.get(k) for k in
            ('word', 'pos', 'definition', 'example', 'gap', 'category', 'cefr_level', 'order')}
    data['synonyms_text'] = ', '.join(payload.get('synonyms') or [])
    data['antonyms_text'] = ', '.join(payload.get('antonyms') or [])
    return data


@staff_required
def word_create(request):
    payload, err = _json_body(request)
    if err:
        return err
    form = WordForm(_word_form_data(payload))
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_word_json(form.save()))


@staff_required
@require_http_methods(['PATCH', 'DELETE'])
def word_detail(request, pk):
    word = get_object_or_404(Word, pk=pk)
    if request.method == 'DELETE':
        word.delete()
        return JsonResponse({'ok': True})
    payload, err = _json_body(request)
    if err:
        return err
    form = WordForm(_word_form_data(payload), instance=word)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_word_json(form.save()))


def _category_json(c):
    return {
        'id': c.id, 'slug': c.slug, 'name': c.name, 'icon': c.icon,
        'cefr_code': c.cefr_level.code if c.cefr_level else None,
        'bg_hex': c.color.bg_hex if c.color else None,
        'text_hex': c.color.text_hex if c.color else None, 'order': c.order,
    }


@staff_required
def category_create(request):
    payload, err = _json_body(request)
    if err:
        return err
    form = CategoryForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_category_json(form.save()))


@staff_required
@require_http_methods(['PATCH', 'DELETE'])
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'DELETE':
        category.delete()
        return JsonResponse({'ok': True})
    payload, err = _json_body(request)
    if err:
        return err
    form = CategoryForm(payload, instance=category)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_category_json(form.save()))


def _topic_json(t):
    return {'id': t.id, 'slug': t.slug, 'title': t.title, 'tag': t.tag,
            'cefr_label': t.cefr_label, 'blurb': t.blurb, 'stage': t.stage,
            'order': t.order}


@staff_required
@require_http_methods(['POST'])
def grammar_topic_create(request):
    payload, err = _json_body(request)
    if err:
        return err
    form = GrammarTopicForm(payload)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_topic_json(form.save()))


@staff_required
@require_http_methods(['PATCH', 'DELETE'])
def grammar_topic_detail(request, pk):
    topic = get_object_or_404(GrammarTopic, pk=pk)
    if request.method == 'DELETE':
        topic.delete()
        return JsonResponse({'ok': True})
    payload, err = _json_body(request)
    if err:
        return err
    form = GrammarTopicForm(payload, instance=topic)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(_topic_json(form.save()))


def _block_json(b):
    return {'id': b.id, 'topic': b.topic_id, 'type': b.type, 'title': b.title,
            'body': b.body, 'data': b.data, 'order': b.order}


def _question_json(q):
    return {'id': q.id, 'topic': q.topic_id, 'qtype': q.qtype, 'prompt': q.prompt,
            'options': q.options, 'answers': q.answers, 'why': q.why, 'order': q.order}


def _child_create(request, form_cls, to_json):
    payload, err = _json_body(request)
    if err:
        return err
    topic = get_object_or_404(GrammarTopic, pk=payload.get('topic'))
    # Convert JSONField dicts to JSON strings for form processing
    form_data = dict(payload)
    if 'data' in form_data and isinstance(form_data['data'], dict):
        form_data['data'] = json.dumps(form_data['data'])
    form = form_cls(form_data)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    obj = form.save(commit=False)
    obj.topic = topic
    obj.save()
    return JsonResponse(to_json(obj))


def _child_detail(request, obj, form_cls, to_json):
    if request.method == 'DELETE':
        obj.delete()
        return JsonResponse({'ok': True})
    payload, err = _json_body(request)
    if err:
        return err
    # Convert JSONField dicts to JSON strings for form processing
    form_data = dict(payload)
    if 'data' in form_data and isinstance(form_data['data'], dict):
        form_data['data'] = json.dumps(form_data['data'])
    form = form_cls(form_data, instance=obj)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    return JsonResponse(to_json(form.save()))


@staff_required
@require_http_methods(['POST'])
def grammar_block_create(request):
    return _child_create(request, GrammarLessonBlockForm, _block_json)


@staff_required
@require_http_methods(['PATCH', 'DELETE'])
def grammar_block_detail(request, pk):
    return _child_detail(request, get_object_or_404(GrammarLessonBlock, pk=pk),
                         GrammarLessonBlockForm, _block_json)


@staff_required
@require_http_methods(['POST'])
def grammar_question_create(request):
    return _child_create(request, GrammarQuestionForm, _question_json)


@staff_required
@require_http_methods(['PATCH', 'DELETE'])
def grammar_question_detail(request, pk):
    return _child_detail(request, get_object_or_404(GrammarQuestion, pk=pk),
                         GrammarQuestionForm, _question_json)
