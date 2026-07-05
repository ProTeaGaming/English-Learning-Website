# Grammar Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Grammar under-construction placeholder in the LexiLoop Django product with a database-backed grammar curriculum: 36 topics across 3 CEFR stages, each with a lesson page and a 10-question quiz, editable via the staff dashboard, with localStorage progress tracking.

**Architecture:** Models live in the `vocab` app, a read-only nested JSON endpoint in the `api` app, staff CRUD in the `dashboard` app (mirroring the existing Words pattern), and a `grammar-content.json` seed file loaded by an idempotent `import_grammar` management command. The SPA (`vocab-master.html`) fetches `/api/grammar/` once per session and renders home/lesson/quiz views entirely client-side.

**Tech Stack:** Django 5 + SQLite, pytest-django (with pytest-mock for MFA mocking), vanilla JS + GSAP in a single-file SPA, Bootstrap 5 dashboard templates.

**Spec:** `docs/superpowers/specs/2026-07-05-grammar-section-design.md`

## Global Constraints

- All Django commands run from `D:\IT RELATED\CLAUDE BOMBASTIC AI\ielts-vocab-master\Python\Django` (PowerShell).
- Tests: `python -m pytest <file> -v`. The full suite must stay green: `python -m pytest`.
- Git: commit after every task. Push only to `elw` remote (`git push elw main`) and only if asked — NEVER push to `origin`.
- Django product only. Do not touch `Python/Flask/`, `PHP/`, or `React-Native/` files.
- UI: no emoji — icons come from the inline SVG sprite (`#i-*` ids) already in `vocab-master.html`. LexiLoop luxury/editorial design language; reuse existing CSS classes wherever possible.
- Stage ids are exactly `beginner`, `independent`, `expert`. CEFR labels use an en-dash: `A1–A2`, `B1–B2`, `C1–C2`.
- localStorage progress key is exactly `grammarProgress`; pass threshold is 80%.
- Dashboard views are `@role_required('staff')`; dashboard tests must mock MFA: `mocker.patch('allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled', return_value=True)`.
- `vocab-master.html` is ~5,000 lines. Anchor edits on unique code snippets, not line numbers.

---

### Task 1: Grammar models + migration

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab/models.py` (append at end)
- Create: `ielts-vocab-master/Python/Django/vocab/migrations/XXXX_grammartopic_grammarlessonblock_grammarquestion.py` (generated)
- Test: `ielts-vocab-master/Python/Django/tests/test_grammar_models.py`

**Interfaces:**
- Consumes: nothing new (existing `django.db.models`).
- Produces: `GrammarTopic(slug, title, tag, cefr_label, blurb, stage, order)` with `STAGES` choices; `GrammarLessonBlock(topic FK related_name='blocks', type, title, body, data, order)` with `TYPES` choices; `GrammarQuestion(topic FK related_name='questions', qtype, prompt, options, answers, why, order)` with `QTYPES` choices. All three ordered by `['order']`. Tasks 2–4 import these from `vocab.models`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_grammar_models.py`:

```python
import pytest
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.mark.django_db
def test_topic_str_and_ordering():
    t2 = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=1,
    )
    t1 = GrammarTopic.objects.create(
        slug='word-forms', title='Word Forms', tag='Word Building',
        cefr_label='A1–A2', blurb='Noun, verb, adjective, adverb.',
        stage='beginner', order=0,
    )
    assert str(t2) == 'Articles (a/an/the)'
    assert list(GrammarTopic.objects.all()) == [t1, t2]


@pytest.mark.django_db
def test_blocks_and_questions_cascade_and_order():
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='x', stage='beginner', order=0,
    )
    b2 = GrammarLessonBlock.objects.create(topic=t, type='rule', title='Form', body='<p>a + consonant sound</p>', order=1)
    b1 = GrammarLessonBlock.objects.create(topic=t, type='intro', body='<p>Articles come before nouns.</p>', order=0)
    q = GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She is ___ engineer.',
        options=['a', 'an', 'the', '(no article)'], answers=[1],
        why='"Engineer" starts with a vowel sound.', order=0,
    )
    assert list(t.blocks.all()) == [b1, b2]
    assert list(t.questions.all()) == [q]
    assert q.options[1] == 'an'
    assert q.answers == [1]
    t.delete()
    assert GrammarLessonBlock.objects.count() == 0
    assert GrammarQuestion.objects.count() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grammar_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'GrammarTopic' from 'vocab.models'`

- [ ] **Step 3: Add the models**

Append to `vocab/models.py`:

```python
class GrammarTopic(models.Model):
    STAGES = [
        ('beginner', 'Beginner'),
        ('independent', 'Independent'),
        ('expert', 'Expert'),
    ]
    slug       = models.SlugField(max_length=100, unique=True)
    title      = models.CharField(max_length=200)
    tag        = models.CharField(max_length=50)
    cefr_label = models.CharField(max_length=10)
    blurb      = models.CharField(max_length=300)
    stage      = models.CharField(max_length=12, choices=STAGES)
    order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class GrammarLessonBlock(models.Model):
    TYPES = [
        ('intro', 'Intro'),
        ('rule', 'Rule'),
        ('table', 'Table'),
        ('examples', 'Examples'),
        ('tip', 'Tip'),
    ]
    topic = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='blocks')
    type  = models.CharField(max_length=10, choices=TYPES)
    title = models.CharField(max_length=200, blank=True)
    body  = models.TextField(blank=True)
    data  = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.topic.slug} · {self.type} #{self.order}'


class GrammarQuestion(models.Model):
    QTYPES = [
        ('mcq', 'Multiple choice'),
        ('gap', 'Fill the gap'),
        ('transform', 'Transformation'),
    ]
    topic   = models.ForeignKey(GrammarTopic, on_delete=models.CASCADE, related_name='questions')
    qtype   = models.CharField(max_length=10, choices=QTYPES)
    prompt  = models.TextField()
    options = models.JSONField(default=list, blank=True)
    answers = models.JSONField(default=list)
    why     = models.TextField()
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.topic.slug} · {self.qtype} #{self.order}'
```

- [ ] **Step 4: Make and apply the migration**

Run: `python manage.py makemigrations vocab`
Expected: `Migrations for 'vocab': ... Create model GrammarTopic ... GrammarLessonBlock ... GrammarQuestion`
Run: `python manage.py migrate`
Expected: `Applying vocab.XXXX... OK`

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_grammar_models.py -v`
Expected: 2 passed
Run: `python -m pytest`
Expected: all pass (no regressions)

- [ ] **Step 6: Commit**

```powershell
git add vocab/models.py vocab/migrations/ tests/test_grammar_models.py
git commit -m "feat(grammar): add GrammarTopic, GrammarLessonBlock, GrammarQuestion models"
```

---

### Task 2: `/api/grammar/` endpoint

**Files:**
- Modify: `ielts-vocab-master/Python/Django/api/views.py` (append view)
- Modify: `ielts-vocab-master/Python/Django/api/urls.py` (add route)
- Test: `ielts-vocab-master/Python/Django/tests/test_grammar_api.py`

**Interfaces:**
- Consumes: `GrammarTopic` (with `.blocks`, `.questions`) from Task 1.
- Produces: `GET /api/grammar/` → JSON list of exactly 3 stage objects `{id, name, cefr, topics: [{slug, title, tag, cefr, blurb, lesson: [{type, title, body, data}], quiz: [{qtype, prompt, options, answers, why}]}]}` in order beginner, independent, expert. Tasks 8–10 consume this shape.

- [ ] **Step 1: Write the failing test**

Create `tests/test_grammar_api.py`:

```python
import json
import pytest
from django.test import Client
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


@pytest.fixture
def grammar_data(db):
    t = GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(topic=t, type='intro', body='<p>Articles come before nouns.</p>', order=0)
    GrammarLessonBlock.objects.create(
        topic=t, type='table', title='Forms',
        data={'head': ['Article', 'Use'], 'rows': [['a', 'consonant sound']]}, order=1,
    )
    GrammarQuestion.objects.create(
        topic=t, qtype='mcq', prompt='She studies at ___ university in London.',
        options=['a', 'an', 'the', '(no article)'], answers=[0],
        why='"University" starts with a /j/ (consonant) sound, so we use "a".', order=0,
    )
    return t


@pytest.mark.django_db
def test_grammar_endpoint_nests_stages_topics_blocks_questions(grammar_data):
    r = Client().get('/api/grammar/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert [s['id'] for s in data] == ['beginner', 'independent', 'expert']
    beginner = data[0]
    assert beginner['name'] == 'Beginner'
    assert beginner['cefr'] == 'A1–A2'
    topic = beginner['topics'][0]
    assert topic['slug'] == 'articles'
    assert topic['cefr'] == 'A1–A2'
    assert topic['lesson'][0]['type'] == 'intro'
    assert topic['lesson'][1]['data']['head'] == ['Article', 'Use']
    assert topic['quiz'][0]['options'] == ['a', 'an', 'the', '(no article)']
    assert topic['quiz'][0]['answers'] == [0]
    assert data[1]['topics'] == []
    assert data[2]['topics'] == []


@pytest.mark.django_db
def test_grammar_endpoint_avoids_n_plus_one(grammar_data, django_assert_num_queries):
    with django_assert_num_queries(3):  # topics + prefetched blocks + prefetched questions
        Client().get('/api/grammar/')


@pytest.mark.django_db
def test_grammar_endpoint_rejects_post(grammar_data):
    r = Client().post('/api/grammar/')
    assert r.status_code == 405
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grammar_api.py -v`
Expected: FAIL — 404 on `/api/grammar/` (route missing)

- [ ] **Step 3: Add view and route**

In `api/views.py`, change the import line to include the grammar models and append the view:

```python
from vocab.models import CEFRLevel, Category, Word, GrammarTopic
```

```python
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
```

In `api/urls.py` add to `urlpatterns`:

```python
    path('grammar/', views.grammar, name='api_grammar'),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_grammar_api.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```powershell
git add api/views.py api/urls.py tests/test_grammar_api.py
git commit -m "feat(grammar): add /api/grammar/ nested read endpoint"
```

---

### Task 3: `import_grammar` management command

**Files:**
- Create: `ielts-vocab-master/Python/Django/vocab/management/commands/import_grammar.py`
- Test: `ielts-vocab-master/Python/Django/tests/test_import_grammar.py`

**Interfaces:**
- Consumes: the three models from Task 1.
- Produces: `python manage.py import_grammar [--file PATH]` — reads a JSON array of topic objects (schema below), upserts topics by `slug` (order = array index), and fully replaces each topic's blocks and questions. Default file: `<Django root>/grammar-content.json` (created in Task 5). Tasks 5–7 rely on `--file`-less invocation; tests use `--file`.

**Seed JSON schema (one array element per topic):**

```json
{
  "slug": "articles",
  "stage": "beginner",
  "title": "Articles (a/an/the)",
  "tag": "Determiners",
  "cefr": "A1–A2",
  "blurb": "One-line card teaser.",
  "lesson": [
    {"type": "intro", "body": "<p>HTML…</p>"},
    {"type": "rule", "title": "Form", "body": "<p>HTML…</p>"},
    {"type": "table", "title": "Overview", "data": {"head": ["…"], "rows": [["…"]]}},
    {"type": "examples", "data": {"items": [{"en": "Sentence.", "note": "Why it works."}]}},
    {"type": "tip", "body": "<p>IELTS tip HTML…</p>"}
  ],
  "quiz": [
    {"qtype": "mcq", "prompt": "…", "options": ["A", "B", "C", "D"], "answers": [0], "why": "…"},
    {"qtype": "gap", "prompt": "Sentence with ___ marker.", "answers": ["accepted", "variants"], "why": "…"},
    {"qtype": "transform", "prompt": "Rewrite instruction + given sentence.", "answers": ["accepted variant"], "why": "…"}
  ]
}
```

- [ ] **Step 1: Write the failing test**

Create `tests/test_import_grammar.py`:

```python
import json
import pytest
from django.core.management import call_command
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion

TOPIC = {
    'slug': 'articles', 'stage': 'beginner', 'title': 'Articles (a/an/the)',
    'tag': 'Determiners', 'cefr': 'A1–A2', 'blurb': 'When to use a, an and the.',
    'lesson': [
        {'type': 'intro', 'body': '<p>Articles come before nouns.</p>'},
        {'type': 'table', 'title': 'Forms', 'data': {'head': ['Article'], 'rows': [['a']]}},
    ],
    'quiz': [
        {'qtype': 'mcq', 'prompt': 'She is ___ engineer.',
         'options': ['a', 'an', 'the', '(no article)'], 'answers': [1],
         'why': '"Engineer" starts with a vowel sound.'},
        {'qtype': 'gap', 'prompt': 'I saw ___ moon last night.', 'answers': ['the'],
         'why': 'There is only one moon — unique things take "the".'},
    ],
}


@pytest.fixture
def seed_file(tmp_path):
    path = tmp_path / 'grammar.json'
    path.write_text(json.dumps([TOPIC]), encoding='utf-8')
    return path


@pytest.mark.django_db
def test_import_creates_topic_blocks_questions(seed_file):
    call_command('import_grammar', file=str(seed_file))
    t = GrammarTopic.objects.get(slug='articles')
    assert t.stage == 'beginner'
    assert t.cefr_label == 'A1–A2'
    assert t.blocks.count() == 2
    assert t.questions.count() == 2
    assert t.questions.last().answers == ['the']


@pytest.mark.django_db
def test_import_is_idempotent_and_replaces_children(seed_file, tmp_path):
    call_command('import_grammar', file=str(seed_file))
    call_command('import_grammar', file=str(seed_file))
    assert GrammarTopic.objects.count() == 1
    assert GrammarLessonBlock.objects.count() == 2
    assert GrammarQuestion.objects.count() == 2

    changed = dict(TOPIC, title='Articles!', quiz=TOPIC['quiz'][:1])
    path2 = tmp_path / 'grammar2.json'
    path2.write_text(json.dumps([changed]), encoding='utf-8')
    call_command('import_grammar', file=str(path2))
    t = GrammarTopic.objects.get(slug='articles')
    assert t.title == 'Articles!'
    assert t.questions.count() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_import_grammar.py -v`
Expected: FAIL with `CommandError: Unknown command: 'import_grammar'`

- [ ] **Step 3: Write the command**

Create `vocab/management/commands/import_grammar.py`:

```python
import json
import pathlib
from django.core.management.base import BaseCommand, CommandError
from vocab.models import GrammarTopic, GrammarLessonBlock, GrammarQuestion


class Command(BaseCommand):
    help = 'Seed grammar topics from grammar-content.json. Idempotent (upsert by slug).'

    def add_arguments(self, parser):
        parser.add_argument('--file', default=None,
                            help='Path to grammar JSON (default: <project root>/grammar-content.json)')

    def handle(self, *args, **options):
        path = pathlib.Path(options['file']) if options['file'] \
            else pathlib.Path(__file__).resolve().parents[3] / 'grammar-content.json'
        if not path.exists():
            raise CommandError(f'Grammar content file not found: {path}')
        topics = json.loads(path.read_text(encoding='utf-8'))

        for order, t in enumerate(topics):
            topic, _ = GrammarTopic.objects.update_or_create(
                slug=t['slug'],
                defaults={
                    'title': t['title'], 'tag': t['tag'], 'cefr_label': t['cefr'],
                    'blurb': t['blurb'], 'stage': t['stage'], 'order': order,
                },
            )
            topic.blocks.all().delete()
            for i, b in enumerate(t['lesson']):
                GrammarLessonBlock.objects.create(
                    topic=topic, type=b['type'], title=b.get('title', ''),
                    body=b.get('body', ''), data=b.get('data', {}), order=i,
                )
            topic.questions.all().delete()
            for i, q in enumerate(t['quiz']):
                GrammarQuestion.objects.create(
                    topic=topic, qtype=q['qtype'], prompt=q['prompt'],
                    options=q.get('options', []), answers=q['answers'],
                    why=q['why'], order=i,
                )

        self.stdout.write(self.style.SUCCESS(
            f'Done. Grammar topics: {GrammarTopic.objects.count()}, '
            f'blocks: {GrammarLessonBlock.objects.count()}, '
            f'questions: {GrammarQuestion.objects.count()}'
        ))
```

Note: `parents[3]` from `vocab/management/commands/import_grammar.py` resolves to the Django project root (`commands` → `management` → `vocab` → root).

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_import_grammar.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```powershell
git add vocab/management/commands/import_grammar.py tests/test_import_grammar.py
git commit -m "feat(grammar): add idempotent import_grammar seed command"
```

---

### Task 4: Dashboard CRUD for grammar

**Files:**
- Modify: `ielts-vocab-master/Python/Django/dashboard/forms.py` (append 3 forms)
- Modify: `ielts-vocab-master/Python/Django/dashboard/views.py` (append views; extend index context)
- Modify: `ielts-vocab-master/Python/Django/dashboard/urls.py` (add 12 routes)
- Modify: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/base.html` (nav link)
- Modify: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/index.html` (count card)
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/list.html`
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/form.html`
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/blocks.html`
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/block_form.html`
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/questions.html`
- Create: `ielts-vocab-master/Python/Django/dashboard/templates/dashboard/grammar/question_form.html`
- Test: `ielts-vocab-master/Python/Django/tests/test_dashboard_grammar.py`

**Interfaces:**
- Consumes: models from Task 1; `role_required` from `accounts.decorators`.
- Produces: URL names `dashboard_grammar_list/add/edit/delete`, `dashboard_grammar_blocks/block_add/block_edit/block_delete`, `dashboard_grammar_questions/question_add/question_edit/question_delete`; forms `GrammarTopicForm`, `GrammarLessonBlockForm`, `GrammarQuestionForm` with JSON shape validation. Nothing downstream consumes these — this is a leaf feature.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dashboard_grammar.py`:

```python
import pytest
from django.test import Client
from vocab.models import GrammarTopic, GrammarQuestion


@pytest.fixture
def staff_client(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    return c


@pytest.fixture
def topic(db):
    return GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1–A2', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )


@pytest.mark.django_db
def test_grammar_list_requires_staff(regular_user):
    c = Client()
    c.force_login(regular_user)
    assert c.get('/dashboard/grammar/').status_code == 403


@pytest.mark.django_db
def test_grammar_list_shows_topics_and_stage_filter(staff_client, topic):
    r = staff_client.get('/dashboard/grammar/')
    assert r.status_code == 200
    assert b'Articles (a/an/the)' in r.content
    r = staff_client.get('/dashboard/grammar/?stage=expert')
    assert b'Articles (a/an/the)' not in r.content


@pytest.mark.django_db
def test_topic_add_and_delete(staff_client):
    r = staff_client.post('/dashboard/grammar/add/', {
        'slug': 'passive-voice', 'title': 'Passive & Active Voice', 'tag': 'Voice',
        'cefr_label': 'B1–B2', 'blurb': 'Focus on the action, not the doer.',
        'stage': 'independent', 'order': 13,
    })
    assert r.status_code == 302
    t = GrammarTopic.objects.get(slug='passive-voice')
    r = staff_client.post(f'/dashboard/grammar/{t.pk}/delete/')
    assert r.status_code == 302
    assert not GrammarTopic.objects.filter(slug='passive-voice').exists()


@pytest.mark.django_db
def test_question_add_valid_mcq(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'She is ___ engineer.',
        'options': '["a", "an", "the", "(no article)"]',
        'answers': '[1]', 'why': 'Vowel sound.', 'order': 0,
    })
    assert r.status_code == 302
    q = GrammarQuestion.objects.get(topic=topic)
    assert q.answers == [1]


@pytest.mark.django_db
def test_question_add_rejects_mcq_with_three_options(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'mcq', 'prompt': 'x', 'options': '["a", "b", "c"]',
        'answers': '[0]', 'why': 'x', 'order': 0,
    })
    assert r.status_code == 200  # re-rendered with errors
    assert b'exactly 4 options' in r.content
    assert GrammarQuestion.objects.count() == 0


@pytest.mark.django_db
def test_question_add_rejects_gap_without_string_answers(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/questions/add/', {
        'qtype': 'gap', 'prompt': 'I saw ___ moon.', 'options': '[]',
        'answers': '[1]', 'why': 'x', 'order': 0,
    })
    assert r.status_code == 200
    assert b'non-empty strings' in r.content


@pytest.mark.django_db
def test_block_add_rejects_table_without_head_rows(staff_client, topic):
    r = staff_client.post(f'/dashboard/grammar/{topic.pk}/blocks/add/', {
        'type': 'table', 'title': 'Forms', 'body': '', 'data': '{}', 'order': 0,
    })
    assert r.status_code == 200
    assert b'head' in r.content


@pytest.mark.django_db
def test_index_shows_grammar_count(staff_client, topic):
    r = staff_client.get('/dashboard/')
    assert b'Grammar topics' in r.content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_dashboard_grammar.py -v`
Expected: FAIL — 404s on `/dashboard/grammar/` routes; index missing "Grammar topics"

- [ ] **Step 3: Add forms**

In `dashboard/forms.py`, extend the models import and append:

```python
from vocab.models import Word, Category, Color, CEFRLevel, GrammarTopic, GrammarLessonBlock, GrammarQuestion
```

```python
class GrammarTopicForm(forms.ModelForm):
    class Meta:
        model = GrammarTopic
        fields = ['slug', 'title', 'tag', 'cefr_label', 'blurb', 'stage', 'order']
        widgets = {'blurb': forms.Textarea(attrs={'rows': 2})}


class GrammarLessonBlockForm(forms.ModelForm):
    class Meta:
        model = GrammarLessonBlock
        fields = ['type', 'title', 'body', 'data', 'order']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 5}),
            'data': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'table: {"head": [...], "rows": [[...]]} — examples: {"items": [{"en": "...", "note": "..."}]}',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        btype = cleaned.get('type')
        data  = cleaned.get('data') or {}
        if btype == 'table':
            if not isinstance(data.get('head'), list) or not isinstance(data.get('rows'), list):
                raise forms.ValidationError('Table blocks need data with "head" and "rows" lists.')
        elif btype == 'examples':
            items = data.get('items')
            if not isinstance(items, list) or not items:
                raise forms.ValidationError('Examples blocks need data {"items": [...]} with at least one item.')
        elif not cleaned.get('body'):
            raise forms.ValidationError('Intro, rule and tip blocks need body text.')
        return cleaned


class GrammarQuestionForm(forms.ModelForm):
    class Meta:
        model = GrammarQuestion
        fields = ['qtype', 'prompt', 'options', 'answers', 'why', 'order']
        widgets = {
            'prompt':  forms.Textarea(attrs={'rows': 2}),
            'why':     forms.Textarea(attrs={'rows': 2}),
            'options': forms.Textarea(attrs={'rows': 2, 'placeholder': '["opt A", "opt B", "opt C", "opt D"] (mcq only)'}),
            'answers': forms.Textarea(attrs={'rows': 2, 'placeholder': 'mcq: [1] (correct index) — gap/transform: ["accepted", "answers"]'}),
        }

    def clean(self):
        cleaned = super().clean()
        qtype   = cleaned.get('qtype')
        options = cleaned.get('options') or []
        answers = cleaned.get('answers')
        if qtype == 'mcq':
            if not isinstance(options, list) or len(options) != 4:
                self.add_error('options', 'MCQ questions need exactly 4 options.')
            elif (not isinstance(answers, list) or len(answers) != 1
                    or not isinstance(answers[0], int) or not 0 <= answers[0] <= 3):
                self.add_error('answers', 'MCQ answers must be [index] with index 0–3.')
        else:
            if (not isinstance(answers, list) or not answers
                    or not all(isinstance(a, str) and a.strip() for a in answers)):
                self.add_error('answers', 'Gap/transform answers must be a list of non-empty strings.')
        return cleaned
```

- [ ] **Step 4: Add views**

In `dashboard/views.py`, extend imports:

```python
from vocab.models import Word, Category, CEFRLevel, Color, GrammarTopic, GrammarLessonBlock, GrammarQuestion
from .forms import (WordForm, CategoryForm, ColorForm, CEFRForm, UserRoleForm,
                    GrammarTopicForm, GrammarLessonBlockForm, GrammarQuestionForm)
```

In `index`, add to `context`:

```python
        'grammar_count': GrammarTopic.objects.count(),
```

Append at the end of the file:

```python
# ── Grammar ─────────────────────────────────────────────────
@role_required('staff')
def grammar_topic_list(request):
    stage = request.GET.get('stage', '')
    qs = GrammarTopic.objects.order_by('order')
    if stage:
        qs = qs.filter(stage=stage)
    return render(request, 'dashboard/grammar/list.html', {
        'topics': qs, 'stages': GrammarTopic.STAGES, 'selected_stage': stage,
    })


@role_required('staff')
def grammar_topic_add(request):
    form = GrammarTopicForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Grammar topic added.')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def grammar_topic_edit(request, pk):
    topic = get_object_or_404(GrammarTopic, pk=pk)
    form = GrammarTopicForm(request.POST or None, instance=topic)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Grammar topic updated.')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/form.html', {'form': form, 'action': 'Edit', 'obj': topic})


@role_required('staff')
def grammar_topic_delete(request, pk):
    topic = get_object_or_404(GrammarTopic, pk=pk)
    if request.method == 'POST':
        topic.delete()
        messages.success(request, 'Grammar topic deleted (with its blocks and questions).')
        return redirect('dashboard_grammar_list')
    return render(request, 'dashboard/grammar/list.html', {
        'topics': GrammarTopic.objects.order_by('order'),
        'stages': GrammarTopic.STAGES, 'selected_stage': '',
        'confirm_delete': topic,
    })


@role_required('staff')
def grammar_block_list(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    return render(request, 'dashboard/grammar/blocks.html', {'topic': topic, 'blocks': topic.blocks.all()})


@role_required('staff')
def grammar_block_add(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    form = GrammarLessonBlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        block = form.save(commit=False)
        block.topic = topic
        block.save()
        messages.success(request, 'Lesson block added.')
        return redirect('dashboard_grammar_blocks', topic_pk=topic.pk)
    return render(request, 'dashboard/grammar/block_form.html', {'form': form, 'action': 'Add', 'topic': topic})


@role_required('staff')
def grammar_block_edit(request, pk):
    block = get_object_or_404(GrammarLessonBlock, pk=pk)
    form = GrammarLessonBlockForm(request.POST or None, instance=block)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Lesson block updated.')
        return redirect('dashboard_grammar_blocks', topic_pk=block.topic_id)
    return render(request, 'dashboard/grammar/block_form.html', {'form': form, 'action': 'Edit', 'topic': block.topic})


@role_required('staff')
def grammar_block_delete(request, pk):
    block = get_object_or_404(GrammarLessonBlock, pk=pk)
    topic_pk = block.topic_id
    if request.method == 'POST':
        block.delete()
        messages.success(request, 'Lesson block deleted.')
    return redirect('dashboard_grammar_blocks', topic_pk=topic_pk)


@role_required('staff')
def grammar_question_list(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    return render(request, 'dashboard/grammar/questions.html', {'topic': topic, 'questions': topic.questions.all()})


@role_required('staff')
def grammar_question_add(request, topic_pk):
    topic = get_object_or_404(GrammarTopic, pk=topic_pk)
    form = GrammarQuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.topic = topic
        question.save()
        messages.success(request, 'Question added.')
        return redirect('dashboard_grammar_questions', topic_pk=topic.pk)
    return render(request, 'dashboard/grammar/question_form.html', {'form': form, 'action': 'Add', 'topic': topic})


@role_required('staff')
def grammar_question_edit(request, pk):
    question = get_object_or_404(GrammarQuestion, pk=pk)
    form = GrammarQuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Question updated.')
        return redirect('dashboard_grammar_questions', topic_pk=question.topic_id)
    return render(request, 'dashboard/grammar/question_form.html', {'form': form, 'action': 'Edit', 'topic': question.topic})


@role_required('staff')
def grammar_question_delete(request, pk):
    question = get_object_or_404(GrammarQuestion, pk=pk)
    topic_pk = question.topic_id
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted.')
    return redirect('dashboard_grammar_questions', topic_pk=topic_pk)
```

- [ ] **Step 5: Add URLs**

In `dashboard/urls.py`, add to `urlpatterns`:

```python
    path('grammar/', views.grammar_topic_list, name='dashboard_grammar_list'),
    path('grammar/add/', views.grammar_topic_add, name='dashboard_grammar_add'),
    path('grammar/<int:pk>/edit/', views.grammar_topic_edit, name='dashboard_grammar_edit'),
    path('grammar/<int:pk>/delete/', views.grammar_topic_delete, name='dashboard_grammar_delete'),
    path('grammar/<int:topic_pk>/blocks/', views.grammar_block_list, name='dashboard_grammar_blocks'),
    path('grammar/<int:topic_pk>/blocks/add/', views.grammar_block_add, name='dashboard_grammar_block_add'),
    path('grammar/blocks/<int:pk>/edit/', views.grammar_block_edit, name='dashboard_grammar_block_edit'),
    path('grammar/blocks/<int:pk>/delete/', views.grammar_block_delete, name='dashboard_grammar_block_delete'),
    path('grammar/<int:topic_pk>/questions/', views.grammar_question_list, name='dashboard_grammar_questions'),
    path('grammar/<int:topic_pk>/questions/add/', views.grammar_question_add, name='dashboard_grammar_question_add'),
    path('grammar/questions/<int:pk>/edit/', views.grammar_question_edit, name='dashboard_grammar_question_edit'),
    path('grammar/questions/<int:pk>/delete/', views.grammar_question_delete, name='dashboard_grammar_question_delete'),
```

- [ ] **Step 6: Create templates**

`dashboard/templates/dashboard/grammar/list.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}Grammar{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h1>Grammar Topics</h1>
  <a href="{% url 'dashboard_grammar_add' %}" class="btn btn-success">+ Add Topic</a>
</div>

<form class="row g-2 mb-3" method="get">
  <div class="col-md-3">
    <select name="stage" class="form-select">
      <option value="">All stages</option>
      {% for value, label in stages %}
        <option value="{{ value }}" {% if selected_stage == value %}selected{% endif %}>{{ label }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-auto"><button class="btn btn-outline-secondary">Filter</button></div>
</form>

{% if confirm_delete %}
<div class="alert alert-danger">
  Delete <strong>{{ confirm_delete.title }}</strong> and all its blocks and questions?
  <form method="post" action="{% url 'dashboard_grammar_delete' confirm_delete.pk %}" class="d-inline">
    {% csrf_token %}<button class="btn btn-sm btn-danger ms-2">Yes, delete</button>
  </form>
  <a href="{% url 'dashboard_grammar_list' %}" class="btn btn-sm btn-secondary ms-1">Cancel</a>
</div>
{% endif %}

<table class="table table-striped table-hover">
  <thead><tr>
    <th>#</th><th>Title</th><th>Stage</th><th>CEFR</th><th>Tag</th><th>Blocks</th><th>Questions</th><th></th>
  </tr></thead>
  <tbody>
    {% for t in topics %}
    <tr>
      <td>{{ t.order }}</td>
      <td><strong>{{ t.title }}</strong><br><small class="text-muted">{{ t.slug }}</small></td>
      <td>{{ t.get_stage_display }}</td>
      <td>{{ t.cefr_label }}</td>
      <td>{{ t.tag }}</td>
      <td><a href="{% url 'dashboard_grammar_blocks' t.pk %}">{{ t.blocks.count }}</a></td>
      <td><a href="{% url 'dashboard_grammar_questions' t.pk %}">{{ t.questions.count }}</a></td>
      <td class="text-nowrap">
        <a href="{% url 'dashboard_grammar_edit' t.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
        <a href="{% url 'dashboard_grammar_delete' t.pk %}" class="btn btn-sm btn-outline-danger">Del</a>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="8" class="text-center text-muted">No grammar topics found.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`dashboard/templates/dashboard/grammar/form.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Grammar Topic{% endblock %}
{% block content %}
<h1>{{ action }} Grammar Topic{% if obj %}: {{ obj.title }}{% endif %}</h1>
{% if obj %}
<p>
  <a href="{% url 'dashboard_grammar_blocks' obj.pk %}" class="btn btn-sm btn-outline-secondary">Lesson blocks ({{ obj.blocks.count }})</a>
  <a href="{% url 'dashboard_grammar_questions' obj.pk %}" class="btn btn-sm btn-outline-secondary">Questions ({{ obj.questions.count }})</a>
</p>
{% endif %}
<form method="post" class="mt-3" style="max-width:700px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>
    {{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  {% if form.non_field_errors %}<div class="text-danger small mb-3">{{ form.non_field_errors }}</div>{% endif %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_grammar_list' %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

`dashboard/templates/dashboard/grammar/blocks.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}Blocks — {{ topic.title }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h1>Lesson Blocks — {{ topic.title }}</h1>
  <a href="{% url 'dashboard_grammar_block_add' topic.pk %}" class="btn btn-success">+ Add Block</a>
</div>
<p><a href="{% url 'dashboard_grammar_list' %}">&larr; All topics</a></p>
<table class="table table-striped table-hover">
  <thead><tr><th>#</th><th>Type</th><th>Title</th><th>Body / Data</th><th></th></tr></thead>
  <tbody>
    {% for b in blocks %}
    <tr>
      <td>{{ b.order }}</td>
      <td>{{ b.get_type_display }}</td>
      <td>{{ b.title }}</td>
      <td class="text-truncate" style="max-width:400px">{{ b.body|default:b.data }}</td>
      <td class="text-nowrap">
        <a href="{% url 'dashboard_grammar_block_edit' b.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
        <form method="post" action="{% url 'dashboard_grammar_block_delete' b.pk %}" class="d-inline"
              onsubmit="return confirm('Delete this block?');">
          {% csrf_token %}<button class="btn btn-sm btn-outline-danger">Del</button>
        </form>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="5" class="text-center text-muted">No blocks yet.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`dashboard/templates/dashboard/grammar/block_form.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Block — {{ topic.title }}{% endblock %}
{% block content %}
<h1>{{ action }} Lesson Block — {{ topic.title }}</h1>
<form method="post" class="mt-3" style="max-width:700px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>
    {{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  {% if form.non_field_errors %}<div class="text-danger small mb-3">{{ form.non_field_errors }}</div>{% endif %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_grammar_blocks' topic.pk %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

`dashboard/templates/dashboard/grammar/questions.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}Questions — {{ topic.title }}{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h1>Questions — {{ topic.title }}</h1>
  <a href="{% url 'dashboard_grammar_question_add' topic.pk %}" class="btn btn-success">+ Add Question</a>
</div>
<p><a href="{% url 'dashboard_grammar_list' %}">&larr; All topics</a></p>
<table class="table table-striped table-hover">
  <thead><tr><th>#</th><th>Type</th><th>Prompt</th><th>Answers</th><th></th></tr></thead>
  <tbody>
    {% for q in questions %}
    <tr>
      <td>{{ q.order }}</td>
      <td>{{ q.get_qtype_display }}</td>
      <td class="text-truncate" style="max-width:400px">{{ q.prompt }}</td>
      <td class="text-truncate" style="max-width:200px">{{ q.answers }}</td>
      <td class="text-nowrap">
        <a href="{% url 'dashboard_grammar_question_edit' q.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
        <form method="post" action="{% url 'dashboard_grammar_question_delete' q.pk %}" class="d-inline"
              onsubmit="return confirm('Delete this question?');">
          {% csrf_token %}<button class="btn btn-sm btn-outline-danger">Del</button>
        </form>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="5" class="text-center text-muted">No questions yet.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`dashboard/templates/dashboard/grammar/question_form.html`:

```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Question — {{ topic.title }}{% endblock %}
{% block content %}
<h1>{{ action }} Question — {{ topic.title }}</h1>
<form method="post" class="mt-3" style="max-width:700px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>
    {{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  {% if form.non_field_errors %}<div class="text-danger small mb-3">{{ form.non_field_errors }}</div>{% endif %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_grammar_questions' topic.pk %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

- [ ] **Step 7: Add nav link and index card**

In `dashboard/templates/dashboard/base.html`, after the Words link add:

```html
    <a class="text-white text-decoration-none" href="/dashboard/grammar/">Grammar</a>
```

In `dashboard/templates/dashboard/index.html`, after the Categories card `</div>` (the `col-md-3` wrapper) add:

```html
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h2 class="card-title">{{ grammar_count }}</h2>
        <p class="card-text text-muted">Grammar topics</p>
        <a href="/dashboard/grammar/" class="btn btn-sm btn-primary">Manage</a>
      </div>
    </div>
  </div>
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_dashboard_grammar.py -v`
Expected: 8 passed
Run: `python -m pytest`
Expected: all pass

- [ ] **Step 9: Commit**

```powershell
git add dashboard/ tests/test_dashboard_grammar.py
git commit -m "feat(grammar): dashboard CRUD for topics, lesson blocks and questions"
```

---

### Task 5: Author `grammar-content.json` — Beginner stage (12 topics) + first seed

**Files:**
- Create: `ielts-vocab-master/Python/Django/grammar-content.json`

**Interfaces:**
- Consumes: JSON schema from Task 3.
- Produces: `grammar-content.json` containing the 12 `beginner` topics (array order = display order). Tasks 6–7 append to this file; Task 8+ renders it.

This is a content-authoring task. Every topic MUST follow the schema from Task 3 and these rules:

- **Lesson:** exactly 1 `intro`, 1–3 `rule` blocks, 0–2 `table` blocks, exactly 1 `examples` block with 4–6 items, exactly 1 `tip` block (IELTS-angled), in that general order.
- **Quiz:** exactly 10 questions per topic; mostly `mcq` (4 options) and `gap`; at most 2 `transform`. Every question has a one-sentence `why`. `gap` prompts contain `___`. `gap`/`transform` `answers` list all reasonable accepted variants (contractions, "will not"/"won't" etc.). All `mcq` `answers` are `[index]` with index 0–3; vary the correct index across questions.
- **Register:** IELTS-flavoured example sentences (academic/graph/essay contexts where natural). British spelling. HTML in `body` fields limited to `<p>`, `<b>`, `<em>`, `<br>`, `<code>`.
- **No emoji anywhere.**

The 12 beginner topics, in order (slug · title · tag · cefr):

| # | slug | title | tag | cefr |
|---|---|---|---|---|
| 1 | `present-simple-continuous` | Present Simple & Continuous | Tenses | A1–A2 |
| 2 | `past-simple-continuous` | Past Simple & Continuous | Tenses | A1–A2 |
| 3 | `future-forms` | Future Forms (will / going to) | Tenses | A1–A2 |
| 4 | `question-forms` | Question Forms & Short Answers | Sentence | A1–A2 |
| 5 | `word-forms` | Word Forms (noun/verb/adj/adv) | Word Building | A1–A2 |
| 6 | `articles` | Articles (a/an/the) | Determiners | A1–A2 |
| 7 | `nouns-plurals` | Nouns, Plurals & Countability | Nouns | A1–A2 |
| 8 | `quantifiers` | Quantifiers & There is/are | Determiners | A1–A2 |
| 9 | `pronouns-possessives` | Pronouns & Possessives | Pronouns | A1–A2 |
| 10 | `comparatives-superlatives` | Comparatives & Superlatives | Adjectives | A1–A2 |
| 11 | `prepositions-time-place` | Prepositions of Time & Place | Prepositions | A1–A2 |
| 12 | `adverbs-word-order` | Adverbs & Word Order | Sentence | A1–A2 |

Folded sub-points: imperatives → `question-forms`; there is/are → `quantifiers`.

**Canonical worked example — the `articles` topic must be authored exactly like this** (the other 11 follow the same shape with their own content):

```json
{
  "slug": "articles",
  "stage": "beginner",
  "title": "Articles (a/an/the)",
  "tag": "Determiners",
  "cefr": "A1–A2",
  "blurb": "Choose between a, an, the — or no article at all.",
  "lesson": [
    {"type": "intro", "body": "<p>Articles are small words with a big job: they tell the reader whether a noun is <b>one of many</b> (<em>a city</em>) or <b>a specific one</b> (<em>the city we visited</em>). English has three choices: <b>a/an</b>, <b>the</b>, and no article at all.</p>"},
    {"type": "rule", "title": "A or An", "body": "<p>Use <b>a</b> before a consonant <em>sound</em> and <b>an</b> before a vowel <em>sound</em>. It is the sound that matters, not the letter: <em>a university</em> (/j/ sound), <em>an hour</em> (silent h).</p>"},
    {"type": "rule", "title": "The", "body": "<p>Use <b>the</b> when both speaker and listener know which one: something already mentioned (<em>a graph… the graph shows</em>), unique things (<em>the internet, the environment</em>), and superlatives (<em>the largest city</em>).</p>"},
    {"type": "rule", "title": "No article", "body": "<p>Use <b>no article</b> for plural or uncountable nouns in general statements: <em>Cities are growing</em>, <em>Education is important</em> — very common in IELTS essay openings.</p>"},
    {"type": "table", "title": "Quick map", "data": {"head": ["Situation", "Article", "Example"], "rows": [
      ["First mention, one of many", "a / an", "The chart shows a factory."],
      ["Known / already mentioned", "the", "The factory produces steel."],
      ["Unique things", "the", "the government, the environment"],
      ["General plurals & uncountables", "(none)", "Pollution damages cities."]
    ]}},
    {"type": "examples", "data": {"items": [
      {"en": "The graph shows an increase in car ownership.", "note": "\"increase\" begins with a vowel sound — an."},
      {"en": "A minority of respondents disagreed, and the majority supported the plan.", "note": "First mention takes a; the known group takes the."},
      {"en": "Unemployment rose sharply in the 1990s.", "note": "Uncountable noun in a general statement — no article; decades take the."},
      {"en": "She attends a university in the largest city in Vietnam.", "note": "a + consonant sound /j/; superlative takes the."},
      {"en": "Governments should invest in public transport.", "note": "General plural statement — no article."}
    ]}},
    {"type": "tip", "body": "<p>In Writing Task 1, your first sentence usually introduces the visual with <b>the</b>: <em>The chart illustrates…</em>. But trends inside it are often first mentions: <em>there was a sharp rise…</em>. Mixing these up is one of the most common band-lowering slips.</p>"}
  ],
  "quiz": [
    {"qtype": "mcq", "prompt": "She is ___ engineer at a software company.", "options": ["a", "an", "the", "(no article)"], "answers": [1], "why": "\"Engineer\" begins with a vowel sound, so we use \"an\"."},
    {"qtype": "mcq", "prompt": "He graduated from ___ university in Hanoi.", "options": ["an", "a", "the", "(no article)"], "answers": [1], "why": "\"University\" starts with a /j/ (consonant) sound, so \"a\" is correct."},
    {"qtype": "gap", "prompt": "The chart shows ___ number of visitors between 2010 and 2020.", "answers": ["the"], "why": "\"The number of\" is a fixed, specific reference — it takes \"the\"."},
    {"qtype": "mcq", "prompt": "___ pollution is a serious problem in many cities.", "options": ["A", "An", "The", "(no article)"], "answers": [3], "why": "Uncountable noun in a general statement — no article."},
    {"qtype": "gap", "prompt": "There was ___ sharp increase in exports, and the increase continued until 2019.", "answers": ["a"], "why": "First mention of the increase is one of many — \"a\"; the second mention takes \"the\"."},
    {"qtype": "mcq", "prompt": "It took her ___ hour to finish the reading section.", "options": ["a", "an", "the", "(no article)"], "answers": [1], "why": "The \"h\" in \"hour\" is silent, so the word begins with a vowel sound."},
    {"qtype": "mcq", "prompt": "Ho Chi Minh City is ___ largest city in Vietnam.", "options": ["a", "an", "the", "(no article)"], "answers": [2], "why": "Superlatives always take \"the\"."},
    {"qtype": "gap", "prompt": "___ internet has transformed how students prepare for exams.", "answers": ["the"], "why": "Unique, one-of-a-kind things take \"the\"."},
    {"qtype": "gap", "prompt": "In general, ___ children learn languages faster than adults.", "answers": ["(no article)", "no article", "-"], "why": "General plural statement — no article is used."},
    {"qtype": "transform", "prompt": "Rewrite with the correct articles: \"Graph shows increase in number of tourists.\"", "answers": ["The graph shows an increase in the number of tourists.", "The graph shows an increase in the number of tourists"], "why": "The known visual takes \"the\"; a first-mention rise takes \"an\"; \"the number of\" is fixed."}
  ]
}
```

- [ ] **Step 1: Create `grammar-content.json`** as a JSON array containing the 12 beginner topics in table order, with the `articles` topic exactly as above and the other 11 authored to the same rules. Grammar accuracy matters more than speed — double-check every `answers` value against the rule the question tests.

- [ ] **Step 2: Validate the JSON parses and seeds**

Run: `python -c "import json; d=json.load(open('grammar-content.json', encoding='utf-8')); print(len(d), sum(len(t['quiz']) for t in d))"`
Expected: `12 120`
Run: `python manage.py import_grammar`
Expected: `Done. Grammar topics: 12, blocks: ..., questions: 120`

- [ ] **Step 3: Verify idempotency and API output**

Run: `python manage.py import_grammar` (again)
Expected: same counts, no duplicates.
Run: `python -m pytest`
Expected: all pass.

- [ ] **Step 4: Commit**

```powershell
git add grammar-content.json
git commit -m "feat(grammar): author beginner-stage curriculum (12 topics, 120 questions)"
```

---

### Task 6: Author Independent stage (12 topics) + re-seed

**Files:**
- Modify: `ielts-vocab-master/Python/Django/grammar-content.json` (append 12 topics)

**Interfaces:** same schema and authoring rules as Task 5 (see Task 3 schema; Task 5 rules for lesson/quiz shape, register, accepted-variant answers, no emoji). Use the `articles` topic already in the file as the canonical shape reference.

The 12 independent topics, in order (slug · title · tag · cefr — all `"stage": "independent"`, `"cefr": "B1–B2"`):

| # | slug | title | tag |
|---|---|---|---|
| 13 | `perfect-tenses` | Perfect Tenses | Tenses |
| 14 | `passive-voice` | Passive & Active Voice | Voice |
| 15 | `reported-speech` | Reported Speech | Sentence |
| 16 | `conditionals` | Conditionals 0–3 | Conditionals |
| 17 | `relative-clauses` | Relative Clauses | Clauses |
| 18 | `modal-verbs` | Modal Verbs | Modals |
| 19 | `gerunds-infinitives` | Gerunds vs Infinitives | Verb Patterns |
| 20 | `used-to` | Used to / Would / Be used to | Verb Patterns |
| 21 | `wish-if-only` | Wish & If only | Unreal Forms |
| 22 | `causatives` | Causatives (have/get something done) | Voice |
| 23 | `question-tags-indirect` | Question Tags & Indirect Questions | Sentence |
| 24 | `linking-words` | Linking Words & Cohesion | Cohesion |

Folded sub-points: future perfect/continuous → `perfect-tenses`; defining vs non-defining → `relative-clauses`; basic can/must → `modal-verbs`; so/such/too/enough → `linking-words`.

- [ ] **Step 1: Append the 12 topics** to the JSON array (after the beginner topics — array order is display order).

- [ ] **Step 2: Validate and re-seed**

Run: `python -c "import json; d=json.load(open('grammar-content.json', encoding='utf-8')); print(len(d), sum(len(t['quiz']) for t in d))"`
Expected: `24 240`
Run: `python manage.py import_grammar`
Expected: `Done. Grammar topics: 24, ... questions: 240`

- [ ] **Step 3: Commit**

```powershell
git add grammar-content.json
git commit -m "feat(grammar): author independent-stage curriculum (12 topics, 120 questions)"
```

---

### Task 7: Author Expert stage (12 topics) + re-seed

**Files:**
- Modify: `ielts-vocab-master/Python/Django/grammar-content.json` (append 12 topics)

**Interfaces:** same schema and authoring rules as Tasks 5–6.

The 12 expert topics, in order (all `"stage": "expert"`, `"cefr": "C1–C2"`):

| # | slug | title | tag |
|---|---|---|---|
| 25 | `inversion-emphasis` | Inversion & Emphasis | Emphasis |
| 26 | `cleft-sentences` | Cleft Sentences | Emphasis |
| 27 | `subjunctive-unreal-past` | Subjunctive & Unreal Past | Unreal Forms |
| 28 | `advanced-modality` | Advanced Modality | Modals |
| 29 | `participle-clauses` | Participle Clauses | Clauses |
| 30 | `nominalisation` | Nominalisation | Academic Style |
| 31 | `hedging-academic-tone` | Hedging & Academic Tone | Academic Style |
| 32 | `mixed-conditionals` | Mixed Conditionals | Conditionals |
| 33 | `ellipsis-substitution` | Ellipsis & Substitution | Cohesion |
| 34 | `dummy-subjects` | Dummy Subjects (it/there) | Sentence |
| 35 | `fronting-ever-clauses` | Fronting & -ever Clauses | Emphasis |
| 36 | `gradable-adjectives` | Gradable Adjectives & Intensifiers | Adjectives |

Folded sub-points: reduced relative clauses → `participle-clauses`; emphasis with "do" → `inversion-emphasis`; -ed/-ing adjectives → `gradable-adjectives`. Expert tips should target band 8+ writing/speaking (hedged claims, academic register, sentence variety).

- [ ] **Step 1: Append the 12 topics** to the JSON array.

- [ ] **Step 2: Validate and re-seed**

Run: `python -c "import json; d=json.load(open('grammar-content.json', encoding='utf-8')); print(len(d), sum(len(t['quiz']) for t in d))"`
Expected: `36 360`
Run: `python manage.py import_grammar`
Expected: `Done. Grammar topics: 36, ... questions: 360`
Run: `python -m pytest`
Expected: all pass.

- [ ] **Step 3: Commit**

```powershell
git add grammar-content.json
git commit -m "feat(grammar): author expert-stage curriculum (12 topics, 120 questions)"
```

---

### Task 8: SPA — page skeleton, data loading, Grammar home

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (3 edits: page markup, CSS, JS)

No JS test runner exists for the single-file SPA — verification is by browser, matching how every existing SPA feature ships. Steps below include exact manual checks.

**Interfaces:**
- Consumes: `GET /api/grammar/` (Task 2 shape); existing globals `API_BASE`, `CEFR_COLORS`, CSS classes `section-block-*`, `cat-*`, `setup-card`, `btn`, `page-head`, `eyebrow`; `goToPage` navigation.
- Produces: `renderGrammarHome()`, `loadGrammar()` (memoised fetch), `showGrammarView(id)`, `openGrammarTopic(topic)` (stub in this task, real in Task 9), progress helpers `loadGrammarProgress()`, `saveGrammarProgress(p)`, `grammarTopicDone(slug)`, `recordGrammarScore(slug, pct)`, `cefrRangePillHtml(label)`. Tasks 9–10 build on these exact names.

- [ ] **Step 1: Replace the Grammar page markup**

Find the section starting `<!-- ===== GRAMMAR PAGE ===== -->` and replace the whole `<section id="page-grammar" ...>...</section>` block with:

```html
  <!-- ===== GRAMMAR PAGE ===== -->
  <section id="page-grammar" class="page">
    <div id="grammarHome">
      <div class="page-head">
        <span class="eyebrow">Section 02 / Grammar</span>
        <h1>Grammar</h1>
        <p>From first tenses to advanced structures — a lesson and a practice set for every stage.</p>
      </div>
      <div id="grammarStages"></div>
    </div>
    <div id="grammarLesson" style="display:none;"></div>
    <div id="grammarQuizView" class="quiz-wrap" style="display:none;"></div>
    <div id="grammarResult" class="result-card" style="display:none;"></div>
  </section>
```

- [ ] **Step 2: Add grammar CSS**

In the `<style>` block, directly before the `/* responsive */`-related `@media` rules near `.q-card,.setup-card,.result-card{padding:20px;}` (or, simpler, immediately after the `.cat-card:hover .cat-arrow{...}` rule), add:

```css
/* ── Grammar section ── */
.gram-card-blurb{font-size:.85rem;color:var(--muted);margin-top:4px;line-height:1.45;}
.gram-lesson{max-width:760px;margin:0 auto;}
.gram-block{margin-bottom:22px;line-height:1.65;}
.gram-intro{font-size:1.04rem;color:var(--muted);}
.gram-rule{border:1px solid rgba(var(--vio),.28);background:rgba(var(--vio),.06);border-radius:14px;padding:16px 20px;}
.gram-rule h3{font-size:.78rem;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;color:rgb(var(--vio));}
.gram-table-title{font-size:.78rem;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;color:var(--muted);}
.gram-table{width:100%;border-collapse:collapse;font-size:.94rem;}
.gram-table th{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);text-align:left;}
.gram-table th,.gram-table td{padding:9px 12px;border-bottom:1px solid rgba(128,128,128,.18);}
.gram-ex{padding:10px 0;border-bottom:1px dashed rgba(128,128,128,.22);}
.gram-ex-en{font-size:1rem;}
.gram-ex-note{font-size:.85rem;color:var(--muted);margin-top:2px;}
.gram-tip{border-left:3px solid rgb(var(--vio));padding:12px 16px;background:rgba(var(--vio),.05);border-radius:0 12px 12px 0;}
.gram-tip-label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.14em;color:rgb(var(--vio));margin-bottom:4px;}
.gram-gap-input{width:100%;max-width:340px;padding:10px 14px;border-radius:10px;border:1px solid rgba(128,128,128,.35);background:transparent;color:inherit;font:inherit;}
.gram-gap-input:focus{outline:none;border-color:rgb(var(--vio));}
.gram-gap-input.correct{border-color:#10b981;}
.gram-gap-input.wrong{border-color:#ef4444;}
```

- [ ] **Step 3: Add the grammar JS module**

In the `<script>` block, immediately before the `/* ════ NAVIGATION ════ */` banner comment, insert:

```js
/* ════════════════════════════════════════════════════════
   GRAMMAR SECTION
   ════════════════════════════════════════════════════════ */
const GRAMMAR_PROGRESS_KEY = 'grammarProgress';
const GRAMMAR_PASS_PCT = 80;
let GRAMMAR_STAGES_DATA = null;   // fetched once per session
let grammarLoading = null;        // in-flight fetch promise

function loadGrammarProgress(){
  try { return JSON.parse(localStorage.getItem(GRAMMAR_PROGRESS_KEY)) || {}; }
  catch(e){ return {}; }
}
function saveGrammarProgress(p){
  try { localStorage.setItem(GRAMMAR_PROGRESS_KEY, JSON.stringify(p)); } catch(e){}
}
function grammarTopicDone(slug){
  const rec = loadGrammarProgress()[slug];
  return !!(rec && rec.done);
}
function recordGrammarScore(slug, pct){
  const p = loadGrammarProgress();
  const prev = p[slug] || { best: 0, done: false };
  const best = Math.max(prev.best, pct);
  p[slug] = { best, done: prev.done || best >= GRAMMAR_PASS_PCT };
  saveGrammarProgress(p);
}

function cefrRangePillHtml(label){
  const first = String(label).split('–')[0];
  const c = CEFR_COLORS[first] || '#888';
  return `<span class="cat-cefr-pill" style="background:${c}1c;border:1px solid ${c}55;color:${c}">${label}</span>`;
}

function loadGrammar(){
  if (GRAMMAR_STAGES_DATA) return Promise.resolve(GRAMMAR_STAGES_DATA);
  if (!grammarLoading){
    grammarLoading = fetch(`${API_BASE}/grammar/`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => { GRAMMAR_STAGES_DATA = data; return data; })
      .catch(err => { grammarLoading = null; throw err; });
  }
  return grammarLoading;
}

function showGrammarView(view){
  ['grammarHome', 'grammarLesson', 'grammarQuizView', 'grammarResult'].forEach(id => {
    document.getElementById(id).style.display = (id === view) ? '' : 'none';
  });
}

function renderGrammarHome(){
  showGrammarView('grammarHome');
  const wrap = document.getElementById('grammarStages');
  wrap.innerHTML = `<p class="sub" style="text-align:center;">Loading grammar…</p>`;
  loadGrammar().then(stages => {
    wrap.innerHTML = '';
    stages.forEach((stage, i) => wrap.appendChild(renderGrammarStage(stage, i + 1)));
    if (typeof gsap !== 'undefined'){
      gsap.fromTo(wrap.querySelectorAll('.cat-card'), {opacity:0, y:16},
        {opacity:1, y:0, duration:.35, ease:'power2.out', stagger:{amount:.25, from:'start'}});
    }
  }).catch(() => {
    wrap.innerHTML = `
      <div class="setup-card" style="text-align:center;">
        <p class="sub">Couldn't load the grammar library. Check your connection and try again.</p>
        <button class="btn" id="grammarRetryBtn">Retry</button>
      </div>`;
    document.getElementById('grammarRetryBtn').addEventListener('click', renderGrammarHome);
  });
}

function renderGrammarStage(stage, num){
  const progress = loadGrammarProgress();
  const doneCnt = stage.topics.filter(t => grammarTopicDone(t.slug)).length;
  const pct = stage.topics.length ? Math.round(doneCnt / stage.topics.length * 100) : 0;
  const wrap = document.createElement('div');
  wrap.className = 'section-block open';
  wrap.innerHTML = `
    <div class="section-block-header">
      <div class="section-block-num">${String(num).padStart(2, '0')}</div>
      <div class="section-block-info">
        <div class="section-block-name">${stage.name}</div>
        <div class="section-block-meta">${stage.cefr} · ${stage.topics.length} topic${stage.topics.length !== 1 ? 's' : ''}</div>
      </div>
      <div class="section-block-right">
        <div class="section-block-prog">
          <div class="section-block-pbar"><div class="section-block-pfill" style="width:${pct}%"></div></div>
          <div class="section-block-pct">${doneCnt}/${stage.topics.length}</div>
        </div>
        <span class="section-block-chevron">›</span>
      </div>
    </div>
    <div class="section-block-divider"></div>
    <div class="section-block-body">
      <div class="section-block-body-inner"><div class="cat-grid"></div></div>
    </div>`;
  const header = wrap.querySelector('.section-block-header');
  const body = wrap.querySelector('.section-block-body');
  body.style.maxHeight = 'none';
  header.addEventListener('click', () => {
    const opening = !wrap.classList.contains('open');
    wrap.classList.toggle('open', opening);
    body.style.maxHeight = opening ? body.scrollHeight + 'px' : '0';
  });
  const grid = wrap.querySelector('.cat-grid');
  stage.topics.forEach(t => {
    const done = grammarTopicDone(t.slug);
    const best = (progress[t.slug] || {}).best || 0;
    const card = document.createElement('div');
    card.className = 'cat-card t-tv';
    card.innerHTML = `
      <div class="cat-card-top">
        <span class="cat-tag">${t.tag}</span>
        ${cefrRangePillHtml(t.cefr)}
        <svg class="ico cat-arrow" aria-hidden="true"><use href="#i-arrow-up-right"/></svg>
      </div>
      <div class="cat-name">${t.title}</div>
      <div class="gram-card-blurb">${t.blurb}</div>
      <div class="cat-pbar-row">
        <div class="cat-pbar"><div class="cat-pfill" style="width:${best}%;${done ? 'background:#10b981;' : ''}"></div></div>
        ${done
          ? '<svg class="ico cat-medal" aria-label="Mastered"><use href="#i-medal"/></svg>'
          : `<span class="cat-plabel">${best ? `best ${best}%` : 'not started'}</span>`}
      </div>`;
    card.addEventListener('click', () => openGrammarTopic(t));
    grid.appendChild(card);
  });
  return wrap;
}

function openGrammarTopic(topic){
  // Real implementation in the lesson-view task.
  console.log('openGrammarTopic', topic.slug);
}
```

- [ ] **Step 4: Hook into navigation**

In `goToPage`, extend the page-render dispatch:

```js
  if (pageId === "list") renderBrowse();
  else if (pageId === "examples") renderExamplesFilters();
  else if (pageId === "test") renderTestMode();
  else if (pageId === "grammar") renderGrammarHome();
```

- [ ] **Step 5: Manual verification**

Start the server:

```powershell
Start-Process cmd -ArgumentList @("/k", "python manage.py runserver") -WorkingDirectory "D:\IT RELATED\CLAUDE BOMBASTIC AI\ielts-vocab-master\Python\Django" -WindowStyle Normal
```

Open `http://localhost:8000`, click the **Grammar** tab. Expected:
- Three stage groups (01 Beginner A1–A2, 02 Independent B1–B2, 03 Expert C1–C2), each showing `0/12` and 12 topic cards with tag pill, CEFR chip, blurb, "not started" label.
- Stage headers collapse/expand on click.
- Clicking a card logs `openGrammarTopic <slug>` in the console (stub).
- Both themes (toggle top-right) render the cards and stage headers legibly.
- DevTools Network: exactly one `/api/grammar/` request even after leaving and re-entering the tab.

- [ ] **Step 6: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): SPA grammar home — stage groups, topic cards, progress bars"
```

---

### Task 9: SPA — lesson view

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (replace the `openGrammarTopic` stub; add `grammarBlockHtml`)

**Interfaces:**
- Consumes: `showGrammarView`, `renderGrammarHome`, `cefrRangePillHtml`, `startGrammarQuiz(topic)` (stub in this task, real in Task 10); topic shape from `/api/grammar/`; CSS classes from Task 8.
- Produces: `openGrammarTopic(topic)` rendering the full lesson; `grammarBlockHtml(block)`.

- [ ] **Step 1: Replace the stub**

Replace the stub `openGrammarTopic` from Task 8 with:

```js
function openGrammarTopic(topic){
  showGrammarView('grammarLesson');
  const el = document.getElementById('grammarLesson');
  el.innerHTML = `
    <button class="back-btn" id="grammarBackBtn">← All grammar</button>
    <div class="page-head" style="margin-bottom:26px;">
      <span class="eyebrow">Grammar / ${topic.tag}</span>
      <h1>${topic.title} ${cefrRangePillHtml(topic.cefr)}</h1>
      <p>${topic.blurb}</p>
    </div>
    <div class="gram-lesson">${topic.lesson.map(grammarBlockHtml).join('')}</div>
    ${topic.quiz.length
      ? `<div style="text-align:center;margin-top:30px;">
           <button class="btn" id="grammarPracticeBtn">Practice — ${topic.quiz.length} question${topic.quiz.length !== 1 ? 's' : ''}</button>
         </div>`
      : ''}`;
  document.getElementById('grammarBackBtn').addEventListener('click', renderGrammarHome);
  const practiceBtn = document.getElementById('grammarPracticeBtn');
  if (practiceBtn) practiceBtn.addEventListener('click', () => startGrammarQuiz(topic));
  document.getElementById('page-grammar').scrollIntoView({behavior: 'smooth', block: 'start'});
  if (typeof gsap !== 'undefined'){
    gsap.fromTo(el, {opacity:0, y:14}, {opacity:1, y:0, duration:.4, ease:'power2.out'});
  }
}

function grammarBlockHtml(block){
  switch (block.type){
    case 'intro':
      return `<div class="gram-block gram-intro">${block.body}</div>`;
    case 'rule':
      return `<div class="gram-block gram-rule">${block.title ? `<h3>${block.title}</h3>` : ''}${block.body}</div>`;
    case 'table': {
      const head = (block.data.head || []).map(h => `<th>${h}</th>`).join('');
      const rows = (block.data.rows || []).map(r => `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`).join('');
      return `<div class="gram-block">
        ${block.title ? `<h3 class="gram-table-title">${block.title}</h3>` : ''}
        <div style="overflow-x:auto;"><table class="gram-table"><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>
      </div>`;
    }
    case 'examples':
      return `<div class="gram-block gram-examples">${(block.data.items || []).map(it =>
        `<div class="gram-ex"><div class="gram-ex-en">${it.en}</div>${it.note ? `<div class="gram-ex-note">${it.note}</div>` : ''}</div>`
      ).join('')}</div>`;
    case 'tip':
      return `<div class="gram-block gram-tip"><span class="gram-tip-label">IELTS tip</span>${block.body}</div>`;
    default:
      return '';
  }
}

function startGrammarQuiz(topic){
  // Real implementation in the quiz task.
  console.log('startGrammarQuiz', topic.slug);
}
```

- [ ] **Step 2: Manual verification**

Reload `http://localhost:8000`, open Grammar → click **Articles (a/an/the)**. Expected:
- Breadcrumb "← All grammar" returns to the stage list.
- Eyebrow reads "Grammar / Determiners"; title shows the CEFR chip.
- Intro paragraph, three violet rule boxes with uppercase headings, the "Quick map" table, 5 example sentences with notes, and the "IELTS tip" callout render in order.
- "Practice — 10 questions" button logs `startGrammarQuiz articles` (stub).
- Check one topic from each stage; check both themes.

- [ ] **Step 3: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): SPA lesson view — rule boxes, tables, examples, tips"
```

---

### Task 10: SPA — quiz engine, results, progress, reset integration

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (replace `startGrammarQuiz` stub; add quiz functions; extend reset handler)

**Interfaces:**
- Consumes: `showGrammarView`, `openGrammarTopic`, `renderGrammarHome`, `recordGrammarScore`, `GRAMMAR_PASS_PCT`; question shape `{qtype, prompt, options, answers, why}`; CSS classes `q-card/q-opt/q-feedback/q-next/progress-bar/result-*` (existing) and `gram-gap-input` (Task 8).
- Produces: working quiz for all three question types; scores recorded to `grammarProgress`; reset button clears grammar progress.

- [ ] **Step 1: Replace the stub with the quiz engine**

Replace the stub `startGrammarQuiz` with:

```js
const grammarQuiz = { topic: null, idx: 0, score: 0 };

function grammarNorm(s){
  return String(s).trim().replace(/\s+/g, ' ').toLowerCase();
}

function startGrammarQuiz(topic){
  grammarQuiz.topic = topic;
  grammarQuiz.idx = 0;
  grammarQuiz.score = 0;
  showGrammarView('grammarQuizView');
  renderGrammarQuestion();
}

function renderGrammarQuestion(){
  const t = grammarQuiz.topic;
  const q = t.quiz[grammarQuiz.idx];
  const total = t.quiz.length;
  const view = document.getElementById('grammarQuizView');
  const pct = Math.round(((grammarQuiz.idx + 1) / total) * 100);
  const isTyped = q.qtype !== 'mcq';
  const promptLabel = q.qtype === 'mcq' ? 'Choose the correct option'
    : q.qtype === 'gap' ? 'Fill the gap' : 'Rewrite the sentence';
  view.innerHTML = `
    <button class="back-btn" id="grammarQuizLeaveBtn">← Leave</button>
    <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
    <div class="q-meta"><span>Question ${grammarQuiz.idx + 1} of ${total}</span><span>Score: ${grammarQuiz.score}</span></div>
    <div class="q-card">
      <div class="q-prompt">${promptLabel}</div>
      <div class="q-text">${q.prompt}</div>
      ${isTyped
        ? `<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
             <input class="gram-gap-input" id="grammarGapInput" type="text" autocomplete="off" spellcheck="false" aria-label="Your answer">
             <button class="btn" id="grammarCheckBtn">Check</button>
           </div>`
        : `<div class="q-options">${q.options.map((opt, i) => `<button class="q-opt" data-i="${i}">${opt}</button>`).join('')}</div>`}
      <div class="q-feedback"></div>
      <div class="q-next" style="display:none;"><button class="btn" id="grammarNextBtn">${grammarQuiz.idx + 1 === total ? 'See Results' : 'Next Question'}</button></div>
    </div>`;
  document.getElementById('grammarQuizLeaveBtn').addEventListener('click', () => openGrammarTopic(t));
  if (isTyped){
    const input = document.getElementById('grammarGapInput');
    document.getElementById('grammarCheckBtn').addEventListener('click', () => checkGrammarTyped(q, input));
    input.addEventListener('keydown', e => { if (e.key === 'Enter') checkGrammarTyped(q, input); });
    input.focus();
  } else {
    view.querySelectorAll('.q-opt').forEach(btn => {
      btn.addEventListener('click', () => checkGrammarMcq(q, btn));
    });
  }
  if (typeof gsap !== 'undefined'){
    gsap.fromTo(view.querySelector('.q-card'), {opacity:0, y:14}, {opacity:1, y:0, duration:.35, ease:'power2.out'});
  }
}

function grammarShowFeedback(isCorrect, feedbackHtml){
  const view = document.getElementById('grammarQuizView');
  if (isCorrect) grammarQuiz.score++;
  view.querySelector('.q-feedback').innerHTML = feedbackHtml;
  view.querySelector('.q-meta span:last-child').textContent = `Score: ${grammarQuiz.score}`;
  view.querySelector('.q-next').style.display = 'flex';
  document.getElementById('grammarNextBtn').addEventListener('click', () => {
    grammarQuiz.idx++;
    if (grammarQuiz.idx < grammarQuiz.topic.quiz.length) renderGrammarQuestion();
    else showGrammarResult();
  });
}

function checkGrammarMcq(q, selectedBtn){
  const view = document.getElementById('grammarQuizView');
  const correctIdx = q.answers[0];
  const isCorrect = Number(selectedBtn.dataset.i) === correctIdx;
  view.querySelectorAll('.q-opt').forEach(btn => {
    btn.disabled = true;
    if (Number(btn.dataset.i) === correctIdx) btn.classList.add('correct');
    else if (btn === selectedBtn) btn.classList.add('wrong');
  });
  grammarShowFeedback(isCorrect, `<b>${isCorrect ? 'Correct!' : 'Not quite.'}</b> ${q.why}`);
}

function checkGrammarTyped(q, input){
  if (input.disabled) return;
  if (!grammarNorm(input.value)){
    document.querySelector('#grammarQuizView .q-feedback').innerHTML = 'Type an answer first — blank submissions aren\'t counted.';
    return;
  }
  const isCorrect = q.answers.some(a => grammarNorm(a) === grammarNorm(input.value));
  input.disabled = true;
  document.getElementById('grammarCheckBtn').disabled = true;
  input.classList.add(isCorrect ? 'correct' : 'wrong');
  const feedback = isCorrect
    ? `<b>Correct!</b> ${q.why}`
    : `<b>Not quite.</b> The answer is “${q.answers[0]}”. ${q.why}`;
  grammarShowFeedback(isCorrect, feedback);
}

function showGrammarResult(){
  const t = grammarQuiz.topic;
  const total = t.quiz.length;
  const score = grammarQuiz.score;
  const pct = Math.round((score / total) * 100);
  recordGrammarScore(t.slug, pct);
  showGrammarView('grammarResult');
  const result = document.getElementById('grammarResult');
  result.innerHTML = `
    <h2>${t.title}</h2>
    <div class="result-score" id="grammarScoreNum">0</div>
    <div class="result-msg">You scored ${score} out of ${total} (${pct}%). ${pct >= GRAMMAR_PASS_PCT
      ? 'Topic mastered — it now counts toward your stage progress.'
      : `Score ${GRAMMAR_PASS_PCT}% or higher to master this topic.`}</div>
    <div class="result-actions">
      <button class="btn" id="grammarRetryBtn2">Try Again</button>
      <button class="btn secondary" id="grammarBackLessonBtn">Back to Lesson</button>
      <button class="btn secondary" id="grammarBackHomeBtn">Back to Grammar</button>
    </div>`;
  const scoreEl = document.getElementById('grammarScoreNum');
  if (typeof gsap !== 'undefined'){
    gsap.to({val: 0}, {val: score, duration: 1, ease: 'power1.out', onUpdate(){
      scoreEl.textContent = Math.round(this.targets()[0].val);
    }});
  } else {
    scoreEl.textContent = score;
  }
  document.getElementById('grammarRetryBtn2').addEventListener('click', () => startGrammarQuiz(t));
  document.getElementById('grammarBackLessonBtn').addEventListener('click', () => openGrammarTopic(t));
  document.getElementById('grammarBackHomeBtn').addEventListener('click', renderGrammarHome);
}
```

- [ ] **Step 2: Extend the reset handler**

In the `resetProgressBtn` click handler, add one line after `localStorage.removeItem("ivm_learned_words");`:

```js
    localStorage.removeItem("grammarProgress");
```

- [ ] **Step 3: Manual verification**

Reload, Grammar → Articles → Practice:
- MCQ: click a wrong option → correct one highlights green, chosen red, feedback shows the `why`; Next advances.
- Gap: submit empty → nudge shows, question not consumed; correct typed answer (any case, extra spaces) accepted.
- Transform (Q10): accepted with/without trailing period per the `answers` variants.
- Result card: score counts up; ≥80% shows "Topic mastered".
- Back to Grammar: Articles card shows green bar + medal; Beginner stage bar reads `1/12`.
- Reload the page: progress persists. Retry with a worse score: best % and mastered state do NOT regress.
- Leave mid-quiz via "← Leave": no score recorded.
- Reset button (top bar): confirm → grammar progress cleared along with vocab progress.
- `localStorage.setItem('grammarProgress', '{broken')` in console + reload → Grammar home renders with all topics "not started" (no crash).

- [ ] **Step 4: Run the backend suite one more time**

Run: `python -m pytest`
Expected: all pass.

- [ ] **Step 5: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): SPA quiz engine with mcq/gap/transform, results and progress"
```

---

### Task 11: Final verification pass

**Files:** none (verification only; fix-forward if issues found)

- [ ] **Step 1: Full backend suite**

Run: `python -m pytest`
Expected: all pass.

- [ ] **Step 2: Content spot-check via dashboard**

With a staff account at `http://localhost:8000/dashboard/grammar/`:
- 36 topics listed; stage filter shows 12 per stage.
- Open 2 topics per stage → blocks and questions lists render; edit one block and one question, save, confirm the change appears on `/api/grammar/` and in the SPA lesson after reload.
- Dashboard index shows the "Grammar topics: 36" card.

- [ ] **Step 3: SPA click-through**

Per the spec's verification list: visit every stage; open at least 4 lessons per stage end-to-end (lesson → quiz → result); confirm stage progress bars update; check light and dark themes; confirm the topbar "Learned x/5000" counter never changes from grammar activity.

- [ ] **Step 4: Grammar accuracy spot-check**

For 2 random topics per stage, read all 10 questions and verify each `answers` value is actually correct English for the rule being tested. Fix any content errors in `grammar-content.json`, re-run `python manage.py import_grammar`, and commit fixes.

- [ ] **Step 5: Final commit (if fixes were made)**

```powershell
git add grammar-content.json vocab-master.html
git commit -m "fix(grammar): content and polish fixes from final verification"
```
