# VocabLarry Professional Environment — Vocabulary Word Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `/vocabulary/word/` "Coming soon" stub with a real, filterable, paginated sitewide word index — production's "Word" nav tab, rebuilt on VLPE's own server-rendering conventions rather than production's client-side/modal mechanism.

**Architecture:** Two sequential tasks. Task 1 is pure CSS (new chip-color and card-tag rules), changes no markup, verified only by the full suite staying green. Task 2 replaces the stub view/template with the complete guest-visible page: search + category dropdown + stage tabs + CEFR chips + hover-reveal card grid + pagination, matching `vocab_browse`'s existing GET-query-param, server-side-filtering convention. Task 3 adds the authenticated-only layer on top: a progress chip filter and the existing per-word progress toggle, reusing `vocab-word.js`'s already-built `window.vocabToggleWord` handler — no new JS.

**Tech Stack:** Django templates, server-side ORM filtering (no client-side JS filtering), plain CSS (existing custom-property/chip system), pytest + Django test client.

## Global Constraints

- Only files under `VocabLarry Professional Environment/` may be modified. `VocabLarry/` (production) is read-only reference material.
- `--violet` is a space-separated RGB triplet custom property — always `rgb(var(--violet) / X)`, never `rgba(var(--violet), X)` (silent-failure bug class already documented in this codebase).
- All filtering is server-side via GET query params (`q`, `category`, `stage`, `cefr`, `progress`, `page`) and plain `<a href>`/`<form method="get">` — no client-side JS filtering logic. The category `<select>` submits via a plain "Filter" button, not an `onchange` auto-submit — zero new inline JS on this page until Task 3's progress-toggle wiring (which reuses existing `vocab-word.js`, not new logic).
- Category filtering is a plain `<select>` dropdown (250 real categories — the same call already made for Vocab Quiz's setup page), not chips. Stage and CEFR are chip rows.
- No cross-reference links (word→word) on this page's cards — `_resolve_word_refs` stays exclusive to `word_detail.html`. Only the word headword itself is a link (to `vocabulary_word_detail`); the rest of each card is not a navigation target.
- No bulk actions (`Mark All`/`Reset All`) on this page.
- No new i18n keys for this page's new content (search placeholder, stage/progress labels) — matches the Vocab Quiz visual retrofit's identical precedent (new page-specific text is out of scope for the client-side i18n dict). Existing shared keys already in the stub (`nav.category`/`nav.word`/`nav.quiz`) are kept as-is.
- No changes to `word_detail.html`, `_resolve_word_refs`, `vocab-word.js`, or `urls.py` (the `vocabulary_word_list` URL name/path already exists and is unchanged — only its view function body and template change).

---

### Task 1: CSS foundation — Word-page CEFR/progress chip colors + card category-tag style

**Files:**
- Modify: `VocabLarry Professional Environment/static/css/base.css:441-452` (the combined CEFR chip-color selector list) and the status-chip rules directly below it
- Modify: `VocabLarry Professional Environment/static/css/vocab.css` (append new `.word-card .word-cat` rule)

**Interfaces:**
- Consumes: nothing new.
- Produces: CSS attribute selectors `data-word-cefr="X"` (12 codes) and `data-word-status="learned"/"little"/"none"` that Task 2/3's templates will use on `.chip` elements; a `.word-cat` class Task 2's template will use inside `.word-card .face`.
- This task changes no markup, so no existing test's assertions change. Verified by re-running the full existing suite (must stay green) — there is no automated way to assert CSS content in this codebase's test suite, matching the established precedent from the Vocab Quiz and Grammar Quiz visual retrofits' own CSS-foundation tasks.

- [ ] **Step 1: Extend the 12 CEFR chip-color rules in base.css to also match `data-word-cefr`**

In `VocabLarry Professional Environment/static/css/base.css`, find these 12 lines (added most recently by the Grammar Quiz visual retrofit, extending the original 2-attribute list to 3):

```css
.chip.active[data-browse-cefr="A1"],.chip.active[data-quiz-cefr="A1"],.chip.active[data-grammar-cefr="A1"]{ background: var(--a1); }
.chip.active[data-browse-cefr="A1+"],.chip.active[data-quiz-cefr="A1+"],.chip.active[data-grammar-cefr="A1+"]{ background: var(--a1p); }
.chip.active[data-browse-cefr="A2"],.chip.active[data-quiz-cefr="A2"],.chip.active[data-grammar-cefr="A2"]{ background: var(--a2); }
.chip.active[data-browse-cefr="A2+"],.chip.active[data-quiz-cefr="A2+"],.chip.active[data-grammar-cefr="A2+"]{ background: var(--a2p); }
.chip.active[data-browse-cefr="B1"],.chip.active[data-quiz-cefr="B1"],.chip.active[data-grammar-cefr="B1"]{ background: var(--b1); }
.chip.active[data-browse-cefr="B1+"],.chip.active[data-quiz-cefr="B1+"],.chip.active[data-grammar-cefr="B1+"]{ background: var(--b1p); }
.chip.active[data-browse-cefr="B2"],.chip.active[data-quiz-cefr="B2"],.chip.active[data-grammar-cefr="B2"]{ background: var(--b2); }
.chip.active[data-browse-cefr="B2+"],.chip.active[data-quiz-cefr="B2+"],.chip.active[data-grammar-cefr="B2+"]{ background: var(--b2p); }
.chip.active[data-browse-cefr="C1"],.chip.active[data-quiz-cefr="C1"],.chip.active[data-grammar-cefr="C1"]{ background: var(--c1); }
.chip.active[data-browse-cefr="C1+"],.chip.active[data-quiz-cefr="C1+"],.chip.active[data-grammar-cefr="C1+"]{ background: var(--c1p); }
.chip.active[data-browse-cefr="C2"],.chip.active[data-quiz-cefr="C2"],.chip.active[data-grammar-cefr="C2"]{ background: var(--c2); }
.chip.active[data-browse-cefr="C2+"],.chip.active[data-quiz-cefr="C2+"],.chip.active[data-grammar-cefr="C2+"]{ background: var(--c2p); }
```

Replace with (adding `,.chip.active[data-word-cefr="X"]` to each):

```css
.chip.active[data-browse-cefr="A1"],.chip.active[data-quiz-cefr="A1"],.chip.active[data-grammar-cefr="A1"],.chip.active[data-word-cefr="A1"]{ background: var(--a1); }
.chip.active[data-browse-cefr="A1+"],.chip.active[data-quiz-cefr="A1+"],.chip.active[data-grammar-cefr="A1+"],.chip.active[data-word-cefr="A1+"]{ background: var(--a1p); }
.chip.active[data-browse-cefr="A2"],.chip.active[data-quiz-cefr="A2"],.chip.active[data-grammar-cefr="A2"],.chip.active[data-word-cefr="A2"]{ background: var(--a2); }
.chip.active[data-browse-cefr="A2+"],.chip.active[data-quiz-cefr="A2+"],.chip.active[data-grammar-cefr="A2+"],.chip.active[data-word-cefr="A2+"]{ background: var(--a2p); }
.chip.active[data-browse-cefr="B1"],.chip.active[data-quiz-cefr="B1"],.chip.active[data-grammar-cefr="B1"],.chip.active[data-word-cefr="B1"]{ background: var(--b1); }
.chip.active[data-browse-cefr="B1+"],.chip.active[data-quiz-cefr="B1+"],.chip.active[data-grammar-cefr="B1+"],.chip.active[data-word-cefr="B1+"]{ background: var(--b1p); }
.chip.active[data-browse-cefr="B2"],.chip.active[data-quiz-cefr="B2"],.chip.active[data-grammar-cefr="B2"],.chip.active[data-word-cefr="B2"]{ background: var(--b2); }
.chip.active[data-browse-cefr="B2+"],.chip.active[data-quiz-cefr="B2+"],.chip.active[data-grammar-cefr="B2+"],.chip.active[data-word-cefr="B2+"]{ background: var(--b2p); }
.chip.active[data-browse-cefr="C1"],.chip.active[data-quiz-cefr="C1"],.chip.active[data-grammar-cefr="C1"],.chip.active[data-word-cefr="C1"]{ background: var(--c1); }
.chip.active[data-browse-cefr="C1+"],.chip.active[data-quiz-cefr="C1+"],.chip.active[data-grammar-cefr="C1+"],.chip.active[data-word-cefr="C1+"]{ background: var(--c1p); }
.chip.active[data-browse-cefr="C2"],.chip.active[data-quiz-cefr="C2"],.chip.active[data-grammar-cefr="C2"],.chip.active[data-word-cefr="C2"]{ background: var(--c2); }
.chip.active[data-browse-cefr="C2+"],.chip.active[data-quiz-cefr="C2+"],.chip.active[data-grammar-cefr="C2+"],.chip.active[data-word-cefr="C2+"]{ background: var(--c2p); }
```

- [ ] **Step 2: Add new per-word progress chip color rules**

Directly after the 12 lines above (before the existing `.chip.active[data-browse-status="completed"]...` rules), add:

```css
/* Per-word progress chips (Word page) — intentionally separate rules
   from the category-aggregate completed/inProgress/notStarted rules
   above: those use different color tokens (--c1/--muted for a partial
   aggregate), while a single word's own state should match the exact
   green/amber already used by .card-toggle/.learn-state-btn elsewhere. */
.chip.active[data-word-status="learned"]{ background: #22c55e; }
.chip.active[data-word-status="little"]{ background: #f59e0b; }
.chip.active[data-word-status="none"]{ background: var(--muted); }
```

- [ ] **Step 3: Add the word-card category-tag style to vocab.css**

Append to the end of `VocabLarry Professional Environment/static/css/vocab.css`:

```css

/* Category tag on the sitewide Word list's cards — this page spans all
   categories, unlike category_word_list.html's single-category grid, so
   each card needs to show which category a word belongs to. */
.word-card .word-cat{
  font-size: .7rem; color: var(--muted); text-decoration: none;
  display: inline-block; margin-top: 4px;
}
.word-card .word-cat:hover{ color: rgb(var(--violet)); text-decoration: underline; }
```

- [ ] **Step 4: Run the full test suite to confirm no regressions**

Run (from `VocabLarry Professional Environment/`): `pytest`
Expected: all 269 existing tests pass (this task changed no markup, so no test assertion is affected).

- [ ] **Step 5: Commit**

```bash
git add "VocabLarry Professional Environment/static/css/base.css" "VocabLarry Professional Environment/static/css/vocab.css"
git commit -m "feat(vlpe): add Word-page CEFR/progress chip colors and card category-tag style"
```

---

### Task 2: Guest-visible word list — search, category/stage/CEFR filters, hover-reveal cards, pagination

**Files:**
- Modify: `VocabLarry Professional Environment/config/views_vocab.py` (replace the `vocabulary_word_list` stub function; add a new `WORD_STAGES` module-level constant)
- Modify: `VocabLarry Professional Environment/templates/vocab/word_list.html` (full-file rewrite)
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py` (remove the obsolete stub test, add new tests)

**Interfaces:**
- Consumes: `_pagination_window(current, total)` (already defined in `views_vocab.py`, used by `vocab_category`) — reused as-is, no signature change. CSS classes from Task 1 (`data-word-cefr`, `.word-cat`) plus pre-existing `.filters`/`.search-row`/`.filter-row`/`.filter-label`/`.chip`/`.clear-btn`/`.card-grid`/`.word-card`/`.face`/`.pos`/`.reveal`/`.rdef`/`.rrow`/`.rex`/`.cefr-badge`/`.pagination`/`.page-btn`/`.page-ellipsis`.
- Produces: `WORD_STAGES = [(id, label, [cefr_codes...]), ...]` — a module-level constant in `views_vocab.py` that Task 3 does not need to change. Context keys `page_obj`, `pagination_window`, `categories`, `cefr_levels`, `stages`, `query`, `category_filter`, `stage_filter`, `cefr_filter` — Task 3 adds `progress_filter` alongside these without renaming any of them.

This task ships the entire page for guests: search, category dropdown, stage tabs, CEFR chips, hover-reveal cards (definition/synonyms/antonyms/example, no progress toggle yet), pagination, and "Clear filters". No progress chip, no per-card toggle, no auth-conditional behavior at all yet — Task 3 adds that layer on top without touching any of this task's code paths.

- [ ] **Step 1: Remove the obsolete stub test and write the new failing tests**

In `VocabLarry Professional Environment/tests/test_vocab_pages.py`, delete this test (it asserts the "Coming soon" placeholder, which this task removes):

```python
@pytest.mark.django_db
def test_vocabulary_word_list_stub_renders():
    c = Client()
    r = c.get('/vocabulary/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'Section 01 / Vocabulary' in html
    assert '<h1>Word</h1>' in html
    assert 'Coming soon.' in html
```

Add these tests in its place (same location in the file). They need `from django.db import connection` and `from django.test.utils import CaptureQueriesContext` added to the file's imports:

```python
@pytest.mark.django_db
def test_vocabulary_word_list_renders(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small domesticated feline.', category=category, cefr_level=cefr_a1, order=1)
    c = Client()
    r = c.get('/vocabulary/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert '<h1>Word</h1>' in html
    assert 'Cat' in html
    assert 'A small domesticated feline.' in html


@pytest.mark.django_db
def test_vocabulary_word_list_search_matches_word_definition_synonyms_antonyms(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small domesticated feline.', category=category, cefr_level=cefr_a1, order=1)
    Word.objects.create(word='Dog', definition='A loyal companion.', synonyms=['Canine'], category=category, cefr_level=cefr_a1, order=2)
    Word.objects.create(word='Fish', definition='Lives in water.', antonyms=['Bird'], category=category, cefr_level=cefr_a1, order=3)
    c = Client()

    r = c.get('/vocabulary/word/', {'q': 'feline'})
    html = r.content.decode()
    assert 'Cat' in html and 'Dog' not in html and 'Fish' not in html

    r = c.get('/vocabulary/word/', {'q': 'canine'})
    html = r.content.decode()
    assert 'Dog' in html and 'Cat' not in html

    r = c.get('/vocabulary/word/', {'q': 'bird'})
    html = r.content.decode()
    assert 'Fish' in html and 'Cat' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_category_filter(cefr_a1):
    animals = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    food = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A feline.', category=animals, cefr_level=cefr_a1, order=1)
    Word.objects.create(word='Bread', definition='A baked food.', category=food, cefr_level=cefr_a1, order=1)
    c = Client()
    r = c.get('/vocabulary/word/', {'category': 'animals'})
    html = r.content.decode()
    assert 'Cat' in html and 'Bread' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_stage_filter(cefr_a1, cefr_b1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    Word.objects.create(word='Contemplate', definition='To think deeply.', category=category, cefr_level=cefr_b1, order=2)
    c = Client()
    r = c.get('/vocabulary/word/', {'stage': 'basic'})
    html = r.content.decode()
    assert 'Cat' in html and 'Contemplate' not in html

    r = c.get('/vocabulary/word/', {'stage': 'intermediate'})
    html = r.content.decode()
    assert 'Contemplate' in html and 'Cat' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_cefr_filter(cefr_a1, cefr_b1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    Word.objects.create(word='Contemplate', definition='To think deeply.', category=category, cefr_level=cefr_b1, order=2)
    c = Client()
    r = c.get('/vocabulary/word/', {'cefr': 'A1'})
    html = r.content.decode()
    assert 'Cat' in html and 'Contemplate' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    c = Client()
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert html.count('class="word-card') == 25
    assert 'class="pagination"' in html

    r2 = c.get('/vocabulary/word/', {'page': 2})
    html2 = r2.content.decode()
    assert html2.count('class="word-card') == 5


@pytest.mark.django_db
def test_vocabulary_word_list_out_of_range_page_falls_back_to_last_page(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    c = Client()
    r = c.get('/vocabulary/word/', {'page': 999})
    assert r.status_code == 200
    html = r.content.decode()
    assert html.count('class="word-card') == 5


@pytest.mark.django_db
def test_vocabulary_word_list_category_dropdown_lists_all_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert '<option value="animals">Animals</option>' in html
    assert '<option value="food">Food</option>' in html


@pytest.mark.django_db
def test_vocabulary_word_list_word_links_to_detail_page(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    c = Client()
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert f'href="/vocabulary/word/{word.pk}/"' in html


@pytest.mark.django_db
def test_vocabulary_word_list_clear_filters_link_present(cefr_a1):
    c = Client()
    r = c.get('/vocabulary/word/', {'q': 'cat', 'cefr': 'A1'})
    html = r.content.decode()
    assert 'class="clear-btn" href="/vocabulary/word/"' in html


@pytest.mark.django_db
def test_vocabulary_word_list_query_count_does_not_scale_with_word_count(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(5):
        Word.objects.create(word=f'Word{i}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    c = Client()
    with CaptureQueriesContext(connection) as ctx_small:
        c.get('/vocabulary/word/')
    small_count = len(ctx_small.captured_queries)

    for i in range(5, 30):
        Word.objects.create(word=f'Word{i}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    with CaptureQueriesContext(connection) as ctx_large:
        c.get('/vocabulary/word/')
    large_count = len(ctx_large.captured_queries)

    assert large_count == small_count
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_word_list" -v`
Expected: FAIL — the stub view returns only "Coming soon", none of the new assertions match yet.

- [ ] **Step 3: Add the `WORD_STAGES` constant and replace the `vocabulary_word_list` view**

In `VocabLarry Professional Environment/config/views_vocab.py`, add this module-level constant directly above the existing `def vocabulary_word_list(request):` stub (currently at line 162-163):

```python
WORD_STAGES = [
    ('basic', 'Basic', ['A1', 'A1+', 'A2', 'A2+']),
    ('intermediate', 'Intermediate', ['B1', 'B1+', 'B2', 'B2+']),
    ('advanced', 'Advanced', ['C1', 'C1+', 'C2', 'C2+']),
]
```

Replace the existing stub:

```python
def vocabulary_word_list(request):
    return render(request, 'vocab/word_list.html')
```

with:

```python
@ensure_csrf_cookie
def vocabulary_word_list(request):
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()

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

    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

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
    })
```

Note: `words` becomes a plain Python list whenever `query` is set (JSONField list-substring matching has no portable ORM expression) — but only after the `category`/`stage`/`cefr` DB-level filters have already narrowed it, so it never scans the full unfiltered word table. The `else: words = list(words)` branch keeps the type consistent (`Paginator` accepts either a queryset or a list, but this task's tests and Task 3's additions assume a plain list either way).

- [ ] **Step 4: Rewrite word_list.html**

Replace the entire content of `VocabLarry Professional Environment/templates/vocab/word_list.html` with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Word — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-word-list">
  <h1>Word</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip active" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>

  <div class="filters">
    <form method="get" class="search-row">
      <input type="search" name="q" value="{{ query }}" placeholder="Search words, definitions, synonyms…">
      <select name="category">
        <option value="">All categories</option>
        {% for category in categories %}
        <option value="{{ category.slug }}"{% if category.slug == category_filter %} selected{% endif %}>{{ category.name }}</option>
        {% endfor %}
      </select>
      {% if stage_filter %}<input type="hidden" name="stage" value="{{ stage_filter }}">{% endif %}
      {% if cefr_filter %}<input type="hidden" name="cefr" value="{{ cefr_filter }}">{% endif %}
      <button type="submit" class="btn">Filter</button>
    </form>
    <div class="filter-row">
      <span class="filter-label">Stage</span>
      <a class="chip{% if not stage_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}">All</a>
      {% for sid, label, codes in stages %}
      <a class="chip{% if stage_filter == sid %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&stage={{ sid }}">{{ label }}</a>
      {% endfor %}
    </div>
    <div class="filter-row">
      <span class="filter-label">CEFR</span>
      <a class="chip{% if not cefr_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}">All</a>
      {% for level in cefr_levels %}
      <a class="chip{% if cefr_filter == level.code %} active{% endif %}" data-word-cefr="{{ level.code }}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}&cefr={{ level.code }}">{{ level.code }}</a>
      {% endfor %}
    </div>
    <div class="filter-row" style="justify-content:flex-end;">
      <a class="clear-btn" href="{% url 'vocabulary_word_list' %}">Clear filters</a>
    </div>
  </div>

  {% if page_obj %}
  <div class="card-grid">
    {% for word in page_obj %}
    <div class="word-card">
      <div class="face">
        <div>
          <div class="word"><a href="{% url 'vocabulary_word_detail' word.pk %}">{{ word.word }}</a></div>
          {% if word.pos %}<div class="pos">{{ word.pos }}</div>{% endif %}
          <a class="word-cat" href="{% url 'vocabulary_category_detail' word.category.slug %}">{{ word.category.name }}</a>
        </div>
        {% if word.cefr_level %}<span class="cefr-badge {{ word.cefr_level.code }}">{{ word.cefr_level.code }}</span>{% endif %}
      </div>
      <div class="reveal">
        <div class="rdef">{{ word.definition }}</div>
        {% if word.synonyms %}<div class="rrow"><b>Synonyms:</b> {{ word.synonyms|join:", " }}</div>{% endif %}
        {% if word.antonyms %}<div class="rrow"><b>Antonyms:</b> {{ word.antonyms|join:", " }}</div>{% endif %}
        {% if word.example %}<div class="rex">"{{ word.example }}"</div>{% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="pagination">
    <a class="page-btn{% if not page_obj.has_previous %} disabled{% endif %}"
       href="{% if page_obj.has_previous %}?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&page={{ page_obj.previous_page_number }}{% else %}#{% endif %}">«</a>
    {% for p in pagination_window %}
      {% if p is None %}<span class="page-ellipsis">…</span>
      {% else %}<a class="page-btn{% if p == page_obj.number %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&page={{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
    <a class="page-btn{% if not page_obj.has_next %} disabled{% endif %}"
       href="{% if page_obj.has_next %}?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&page={{ page_obj.next_page_number }}{% else %}#{% endif %}">»</a>
  </nav>
  {% endif %}
  {% else %}
  <p class="vocab-empty">No words match your search.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `pytest tests/test_vocab_pages.py -k "vocabulary_word_list" -v`
Expected: PASS — all tests from Step 1.

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass (269 existing minus the 1 removed stub test, plus the 11 new tests from Step 1 = 279).

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be fully verified by the Python test suite (visual hover-reveal behavior). Using a browser (or Playwright), navigate to `/vocabulary/word/` and confirm:
- The card grid renders with hover-reveal working (definition/synonyms/antonyms/example appear on hover, hidden at rest).
- Selecting a category from the dropdown and clicking "Filter" narrows the grid correctly.
- Clicking a Stage tab and a CEFR chip both narrow the grid and show the correct chip as active (with the correct CEFR color).
- Typing a search term and submitting narrows the grid to matching words only.
- Pagination links navigate between pages while preserving the currently active filters.
- "Clear filters" resets to the unfiltered, page-1 view.
- Both dark (default) and light theme render the filter bar and cards correctly.

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/config/views_vocab.py" "VocabLarry Professional Environment/templates/vocab/word_list.html" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): replace Vocabulary Word stub with a real filterable, paginated word index"
```

---

### Task 3: Authenticated progress — progress chip filter + inline per-word progress toggle

**Files:**
- Modify: `VocabLarry Professional Environment/config/views_vocab.py:vocabulary_word_list` (add progress filtering + per-word `learn_state` annotation)
- Modify: `VocabLarry Professional Environment/templates/vocab/word_list.html` (add the progress filter-row, the learn-state-row inside each card's reveal, and the toggle-wiring script)
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py` (add new tests)

**Interfaces:**
- Consumes: Task 2's `vocabulary_word_list` view and template, `WORD_STAGES`, and all Task 2 context keys (extends, does not rename, any of them). The existing `window.vocabToggleWord(btn)` handler from `static/js/vocab-word.js` (already used identically by `category_word_list.html`) and the existing `.card-toggle`/`data-word-id`/`data-state` markup contract it binds to.
- Produces: no new interfaces consumed elsewhere — this is the final layer on this page.

- [ ] **Step 1: Write the failing tests**

Add to `VocabLarry Professional Environment/tests/test_vocab_pages.py` (after the tests added in Task 2):

```python
@pytest.mark.django_db
def test_vocabulary_word_list_progress_chip_hidden_for_guests(cefr_a1):
    c = Client()
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert 'data-word-status' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_progress_chip_shown_for_authenticated_users(cefr_a1, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert 'data-word-status="learned"' in html
    assert 'data-word-status="little"' in html
    assert 'data-word-status="none"' in html


@pytest.mark.django_db
def test_vocabulary_word_list_progress_filter_learned(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    w2 = Word.objects.create(word='Dog', definition='A canine.', category=category, cefr_level=cefr_a1, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/word/', {'progress': 'learned'})
    html = r.content.decode()
    assert '>Cat<' in html and '>Dog<' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_progress_filter_little(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    w2 = Word.objects.create(word='Dog', definition='A canine.', category=category, cefr_level=cefr_a1, order=2)
    regular_user.learn_map = {str(w1.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/word/', {'progress': 'little'})
    html = r.content.decode()
    assert '>Cat<' in html and '>Dog<' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_progress_filter_none(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    w2 = Word.objects.create(word='Dog', definition='A canine.', category=category, cefr_level=cefr_a1, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/word/', {'progress': 'none'})
    html = r.content.decode()
    assert '>Dog<' in html and '>Cat<' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_progress_filter_ignored_for_guests(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    c = Client()
    r = c.get('/vocabulary/word/', {'progress': 'learned'})
    html = r.content.decode()
    assert '>Cat<' in html


@pytest.mark.django_db
def test_vocabulary_word_list_toggle_button_present_for_authenticated_user(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert f'data-word-id="{word.pk}"' in html
    assert 'class="card-toggle"' in html
    assert 'vocab-word.js' in html


@pytest.mark.django_db
def test_vocabulary_word_list_toggle_button_absent_for_guest(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A feline.', category=category, cefr_level=cefr_a1, order=1)
    c = Client()
    r = c.get('/vocabulary/word/')
    html = r.content.decode()
    assert 'class="card-toggle"' not in html
    assert 'vocab-word.js' not in html


@pytest.mark.django_db
def test_vocabulary_word_list_authenticated_query_count_does_not_scale_with_word_count(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(5):
        Word.objects.create(word=f'Word{i}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    c = Client()
    c.force_login(regular_user)
    with CaptureQueriesContext(connection) as ctx_small:
        c.get('/vocabulary/word/')
    small_count = len(ctx_small.captured_queries)

    for i in range(5, 30):
        Word.objects.create(word=f'Word{i}', definition='def', category=category, cefr_level=cefr_a1, order=i)
    with CaptureQueriesContext(connection) as ctx_large:
        c.get('/vocabulary/word/')
    large_count = len(ctx_large.captured_queries)

    assert large_count == small_count
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest tests/test_vocab_pages.py -k "progress or toggle" -v`
Expected: FAIL — Task 2's view/template have no progress filtering or toggle markup yet.

- [ ] **Step 3: Add progress filtering and `learn_state` annotation to the view**

In `VocabLarry Professional Environment/config/views_vocab.py`, in `vocabulary_word_list` (from Task 2), add `progress_filter` alongside the other query-param reads:

```python
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()
```

Directly after the existing `query` filtering block (the `if query: ... else: words = list(words)` from Task 2) and before the `paginator = Paginator(words, 25)` line, insert:

```python
    if request.user.is_authenticated and progress_filter in ('learned', 'little', 'none'):
        learn_map = request.user.learn_map

        def _matches_progress(w):
            state = learn_map.get(str(w.pk))
            if progress_filter == 'none':
                return state not in ('learned', 'little')
            return state == progress_filter

        words = [w for w in words if _matches_progress(w)]
```

The existing two lines from Task 2 (`paginator = Paginator(words, 25)` and `page_obj = paginator.get_page(request.GET.get('page', 1))`) stay unchanged. Directly after them, insert this new per-word `learn_state` annotation block (mirrors `vocab_category`'s existing identical pattern) — the surrounding two lines are shown below only for placement context, not to be duplicated:

```python
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    # --- new lines below, inserted directly after the two existing lines above ---
    if request.user.is_authenticated:
        learn_map = request.user.learn_map
        for word in page_obj:
            word.learn_state = learn_map.get(str(word.pk))
    else:
        for word in page_obj:
            word.learn_state = None
```

Finally, add `'progress_filter': progress_filter,` to the `render(...)` context dict, alongside the existing `'cefr_filter': cefr_filter,` line.

- [ ] **Step 4: Rewrite the template with the progress filter-row, learn-state-row, and toggle script**

Replace the entire content of `VocabLarry Professional Environment/templates/vocab/word_list.html` with (this is Task 2's version with `progress_filter` propagated through every filter link/hidden-input/pagination link, the new auth-only Progress filter-row added, and the auth-only learn-state-row + toggle script added — every difference from Task 2's version is a `progress_filter`-related addition, nothing else changes):

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Word — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-word-list">
  <h1>Word</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip active" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>

  <div class="filters">
    <form method="get" class="search-row">
      <input type="search" name="q" value="{{ query }}" placeholder="Search words, definitions, synonyms…">
      <select name="category">
        <option value="">All categories</option>
        {% for category in categories %}
        <option value="{{ category.slug }}"{% if category.slug == category_filter %} selected{% endif %}>{{ category.name }}</option>
        {% endfor %}
      </select>
      {% if stage_filter %}<input type="hidden" name="stage" value="{{ stage_filter }}">{% endif %}
      {% if cefr_filter %}<input type="hidden" name="cefr" value="{{ cefr_filter }}">{% endif %}
      {% if progress_filter %}<input type="hidden" name="progress" value="{{ progress_filter }}">{% endif %}
      <button type="submit" class="btn">Filter</button>
    </form>
    <div class="filter-row">
      <span class="filter-label">Stage</span>
      <a class="chip{% if not stage_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}">All</a>
      {% for sid, label, codes in stages %}
      <a class="chip{% if stage_filter == sid %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&stage={{ sid }}">{{ label }}</a>
      {% endfor %}
    </div>
    <div class="filter-row">
      <span class="filter-label">CEFR</span>
      <a class="chip{% if not cefr_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}">All</a>
      {% for level in cefr_levels %}
      <a class="chip{% if cefr_filter == level.code %} active{% endif %}" data-word-cefr="{{ level.code }}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&cefr={{ level.code }}">{{ level.code }}</a>
      {% endfor %}
    </div>
    {% if user.is_authenticated %}
    <div class="filter-row">
      <span class="filter-label">Progress</span>
      <a class="chip{% if not progress_filter %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}">All</a>
      <a class="chip{% if progress_filter == 'learned' %} active{% endif %}" data-word-status="learned" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=learned">Learned</a>
      <a class="chip{% if progress_filter == 'little' %} active{% endif %}" data-word-status="little" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=little">Little Bit</a>
      <a class="chip{% if progress_filter == 'none' %} active{% endif %}" data-word-status="none" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=none">Not Learned</a>
    </div>
    {% endif %}
    <div class="filter-row" style="justify-content:flex-end;">
      <a class="clear-btn" href="{% url 'vocabulary_word_list' %}">Clear filters</a>
    </div>
  </div>

  {% if page_obj %}
  <div class="card-grid">
    {% for word in page_obj %}
    <div class="word-card{% if word.learn_state == 'learned' %} learned{% elif word.learn_state == 'little' %} little{% endif %}">
      <div class="face">
        <div>
          <div class="word"><a href="{% url 'vocabulary_word_detail' word.pk %}">{{ word.word }}</a></div>
          {% if word.pos %}<div class="pos">{{ word.pos }}</div>{% endif %}
          <a class="word-cat" href="{% url 'vocabulary_category_detail' word.category.slug %}">{{ word.category.name }}</a>
        </div>
        {% if word.cefr_level %}<span class="cefr-badge {{ word.cefr_level.code }}">{{ word.cefr_level.code }}</span>{% endif %}
      </div>
      <div class="reveal">
        <div class="rdef">{{ word.definition }}</div>
        {% if word.synonyms %}<div class="rrow"><b>Synonyms:</b> {{ word.synonyms|join:", " }}</div>{% endif %}
        {% if word.antonyms %}<div class="rrow"><b>Antonyms:</b> {{ word.antonyms|join:", " }}</div>{% endif %}
        {% if word.example %}<div class="rex">"{{ word.example }}"</div>{% endif %}
        {% if user.is_authenticated %}
        <div class="learn-state-row">
          <span class="learn-state-label">Progress:</span>
          <button type="button" class="card-toggle" data-word-id="{{ word.pk }}"
                  data-state="{{ word.learn_state|default:'none' }}">
            {% if word.learn_state == 'learned' %}Learned{% elif word.learn_state == 'little' %}Little Bit{% else %}Not Learned{% endif %}
          </button>
        </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="pagination">
    <a class="page-btn{% if not page_obj.has_previous %} disabled{% endif %}"
       href="{% if page_obj.has_previous %}?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ page_obj.previous_page_number }}{% else %}#{% endif %}">«</a>
    {% for p in pagination_window %}
      {% if p is None %}<span class="page-ellipsis">…</span>
      {% else %}<a class="page-btn{% if p == page_obj.number %} active{% endif %}" href="?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
    <a class="page-btn{% if not page_obj.has_next %} disabled{% endif %}"
       href="{% if page_obj.has_next %}?q={{ query|urlencode }}{% if category_filter %}&category={{ category_filter }}{% endif %}{% if stage_filter %}&stage={{ stage_filter }}{% endif %}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}&page={{ page_obj.next_page_number }}{% else %}#{% endif %}">»</a>
  </nav>
  {% endif %}
  {% else %}
  <p class="vocab-empty">No words match your search.</p>
  {% endif %}
</section>
{% endblock %}
{% block extra_body %}
{% if user.is_authenticated %}
<script src="{% static 'js/vocab-word.js' %}" defer></script>
<script>
(function(){
  document.addEventListener("DOMContentLoaded", function(){
    document.querySelectorAll(".card-toggle").forEach(function(btn){
      btn.addEventListener("click", function(){ window.vocabToggleWord(btn); });
    });
  });
})();
</script>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `pytest tests/test_vocab_pages.py -k "progress or toggle" -v`
Expected: PASS.

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass (279 from Task 2 plus 9 new = 288).

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be fully verified by the Python test suite (real click → real POST → real DB write). Using a browser (or Playwright) with a real logged-in test account:
- Confirm the Progress chip row appears only when logged in, and clicking each chip (All/Learned/Little Bit/Not Learned) filters the grid correctly while preserving any active search/category/stage/CEFR filters.
- Confirm each card's hover-reveal shows a working progress toggle button that cycles not-learned → little → learned → not-learned on repeated clicks, and that the change persists after a page reload (real `/auth/sync/` round-trip, reusing `vocab-word.js`'s existing GET-then-merge-then-POST logic — no new write logic to verify beyond confirming this page's markup binds to it correctly).
- Confirm a guest session shows no Progress chip row and no toggle button anywhere on the page.
- Confirm the `.word-card.learned`/`.word-card.little` outer-border styling updates correctly after toggling.

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/config/views_vocab.py" "VocabLarry Professional Environment/templates/vocab/word_list.html" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): add authenticated progress filter and per-word toggle to the Word list"
```
