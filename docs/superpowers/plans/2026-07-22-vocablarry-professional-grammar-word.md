# VocabLarry Professional Environment — Grammar Word Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `/grammar/word/` "Coming soon" stub with a real, filterable, paginated reference page covering two tabs — Irregular Verbs and Comparisons — reading directly from the existing `GrammarLessonBlock` table content (no new models).

**Architecture:** Two sequential tasks. Task 1 is pure CSS (a new `.pattern-badge` family for the Verbs tab's Pattern column), verified only by the full suite staying green. Task 2 replaces the stub view/template with the complete feature: a `set` tab switcher (Verbs/Comparisons), search, a Pattern chip filter (Verbs only), a paginated reference table reusing the existing `.gram-table` component, and a computed (not stored) Pattern classification per verb row.

**Tech Stack:** Django templates, server-side ORM/Python filtering (no client-side JS filtering), plain CSS (existing custom-property/badge system), pytest + Django test client.

## Global Constraints

- Only files under `VocabLarry Professional Environment/` may be modified. `VocabLarry/` (production) is read-only reference material.
- No new models, no migration — the view reads `GrammarLessonBlock.objects.get(topic__slug=X, type='table').data` directly for `X` in `{'irregular-verbs', 'comparison-structures'}`.
- All filtering is server-side via GET query params (`set`, `q`, `pattern`, `page`) and plain `<a href>`/`<form method="get">` — no client-side JS filtering logic.
- Pattern classification (AAA/ABA/ABB/ABC) is computed at render time from each row's 3 existing cell values — never stored, never a new model field.
- Comparisons tab has no Pattern filter (doesn't apply) and no regular -er/-est content (scoped to the irregular lesson-table rows only).
- No progress/mastery tracking, no per-row detail page, no bulk actions on this page.
- `pytest.ini` sets `addopts = --no-migrations` — the real production `irregular-verbs`/`comparison-structures` content will NOT exist in any test's database. Every test must create its own `GrammarTopic`/`GrammarLessonBlock` fixture rows directly (matching the existing `topic_with_blocks` fixture pattern already in `tests/test_grammar_pages.py`), never assume real seeded data is present.
- No changes to `templates/grammar/topic_detail.html`, the `GrammarLessonBlock`/`GrammarTopic` models, or `urls.py` (the `grammar_word` URL name/path already exists and is unchanged — only its view function body and template change).

---

### Task 1: CSS foundation — Pattern badge colors

**Files:**
- Modify: `VocabLarry Professional Environment/static/css/grammar.css` (append new rules)

**Interfaces:**
- Consumes: nothing new.
- Produces: `.pattern-badge` base class + `.pattern-badge.AAA`/`.ABA`/`.ABB`/`.ABC` modifier classes that Task 2's template will use inside the Verbs table's Pattern column.
- This task changes no markup, so no existing test's assertions change. Verified by re-running the full existing suite (must stay green) — matches the established precedent from every prior VLPE CSS-foundation task (no automated way to assert CSS content in this codebase's test suite).

- [ ] **Step 1: Append the Pattern badge CSS to grammar.css**

Append to the end of `VocabLarry Professional Environment/static/css/grammar.css`:

```css

/* Verb Pattern badges (Grammar Word page) — same structural shape as
   .cefr-badge (base.css) but with its own 4-color scheme, since Pattern
   (AAA/ABA/ABB/ABC) is an unrelated classification, not a CEFR level. */
.pattern-badge{
  font-size: .68rem; font-weight: 800; padding: 3px 9px; border-radius: 6px;
  color: #fff; letter-spacing: .06em; flex-shrink: 0; display: inline-block;
  font-family: 'JetBrains Mono', monospace;
}
.pattern-badge.AAA{ background: #10b981; }
.pattern-badge.ABA{ background: #6366f1; }
.pattern-badge.ABB{ background: #f59e0b; }
.pattern-badge.ABC{ background: #ef4444; }
```

- [ ] **Step 2: Run the full test suite to confirm no regressions**

Run (from `VocabLarry Professional Environment/`): `pytest`
Expected: all existing tests pass (this task changed no markup, so no test assertion is affected).

- [ ] **Step 3: Commit**

```bash
git add "VocabLarry Professional Environment/static/css/grammar.css"
git commit -m "feat(vlpe): add Verb Pattern badge colors for the Grammar Word page"
```

---

### Task 2: Grammar Word view + template — set switcher, search, Pattern filter, paginated table

**Files:**
- Modify: `VocabLarry Professional Environment/config/views_grammar.py` (replace the `grammar_word` stub; add `_classify_verb_pattern`, `_pagination_window`, `GRAMWORD_SETS`)
- Modify: `VocabLarry Professional Environment/templates/grammar/word.html` (full-file rewrite)
- Modify: `VocabLarry Professional Environment/tests/test_grammar_pages.py` (remove the obsolete stub test if one exists, add new tests + fixture)

**Interfaces:**
- Consumes: CSS from Task 1 (`.pattern-badge` + 4 modifiers). Pre-existing `.gram-table`/`.gram-table-wrap` CSS (`grammar.css`), `.filters`/`.search-row`/`.filter-row`/`.chip`/`.clear-btn`/`.pagination`/`.page-btn`/`.page-ellipsis` (`base.css`), `.headline-bar`/`.headline-btn` (`grammar.css`, reused here as a plain 2-item tab switcher with no `data-grammar-stage` attribute, so only the generic active/hover styling applies — not the stage-specific color rules).
- Produces: no new interfaces consumed by other tasks — this is the final piece of this sub-project.

- [ ] **Step 1: Remove the obsolete stub test and write the failing tests**

In `VocabLarry Professional Environment/tests/test_grammar_pages.py`, delete this test (it asserts the "Coming soon" placeholder, which this task removes):

```python
@pytest.mark.django_db
def test_grammar_word_stub_renders():
    c = Client()
    r = c.get('/grammar/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'Section 02 / Grammar' in html
    assert '<h1>Word</h1>' in html
    assert 'Coming soon.' in html
```

Add this fixture and these tests (place the fixture near the top of the file alongside the existing `topic_with_blocks` fixture, and the tests anywhere sensible — e.g. directly after any tests for `grammar_word`/near the end of the file):

```python
@pytest.fixture
def gramword_topics(db):
    from vocab.models import GrammarLessonBlock

    verbs_topic = GrammarTopic.objects.create(
        slug='irregular-verbs', title='Irregular Verbs',
        tag='Verbs', cefr_label='A2', blurb='Common irregular verb forms.',
        stage='beginner', order=0,
    )
    GrammarLessonBlock.objects.create(
        topic=verbs_topic, type='table', title='Irregular Verbs',
        data={
            'head': ['Base (V1)', 'Past simple (V2)', 'Past participle (V3)'],
            'rows': [
                ['cut', 'cut', 'cut'],
                ['buy', 'bought', 'bought'],
                ['come', 'came', 'come'],
                ['go', 'went', 'gone'],
            ],
        },
        order=0,
    )

    comparisons_topic = GrammarTopic.objects.create(
        slug='comparison-structures', title='Comparison Structures',
        tag='Adjectives', cefr_label='A2', blurb='Irregular comparative/superlative forms.',
        stage='beginner', order=1,
    )
    GrammarLessonBlock.objects.create(
        topic=comparisons_topic, type='table', title='Irregular Comparisons',
        data={
            'head': ['Base', 'Comparative', 'Superlative'],
            'rows': [
                ['good / well', 'better', 'best'],
                ['bad / badly', 'worse', 'worst'],
                ['far', 'further / farther', 'furthest / farthest'],
            ],
        },
        order=0,
    )
    return {'verbs': verbs_topic, 'comparisons': comparisons_topic}


def test_classify_verb_pattern_all_four_branches():
    from config.views_grammar import _classify_verb_pattern
    assert _classify_verb_pattern('cut', 'cut', 'cut') == 'AAA'
    assert _classify_verb_pattern('buy', 'bought', 'bought') == 'ABB'
    assert _classify_verb_pattern('come', 'came', 'come') == 'ABA'
    assert _classify_verb_pattern('go', 'went', 'gone') == 'ABC'


@pytest.mark.django_db
def test_grammar_word_default_set_is_verbs(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/')
    assert r.status_code == 200
    html = r.content.decode()
    assert '>cut<' in html
    assert 'class="headline-btn active" href="?set=verbs"' in html


@pytest.mark.django_db
def test_grammar_word_verbs_table_has_pattern_column(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/')
    html = r.content.decode()
    assert 'class="pattern-badge AAA">AAA</span>' in html
    assert 'class="pattern-badge ABB">ABB</span>' in html
    assert 'class="pattern-badge ABA">ABA</span>' in html
    assert 'class="pattern-badge ABC">ABC</span>' in html


@pytest.mark.django_db
def test_grammar_word_comparisons_set(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'set': 'comparisons'})
    html = r.content.decode()
    assert '>better<' in html
    assert '>worse<' in html
    assert 'pattern-badge' not in html
    assert 'class="filter-label">Pattern</span>' not in html


@pytest.mark.django_db
def test_grammar_word_search_matches_any_column(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'q': 'went'})
    html = r.content.decode()
    assert '>go<' in html and '>cut<' not in html and '>buy<' not in html


@pytest.mark.django_db
def test_grammar_word_pattern_filter(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'pattern': 'ABB'})
    html = r.content.decode()
    assert '>buy<' in html
    assert '>cut<' not in html and '>come<' not in html and '>go<' not in html


@pytest.mark.django_db
def test_grammar_word_pattern_filter_ignored_on_comparisons(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'set': 'comparisons', 'pattern': 'AAA'})
    html = r.content.decode()
    assert '>better<' in html
    assert '>worse<' in html


@pytest.mark.django_db
def test_grammar_word_clear_filters_link_present(gramword_topics):
    c = Client()
    r = c.get('/grammar/word/', {'q': 'cut', 'pattern': 'AAA'})
    html = r.content.decode()
    assert 'class="clear-btn" href="/grammar/word/"' in html
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest tests/test_grammar_pages.py -k "grammar_word or classify_verb_pattern" -v`
Expected: FAIL — the stub view returns only "Coming soon" (or `_classify_verb_pattern` doesn't exist yet).

- [ ] **Step 3: Replace the `grammar_word` view and add its helpers**

In `VocabLarry Professional Environment/config/views_grammar.py`, change the import line:

```python
from vocab.models import GrammarSection, GrammarTopic
```

to:

```python
from django.core.paginator import Paginator

from vocab.models import GrammarLessonBlock, GrammarSection, GrammarTopic
```

Add these module-level definitions (near the other module-level constants like `GRAMMAR_CARD_THEMES`):

```python
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
```

Replace the existing stub:

```python
def grammar_word(request):
    return render(request, 'grammar/word.html')
```

with:

```python
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
```

- [ ] **Step 4: Rewrite word.html**

Replace the entire content of `VocabLarry Professional Environment/templates/grammar/word.html` with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Word — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-word">
  <h1>Word</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip active" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>

  <div class="headline-bar">
    <a class="headline-btn{% if active_set == 'verbs' %} active{% endif %}" href="?set=verbs">Irregular Verbs</a>
    <a class="headline-btn{% if active_set == 'comparisons' %} active{% endif %}" href="?set=comparisons">Comparisons</a>
  </div>

  <div class="filters">
    <form method="get" class="search-row">
      <input type="hidden" name="set" value="{{ active_set }}">
      <input type="search" name="q" value="{{ query }}" placeholder="Search…">
      <button type="submit" class="btn">Filter</button>
    </form>
    {% if active_set == 'verbs' %}
    <div class="filter-row">
      <span class="filter-label">Pattern</span>
      <a class="chip{% if not pattern_filter %} active{% endif %}" href="?set=verbs{% if query %}&q={{ query|urlencode }}{% endif %}">All</a>
      <a class="chip{% if pattern_filter == 'AAA' %} active{% endif %}" href="?set=verbs{% if query %}&q={{ query|urlencode }}{% endif %}&pattern=AAA">AAA</a>
      <a class="chip{% if pattern_filter == 'ABA' %} active{% endif %}" href="?set=verbs{% if query %}&q={{ query|urlencode }}{% endif %}&pattern=ABA">ABA</a>
      <a class="chip{% if pattern_filter == 'ABB' %} active{% endif %}" href="?set=verbs{% if query %}&q={{ query|urlencode }}{% endif %}&pattern=ABB">ABB</a>
      <a class="chip{% if pattern_filter == 'ABC' %} active{% endif %}" href="?set=verbs{% if query %}&q={{ query|urlencode }}{% endif %}&pattern=ABC">ABC</a>
    </div>
    {% endif %}
    <div class="filter-row" style="justify-content:flex-end;">
      <a class="clear-btn" href="{% url 'grammar_word' %}">Clear filters</a>
    </div>
  </div>

  {% if page_obj %}
  <div class="gram-table-wrap"><div style="overflow-x:auto;"><table class="gram-table"><thead><tr>
    {% for h in head %}<th>{{ h }}</th>{% endfor %}
    {% if active_set == 'verbs' %}<th>Pattern</th>{% endif %}
  </tr></thead><tbody>
    {% for entry in page_obj %}<tr>
      {% for cell in entry.cells %}<td>{{ cell }}</td>{% endfor %}
      {% if active_set == 'verbs' %}<td><span class="pattern-badge {{ entry.pattern }}">{{ entry.pattern }}</span></td>{% endif %}
    </tr>{% endfor %}
  </tbody></table></div></div>
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="pagination">
    <a class="page-btn{% if not page_obj.has_previous %} disabled{% endif %}"
       href="{% if page_obj.has_previous %}?set={{ active_set }}{% if query %}&q={{ query|urlencode }}{% endif %}{% if pattern_filter %}&pattern={{ pattern_filter }}{% endif %}&page={{ page_obj.previous_page_number }}{% else %}#{% endif %}">«</a>
    {% for p in pagination_window %}
      {% if p is None %}<span class="page-ellipsis">…</span>
      {% else %}<a class="page-btn{% if p == page_obj.number %} active{% endif %}" href="?set={{ active_set }}{% if query %}&q={{ query|urlencode }}{% endif %}{% if pattern_filter %}&pattern={{ pattern_filter }}{% endif %}&page={{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
    <a class="page-btn{% if not page_obj.has_next %} disabled{% endif %}"
       href="{% if page_obj.has_next %}?set={{ active_set }}{% if query %}&q={{ query|urlencode }}{% endif %}{% if pattern_filter %}&pattern={{ pattern_filter }}{% endif %}&page={{ page_obj.next_page_number }}{% else %}#{% endif %}">»</a>
  </nav>
  {% endif %}
  {% else %}
  <p class="grammar-empty">No entries match your search.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `pytest tests/test_grammar_pages.py -k "grammar_word or classify_verb_pattern" -v`
Expected: PASS.

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass (293 existing minus the 1 removed stub test, plus the 8 new tests from Step 1 = 300).

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be fully verified by the Python test suite (visual table/badge rendering). Using a browser (or Playwright), navigate to `/grammar/word/` and confirm:
- The Verbs tab renders a table with a Pattern column showing correctly colored badges (AAA green, ABA indigo, ABB amber, ABC red, per the CSS from Task 1).
- Switching to the Comparisons tab (clicking the headline-bar button) shows its own table with no Pattern column and no Pattern filter row.
- Searching and filtering by Pattern narrow the table correctly; "Clear filters" resets both.
- Both dark (default) and light theme render the table/filter bar correctly (this reuses already-themed CSS, so should need no new theme-specific rules — confirm this holds).

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/word.html" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "feat(vlpe): replace Grammar Word stub with a real Verbs/Comparisons reference table"
```
