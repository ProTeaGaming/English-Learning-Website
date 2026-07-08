# Site Debug Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Staff-only "Debug mode" on the main VocabLarry site: browse the real site, flip Debug on, and add/edit/delete vocab + grammar content inline via new staff-gated JSON write endpoints.

**Architecture:** Backend adds function-based write views in the `api` app (create/update/delete for Word, Category, GrammarTopic, GrammarLessonBlock, GrammarQuestion) that validate through the existing dashboard `ModelForm`s and are gated by a JSON-returning staff decorator. Frontend (single-file SPA `vocab-master.html`) gains a `state.auth.isStaff` flag from `/auth/session/`, a Debug toggle in the profile menu, an amber DEBUG ribbon, a generic debug modal driven by per-model field configs, and per-surface ✎/✕/+ controls that call the write API then re-fetch and re-render.

**Tech Stack:** Django 5 (function-based views, ModelForms, JsonResponse), pytest + pytest-django + pytest-mock, vanilla JS in `vocab-master.html`.

**Spec:** `docs/superpowers/specs/2026-07-08-site-debug-mode-design.md`

## Global Constraints

- Everything lives in `VocabLarry/Python/Django/` (Django product only; no Flask/PHP/React changes).
- Run tests with `python -m pytest tests` from `VocabLarry/Python/Django/` (`manage.py test` finds 0 tests). Suite currently passes 42/42.
- No new dependencies (no DRF). Follow the existing function-based view idiom in `api/views.py`.
- Staff test everywhere: `user.is_staff or role in ('staff', 'admin')` — reuse `_ROLE_ORDER` from `accounts/decorators.py`.
- Write endpoints return: object JSON on success, `{"errors": {...}}` with status 400 on validation failure, `{"error": "staff only"}` with status 403 for non-staff, `{"ok": true}` on DELETE.
- CEFR levels and colors are NOT editable from the site (out of scope).
- Git: commit after each task; do NOT push (user pushes to `elw` explicitly when ready). Never push to `origin`.
- All paths below are relative to `VocabLarry/Python/Django/` unless they start with `docs/`.

---

### Task 1: `isStaff` in the session endpoint

**Files:**
- Modify: `accounts/decorators.py` (add `is_staff_user` helper)
- Modify: `accounts/views.py:23-34` (`session` view)
- Test: `tests/test_debug_api.py` (new file)

**Interfaces:**
- Produces: `is_staff_user(user) -> bool` in `accounts/decorators.py` (used by Task 2's decorator); `GET /auth/session/` response gains `"isStaff": bool` (used by SPA Task 7).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_debug_api.py`:

```python
import pytest
from django.test import Client


@pytest.fixture
def logged_in(mocker):
    """Client factory: log a user in with allauth MFA check stubbed out."""
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    def _login(user):
        c = Client()
        c.force_login(user)
        return c
    return _login


@pytest.mark.django_db
def test_session_reports_is_staff_false_for_regular_user(logged_in, regular_user):
    r = logged_in(regular_user).get('/auth/session/')
    assert r.status_code == 200
    assert r.json()['isStaff'] is False


@pytest.mark.django_db
def test_session_reports_is_staff_true_for_staff_and_admin(logged_in, staff_user, admin_user):
    assert logged_in(staff_user).get('/auth/session/').json()['isStaff'] is True
    assert logged_in(admin_user).get('/auth/session/').json()['isStaff'] is True


@pytest.mark.django_db
def test_session_anonymous_has_no_is_staff_key():
    r = Client().get('/auth/session/')
    assert r.json() == {'loggedIn': False}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_debug_api.py -v`
Expected: the two `isStaff` tests FAIL with `KeyError: 'isStaff'`; the anonymous test passes.

- [ ] **Step 3: Implement**

In `accounts/decorators.py`, add after `_ROLE_ORDER`:

```python
def is_staff_user(user) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    return user.is_staff or _ROLE_ORDER.get(getattr(user, 'role', 'user'), 0) >= 1
```

In `accounts/views.py`, add the import and extend the `session` response dict:

```python
from .decorators import is_staff_user
```

and in `session()` add one key to the logged-in `JsonResponse`:

```python
        'picture': _picture_url(request, u),
        'isStaff': is_staff_user(u),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_debug_api.py -v`
Expected: all PASS. Then `python -m pytest tests -q` — full suite passes.

- [ ] **Step 5: Commit**

```bash
git add tests/test_debug_api.py accounts/decorators.py accounts/views.py
git commit -m "feat(api): expose isStaff in session endpoint"
```

---

### Task 2: Staff JSON gate + Word write endpoints

**Files:**
- Create: `api/write_views.py`
- Modify: `api/views.py` (words view: GET+POST dispatch)
- Modify: `api/urls.py`
- Test: `tests/test_debug_api.py` (extend)

**Interfaces:**
- Consumes: `is_staff_user` from `accounts.decorators` (Task 1); `WordForm` from `dashboard.forms`.
- Produces (used by Tasks 3–6 and the SPA):
  - `staff_required(view)` decorator in `api/write_views.py` → 403 JSON for non-staff/anonymous
  - `_json_body(request) -> dict` (raises `ValueError` on bad JSON → view returns 400)
  - `POST /api/words/` create, `PATCH /api/words/<pk>/` update (full field set), `DELETE /api/words/<pk>/`
  - Word payload keys: `word, pos, definition, example, gap, category (pk), cefr_level (pk), order, synonyms (list), antonyms (list)`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_debug_api.py`:

```python
from vocab.models import CEFRLevel, Color, Category, Word


@pytest.fixture
def cefr_b1(db):
    return CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)


@pytest.fixture
def category(db, cefr_b1):
    color = Color.objects.create(name='Violet', bg_hex='#7c3aed', text_hex='#ffffff')
    return Category.objects.create(
        slug='travel', name='Travel', icon='✈️',
        cefr_level=cefr_b1, color=color, order=0,
    )


@pytest.fixture
def word(db, category, cefr_b1):
    return Word.objects.create(
        word='journey', pos='noun', definition='a trip', example='A long journey.',
        gap='A long ___.', category=category, cefr_level=cefr_b1, order=0,
        synonyms=['trip'], antonyms=[],
    )


def word_payload(category, cefr_b1, **over):
    p = {
        'word': 'voyage', 'pos': 'noun', 'definition': 'a long trip by sea',
        'example': 'The voyage took weeks.', 'gap': 'The ___ took weeks.',
        'category': category.pk, 'cefr_level': cefr_b1.pk, 'order': 1,
        'synonyms': ['journey', 'trip'], 'antonyms': [],
    }
    p.update(over)
    return p


@pytest.mark.django_db
def test_word_write_endpoints_reject_non_staff(logged_in, regular_user, word, category, cefr_b1):
    anon = Client()
    user = logged_in(regular_user)
    payload = word_payload(category, cefr_b1)
    for c in (anon, user):
        assert c.post('/api/words/', payload, content_type='application/json').status_code == 403
        assert c.patch(f'/api/words/{word.pk}/', payload, content_type='application/json').status_code == 403
        assert c.delete(f'/api/words/{word.pk}/').status_code == 403
    assert Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_staff_can_create_word(logged_in, staff_user, category, cefr_b1):
    r = logged_in(staff_user).post(
        '/api/words/', word_payload(category, cefr_b1), content_type='application/json')
    assert r.status_code == 200
    body = r.json()
    assert body['word'] == 'voyage'
    assert body['synonyms'] == ['journey', 'trip']
    assert Word.objects.filter(word='voyage').exists()


@pytest.mark.django_db
def test_staff_can_update_word(logged_in, staff_user, word, category, cefr_b1):
    payload = word_payload(category, cefr_b1, word='journey', definition='an act of travelling')
    r = logged_in(staff_user).patch(
        f'/api/words/{word.pk}/', payload, content_type='application/json')
    assert r.status_code == 200
    word.refresh_from_db()
    assert word.definition == 'an act of travelling'


@pytest.mark.django_db
def test_staff_can_delete_word(logged_in, staff_user, word):
    r = logged_in(staff_user).delete(f'/api/words/{word.pk}/')
    assert r.status_code == 200 and r.json() == {'ok': True}
    assert not Word.objects.filter(pk=word.pk).exists()


@pytest.mark.django_db
def test_word_create_missing_field_returns_400_with_errors(logged_in, staff_user, category, cefr_b1):
    payload = word_payload(category, cefr_b1, word='')
    r = logged_in(staff_user).post('/api/words/', payload, content_type='application/json')
    assert r.status_code == 400
    assert 'word' in r.json()['errors']


@pytest.mark.django_db
def test_word_create_bad_json_returns_400(logged_in, staff_user):
    r = logged_in(staff_user).post('/api/words/', 'not json', content_type='application/json')
    assert r.status_code == 400
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_debug_api.py -v`
Expected: new tests FAIL (POST to `/api/words/` currently 405 from `@require_GET`; `/api/words/<pk>/` is 404).

- [ ] **Step 3: Implement**

Create `api/write_views.py`:

```python
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
```

In `api/views.py`, change the `words` read view to dispatch POST to the create view. Replace the decorator/def:

```python
from django.views.decorators.http import require_GET, require_http_methods
from . import write_views


@require_http_methods(['GET', 'POST'])
def words(request):
    if request.method == 'POST':
        return write_views.word_create(request)
    qs = Word.objects.select_related('cefr_level', 'category').order_by('category__order', 'order')
    ...  # existing list code unchanged
```

In `api/urls.py` add:

```python
from . import views, write_views

    path('words/<int:pk>/', write_views.word_detail, name='api_word_detail'),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_debug_api.py -v` → all PASS.
Run: `python -m pytest tests -q` → full suite passes (the GET words tests must still pass).

- [ ] **Step 5: Commit**

```bash
git add api/write_views.py api/views.py api/urls.py tests/test_debug_api.py
git commit -m "feat(api): staff-gated word create/update/delete endpoints"
```

---

### Task 3: Category write endpoints

**Files:**
- Modify: `api/write_views.py`, `api/views.py` (categories view GET+POST dispatch), `api/urls.py`
- Test: `tests/test_debug_api.py` (extend)

**Interfaces:**
- Consumes: `staff_required`, `_json_body` (Task 2); `CategoryForm` from `dashboard.forms`.
- Produces: `POST /api/categories/`, `PATCH/DELETE /api/categories/<pk>/`. Payload keys: `slug, name, icon, cefr_level (pk), color (pk), order`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_debug_api.py`:

```python
@pytest.mark.django_db
def test_category_write_endpoints_reject_non_staff(logged_in, regular_user, category):
    c = logged_in(regular_user)
    assert c.post('/api/categories/', {}, content_type='application/json').status_code == 403
    assert c.patch(f'/api/categories/{category.pk}/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/categories/{category.pk}/').status_code == 403


@pytest.mark.django_db
def test_staff_can_create_update_delete_category(logged_in, staff_user, category, cefr_b1):
    c = logged_in(staff_user)
    payload = {'slug': 'work', 'name': 'Work', 'icon': '💼',
               'cefr_level': cefr_b1.pk, 'color': category.color.pk, 'order': 5}
    r = c.post('/api/categories/', payload, content_type='application/json')
    assert r.status_code == 200 and r.json()['slug'] == 'work'
    new_pk = r.json()['id']

    payload['name'] = 'Work & Career'
    r = c.patch(f'/api/categories/{new_pk}/', payload, content_type='application/json')
    assert r.status_code == 200 and r.json()['name'] == 'Work & Career'

    r = c.delete(f'/api/categories/{new_pk}/')
    assert r.status_code == 200
    assert not Category.objects.filter(pk=new_pk).exists()


@pytest.mark.django_db
def test_category_create_duplicate_slug_returns_400(logged_in, staff_user, category, cefr_b1):
    payload = {'slug': 'travel', 'name': 'Travel 2', 'icon': 'x',
               'cefr_level': cefr_b1.pk, 'color': category.color.pk, 'order': 9}
    r = logged_in(staff_user).post('/api/categories/', payload, content_type='application/json')
    assert r.status_code == 400 and 'slug' in r.json()['errors']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_debug_api.py -k category -v`
Expected: FAIL (405 / 404).

- [ ] **Step 3: Implement**

In `api/write_views.py` add (imports: `CategoryForm`, `Category`):

```python
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
```

In `api/views.py`, give `categories` the same GET+POST dispatch as `words` (POST → `write_views.category_create`). In `api/urls.py` add `path('categories/<int:pk>/', write_views.category_detail, name='api_category_detail')`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests -q` → full suite passes.

- [ ] **Step 5: Commit**

```bash
git add api/write_views.py api/views.py api/urls.py tests/test_debug_api.py
git commit -m "feat(api): staff-gated category create/update/delete endpoints"
```

---

### Task 4: Grammar read API exposes ids and order

**Files:**
- Modify: `api/views.py:61-86` (`grammar` view)
- Modify (if assertions break): `tests/test_grammar_api.py`

**Interfaces:**
- Produces: grammar GET response topics gain `"id"` and `"order"`; each `lesson` block gains `"id"` and `"order"`; each `quiz` question gains `"id"` and `"order"`. Existing keys unchanged (SPA Tasks 8–9 rely on these ids to call write endpoints).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_debug_api.py`:

```python
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.fixture
def topic(db):
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles', tag='Determiners',
        cefr_label='A1', blurb='a/an/the', stage='beginner', order=0)
    GrammarLessonBlock.objects.create(topic=t, type='intro', body='Intro text.', order=0)
    GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She is ___ engineer.',
        options=['a', 'an', 'the', '(none)'], answers=[1], why='Vowel sound.', order=0)
    return t


@pytest.mark.django_db
def test_grammar_api_includes_ids_and_order(topic):
    r = Client().get('/api/grammar/')
    beginner = next(s for s in r.json() if s['id'] == 'beginner')
    t = beginner['topics'][0]
    assert t['id'] == topic.pk and t['order'] == 0
    assert t['lesson'][0]['id'] and t['lesson'][0]['order'] == 0
    assert t['quiz'][0]['id'] and t['quiz'][0]['order'] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_debug_api.py::test_grammar_api_includes_ids_and_order -v`
Expected: FAIL with `KeyError: 'id'`.

- [ ] **Step 3: Implement**

In `api/views.py` `grammar()`, extend the three dicts:

```python
        by_stage.setdefault(t.stage, []).append({
            'id':    t.id,
            'order': t.order,
            'slug':  t.slug,
            ...
            'lesson': [
                {'id': b.id, 'order': b.order, 'type': b.type, 'title': b.title,
                 'body': b.body, 'data': b.data}
                for b in t.blocks.all()
            ],
            'quiz': [
                {'id': q.id, 'order': q.order, 'qtype': q.qtype, 'prompt': q.prompt,
                 'options': q.options, 'answers': q.answers, 'why': q.why}
                for q in t.questions.all()
            ],
        })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests -q`
Expected: all pass. If `tests/test_grammar_api.py` asserts exact dict equality on topics/blocks/questions, update those expected dicts to include the new `id`/`order` keys (adding keys is the intended change; do not remove existing keys).

- [ ] **Step 5: Commit**

```bash
git add api/views.py tests/test_debug_api.py tests/test_grammar_api.py
git commit -m "feat(api): grammar read endpoint exposes ids and order"
```

---

### Task 5: Grammar topic write endpoints

**Files:**
- Modify: `api/write_views.py`, `api/urls.py`
- Test: `tests/test_debug_api.py` (extend)

**Interfaces:**
- Consumes: `staff_required`, `_json_body`; `GrammarTopicForm` from `dashboard.forms`.
- Produces: `POST /api/grammar/topics/`, `PATCH/DELETE /api/grammar/topics/<pk>/`. Payload keys: `slug, title, tag, cefr_label, blurb, stage, order`. Deleting a topic cascades to its blocks/questions (model FK behavior — no extra code).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_debug_api.py`:

```python
def topic_payload(**over):
    p = {'slug': 'passive-voice', 'title': 'Passive Voice', 'tag': 'Voice',
         'cefr_label': 'B1', 'blurb': 'Focus on the action.',
         'stage': 'independent', 'order': 13}
    p.update(over)
    return p


@pytest.mark.django_db
def test_grammar_topic_writes_reject_non_staff(logged_in, regular_user, topic):
    c = logged_in(regular_user)
    assert c.post('/api/grammar/topics/', topic_payload(), content_type='application/json').status_code == 403
    assert c.patch(f'/api/grammar/topics/{topic.pk}/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/topics/{topic.pk}/').status_code == 403


@pytest.mark.django_db
def test_staff_can_create_update_topic(logged_in, staff_user):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/topics/', topic_payload(), content_type='application/json')
    assert r.status_code == 200 and r.json()['slug'] == 'passive-voice'
    pk = r.json()['id']
    r = c.patch(f'/api/grammar/topics/{pk}/',
                topic_payload(title='Passive & Active Voice'), content_type='application/json')
    assert r.status_code == 200 and r.json()['title'] == 'Passive & Active Voice'


@pytest.mark.django_db
def test_topic_delete_cascades_blocks_and_questions(logged_in, staff_user, topic):
    r = logged_in(staff_user).delete(f'/api/grammar/topics/{topic.pk}/')
    assert r.status_code == 200
    assert not GrammarTopic.objects.filter(pk=topic.pk).exists()
    assert GrammarLessonBlock.objects.count() == 0
    assert GrammarQuestion.objects.count() == 0


@pytest.mark.django_db
def test_topic_create_invalid_stage_returns_400(logged_in, staff_user):
    r = logged_in(staff_user).post('/api/grammar/topics/',
                                   topic_payload(stage='wizard'), content_type='application/json')
    assert r.status_code == 400 and 'stage' in r.json()['errors']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_debug_api.py -k topic -v` → FAIL (404).

- [ ] **Step 3: Implement**

In `api/write_views.py` add (imports: `GrammarTopicForm`, `GrammarTopic`):

```python
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
```

In `api/urls.py` add:

```python
    path('grammar/topics/', write_views.grammar_topic_create, name='api_grammar_topic_create'),
    path('grammar/topics/<int:pk>/', write_views.grammar_topic_detail, name='api_grammar_topic_detail'),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests -q` → all pass.

- [ ] **Step 5: Commit**

```bash
git add api/write_views.py api/urls.py tests/test_debug_api.py
git commit -m "feat(api): staff-gated grammar topic write endpoints"
```

---

### Task 6: Grammar block + question write endpoints

**Files:**
- Modify: `api/write_views.py`, `api/urls.py`
- Test: `tests/test_debug_api.py` (extend)

**Interfaces:**
- Consumes: `staff_required`, `_json_body`; `GrammarLessonBlockForm`, `GrammarQuestionForm` from `dashboard.forms` (their `clean()` enforces the JSON shapes).
- Produces:
  - `POST /api/grammar/blocks/` (payload: `topic` pk + `type, title, body, data, order`), `PATCH/DELETE /api/grammar/blocks/<pk>/`
  - `POST /api/grammar/questions/` (payload: `topic` pk + `qtype, prompt, options, answers, why, order`), `PATCH/DELETE /api/grammar/questions/<pk>/`
  - Create views attach the topic via `form.save(commit=False)`; update never moves an object to another topic.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_debug_api.py`:

```python
@pytest.mark.django_db
def test_staff_can_create_update_delete_block(logged_in, staff_user, topic):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/blocks/', {
        'topic': topic.pk, 'type': 'rule', 'title': 'Use "an" before vowels',
        'body': 'Use an before vowel sounds.', 'data': {}, 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200
    pk = r.json()['id']
    r = c.patch(f'/api/grammar/blocks/{pk}/', {
        'type': 'rule', 'title': 'Use "an" before vowel SOUNDS',
        'body': 'an hour, an MP.', 'data': {}, 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200 and 'SOUNDS' in r.json()['title']
    assert c.delete(f'/api/grammar/blocks/{pk}/').status_code == 200


@pytest.mark.django_db
def test_block_create_table_without_head_returns_400(logged_in, staff_user, topic):
    r = logged_in(staff_user).post('/api/grammar/blocks/', {
        'topic': topic.pk, 'type': 'table', 'title': 'T', 'body': '',
        'data': {'rows': [['a']]}, 'order': 2,
    }, content_type='application/json')
    assert r.status_code == 400


@pytest.mark.django_db
def test_staff_can_create_question_and_bad_mcq_rejected(logged_in, staff_user, topic):
    c = logged_in(staff_user)
    r = c.post('/api/grammar/questions/', {
        'topic': topic.pk, 'qtype': 'mcq', 'prompt': 'He bought ___ umbrella.',
        'options': ['a', 'an', 'the', '(none)'], 'answers': [1], 'why': 'Vowel.', 'order': 1,
    }, content_type='application/json')
    assert r.status_code == 200
    r = c.post('/api/grammar/questions/', {
        'topic': topic.pk, 'qtype': 'mcq', 'prompt': 'x',
        'options': ['a', 'b', 'c'], 'answers': [0], 'why': 'x', 'order': 2,
    }, content_type='application/json')
    assert r.status_code == 400 and 'options' in r.json()['errors']


@pytest.mark.django_db
def test_block_and_question_writes_reject_non_staff(logged_in, regular_user, topic):
    c = logged_in(regular_user)
    block = topic.blocks.first()
    q = topic.questions.first()
    assert c.post('/api/grammar/blocks/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/blocks/{block.pk}/').status_code == 403
    assert c.post('/api/grammar/questions/', {}, content_type='application/json').status_code == 403
    assert c.delete(f'/api/grammar/questions/{q.pk}/').status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_debug_api.py -k "block or question" -v` → FAIL (404).

- [ ] **Step 3: Implement**

In `api/write_views.py` add (imports: `GrammarLessonBlockForm`, `GrammarQuestionForm`, `GrammarLessonBlock`, `GrammarQuestion`):

```python
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
    form = form_cls(payload)
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
    form = form_cls(payload, instance=obj)
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
```

In `api/urls.py` add:

```python
    path('grammar/blocks/', write_views.grammar_block_create, name='api_grammar_block_create'),
    path('grammar/blocks/<int:pk>/', write_views.grammar_block_detail, name='api_grammar_block_detail'),
    path('grammar/questions/', write_views.grammar_question_create, name='api_grammar_question_create'),
    path('grammar/questions/<int:pk>/', write_views.grammar_question_detail, name='api_grammar_question_detail'),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests -q` → all pass.

- [ ] **Step 5: Commit**

```bash
git add api/write_views.py api/urls.py tests/test_debug_api.py
git commit -m "feat(api): staff-gated grammar block and question write endpoints"
```

---

### Task 7: SPA debug core — isStaff, toggle, ribbon, fetch helper, modal

**Files:**
- Modify: `vocab-master.html` (all changes in this one file; anchors given per change)

**Interfaces:**
- Consumes: `getCsrf()` (`vocab-master.html:2292`), `state.auth` hydration (`vocab-master.html:2958-2965`), `/auth/session/` `isStaff` (Task 1).
- Produces (used by Tasks 8–9):
  - `state.auth.isStaff` (bool), `debugOn()` → bool (isStaff && sessionStorage flag)
  - `applyDebugMode()` → toggles `body.debug-on` class + ribbon, re-renders current page
  - `debugFetch(url, method, payload)` → Promise (throws `{errors}` object on 400)
  - `openDebugModal({title, fields, initial, onSave})` → generic form modal; field spec `{name, label, type: 'text'|'textarea'|'number'|'select'|'csv'|'json', options?: () => [{value,label}]}`
  - `debugConfirm(message)` → Promise<bool> (uses `window.confirm`)

- [ ] **Step 1: Hydrate `isStaff` into auth state**

At `vocab-master.html:2958-2965`, add `isStaff` to all three `state.auth` assignments (default `false`; from session response use `!!profile.isStaff`). Also add `isStaff:false` to the initial `auth:` object at line 2748.

- [ ] **Step 2: Add debug core JS**

Directly after the `getCsrf()` function (line ~2292), add:

```js
/* ---------- Debug mode (staff-only inline editing) ---------- */
function debugOn(){ return !!(state.auth.isStaff && sessionStorage.getItem('debugMode') === '1'); }

function applyDebugMode(){
  document.body.classList.toggle('debug-on', debugOn());
  let ribbon = document.getElementById('debugRibbon');
  if (debugOn() && !ribbon){
    ribbon = document.createElement('div');
    ribbon.id = 'debugRibbon';
    ribbon.textContent = 'DEBUG';
    document.body.appendChild(ribbon);
  } else if (!debugOn() && ribbon){
    ribbon.remove();
  }
}

async function debugFetch(url, method, payload){
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data;
  return data;
}

function debugConfirm(message){ return Promise.resolve(window.confirm(message)); }

function openDebugModal({ title, fields, initial = {}, onSave }){
  const overlay = document.createElement('div');
  overlay.className = 'dbg-overlay';
  const inputHtml = f => {
    const val = initial[f.name];
    if (f.type === 'select'){
      const opts = f.options().map(o =>
        `<option value="${o.value}" ${String(val) === String(o.value) ? 'selected' : ''}>${o.label}</option>`
      ).join('');
      return `<select name="${f.name}">${opts}</select>`;
    }
    if (f.type === 'textarea' || f.type === 'json'){
      const text = f.type === 'json'
        ? (val === undefined ? '' : JSON.stringify(val))
        : (val ?? '');
      return `<textarea name="${f.name}" rows="3">${text.replace(/</g, '&lt;')}</textarea>`;
    }
    const text = f.type === 'csv' ? (val || []).join(', ') : (val ?? '');
    const type = f.type === 'number' ? 'number' : 'text';
    return `<input type="${type}" name="${f.name}" value="${String(text).replace(/"/g, '&quot;')}">`;
  };
  overlay.innerHTML = `
    <div class="dbg-modal" role="dialog" aria-modal="true">
      <h3>${title}</h3>
      <form>
        ${fields.map(f => `
          <label class="dbg-field" data-field="${f.name}">
            <span>${f.label}</span>
            ${inputHtml(f)}
            <em class="dbg-err" hidden></em>
          </label>`).join('')}
        <div class="dbg-form-err" hidden></div>
        <div class="dbg-actions">
          <button type="button" class="dbg-cancel">Cancel</button>
          <button type="submit" class="dbg-save">Save</button>
        </div>
      </form>
    </div>`;
  const close = () => { overlay.remove(); document.removeEventListener('keydown', esc); };
  const esc = e => { if (e.key === 'Escape') close(); };
  document.addEventListener('keydown', esc);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
  overlay.querySelector('.dbg-cancel').addEventListener('click', close);
  overlay.querySelector('form').addEventListener('submit', async e => {
    e.preventDefault();
    const payload = {};
    let parseError = false;
    fields.forEach(f => {
      const el = overlay.querySelector(`[name="${f.name}"]`);
      const fieldBox = overlay.querySelector(`.dbg-field[data-field="${f.name}"] .dbg-err`);
      fieldBox.hidden = true;
      if (f.type === 'csv'){
        payload[f.name] = el.value.split(',').map(s => s.trim()).filter(Boolean);
      } else if (f.type === 'json'){
        try { payload[f.name] = el.value.trim() ? JSON.parse(el.value) : (f.emptyValue ?? {}); }
        catch { fieldBox.textContent = 'Invalid JSON.'; fieldBox.hidden = false; parseError = true; }
      } else if (f.type === 'number'){
        payload[f.name] = el.value === '' ? null : Number(el.value);
      } else {
        payload[f.name] = el.value;
      }
    });
    if (parseError) return;
    try {
      await onSave(payload);
      close();
    } catch (err) {
      const errors = err && err.errors ? err.errors : { __all__: ['Save failed.'] };
      Object.entries(errors).forEach(([field, msgs]) => {
        const box = overlay.querySelector(`.dbg-field[data-field="${field}"] .dbg-err`)
                 || overlay.querySelector('.dbg-form-err');
        box.textContent = Array.isArray(msgs) ? msgs.join(' ') : String(msgs);
        box.hidden = false;
      });
    }
  });
  document.body.appendChild(overlay);
}
```

- [ ] **Step 3: Add debug CSS**

In the `<style>` block (append near the existing modal styles), add:

```css
/* ---------- Debug mode ---------- */
#debugRibbon{position:fixed;top:10px;right:10px;z-index:9999;background:#f59e0b;color:#1c1400;
  font:700 11px/1 var(--mono,monospace);letter-spacing:.12em;padding:6px 10px;border-radius:6px;
  pointer-events:none;}
.dbg-overlay{position:fixed;inset:0;z-index:9998;background:rgba(10,8,18,.55);backdrop-filter:blur(6px);
  display:flex;align-items:center;justify-content:center;padding:20px;}
.dbg-modal{background:var(--card,#17141f);color:inherit;border:1px solid #f59e0b55;border-radius:14px;
  padding:22px;width:min(560px,100%);max-height:85vh;overflow-y:auto;}
.dbg-modal h3{margin:0 0 14px;font-size:1.05rem;}
.dbg-field{display:block;margin-bottom:10px;font-size:.85rem;}
.dbg-field span{display:block;margin-bottom:4px;opacity:.75;}
.dbg-field input,.dbg-field textarea,.dbg-field select{width:100%;box-sizing:border-box;
  background:rgba(127,127,127,.08);color:inherit;border:1px solid rgba(127,127,127,.25);
  border-radius:8px;padding:8px 10px;font:inherit;}
.dbg-err,.dbg-form-err{color:#f87171;font-style:normal;font-size:.78rem;display:block;margin-top:3px;}
.dbg-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:16px;}
.dbg-actions button{padding:8px 16px;border-radius:8px;border:1px solid rgba(127,127,127,.3);
  background:transparent;color:inherit;cursor:pointer;font:inherit;}
.dbg-actions .dbg-save{background:#f59e0b;border-color:#f59e0b;color:#1c1400;font-weight:700;}
.dbg-ctl{display:none;}
body.debug-on .dbg-ctl{display:inline-flex;align-items:center;gap:4px;}
.dbg-ctl button{border:1px solid #f59e0b66;background:#f59e0b18;color:#f59e0b;border-radius:6px;
  padding:2px 7px;font-size:.72rem;cursor:pointer;line-height:1.4;}
.dbg-ctl button:hover{background:#f59e0b33;}
body.debug-on .dbg-add-card{display:flex;align-items:center;justify-content:center;
  border:2px dashed #f59e0b66;border-radius:14px;color:#f59e0b;cursor:pointer;
  font-weight:700;min-height:120px;}
.dbg-add-card{display:none;}
```

- [ ] **Step 4: Add the Debug toggle to the profile menu**

Find the profile dropdown markup/renderer (search `vocab-master.html` for `Sign out` — the toggle goes in the same menu, just above the sign-out item). Add, rendered only when `state.auth.isStaff`:

```html
<button class="pm-item" id="debugToggle" type="button">Debug mode: Off</button>
```

(match the menu's existing item classes — reuse whatever class the sign-out button uses instead of `pm-item` if it differs) and wire it where the menu's other items get their listeners:

```js
const dbgBtn = document.getElementById('debugToggle');
if (dbgBtn){
  const label = () => `Debug mode: ${debugOn() ? 'On' : 'Off'}`;
  dbgBtn.textContent = label();
  dbgBtn.addEventListener('click', () => {
    sessionStorage.setItem('debugMode', debugOn() ? '0' : '1');
    dbgBtn.textContent = label();
    applyDebugMode();
  });
}
```

Also call `applyDebugMode()` once right after the session hydration completes (after the `state.auth` assignment block at ~2958), so the ribbon appears on reload while the flag is set.

- [ ] **Step 5: Manually verify**

```powershell
Start-Process cmd -ArgumentList @("/k", "python manage.py runserver") -WorkingDirectory "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry\Python\Django" -WindowStyle Normal
```

- Log in at http://127.0.0.1:8000/ as `ieltsadminaccount@gmail.com` → profile menu shows "Debug mode: Off".
- Click it → "On", amber DEBUG ribbon appears top-right; toggle off → ribbon gone.
- Log in as a regular account (or log out) → no toggle, and `sessionStorage.setItem('debugMode','1')` in the console still shows no ribbon (isStaff gate).
- In the console: `openDebugModal({title:'Test', fields:[{name:'x', label:'X', type:'text'}], onSave: async p => console.log(p)})` → modal renders, Escape closes it.

- [ ] **Step 6: Commit**

```bash
git add vocab-master.html
git commit -m "feat(debug): staff-only debug toggle, ribbon, fetch helper and modal shell"
```

---

### Task 8: Vocab debug controls (categories + words)

**Files:**
- Modify: `vocab-master.html` (anchors: `loadVocab()` at ~5000, category-card renderer — find where category cards' HTML is built, search for the category card class used on the home grid; word list/page renderer + `openWordModal` at ~6187)

**Interfaces:**
- Consumes: `debugOn()`, `debugFetch`, `openDebugModal`, `debugConfirm` (Task 7); `POST/PATCH/DELETE /api/words[...]`, `/api/categories[...]` (Tasks 2–3).
- Produces: `DEBUG_FORMS.word` and `DEBUG_FORMS.category` field configs; `debugEditWord(word)`, `debugAddWord()`, `debugDeleteWord(word)`, and category equivalents.

- [ ] **Step 1: Keep database pks + raw fields available**

In `loadVocab()` (~5000–5036): the SPA maps API objects into its own shapes. Ensure the mapped objects keep what editing needs:
- mapped `CATEGORIES` entries keep `pk: c.id` plus raw `slug`, `icon`, `order`, and the pks needed to rebuild a form (`cefr_level` pk isn't in the read response — the category modal instead selects CEFR by code from the loaded CEFR list, mapping code→pk via the `/api/cefr-levels/` data; store that list in a module-level `CEFR_LEVELS_RAW` when `loadVocab` fetches it, or add a fetch if it doesn't already).
- mapped word entries keep `pk: w.id`, `category_id`, and raw `synonyms`/`antonyms`/`order`.
- Colors: the category form needs a color pk; add a one-time `fetch` of color options is NOT available via API — instead the category modal omits `color` on PATCH… **it can't; the form requires all fields.** Resolution: extend the categories read response (in `api/views.py`) with `'cefr_level_id': c.cefr_level_id, 'color_id': c.color_id` so edit payloads can echo them back, and give the modal's `color`/`cefr_level` selects options built from values present on loaded categories (`[...new Map(CATEGORIES.map(c => [c.color_id, c])).values()]` with label = the category's color swatch hex). Update `tests/test_vocab_api.py` if it asserts exact category keys.

- [ ] **Step 2: Define the vocab form configs**

Next to `DEBUG_FORMS` — add below the debug core from Task 7:

```js
const DEBUG_FORMS = {
  word: [
    { name: 'word',       label: 'Word',        type: 'text' },
    { name: 'pos',        label: 'Part of speech', type: 'text' },
    { name: 'definition', label: 'Definition',  type: 'textarea' },
    { name: 'example',    label: 'Example',     type: 'textarea' },
    { name: 'gap',        label: 'Gap sentence', type: 'textarea' },
    { name: 'synonyms',   label: 'Synonyms (comma-separated)', type: 'csv' },
    { name: 'antonyms',   label: 'Antonyms (comma-separated)', type: 'csv' },
    { name: 'category',   label: 'Category',    type: 'select', options: () => CATEGORIES.map(c => ({ value: c.pk, label: c.name })) },
    { name: 'cefr_level', label: 'CEFR level',  type: 'select', options: () => CEFR_LEVELS_RAW.map(l => ({ value: l.id, label: l.code })) },
    { name: 'order',      label: 'Order',       type: 'number' },
  ],
  category: [
    { name: 'slug',       label: 'Slug',  type: 'text' },
    { name: 'name',       label: 'Name',  type: 'text' },
    { name: 'icon',       label: 'Icon (emoji)', type: 'text' },
    { name: 'cefr_level', label: 'CEFR level', type: 'select', options: () => CEFR_LEVELS_RAW.map(l => ({ value: l.id, label: l.code })) },
    { name: 'color',      label: 'Color', type: 'select', options: () => debugColorOptions() },
    { name: 'order',      label: 'Order', type: 'number' },
  ],
};

function debugColorOptions(){
  const seen = new Map();
  CATEGORIES.forEach(c => { if (c.color_id != null && !seen.has(c.color_id)) seen.set(c.color_id, c.bg_hex || '#888'); });
  return [...seen.entries()].map(([value, hex]) => ({ value, label: hex }));
}

async function debugRefreshVocab(){
  await loadVocab();
  renderCurrentPage();   // use the SPA's existing "re-render active page" call — if none exists, call the renderer for the page currently visible (home / category / word page)
}

function debugSaveWord(existing){
  openDebugModal({
    title: existing ? `Edit word: ${existing.w}` : 'Add word',
    fields: DEBUG_FORMS.word,
    initial: existing ? {
      word: existing.w, pos: existing.pos, definition: existing.def,
      example: existing.ex, gap: existing.gap, synonyms: existing.syn || [],
      antonyms: existing.ant || [], category: existing.category_id,
      cefr_level: (CEFR_LEVELS_RAW.find(l => l.code === existing.cefr) || {}).id,
      order: existing.order,
    } : { synonyms: [], antonyms: [], order: 0 },
    onSave: async payload => {
      if (existing) await debugFetch(`/api/words/${existing.pk}/`, 'PATCH', payload);
      else          await debugFetch('/api/words/', 'POST', payload);
      await debugRefreshVocab();
    },
  });
}

async function debugDeleteWord(word){
  if (!await debugConfirm(`Delete "${word.w}"? This cannot be undone.`)) return;
  await debugFetch(`/api/words/${word.pk}/`, 'DELETE');
  await debugRefreshVocab();
}

function debugSaveCategory(existing){
  openDebugModal({
    title: existing ? `Edit category: ${existing.name}` : 'Add category',
    fields: DEBUG_FORMS.category,
    initial: existing ? {
      slug: existing.slug, name: existing.name, icon: existing.icon,
      cefr_level: existing.cefr_level_id, color: existing.color_id, order: existing.order,
    } : { order: CATEGORIES.length },
    onSave: async payload => {
      if (existing) await debugFetch(`/api/categories/${existing.pk}/`, 'PATCH', payload);
      else          await debugFetch('/api/categories/', 'POST', payload);
      await debugRefreshVocab();
    },
  });
}

async function debugDeleteCategory(cat){
  if (!await debugConfirm(`Delete category "${cat.name}" and ALL its words? This cannot be undone.`)) return;
  await debugFetch(`/api/categories/${cat.pk}/`, 'DELETE');
  await debugRefreshVocab();
}
```

Adjust the `existing.*` property names to the SPA's actual mapped word/category field names (check the mapping in `loadVocab()` — e.g. words may use `w`/`def`/`ex`/`syn`/`ant` or full names; use what the mapping produces).

- [ ] **Step 3: Inject controls into the renderers**

- **Category cards** (home + category browse): in the function that builds each category card's HTML, append inside the card (only when `debugOn()`):

```js
${debugOn() && cat.pk ? `
  <span class="dbg-ctl" onclick="event.stopPropagation()">
    <button onclick="debugSaveCategory(CATEGORIES.find(c=>c.pk===${cat.pk}))">✎</button>
    <button onclick="debugDeleteCategory(CATEGORIES.find(c=>c.pk===${cat.pk}))">✕</button>
  </span>` : ''}
```

(`cat.pk` guard skips the synthetic CEFR pseudo-categories from `CEFR_CATEGORIES`.) After each section's cards, append one add-card: `<div class="dbg-add-card" onclick="debugSaveCategory()">+ Add category</div>`.

- **Word page rows and word detail modal** (`openWordModal` ~6187): same pattern — a `.dbg-ctl` span with ✎/✕ per word row, and in the modal footer ✎ "Edit" / ✕ "Delete" buttons calling `debugSaveWord(word)` / `debugDeleteWord(word)`. Add a "+ Add word" button in the Word page browse bar (`debugOn()` only), calling `debugSaveWord()`.

If the renderer attaches events via `addEventListener` rather than inline `onclick`, follow the surrounding style.

- [ ] **Step 4: Manually verify**

With the server running, logged in as the admin, Debug on:
- Edit a category name → card updates in place after save.
- Add a category → appears at the end; delete it → confirm dialog, then gone.
- Edit a word's definition from the word modal → reopens with new text.
- Add + delete a word from the Word page.
- Save with an empty Word field → inline red error under the field, modal stays open.
- Toggle Debug off → all ✎/✕/+ controls disappear. Regular user sees none.
- `python -m pytest tests -q` still green.

- [ ] **Step 5: Commit**

```bash
git add vocab-master.html api/views.py tests/test_vocab_api.py
git commit -m "feat(debug): inline add/edit/delete for categories and words"
```

---

### Task 9: Grammar debug controls (topics, blocks, questions)

**Files:**
- Modify: `vocab-master.html` (anchors: `loadGrammar()` ~3400, `renderGrammarHome()` ~3417, `openGrammarTopic(topic)` ~3535)

**Interfaces:**
- Consumes: Task 7 helpers; grammar ids/order from Task 4; write endpoints from Tasks 5–6.
- Produces: `DEBUG_FORMS.topic/block/question`; `debugSaveTopic/debugDeleteTopic/debugSaveBlock/debugDeleteBlock/debugSaveQuestion/debugDeleteQuestion`.

- [ ] **Step 1: Form configs + actions**

Add below the vocab debug functions:

```js
DEBUG_FORMS.topic = [
  { name: 'slug',       label: 'Slug', type: 'text' },
  { name: 'title',      label: 'Title', type: 'text' },
  { name: 'tag',        label: 'Tag (section)', type: 'text' },
  { name: 'cefr_label', label: 'CEFR label (e.g. B1+)', type: 'text' },
  { name: 'blurb',      label: 'Blurb', type: 'textarea' },
  { name: 'stage',      label: 'Stage', type: 'select', options: () => [
      { value: 'beginner', label: 'Basic' },
      { value: 'independent', label: 'Intermediate' },
      { value: 'expert', label: 'Advanced' }] },
  { name: 'order',      label: 'Order', type: 'number' },
];
DEBUG_FORMS.block = [
  { name: 'type',  label: 'Type', type: 'select', options: () => [
      'intro', 'rule', 'table', 'examples', 'tip'].map(v => ({ value: v, label: v })) },
  { name: 'title', label: 'Title', type: 'text' },
  { name: 'body',  label: 'Body', type: 'textarea' },
  { name: 'data',  label: 'Data (JSON — table: {"head":[],"rows":[]}; examples: {"items":[{"en":"","note":""}]})', type: 'json' },
  { name: 'order', label: 'Order', type: 'number' },
];
DEBUG_FORMS.question = [
  { name: 'qtype',   label: 'Type', type: 'select', options: () => [
      { value: 'mcq', label: 'Multiple choice' },
      { value: 'gap', label: 'Fill the gap' },
      { value: 'transform', label: 'Transformation' }] },
  { name: 'prompt',  label: 'Prompt', type: 'textarea' },
  { name: 'options', label: 'Options (JSON list, mcq only)', type: 'json', emptyValue: [] },
  { name: 'answers', label: 'Answers (mcq: [index] — gap/transform: ["accepted"])', type: 'json', emptyValue: [] },
  { name: 'why',     label: 'Why (explanation)', type: 'textarea' },
  { name: 'order',   label: 'Order', type: 'number' },
];

async function debugRefreshGrammar(topicId){
  await loadGrammar();
  if (topicId != null){
    const topic = GRAMMAR_DATA.flatMap(s => s.topics).find(t => t.id === topicId);
    if (topic){ openGrammarTopic(topic); return; }
  }
  renderGrammarHome();
}
```

(`GRAMMAR_DATA` = whatever module variable `loadGrammar()` stores the `/api/grammar/` response in — use its real name.) Then the six actions:

```js
function debugSaveTopic(existing){
  openDebugModal({
    title: existing ? `Edit topic: ${existing.title}` : 'Add grammar topic',
    fields: DEBUG_FORMS.topic,
    initial: existing ? {
      slug: existing.slug, title: existing.title, tag: existing.tag,
      cefr_label: existing.cefr, blurb: existing.blurb,
      stage: existing.stage, order: existing.order,
    } : { order: 0 },
    onSave: async payload => {
      if (existing) await debugFetch(`/api/grammar/topics/${existing.id}/`, 'PATCH', payload);
      else          await debugFetch('/api/grammar/topics/', 'POST', payload);
      await debugRefreshGrammar();
    },
  });
}

async function debugDeleteTopic(topic){
  if (!await debugConfirm(
    `Delete topic "${topic.title}"? Its lesson blocks and questions are deleted too. This cannot be undone.`)) return;
  await debugFetch(`/api/grammar/topics/${topic.id}/`, 'DELETE');
  await debugRefreshGrammar();
}

function debugSaveBlock(topicId, existing){
  openDebugModal({
    title: existing ? 'Edit lesson block' : 'Add lesson block',
    fields: DEBUG_FORMS.block,
    initial: existing ? {
      type: existing.type, title: existing.title, body: existing.body,
      data: existing.data, order: existing.order,
    } : { data: {}, order: 0 },
    onSave: async payload => {
      if (existing) await debugFetch(`/api/grammar/blocks/${existing.id}/`, 'PATCH', payload);
      else          await debugFetch('/api/grammar/blocks/', 'POST', { ...payload, topic: topicId });
      await debugRefreshGrammar(topicId);
    },
  });
}

async function debugDeleteBlock(topicId, block){
  if (!await debugConfirm('Delete this lesson block? This cannot be undone.')) return;
  await debugFetch(`/api/grammar/blocks/${block.id}/`, 'DELETE');
  await debugRefreshGrammar(topicId);
}

function debugSaveQuestion(topicId, existing){
  openDebugModal({
    title: existing ? 'Edit question' : 'Add question',
    fields: DEBUG_FORMS.question,
    initial: existing ? {
      qtype: existing.qtype, prompt: existing.prompt, options: existing.options,
      answers: existing.answers, why: existing.why, order: existing.order,
    } : { options: [], answers: [], order: 0 },
    onSave: async payload => {
      if (existing) await debugFetch(`/api/grammar/questions/${existing.id}/`, 'PATCH', payload);
      else          await debugFetch('/api/grammar/questions/', 'POST', { ...payload, topic: topicId });
      await debugRefreshGrammar(topicId);
    },
  });
}

async function debugDeleteQuestion(topicId, q){
  if (!await debugConfirm('Delete this question? This cannot be undone.')) return;
  await debugFetch(`/api/grammar/questions/${q.id}/`, 'DELETE');
  await debugRefreshGrammar(topicId);
}
```

Note the topic edit `initial` uses `existing.cefr` (the read API's key for `cefr_label`) and `existing.stage` — stage isn't on the topic dict in the read response (topics are grouped by stage), so when rendering controls pass the enclosing stage group's `id` along, e.g. `debugSaveTopic({ ...topic, stage: stageId })`.

- [ ] **Step 2: Inject controls**

- `renderGrammarHome()` (~3417): ✎/✕ `.dbg-ctl` on each topic card (guard `event.stopPropagation()` so the card's open-topic click doesn't fire) + one `+ Add topic` dbg-add-card per section.
- `openGrammarTopic()` (~3535): per lesson block, a `.dbg-ctl` with ✎/✕ (positioned top-right of the block container); after the last block a `+ Add block` button. Below the lesson (before/near the quiz start button), when `debugOn()`, render a "Manage questions" list: one row per question (`prompt` truncated to ~60 chars) with ✎/✕, plus `+ Add question`.

- [ ] **Step 3: Manually verify**

Debug on, Grammar tab:
- Edit a topic's blurb → card refreshes.
- Add a topic (fill all fields, pick a stage) → appears in the right section. Note from the project docs: a brand-new slug lands in a tag-named fallback section unless added to `GRAMMAR_SECTIONS` in the code — expected, not a bug.
- Open a topic → edit a rule block's body → lesson re-renders with the change.
- Add a table block with bad JSON (`{"rows": []}` only) → 400 error shown in the modal.
- Add an MCQ with 3 options → error under Options; with 4 options + `[1]` answers → saves.
- Delete the test topic → confirm mentions cascade; its blocks/questions gone (check `/api/grammar/`).
- Quiz still runs normally with Debug off.

- [ ] **Step 4: Commit**

```bash
git add vocab-master.html
git commit -m "feat(debug): inline add/edit/delete for grammar topics, blocks and questions"
```

---

### Task 10: Full verification pass

**Files:**
- None new (fixes only if something fails)

- [ ] **Step 1: Full test suite**

Run: `python -m pytest tests -q`
Expected: all pass (42 original + ~20 new).

- [ ] **Step 2: End-to-end click-through**

Server running; three scenarios:
1. **Anonymous:** no toggle, no controls; `fetch('/api/words/', {method:'POST'})` from console → 403.
2. **Regular user (Pichu):** same as anonymous plus normal site works.
3. **Admin:** full Task 8 + Task 9 verification lists pass; Debug survives navigating between tabs (sessionStorage) but a fresh browser session starts Off.

Check both light and dark themes render the ribbon, controls, and modal legibly.

- [ ] **Step 3: Update project memory + commit any fixes**

Update the VocabLarry memory file's feature list with the debug-mode summary (endpoints, toggle location, sessionStorage key). Commit any verification fixes:

```bash
git add -A
git commit -m "fix(debug): verification pass fixes"
```

Do NOT push — the user pushes to `elw` when ready.
