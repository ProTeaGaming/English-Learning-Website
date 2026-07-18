# VocabLarry Professional Environment — Grammar Browse + Topic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Grammar section to VocabLarry Professional Environment — a flat, filterable topic browse page and a topic detail page rendering lesson content (intro/rule/table/examples/tip blocks) — reusing the existing `GrammarTopic`/`GrammarLessonBlock` models and no new backend at all.

**Architecture:** Two Django views (`config/views_grammar.py`) render server-side templates from direct ORM queries against the already-existing `GrammarTopic`/`GrammarLessonBlock` models — no JS, no JSON API calls, matching the "Server-rendered pages query the ORM directly" convention already established by Vocab Browse + Word. `grammar_browse` (`/grammar/`) lists all topics with a title search and a `stage` filter; `grammar_topic_detail` (`/grammar/topic/<slug>/`) renders one topic's ordered lesson blocks, branching template logic per block `type`.

**Tech Stack:** Django function views (no new models/migrations/endpoints), Django templates only (no client-side JS anywhere in this sub-project), pytest + pytest-django for full test coverage.

## Global Constraints

- No new models, no new migrations, no new backend endpoints — `GrammarTopic`, `GrammarLessonBlock` already exist with every field this sub-project needs (see `vocab/models.py`). The existing `/api/grammar/` JSON endpoint is not used by either view in this plan.
- **No section grouping.** Topics render as a flat grid sorted by `order`, exactly as `GrammarTopic.objects.order_by('order')` returns them (the model's own `Meta.ordering` already sorts this way; the explicit `.order_by('order')` call matches this codebase's existing convention of being explicit anyway, e.g. `vocab_category`'s `category.words.order_by('order')`).
- Filters: `?q=` (title `icontains`) and `?stage=` (exact match against `GrammarTopic.STAGES` — `beginner`/`independent`/`expert`). Both optional, both via a GET-submitted form, no client-side JS.
- **No progress/mastery UI anywhere** — there is no quiz in this sub-project, so there is nothing to track.
- Topic detail block rendering, exact per `type`:
  - `intro` / `tip`: render `block.body` with Django's `|safe` filter (it's a `TextField` containing admin-authored HTML — curated, `@staff_required`-gated content, same trust boundary as word definitions/examples in Vocab Browse + Word).
  - `rule`: render `block.title` (if present) + `block.body` (`|safe`) — **inline, in lesson order**, no scroll-pinned/rotating-background effect.
  - `table`: `block.data` always has the shape `{"head": [...], "rows": [[...], ...]}` — render as a plain `<table>`.
  - `examples`: `block.data` always has the shape `{"items": [{"en": "...", "note": "..."(optional)}, ...]}` — render as a list, `note` shown only when present.
- Nav's "Grammar" entry and the home page's "Practice Grammar" hero CTA both become real links to `/grammar/` — no longer disabled.
- Unknown topic slug → standard Django 404 via `get_object_or_404`, matching `vocab_word_detail`/`vocab_category`'s existing convention.
- Fully Python-testable — no manual browser verification step is needed in this plan (unlike the Quiz/Gap/Challenge sub-projects), since every page here is plain server-rendered HTML with zero client-side JS.
- Test with `pytest`, using `from django.test import Client; c = Client()` per-test. Create a new file `tests/test_grammar_pages.py` (there is no existing grammar *pages* test file — `test_grammar_models.py`/`test_grammar_api.py` cover the model and API layers only, matching the pattern where `test_vocab_pages.py` is a separate file from `test_vocab_api.py`).

---

### Task 1: Grammar browse page

**Files:**
- Create: `config/views_grammar.py`
- Modify: `config/urls.py`
- Create: `templates/grammar/browse.html`
- Modify: `templates/partials/nav.html`
- Modify: `templates/home.html`
- Create: `static/css/grammar.css`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Produces: `config.views_grammar.grammar_browse(request)` — renders `grammar/browse.html`, context keys `topics` (queryset), `stages` (`GrammarTopic.STAGES`, a list of `(value, label)` tuples), `query`, `stage_filter`.
- Produces: URL name `grammar_browse` at `/grammar/`.
- Produces: URL name `grammar_topic_detail` at `/grammar/topic/<slug:slug>/`, registered in this task as a stub (Task 2 replaces only its function body) — `browse.html`'s `{% url 'grammar_topic_detail' topic.slug %}` link is evaluated at render time regardless of whether it's clicked, so the URL name must exist now (same forward-reference lesson established in the Vocab Browse + Word sub-project).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_grammar_pages.py`:

```python
import pytest
from django.test import Client

from vocab.models import GrammarTopic


@pytest.fixture
def topic_articles(db):
    return GrammarTopic.objects.create(
        slug='articles', title='Articles (a/an/the)', tag='Determiners',
        cefr_label='A1', blurb='When to use a, an and the.',
        stage='beginner', order=0,
    )


@pytest.mark.django_db
def test_grammar_browse_renders():
    c = Client()
    r = c.get('/grammar/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_lists_topics(topic_articles):
    c = Client()
    r = c.get('/grammar/')
    assert 'Articles (a/an/the)' in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_search_filters_by_title(topic_articles):
    GrammarTopic.objects.create(
        slug='future-forms', title='Future Forms', tag='Tenses',
        cefr_label='A1+', blurb='will vs going to.', stage='beginner', order=1,
    )
    c = Client()
    r = c.get('/grammar/?q=Articles')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Future Forms' not in html


@pytest.mark.django_db
def test_grammar_browse_stage_filter(topic_articles):
    GrammarTopic.objects.create(
        slug='conditionals', title='Conditionals', tag='Conditionals',
        cefr_label='B2', blurb='If clauses.', stage='expert', order=1,
    )
    c = Client()
    r = c.get('/grammar/?stage=expert')
    html = r.content.decode()
    assert 'Conditionals' in html
    assert 'Articles (a/an/the)' not in html


@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/"' in html
    assert 'nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_home_hero_grammar_cta_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'hero.grammar">Practice Grammar</a>' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v
```

Expected: all 6 FAIL — `/grammar/` doesn't resolve yet, and the nav/hero links don't exist yet.

- [ ] **Step 3: Create the view (with Task 2's stub)**

Create `config/views_grammar.py`:

```python
from django.http import HttpResponse
from django.shortcuts import render

from vocab.models import GrammarTopic


def grammar_browse(request):
    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    topics = GrammarTopic.objects.order_by('order')
    if query:
        topics = topics.filter(title__icontains=query)
    if stage_filter:
        topics = topics.filter(stage=stage_filter)
    return render(request, 'grammar/browse.html', {
        'topics': topics,
        'stages': GrammarTopic.STAGES,
        'query': query,
        'stage_filter': stage_filter,
    })


def grammar_topic_detail(request, slug):
    # Stub for Task 2 — real implementation replaces only this function
    # body. Registered now, at the exact path Task 2 specifies, because
    # browse.html's {% url 'grammar_topic_detail' topic.slug %} is
    # evaluated at render time regardless of whether the link is clicked.
    return HttpResponse('Grammar topic detail coming in Task 2', status=501)
```

- [ ] **Step 4: Wire the URLs**

In `config/urls.py`, replace:

```python
from config.views_vocab import (
    vocab_browse, vocab_category, vocab_word_detail,
    vocab_quiz_setup, vocab_quiz_play,
)

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
    path('vocab/quiz/', vocab_quiz_setup, name='vocab_quiz_setup'),
    path('vocab/quiz/play/', vocab_quiz_play, name='vocab_quiz_play'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

with:

```python
from config.views_vocab import (
    vocab_browse, vocab_category, vocab_word_detail,
    vocab_quiz_setup, vocab_quiz_play,
)
from config.views_grammar import grammar_browse, grammar_topic_detail

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
    path('vocab/quiz/', vocab_quiz_setup, name='vocab_quiz_setup'),
    path('vocab/quiz/play/', vocab_quiz_play, name='vocab_quiz_play'),
    path('grammar/', grammar_browse, name='grammar_browse'),
    path('grammar/topic/<slug:slug>/', grammar_topic_detail, name='grammar_topic_detail'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 5: Create the browse template**

Create `templates/grammar/browse.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Grammar — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-browse">
  <h1>Grammar</h1>
  <form method="get" class="grammar-filters">
    <input type="text" name="q" value="{{ query }}" placeholder="Search topics…">
    <select name="stage">
      <option value="">All levels</option>
      {% for value, label in stages %}
        <option value="{{ value }}" {% if value == stage_filter %}selected{% endif %}>{{ label }}</option>
      {% endfor %}
    </select>
    <button type="submit" class="btn">Filter</button>
  </form>
  {% if topics %}
  <div class="grammar-topic-grid">
    {% for topic in topics %}
    <a class="grammar-topic-card" href="{% url 'grammar_topic_detail' topic.slug %}">
      <span class="grammar-topic-tag">{{ topic.tag }}</span>
      <span class="grammar-topic-title">{{ topic.title }}</span>
      <span class="grammar-topic-cefr">{{ topic.cefr_label }}</span>
      <span class="grammar-topic-blurb">{{ topic.blurb }}</span>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <p class="grammar-empty">No topics match your search.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 6: Create the browse-page CSS**

Create `static/css/grammar.css`:

```css
.grammar-browse h1{ margin-top: 32px; }

.grammar-filters{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 16px 0 28px;
}
.grammar-filters input[type="text"],
.grammar-filters select{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 0.95rem;
}
.grammar-filters input[type="text"]{ flex: 1; min-width: 180px; }

.grammar-topic-grid{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
  padding-bottom: 48px;
}
.grammar-topic-card{
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  text-decoration: none;
}
.grammar-topic-tag{
  align-self: flex-start;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(var(--violet), 0.12);
  color: rgb(var(--violet));
}
.grammar-topic-title{ font-weight: 700; }
.grammar-topic-cefr{ font-size: 0.8rem; color: var(--muted); }
.grammar-topic-blurb{ font-size: 0.9rem; color: var(--muted); }
.grammar-empty{ color: var(--muted); padding: 24px 0; }
```

- [ ] **Step 7: Enable the nav link**

In `templates/partials/nav.html`, replace:

```html
    <li><span class="disabled" data-i18n="nav.grammar">Grammar</span> <small data-i18n="nav.comingSoon">Coming soon</small></li>
```

with:

```html
    <li><a href="{% url 'grammar_browse' %}" data-i18n="nav.grammar">Grammar</a></li>
```

- [ ] **Step 8: Enable the home hero CTA**

In `templates/home.html`, replace:

```html
    <span class="btn disabled" data-i18n="hero.grammar">Practice Grammar</span>
```

with:

```html
    <a class="btn" href="{% url 'grammar_browse' %}" data-i18n="hero.grammar">Practice Grammar</a>
```

- [ ] **Step 9: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v
```

Expected: all 6 PASS.

- [ ] **Step 10: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES, including the new ones.

- [ ] **Step 11: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/config/urls.py" "VocabLarry Professional Environment/templates/grammar/browse.html" "VocabLarry Professional Environment/templates/partials/nav.html" "VocabLarry Professional Environment/templates/home.html" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add grammar topic browse page

grammar_browse queries the existing GrammarTopic model directly (no
new backend), with an optional title search and a stage filter over
its existing beginner/independent/expert choices. Topics render as a
flat grid — no section grouping, matching the same deferred-scope call
Vocab Browse + Word already made for its own 75-section layer. Nav and
the home hero CTA both go live. grammar_topic_detail is registered as
a 501 stub (Task 2 implements it) since browse.html already links to it.
EOF
)"
```

---

### Task 2: Grammar topic detail page

**Files:**
- Modify: `config/views_grammar.py`
- Create: `templates/grammar/topic_detail.html`
- Modify: `static/css/grammar.css`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: URL name `grammar_topic_detail` at `/grammar/topic/<slug:slug>/`, registered by Task 1 (stub) — this task replaces only the stub function's body.
- Consumes: `GrammarTopic.blocks` (related name from `GrammarLessonBlock.topic`, unchanged model) — each block has `type` (`intro`/`rule`/`table`/`examples`/`tip`), `title`, `body`, `data`, `order`.
- Produces: no new interfaces — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_grammar_pages.py`:

```python
from vocab.models import GrammarLessonBlock


@pytest.fixture
def topic_with_blocks(db):
    topic = GrammarTopic.objects.create(
        slug='present-simple-continuous', title='Present Simple & Continuous',
        tag='Tenses', cefr_label='A1', blurb='Know when to use which.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='intro',
        body='<p>The present simple describes <b>facts</b>.</p>', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='rule', title='Present Simple',
        body='<p>Form: base verb (+ <b>-s</b>).</p>', order=1,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='table', title='Quick map',
        data={'head': ['Use', 'Tense'], 'rows': [['Fact', 'Present simple']]}, order=2,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='examples',
        data={'items': [
            {'en': 'The sun rises in the east.', 'note': 'General fact.'},
            {'en': 'Prices are rising.'},
        ]}, order=3,
    )
    GrammarLessonBlock.objects.create(
        topic=topic, type='tip', body='<p>Use present simple for charts.</p>', order=4,
    )
    return topic


@pytest.mark.django_db
def test_grammar_topic_detail_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert r.status_code == 200
    assert 'Present Simple & Continuous' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/topic/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_topic_detail_renders_intro_html_unescaped(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert '<b>facts</b>' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_renders_rule_title(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert 'Present Simple' in html
    assert '<b>-s</b>' in html


@pytest.mark.django_db
def test_grammar_topic_detail_renders_table(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert '<th>Use</th>' in html
    assert '<td>Fact</td>' in html


@pytest.mark.django_db
def test_grammar_topic_detail_renders_examples(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert 'The sun rises in the east.' in html
    assert 'General fact.' in html
    assert 'Prices are rising.' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k "topic_detail"
```

Expected: all 6 new tests FAIL. The Task 1 stub returns HTTP 501 for every request regardless of slug — so the "renders" tests fail on status code and missing content, and `test_grammar_topic_detail_unknown_slug_404` also fails (it asserts 404, but the stub returns 501 for that slug too).

- [ ] **Step 3: Replace the stub with the real view**

In `config/views_grammar.py`, replace:

```python
from django.http import HttpResponse
from django.shortcuts import render

from vocab.models import GrammarTopic


def grammar_browse(request):
```

with:

```python
from django.shortcuts import get_object_or_404, render

from vocab.models import GrammarTopic


def grammar_browse(request):
```

Then, still in the same file, replace:

```python
def grammar_topic_detail(request, slug):
    # Stub for Task 2 — real implementation replaces only this function
    # body. Registered now, at the exact path Task 2 specifies, because
    # browse.html's {% url 'grammar_topic_detail' topic.slug %} is
    # evaluated at render time regardless of whether the link is clicked.
    return HttpResponse('Grammar topic detail coming in Task 2', status=501)
```

with:

```python
def grammar_topic_detail(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    blocks = topic.blocks.order_by('order')
    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'blocks': blocks,
    })
```

- [ ] **Step 4: Create the topic detail template**

Create `templates/grammar/topic_detail.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ topic.title }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-topic-detail">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_browse' %}">Grammar</a> / {{ topic.title }}
  </p>
  <h1>{{ topic.title }}</h1>
  <p class="grammar-topic-detail-cefr">{{ topic.cefr_label }}</p>
  <p class="grammar-topic-detail-blurb">{{ topic.blurb }}</p>
  {% for block in blocks %}
    {% if block.type == 'intro' %}
      <div class="grammar-block grammar-block-intro">{{ block.body|safe }}</div>
    {% elif block.type == 'rule' %}
      <div class="grammar-block grammar-block-rule">
        {% if block.title %}<h2>{{ block.title }}</h2>{% endif %}
        {{ block.body|safe }}
      </div>
    {% elif block.type == 'table' %}
      <div class="grammar-block grammar-block-table">
        {% if block.title %}<h2>{{ block.title }}</h2>{% endif %}
        <table>
          <thead>
            <tr>
              {% for h in block.data.head %}<th>{{ h }}</th>{% endfor %}
            </tr>
          </thead>
          <tbody>
            {% for row in block.data.rows %}
            <tr>
              {% for cell in row %}<td>{{ cell }}</td>{% endfor %}
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    {% elif block.type == 'examples' %}
      <div class="grammar-block grammar-block-examples">
        {% if block.title %}<h2>{{ block.title }}</h2>{% endif %}
        <ul class="grammar-examples-list">
          {% for item in block.data.items %}
          <li>
            <span class="grammar-example-en">{{ item.en }}</span>
            {% if item.note %}<span class="grammar-example-note">{{ item.note }}</span>{% endif %}
          </li>
          {% endfor %}
        </ul>
      </div>
    {% elif block.type == 'tip' %}
      <div class="grammar-block grammar-block-tip">{{ block.body|safe }}</div>
    {% endif %}
  {% endfor %}
</section>
{% endblock %}
```

- [ ] **Step 5: Add the topic-detail CSS**

Append to `static/css/grammar.css`:

```css
.grammar-breadcrumb{ color: var(--muted); font-size: 0.9rem; margin: 24px 0 4px; }
.grammar-breadcrumb a{ color: var(--muted); }
.grammar-topic-detail-cefr{
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(var(--violet), 0.12);
  color: rgb(var(--violet));
  margin-bottom: 8px;
}
.grammar-topic-detail-blurb{ color: var(--muted); margin-bottom: 24px; }

.grammar-block{ margin: 20px 0; line-height: 1.6; }
.grammar-block-rule,
.grammar-block-tip{
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--card-bg);
}
.grammar-block-table table{
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
}
.grammar-block-table th,
.grammar-block-table td{
  border: 1px solid var(--border);
  padding: 8px 12px;
  text-align: left;
  font-size: 0.9rem;
}
.grammar-examples-list{
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.grammar-example-en{ display: block; }
.grammar-example-note{ display: block; color: var(--muted); font-size: 0.85rem; }
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v
```

Expected: all tests in the file PASS (Task 1's 6 plus Task 2's 6).

- [ ] **Step 7: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES.

- [ ] **Step 8: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/topic_detail.html" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add grammar topic detail page

grammar_topic_detail replaces its 501 stub, rendering a topic's
GrammarLessonBlocks in order with per-type markup: intro/tip render
body as trusted safe HTML, rule renders inline (no scroll-pinned
effect), table renders data.head/rows as a real <table>, examples
renders data.items with note shown only when present. No practice/quiz
UI — that's a separate future sub-project, as is the 12-section
grouping layer this deliberately skips (same call Vocab Browse + Word
made for its own section layer).
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** every spec bullet has a corresponding step — no new backend (confirmed, only templates/views/urls touched), flat grid no sections (Task 1 Step 5 template has no grouping), search+stage filters (Task 1 Steps 1/3/5), no progress UI (no step adds any), per-type block rendering exactly as specified including the `|safe` trust boundary and inline (non-scroll-pinned) rule treatment (Task 2 Step 4), nav+home CTA enabled (Task 1 Steps 7/8), 404 on unknown slug (Task 2 Step 3), testing fully covers both pages with no manual-browser step (matches the spec's stated testing posture).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code.
- **Type consistency:** `grammar_topic_detail(request, slug)`'s signature matches between Task 1's stub and Task 2's real implementation, and matches the URL pattern `<slug:slug>` in both cases. Context keys (`topics`, `stages`, `query`, `stage_filter` in Task 1; `topic`, `blocks` in Task 2) are used consistently between the views and their templates.
