import json
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from accounts.decorators import is_staff_user
from dashboard.forms import WordForm
from vocab.models import Word


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
