# VocabLarry Professional Environment — Vocab Browse + Word Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add category browse, paginated word-list, and word-detail pages to VocabLarry Professional Environment, including an interactive progress toggle — replacing the "coming soon" Vocabulary nav entry from Foundation with real, working pages.

**Architecture:** Three new server-rendered views/templates querying the existing `vocab` app's models directly via the ORM (no new models, no new JSON API). The one piece of client-side interactivity — the word detail page's progress toggle — reuses the existing `/auth/sync/` endpoint exactly as the production SPA does, via a small `fetch`-based JS module.

**Tech Stack:** Django 5.x (class-based views not used — plain function views, matching Foundation's `config/views.py` pattern), Django's `Paginator`, vanilla JS, pytest + pytest-django.

## Global Constraints

- No new models, no new migrations — `vocab.models.Category`/`Word`/`CEFRLevel` are used as-is.
- No new backend API endpoints — the progress toggle reuses the existing `/auth/sync/` endpoint (`accounts/views.py:sync`) exactly as production's SPA does.
- **`/auth/sync/`'s POST fully replaces `learn_map`** (`request.user.learn_map = body.get('learn_map', {})` in `accounts/views.py` — not a merge). Any client-side write must first `GET` the current full map, mutate only the one word's key, then `POST` the complete map back — never POST a partial map, or every other word's progress gets wiped.
- Word/category content is English-only in this pass — no Vietnamese translation of definitions/names.
- No US/UK dialect-based word substitution — render `Word` fields as stored.
- Category grouping is a flat grid (no 75-section layer) — filterable by CEFR level and a name search box, both server-side query-param filters.
- Pagination: Django's `Paginator`, 25 words per page, `?page=N`.
- Test with `pytest` (`tests/` dir, `DJANGO_SETTINGS_MODULE=config.settings`, `--no-migrations` per `pytest.ini`). Use `from django.test import Client; c = Client()` per-test, matching the existing `tests/test_pages.py` convention (not the `client` pytest-django fixture).
- Reuse `conftest.py`'s existing `regular_user`/`staff_user`/`User` fixtures — do not redefine them.

---

### Task 1: Category browse page

**Files:**
- Create: `config/views_vocab.py`
- Modify: `config/urls.py`
- Create: `templates/vocab/browse.html`
- Create: `static/css/vocab.css`
- Modify: `templates/partials/nav.html`
- Modify: `templates/home.html`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Produces: `config.views_vocab.vocab_browse(request)` — renders `vocab/browse.html`, context keys `categories` (queryset), `cefr_levels` (queryset), `query` (str), `cefr_filter` (str).
- Produces: URL name `vocab_browse` at `/vocab/`.
- Consumes: `templates/base.html`'s `content`/`extra_head`/`title` blocks, `templates/partials/nav.html`'s existing structure (from Foundation).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_vocab_pages.py`:

```python
import pytest
from django.test import Client
from vocab.models import CEFRLevel, Category


@pytest.fixture
def cefr_a1(db):
    return CEFRLevel.objects.create(code='A1', name='Beginner', order=1)


@pytest.fixture
def cefr_b1(db):
    return CEFRLevel.objects.create(code='B1', name='Intermediate', order=2)


@pytest.mark.django_db
def test_vocab_browse_renders():
    c = Client()
    r = c.get('/vocab/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_browse_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocab_browse_search_filters_by_name(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/?q=Animal')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocab_browse_cefr_filter(cefr_a1, cefr_b1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='business-basics', name='Business Basics', order=2, cefr_level=cefr_b1)
    c = Client()
    r = c.get('/vocab/?cefr=B1')
    body = r.content.decode()
    assert 'Business Basics' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_home_nav_links_to_vocab_browse():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    # Vocabulary becomes a real link. Grammar stays disabled/coming-soon
    # on this same page (separate future sub-project) - don't assert
    # "coming soon" is gone entirely, only that Vocabulary now links out.
    assert 'href="/vocab/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all 5 FAIL — `/vocab/` doesn't resolve yet (404), and the nav still shows "Coming soon" for Vocabulary.

- [ ] **Step 3: Create the view**

Create `config/views_vocab.py`:

```python
from django.shortcuts import render

from vocab.models import CEFRLevel, Category


def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    categories = Category.objects.select_related('cefr_level', 'color').order_by('order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
    })
```

- [ ] **Step 4: Wire the URL**

Modify `config/urls.py` — add the import and the route:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home
from config.views_vocab import vocab_browse

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 5: Create `static/css/vocab.css`**

```css
.vocab-browse h1{ margin-top: 32px; }

.vocab-filters{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 16px 0 28px;
}
.vocab-filters input[type="text"],
.vocab-filters select{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 0.95rem;
}
.vocab-filters input[type="text"]{ flex: 1; min-width: 180px; }

.category-grid{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
  padding-bottom: 48px;
}
.category-card{
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--cat-bg, var(--card-bg));
  color: var(--cat-text, var(--text));
  text-decoration: none;
}
.category-icon{ font-size: 1.6rem; }
.category-name{ font-weight: 700; }
.category-cefr{
  align-self: flex-start;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(var(--violet), 0.12);
  color: rgb(var(--violet));
}
.vocab-empty{ color: var(--muted); padding: 24px 0; }

.vocab-breadcrumb{ color: var(--muted); font-size: 0.9rem; margin: 24px 0 4px; }
.vocab-breadcrumb a{ color: var(--muted); }
```

- [ ] **Step 6: Create `templates/vocab/browse.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Vocabulary — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-browse">
  <h1>Vocabulary</h1>
  <form method="get" class="vocab-filters">
    <input type="text" name="q" value="{{ query }}" placeholder="Search categories…">
    <select name="cefr">
      <option value="">All levels</option>
      {% for level in cefr_levels %}
        <option value="{{ level.code }}" {% if level.code == cefr_filter %}selected{% endif %}>{{ level.code }}</option>
      {% endfor %}
    </select>
    <button type="submit" class="btn">Filter</button>
  </form>
  {% if categories %}
  <div class="category-grid">
    {% for category in categories %}
    <a class="category-card" href="{% url 'vocab_category' category.slug %}"
       style="--cat-bg:{{ category.color.bg_hex|default:'#f4f4f8' }}; --cat-text:{{ category.color.text_hex|default:'#16161f' }};">
      <span class="category-icon">{{ category.icon }}</span>
      <span class="category-name">{{ category.name }}</span>
      {% if category.cefr_level %}<span class="category-cefr">{{ category.cefr_level.code }}</span>{% endif %}
    </a>
    {% endfor %}
  </div>
  {% else %}
  <p class="vocab-empty">No categories match your search.</p>
  {% endif %}
</section>
{% endblock %}
```

Note: this template links to `{% url 'vocab_category' category.slug %}`, which doesn't exist until Task 2. That's fine — Django only resolves `{% url %}` tags when the template actually renders, and this task's tests never click through to that URL, so Task 1 is independently green. Task 2 makes the link resolve.

- [ ] **Step 7: Wire the nav and home hero to the new page**

Modify `templates/partials/nav.html` — replace the disabled Vocabulary entry:

```html
    <li><span class="disabled" data-i18n="nav.vocabulary">Vocabulary</span> <small data-i18n="nav.comingSoon">Coming soon</small></li>
```

with:

```html
    <li><a href="{% url 'vocab_browse' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
```

Modify `templates/home.html` — replace the disabled hero CTA:

```html
    <span class="btn btn-primary disabled" data-i18n="hero.start">Start Learning</span>
```

with:

```html
    <a class="btn btn-primary" href="{% url 'vocab_browse' %}" data-i18n="hero.start">Start Learning</a>
```

(Leave the Grammar nav entry and "Practice Grammar" hero CTA disabled — Grammar is a separate future sub-project.)

- [ ] **Step 8: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all 5 PASS.

- [ ] **Step 9: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `101 passed` (96 from Foundation + 5 new). `test_home_page_has_nav_and_hero` (from Foundation's `test_pages.py`) must still pass — it doesn't assert on the hero CTA's `disabled` state, only that `site-nav`/`Sign In`/`hero` markers are present, so this change doesn't break it.

- [ ] **Step 10: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add vocab category browse page

GET /vocab/ lists all categories in a flat grid, filterable by CEFR
level and a name search box (both server-side query-param filters).
Home hero and nav Vocabulary entry now link here instead of showing
"coming soon".
EOF
)"
```

---

### Task 2: Category word list page (pagination)

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `config/urls.py`
- Create: `templates/vocab/category_word_list.html`
- Modify: `static/css/vocab.css`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Produces: `config.views_vocab.vocab_category(request, slug)` — renders `vocab/category_word_list.html`, context keys `category` (single `Category` instance), `page_obj` (Django `Page` object from `Paginator`).
- Produces: URL name `vocab_category` at `/vocab/category/<slug:slug>/`.
- Consumes: `Category.words` related manager (from `vocab.models.Word.category`'s `related_name='words'`), `templates/vocab/browse.html`'s link from Task 1 (now resolves).

- [ ] **Step 1: Write the failing tests**

Extend `tests/test_vocab_pages.py`:

```python
from vocab.models import Word


@pytest.mark.django_db
def test_vocab_category_renders_words(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small pet.', category=category, order=1)
    Word.objects.create(word='Dog', definition='A loyal pet.', category=category, order=2)
    c = Client()
    r = c.get('/vocab/category/animals/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'Dog' in body


@pytest.mark.django_db
def test_vocab_category_unknown_slug_404():
    c = Client()
    r = c.get('/vocab/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocab_category_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r1 = c.get('/vocab/category/animals/')
    body1 = r1.content.decode()
    assert 'Word00' in body1
    assert 'Word29' not in body1  # page 2 content shouldn't leak onto page 1
    r2 = c.get('/vocab/category/animals/?page=2')
    body2 = r2.content.decode()
    assert 'Word29' in body2
    assert 'Word00' not in body2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k vocab_category
```

Expected: all 3 FAIL — `/vocab/category/animals/` doesn't resolve yet (404 for the wrong reason: no route at all).

- [ ] **Step 3: Add the view**

Add to `config/views_vocab.py`:

```python
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404


def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
    })
```

(`get_object_or_404` needs importing — add it to the existing `from django.shortcuts import render` line, making it `from django.shortcuts import get_object_or_404, render`.)

- [ ] **Step 4: Wire the URL**

Modify `config/urls.py`:

```python
from config.views_vocab import vocab_browse, vocab_category

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 5: Create `templates/vocab/category_word_list.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ category.name }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-category">
  <p class="vocab-breadcrumb"><a href="{% url 'vocab_browse' %}">Vocabulary</a> / {{ category.name }}</p>
  <h1>{{ category.name }}</h1>
  <ul class="word-list">
    {% for word in page_obj %}
    <li><a href="{% url 'vocab_word_detail' word.pk %}">{{ word.word }}</a></li>
    {% endfor %}
  </ul>
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="vocab-pagination">
    {% if page_obj.has_previous %}<a href="?page={{ page_obj.previous_page_number }}">Previous</a>{% endif %}
    <span>Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}</span>
    {% if page_obj.has_next %}<a href="?page={{ page_obj.next_page_number }}">Next</a>{% endif %}
  </nav>
  {% endif %}
</section>
{% endblock %}
```

Note: this links to `{% url 'vocab_word_detail' word.pk %}`, which doesn't exist until Task 3 — same forward-reference situation as Task 1's category link, and equally fine for the same reason.

- [ ] **Step 6: Append pagination/word-list CSS**

Append to `static/css/vocab.css`:

```css
.word-list{
  list-style: none;
  padding: 0;
  margin: 20px 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}
.word-list li a{
  display: block;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
}
.vocab-pagination{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 0 48px;
  color: var(--muted);
}
.vocab-pagination a{ font-weight: 700; }
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all 8 tests in the file PASS (5 from Task 1 + 3 new).

- [ ] **Step 8: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `104 passed`.

- [ ] **Step 9: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add paginated word list per category

GET /vocab/category/<slug>/ lists a category's words, 25 per page via
Django's Paginator, each linking out to the word's detail page.
EOF
)"
```

---

### Task 3: Word detail page (static content)

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `config/urls.py`
- Create: `templates/vocab/word_detail.html`
- Modify: `static/css/vocab.css`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Produces: `config.views_vocab.vocab_word_detail(request, pk)` — renders `vocab/word_detail.html`, context keys `word` (single `Word` instance), `learn_state` (`"little"`, `"learned"`, or `None`).
- Produces: URL name `vocab_word_detail` at `/vocab/word/<int:pk>/`.
- Consumes: `templates/vocab/category_word_list.html`'s link from Task 2 (now resolves). This task renders the progress state but does NOT make the toggle clickable — that's Task 4.

- [ ] **Step 1: Write the failing tests**

Extend `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocab_word_detail_renders(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(
        word='Cat', pos='noun', definition='A small domesticated pet.',
        example='The cat slept all day.', synonyms=['feline'], antonyms=[],
        category=category, order=1,
    )
    c = Client()
    r = c.get(f'/vocab/word/{word.pk}/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'A small domesticated pet.' in body
    assert 'The cat slept all day.' in body
    assert 'feline' in body


@pytest.mark.django_db
def test_vocab_word_detail_unknown_id_404():
    c = Client()
    r = c.get('/vocab/word/999999/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocab_word_detail_shows_progress_toggle_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'learn-state-btn' in r.content.decode()


@pytest.mark.django_db
def test_vocab_word_detail_hides_progress_toggle_when_anonymous(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'learn-state-btn' not in r.content.decode()


@pytest.mark.django_db
def test_vocab_word_detail_reflects_existing_progress(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'data-state="learned"' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k vocab_word_detail
```

Expected: all 5 FAIL — no route yet.

- [ ] **Step 3: Add the view**

Add to `config/views_vocab.py` (also add `from vocab.models import Word` to the existing model import line, and `from django.views.decorators.csrf import ensure_csrf_cookie` — the `ensure_csrf_cookie` decorator isn't used until Task 4, but add the import now since Task 4 modifies this same function rather than adding a new one):

```python
from django.views.decorators.csrf import ensure_csrf_cookie
from vocab.models import CEFRLevel, Category, Word


@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    return render(request, 'vocab/word_detail.html', {
        'word': word,
        'learn_state': learn_state,
    })
```

`@ensure_csrf_cookie` is applied now (not deferred to Task 4) because it must be present the first time an authenticated user's browser loads this page, so the `csrftoken` cookie Task 4's JS reads is guaranteed to exist — matching the exact reasoning documented in the original VocabLarry's `config/urls.py` for its own root view.

- [ ] **Step 4: Wire the URL**

Modify `config/urls.py`:

```python
from config.views_vocab import vocab_browse, vocab_category, vocab_word_detail

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 5: Create `templates/vocab/word_detail.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ word.word }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-word-detail">
  <p class="vocab-breadcrumb">
    <a href="{% url 'vocab_browse' %}">Vocabulary</a> /
    <a href="{% url 'vocab_category' word.category.slug %}">{{ word.category.name }}</a> /
    {{ word.word }}
  </p>
  <h1>{{ word.word }}{% if word.pos %} <span class="vocab-pos">{{ word.pos }}</span>{% endif %}</h1>
  <p class="vocab-definition">{{ word.definition }}</p>
  {% if word.example %}<p class="vocab-example">“{{ word.example }}”</p>{% endif %}
  {% if word.synonyms %}<p class="vocab-synonyms"><strong>Synonyms:</strong> {{ word.synonyms|join:", " }}</p>{% endif %}
  {% if word.antonyms %}<p class="vocab-antonyms"><strong>Antonyms:</strong> {{ word.antonyms|join:", " }}</p>{% endif %}
  {% if user.is_authenticated %}
  <div class="learn-state-row">
    <span class="learn-state-label">Progress:</span>
    <button type="button" class="learn-state-btn" data-word-id="{{ word.pk }}"
            data-state="{{ learn_state|default:'none' }}">
      {% if learn_state == 'learned' %}Learned{% elif learn_state == 'little' %}Little Bit{% else %}Not Learned{% endif %}
    </button>
  </div>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 6: Append word-detail CSS**

Append to `static/css/vocab.css`:

```css
.vocab-pos{
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: lowercase;
}
.vocab-definition{ font-size: 1.15rem; margin: 16px 0; }
.vocab-example{ color: var(--muted); font-style: italic; }
.vocab-synonyms, .vocab-antonyms{ color: var(--muted); }

.learn-state-row{
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 28px 0 48px;
}
.learn-state-btn{
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-weight: 700;
  cursor: pointer;
}
.learn-state-btn[data-state="little"]{
  background: #f59e0b; border-color: #f59e0b; color: #1c1917;
}
.learn-state-btn[data-state="learned"]{
  background: #22c55e; border-color: #22c55e; color: #fff;
}
```

(Amber for "little", green for "learned" — matching the color meaning already established in production's `vocablarry.html`.)

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all 13 tests in the file PASS (8 from Tasks 1-2 + 5 new).

- [ ] **Step 8: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `109 passed`.

- [ ] **Step 9: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add word detail page with read-only progress display

GET /vocab/word/<id>/ shows a word's full detail (definition, example,
synonyms, antonyms) and, for signed-in users, their current learn_map
state for this word. The toggle isn't interactive yet - clicking it is
wired up in the next task. @ensure_csrf_cookie added now so the cookie
that task's JS needs is guaranteed present on first page load.
EOF
)"
```

---

### Task 4: Interactive progress toggle

**Files:**
- Create: `static/js/vocab-word.js`
- Modify: `templates/vocab/word_detail.html`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: `/auth/sync/` (`accounts/urls.py` → `accounts/views.py:sync`, unchanged) — `GET` returns `{'learn_map': {...}, 'grammar_map': {...}}`, `POST` with `{'learn_map': {...}}` fully replaces the stored map.
- Consumes: `.learn-state-btn[data-word-id][data-state]` markup from Task 3.
- Produces: no new interfaces for later tasks — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing test**

This task's core correctness property — a toggle write must never clobber another word's progress, because `/auth/sync/`'s POST fully replaces `learn_map` — is testable in Python by simulating exactly what the JS does (GET the current map, mutate one key, POST the full map back), even though the JS itself isn't executed by pytest. Extend `tests/test_vocab_pages.py`:

```python
import json


@pytest.mark.django_db
def test_progress_toggle_round_trip_preserves_other_words(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {'999': 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what static/js/vocab-word.js does on click: GET the current
    # map, mutate only this word's key, POST the full map back.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    learn_map[str(word.pk)] = 'little'
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {'999': 'learned', str(word.pk): 'little'}


@pytest.mark.django_db
def test_vocab_word_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocab_word_detail_loads_toggle_script_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocab/word/{word.pk}/')
    assert 'vocab-word.js' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k "progress_toggle_round_trip or sets_csrf_cookie or loads_toggle_script"
```

Expected: `test_progress_toggle_round_trip_preserves_other_words` and `test_vocab_word_detail_sets_csrf_cookie` already PASS (they only exercise Task 3's `@ensure_csrf_cookie` and the unmodified `/auth/sync/` endpoint — nothing left to build for those two). `test_vocab_word_detail_loads_toggle_script_when_authenticated` FAILS (the script tag doesn't exist yet). This is expected — the round-trip and CSRF-cookie properties were already correct as of Task 3; this task's only new deliverable is actually wiring the button up client-side.

- [ ] **Step 3: Create `static/js/vocab-word.js`**

```javascript
(function(){
  var btn = document.querySelector(".learn-state-btn");
  if (!btn) return;

  var CYCLE = [null, "little", "learned"];
  var LABELS = { null: "Not Learned", little: "Little Bit", learned: "Learned" };

  function readState(){
    var raw = btn.dataset.state;
    return raw === "none" ? null : raw;
  }

  function paint(stateValue){
    btn.dataset.state = stateValue === null ? "none" : stateValue;
    btn.textContent = LABELS[stateValue === null ? "null" : stateValue];
  }

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  btn.addEventListener("click", function(){
    var wordId = btn.dataset.wordId;
    var prevState = readState();
    var nextState = CYCLE[(CYCLE.indexOf(prevState) + 1) % CYCLE.length];
    paint(nextState);

    fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){
        if (!res.ok) throw new Error("sync GET failed");
        return res.json();
      })
      .then(function(data){
        var learnMap = data.learn_map || {};
        if (nextState === null) delete learnMap[wordId];
        else learnMap[wordId] = nextState;
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ learn_map: learnMap }),
        });
      })
      .then(function(res){
        if (!res.ok) throw new Error("sync POST failed");
      })
      .catch(function(){
        paint(prevState);
      });
  });
})();
```

- [ ] **Step 4: Load the script from the word detail page**

Modify `templates/vocab/word_detail.html` — add an `extra_body` block after `{% endblock %}` (the `content` block's closing tag), only when the user is authenticated (the script is a no-op otherwise since `document.querySelector(".learn-state-btn")` returns `null` when the button isn't rendered, but there's no reason to ship the tag to anonymous visitors):

```html
{% endblock %}
{% block extra_body %}
{% if user.is_authenticated %}
<script src="{% static 'js/vocab-word.js' %}" defer></script>
{% endif %}
{% endblock %}
```

(This replaces the file's final `{% endblock %}` line — the `content` block's closing tag stays exactly where it was; this just adds a new block after it.)

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all 16 tests in the file PASS (13 from Tasks 1-3 + 3 new).

- [ ] **Step 6: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `112 passed`.

- [ ] **Step 7: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Sign in (or sign up a throwaway account), navigate to `/vocab/`, click into any category, click into any word. Click the progress button repeatedly — confirm it cycles "Not Learned" (default) → "Little Bit" (amber) → "Learned" (green) → back to "Not Learned", and that reloading the page after clicking preserves whatever state you left it in (proves the write actually persisted, not just the optimistic UI update). Open a second word in another tab, set its progress too, then reload the first word's page — confirm its state is unaffected by the second word's write (proves the GET-then-merge-then-POST round trip isn't clobbering other words). Stop the server (Ctrl+C) when done.

- [ ] **Step 8: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): wire up the interactive progress toggle

static/js/vocab-word.js cycles not-learned -> little -> learned on
click, persisting via the existing /auth/sync/ endpoint. Since that
endpoint fully replaces learn_map rather than merging, the click
handler GETs the current map, mutates only this word's key, and POSTs
the complete map back - verified against a real other-word-untouched
assertion, not just trusted by inspection.
EOF
)"
```

---

## Definition of Done

- `python -m pytest tests -q` is fully green (112 tests).
- `manage.py check` is clean.
- Manual browser check confirms: category browse (grid, CEFR filter, search) → category word list (pagination) → word detail (content + progress toggle) all navigate correctly, and the progress toggle persists across reloads without affecting other words' progress.
- Home hero and nav Vocabulary entry link to real pages instead of showing "coming soon". Grammar entry/CTA remain disabled (separate future sub-project).
- Quiz engine, 75-section grouping, content i18n, and dialect substitution remain explicitly out of scope, unaffected by this work.
