# VocabLarry Professional Environment — Nav & Routing Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure VLPE's Vocabulary/Grammar navigation into production's real
IA — renamed `/vocabulary/`/`/grammar/` URLs, a dropdown nav (Category/Word/Quiz),
two brand-new intro pages, and Reading/Listening/Speaking/Writing placeholder pages.

**Architecture:** Pure Django routing + template + CSS/JS work — no new models, no
migrations, no new backend endpoints. URL names are renamed outright (no
backwards-compat redirects). A new context processor derives which nav section is
active from `request.resolver_match.url_name` so `nav.html` doesn't need a
hand-maintained OR-chain. New CSS/markup for the dropdown nav, mobile hamburger
menu, and intro-page cards is ported from production's actual `vocablarry.html`
(`.home-sec`/`.nav-dropdown`/`.mobile-nav-chip`/`.mobile-page-switcher`), converted
to this codebase's `--violet`/`rgb(var(--violet) / X)` token convention.

**Tech Stack:** Django 5 (server-rendered templates), vanilla JS (no framework),
pytest + Django test `Client`, Playwright for browser-interaction checks.

## Global Constraints

- Full URL rename, not additive routes — every `{% url %}` tag and every test's
  literal path must move from `vocab_*`/`grammar_browse`/`grammar_topic_*`/
  `grammar_test_*` to the new `vocabulary_*`/`grammar_*` names below. Old paths
  (`/vocab/...`, `/grammar/topic/...`, `/grammar/test/...`) must 404.
- No backwards-compatible redirects from old URLs — VLPE has no external inbound
  links to preserve.
- Every Vocabulary URL name starts with `vocabulary_`; every Grammar URL name
  starts with `grammar_`. This is what makes the context processor's prefix match
  work.
- No new models, no new migrations, no new backend/API endpoints anywhere in this
  plan.
- No i18n content translation beyond new chrome labels — every new/changed
  user-facing string gets both an `en` and a `vi` entry in `static/js/i18n.js`,
  matching every existing entry's dual-key pattern.
- The two new "Word" pages (`/vocabulary/word/`, `/grammar/word/`) get real routes
  and stub content this plan — their real content is separate future work
  (sub-projects 2 and 3), not part of this plan.
- Home's hero CTAs ("Start Learning" / "Practice Grammar") keep linking directly
  to the Category page, bypassing the new intro pages.
- Full spec: `docs/superpowers/specs/2026-07-20-vocablarry-professional-nav-routing-skeleton-design.md`.

---

### Task 1: URL rename, new stub routes, and full test-suite migration

**Files:**
- Modify: `config/urls.py`
- Modify: `config/views.py`
- Modify: `config/views_vocab.py`
- Modify: `config/views_grammar.py`
- Modify: `templates/home.html`
- Modify: `templates/partials/nav.html`
- Modify: `templates/vocab/browse.html`
- Modify: `templates/vocab/category_word_list.html`
- Modify: `templates/vocab/word_detail.html`
- Modify: `templates/vocab/quiz_setup.html`
- Modify: `templates/grammar/browse.html`
- Modify: `templates/grammar/topic_detail.html`
- Modify: `templates/grammar/topic_quiz.html`
- Create: `templates/vocab/home.html`
- Create: `templates/vocab/word_list.html`
- Create: `templates/grammar/home.html`
- Create: `templates/grammar/word.html`
- Create: `templates/reading.html`
- Create: `templates/writing.html`
- Create: `templates/listening.html`
- Create: `templates/speaking.html`
- Rename+Modify: `templates/grammar/test_setup.html` → `templates/grammar/quiz_setup.html`
- Rename+Modify: `templates/grammar/test_play.html` → `templates/grammar/quiz_play.html`
- Modify: `tests/test_vocab_pages.py`
- Modify: `tests/test_grammar_pages.py`
- Modify: `tests/test_pages.py`

**Interfaces:**
- Produces: 18 URL names resolvable via `{% url %}`/`reverse()`:
  `vocabulary_home`, `vocabulary_category_list`, `vocabulary_category_detail`,
  `vocabulary_word_list`, `vocabulary_word_detail`, `vocabulary_quiz_setup`,
  `vocabulary_quiz_play`, `grammar_home`, `grammar_category_list`,
  `grammar_category_detail`, `grammar_category_quiz`, `grammar_word`,
  `grammar_quiz_setup`, `grammar_quiz_play`, `reading`, `writing`, `listening`,
  `speaking`. Python view function names are **unchanged** — only the `path()`
  path string and `name=` kwarg move; e.g. `vocab_browse` (function) is now
  registered as `path('vocabulary/category/', vocab_browse, name='vocabulary_category_list')`.

- [ ] **Step 1: Rewrite `config/urls.py`**

Replace the entire file:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home, reading, writing, listening, speaking
from config.views_vocab import (
    vocab_browse, vocab_category, vocab_word_detail,
    vocab_quiz_setup, vocab_quiz_play,
    vocabulary_home, vocabulary_word_list,
)
from config.views_grammar import (
    grammar_browse, grammar_topic_detail, grammar_topic_quiz,
    grammar_test_setup, grammar_test_play,
    grammar_home, grammar_word,
)

urlpatterns = [
    path('', home, name='home'),

    path('vocabulary/', vocabulary_home, name='vocabulary_home'),
    path('vocabulary/category/', vocab_browse, name='vocabulary_category_list'),
    path('vocabulary/category/<slug:slug>/', vocab_category, name='vocabulary_category_detail'),
    path('vocabulary/word/', vocabulary_word_list, name='vocabulary_word_list'),
    path('vocabulary/word/<int:pk>/', vocab_word_detail, name='vocabulary_word_detail'),
    path('vocabulary/quiz/', vocab_quiz_setup, name='vocabulary_quiz_setup'),
    path('vocabulary/quiz/play/', vocab_quiz_play, name='vocabulary_quiz_play'),

    path('grammar/', grammar_home, name='grammar_home'),
    path('grammar/category/', grammar_browse, name='grammar_category_list'),
    path('grammar/category/<slug:slug>/', grammar_topic_detail, name='grammar_category_detail'),
    path('grammar/category/<slug:slug>/quiz/', grammar_topic_quiz, name='grammar_category_quiz'),
    path('grammar/word/', grammar_word, name='grammar_word'),
    path('grammar/quiz/', grammar_test_setup, name='grammar_quiz_setup'),
    path('grammar/quiz/play/', grammar_test_play, name='grammar_quiz_play'),

    path('reading/', reading, name='reading'),
    path('writing/', writing, name='writing'),
    path('listening/', listening, name='listening'),
    path('speaking/', speaking, name='speaking'),

    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 2: Add the 4 stub section views to `config/views.py`**

Replace the entire file:

```python
from django.shortcuts import render

from vocab.models import Category, Word


def home(request):
    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    learned_ids = [int(k) for k, v in learn_map.items() if v == 'learned']
    started_ids = [int(k) for k in learn_map.keys()]
    total_words = Word.objects.count()
    words_learned = len(learned_ids)
    pct_complete = round(words_learned / total_words * 100) if total_words else 0
    categories_started = Category.objects.filter(words__id__in=started_ids).distinct().count()
    return render(request, 'home.html', {
        'words_learned': words_learned,
        'categories_started': categories_started,
        'pct_complete': pct_complete,
    })


def reading(request):
    return render(request, 'reading.html')


def writing(request):
    return render(request, 'writing.html')


def listening(request):
    return render(request, 'listening.html')


def speaking(request):
    return render(request, 'speaking.html')
```

- [ ] **Step 3: Add `vocabulary_home` and `vocabulary_word_list` to `config/views_vocab.py`**

Append to the end of the file:

```python


def vocabulary_home(request):
    return render(request, 'vocab/home.html')


def vocabulary_word_list(request):
    return render(request, 'vocab/word_list.html')
```

- [ ] **Step 4: Add `grammar_home` and `grammar_word` to `config/views_grammar.py`**

Append to the end of the file:

```python


def grammar_home(request):
    return render(request, 'grammar/home.html')


def grammar_word(request):
    return render(request, 'grammar/word.html')
```

- [ ] **Step 5: Create the 4 top-level stub templates**

`templates/reading.html`:

```html
{% extends "base.html" %}
{% block title %}Reading — VocabLarry{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 03 / Reading</span>
  <h1>Reading</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

`templates/writing.html`:

```html
{% extends "base.html" %}
{% block title %}Writing — VocabLarry{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 04 / Writing</span>
  <h1>Writing</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

`templates/listening.html`:

```html
{% extends "base.html" %}
{% block title %}Listening — VocabLarry{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 05 / Listening</span>
  <h1>Listening</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

`templates/speaking.html`:

```html
{% extends "base.html" %}
{% block title %}Speaking — VocabLarry{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 06 / Speaking</span>
  <h1>Speaking</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

- [ ] **Step 6: Create the 2 new "Word" stub templates**

`templates/vocab/word_list.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Word — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 01 / Vocabulary</span>
  <h1>Word</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

`templates/grammar/word.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Word — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 02 / Grammar</span>
  <h1>Word</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

- [ ] **Step 7: Create temporary placeholder intro templates (real content lands in Task 5)**

`templates/vocab/home.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Vocabulary — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 01 / Vocabulary</span>
  <h1>Vocabulary</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

`templates/grammar/home.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Grammar — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="page-stub">
  <span class="eyebrow">Section 02 / Grammar</span>
  <h1>Grammar</h1>
  <p>Coming soon.</p>
</section>
{% endblock %}
```

- [ ] **Step 8: Rename and update the two grammar cross-topic quiz templates**

Rename `templates/grammar/test_setup.html` to `templates/grammar/quiz_setup.html`,
then replace its content:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-test-setup">
  <h1>Quiz</h1>
  <p class="grammar-test-intro">Practice across every topic at once — pick a level, question type, and length.</p>
  <form method="get" action="{% url 'grammar_quiz_play' %}" class="grammar-test-fields">
    <label class="grammar-test-field">
      <span>Level</span>
      <select name="stage">
        <option value="">All levels</option>
        {% for value, label in stages %}
          <option value="{{ value }}">{{ label }}</option>
        {% endfor %}
      </select>
    </label>
    <label class="grammar-test-field">
      <span>Question type</span>
      <select name="qtype">
        <option value="mixed" selected>Mixed</option>
        <option value="mcq">Multichoice</option>
        <option value="gap">Fill the Gap</option>
        <option value="transform">Rewrite the Sentence</option>
      </select>
    </label>
    <label class="grammar-test-field">
      <span>Questions</span>
      <select name="count">
        <option value="10">10 questions</option>
        <option value="20">20 questions</option>
        <option value="30">30 questions</option>
        <option value="all">All questions</option>
      </select>
    </label>
    <button type="submit" class="btn btn-primary">Start Quiz</button>
  </form>
</section>
{% endblock %}
```

Rename `templates/grammar/test_play.html` to `templates/grammar/quiz_play.html`,
then replace its content:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-test-play">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_category_list' %}">Grammar</a> / Quiz
  </p>
  <div id="grammarQuizRoot" data-mode="test"></div>
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/grammar-quiz.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 9: Update `{% url %}` references in every existing template**

`templates/home.html` — change:
```html
    <a class="btn btn-primary" href="{% url 'vocab_browse' %}" data-i18n="hero.start">Start Learning</a>
    <a class="home-btn-outline" href="{% url 'grammar_browse' %}" data-i18n="hero.grammar">Practice Grammar</a>
```
to:
```html
    <a class="btn btn-primary" href="{% url 'vocabulary_category_list' %}" data-i18n="hero.start">Start Learning</a>
    <a class="home-btn-outline" href="{% url 'grammar_category_list' %}" data-i18n="hero.grammar">Practice Grammar</a>
```

`templates/vocab/browse.html` — change:
```html
       href="{% url 'vocab_category' category.slug %}"
```
to:
```html
       href="{% url 'vocabulary_category_detail' category.slug %}"
```

`templates/vocab/category_word_list.html` — change:
```html
  <p class="vocab-breadcrumb"><a href="{% url 'vocab_browse' %}">Vocabulary</a> / {{ category.name }}</p>
```
to:
```html
  <p class="vocab-breadcrumb"><a href="{% url 'vocabulary_category_list' %}">Vocabulary</a> / {{ category.name }}</p>
```
and change:
```html
    <li><a href="{% url 'vocab_word_detail' word.pk %}">{{ word.word }}</a></li>
```
to:
```html
    <li><a href="{% url 'vocabulary_word_detail' word.pk %}">{{ word.word }}</a></li>
```

`templates/vocab/word_detail.html` — change:
```html
    <a href="{% url 'vocab_browse' %}">Vocabulary</a> /
    <a href="{% url 'vocab_category' word.category.slug %}">{{ word.category.name }}</a> /
```
to:
```html
    <a href="{% url 'vocabulary_category_list' %}">Vocabulary</a> /
    <a href="{% url 'vocabulary_category_detail' word.category.slug %}">{{ word.category.name }}</a> /
```

`templates/vocab/quiz_setup.html` — change:
```html
    <form method="get" action="{% url 'vocab_quiz_play' %}" class="vocab-quiz-fields">
```
to:
```html
    <form method="get" action="{% url 'vocabulary_quiz_play' %}" class="vocab-quiz-fields">
```

`templates/grammar/browse.html` — change:
```html
    <a class="grammar-topic-card" href="{% url 'grammar_topic_detail' topic.slug %}">
```
to:
```html
    <a class="grammar-topic-card" href="{% url 'grammar_category_detail' topic.slug %}">
```

`templates/grammar/topic_detail.html` — change:
```html
    <a href="{% url 'grammar_browse' %}">Grammar</a> / {{ topic.title }}
```
to:
```html
    <a href="{% url 'grammar_category_list' %}">Grammar</a> / {{ topic.title }}
```
and change:
```html
  <a class="btn grammar-topic-detail-practice" href="{% url 'grammar_topic_quiz' topic.slug %}">Practice this topic</a>
```
to:
```html
  <a class="btn grammar-topic-detail-practice" href="{% url 'grammar_category_quiz' topic.slug %}">Practice this topic</a>
```

`templates/grammar/topic_quiz.html` — change:
```html
    <a href="{% url 'grammar_browse' %}">Grammar</a> /
    <a href="{% url 'grammar_topic_detail' topic.slug %}">{{ topic.title }}</a> / Practice
```
to:
```html
    <a href="{% url 'grammar_category_list' %}">Grammar</a> /
    <a href="{% url 'grammar_category_detail' topic.slug %}">{{ topic.title }}</a> / Practice
```

`templates/partials/nav.html` — replace the entire `<ul class="nav-links">` block
(this keeps today's flat-tab structure and behavior identical — no dropdown, no
intro-page linking yet, that's Task 4 — only the URL names/hrefs move):
```html
  <ul class="nav-links">
    <li><a class="tab{% if request.resolver_match.url_name == 'vocab_browse' or request.resolver_match.url_name == 'vocab_category' or request.resolver_match.url_name == 'vocab_word_detail' %} active{% endif %}" href="{% url 'vocab_browse' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'vocab_quiz_setup' or request.resolver_match.url_name == 'vocab_quiz_play' %} active{% endif %}" href="{% url 'vocab_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_browse' or request.resolver_match.url_name == 'grammar_topic_detail' or request.resolver_match.url_name == 'grammar_topic_quiz' %} active{% endif %}" href="{% url 'grammar_browse' %}" data-i18n="nav.grammar">Grammar</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_test_setup' or request.resolver_match.url_name == 'grammar_test_play' %} active{% endif %}" href="{% url 'grammar_test_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
    {% if user.role == 'staff' or user.role == 'admin' %}
    <li><a href="{% url 'dashboard_index' %}">Dashboard</a></li>
    {% endif %}
  </ul>
```
with:
```html
  <ul class="nav-links">
    <li><a class="tab{% if request.resolver_match.url_name == 'vocabulary_category_list' or request.resolver_match.url_name == 'vocabulary_category_detail' or request.resolver_match.url_name == 'vocabulary_word_detail' %} active{% endif %}" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'vocabulary_quiz_setup' or request.resolver_match.url_name == 'vocabulary_quiz_play' %} active{% endif %}" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_category_list' or request.resolver_match.url_name == 'grammar_category_detail' or request.resolver_match.url_name == 'grammar_category_quiz' %} active{% endif %}" href="{% url 'grammar_category_list' %}" data-i18n="nav.grammar">Grammar</a></li>
    <li><a class="tab{% if request.resolver_match.url_name == 'grammar_quiz_setup' or request.resolver_match.url_name == 'grammar_quiz_play' %} active{% endif %}" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
    {% if user.role == 'staff' or user.role == 'admin' %}
    <li><a href="{% url 'dashboard_index' %}">Dashboard</a></li>
    {% endif %}
  </ul>
```

- [ ] **Step 10: Update `tests/test_vocab_pages.py`**

Replace the entire file:

```python
import json

import pytest
from django.test import Client
from vocab.models import CEFRLevel, Category, Word


@pytest.fixture
def cefr_a1(db):
    return CEFRLevel.objects.create(code='A1', name='Beginner', order=1)


@pytest.fixture
def cefr_b1(db):
    return CEFRLevel.objects.create(code='B1', name='Intermediate', order=2)


@pytest.mark.django_db
def test_vocabulary_category_list_renders():
    c = Client()
    r = c.get('/vocabulary/category/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_search_filters_by_name(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/category/?q=Animal')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_cefr_filter(cefr_a1, cefr_b1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Category.objects.create(slug='business-basics', name='Business Basics', order=2, cefr_level=cefr_b1)
    c = Client()
    r = c.get('/vocabulary/category/?cefr=B1')
    body = r.content.decode()
    assert 'Business Basics' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_category_list():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    # Vocabulary becomes a real link. Grammar stays disabled/coming-soon
    # on this same page (separate future sub-project) - don't assert
    # "coming soon" is gone entirely, only that Vocabulary now links out.
    assert 'href="/vocabulary/category/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body


@pytest.mark.django_db
def test_vocabulary_category_detail_renders_words(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='A small pet.', category=category, order=1)
    Word.objects.create(word='Dog', definition='A loyal pet.', category=category, order=2)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'Dog' in body


@pytest.mark.django_db
def test_vocabulary_category_detail_unknown_slug_404():
    c = Client()
    r = c.get('/vocabulary/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocabulary_category_detail_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(30):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r1 = c.get('/vocabulary/category/animals/')
    body1 = r1.content.decode()
    assert 'Word00' in body1
    assert 'Word29' not in body1  # page 2 content shouldn't leak onto page 1
    r2 = c.get('/vocabulary/category/animals/?page=2')
    body2 = r2.content.decode()
    assert 'Word29' in body2
    assert 'Word00' not in body2


@pytest.mark.django_db
def test_vocabulary_word_detail_renders(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(
        word='Cat', pos='noun', definition='A small domesticated pet.',
        example='The cat slept all day.', synonyms=['feline'], antonyms=[],
        category=category, order=1,
    )
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'Cat' in body
    assert 'A small domesticated pet.' in body
    assert 'The cat slept all day.' in body
    assert 'feline' in body


@pytest.mark.django_db
def test_vocabulary_word_detail_unknown_id_404():
    c = Client()
    r = c.get('/vocabulary/word/999999/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_vocabulary_word_detail_shows_progress_toggle_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'learn-state-btn' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_word_detail_hides_progress_toggle_when_anonymous(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'learn-state-btn' not in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_word_detail_reflects_existing_progress(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'data-state="learned"' in r.content.decode()


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
def test_vocabulary_word_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocabulary_word_detail_loads_toggle_script_when_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get(f'/vocabulary/word/{word.pk}/')
    assert 'vocab-word.js' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_renders():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_cefr_levels(cefr_a1):
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert '>A1<' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_family_toggle():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'name="family"' in html
    assert 'value="quiz"' in html
    assert 'value="gap"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_lists_gap_submodes():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="gap-context"' in html
    assert 'value="gap-nuance"' in html
    assert 'value="gap-collocation"' in html
    assert 'value="gap-connotation"' in html
    assert 'value="gap-mixed"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_quiz_modes_still_present():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="definition"' in html
    assert 'value="word"' in html
    assert 'value="synonym"' in html
    assert 'value="antonym"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_challenge_family_radio():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'value="challenge" id="familyChallenge"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_challenge_mode_input():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="challengeModeInput"' in html
    assert 'name="mode" value="challenge"' in html


@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_quiz():
    c = Client()
    r = c.get('/')
    assert 'href="/vocabulary/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_renders():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_has_mount_point():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert 'id="quizPlayRoot"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_play_loads_script():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    assert 'vocab-quiz.js' in r.content.decode()


@pytest.mark.django_db
def test_old_vocab_urls_are_gone():
    c = Client()
    assert c.get('/vocab/').status_code == 404
    assert c.get('/vocab/category/animals/').status_code == 404
    assert c.get('/vocab/word/1/').status_code == 404
    assert c.get('/vocab/quiz/').status_code == 404
    assert c.get('/vocab/quiz/play/').status_code == 404


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

- [ ] **Step 11: Update `tests/test_grammar_pages.py`**

Replace the entire file:

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
def test_grammar_category_list_renders():
    c = Client()
    r = c.get('/grammar/category/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_lists_topics(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'Articles (a/an/the)' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_search_filters_by_title(topic_articles):
    GrammarTopic.objects.create(
        slug='future-forms', title='Future Forms', tag='Tenses',
        cefr_label='A1+', blurb='will vs going to.', stage='beginner', order=1,
    )
    c = Client()
    r = c.get('/grammar/category/?q=Articles')
    html = r.content.decode()
    assert 'Articles (a/an/the)' in html
    assert 'Future Forms' not in html


@pytest.mark.django_db
def test_grammar_category_list_stage_filter(topic_articles):
    GrammarTopic.objects.create(
        slug='conditionals', title='Conditionals', tag='Conditionals',
        cefr_label='B2', blurb='If clauses.', stage='expert', order=1,
    )
    c = Client()
    r = c.get('/grammar/category/?stage=expert')
    html = r.content.decode()
    assert 'Conditionals' in html
    assert 'Articles (a/an/the)' not in html


@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/category/"' in html
    assert 'nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_home_hero_grammar_cta_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'hero.grammar">Practice Grammar</a>' in html


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
def test_grammar_category_detail_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert r.status_code == 200
    assert 'Present Simple &amp; Continuous' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/category/does-not-exist/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_category_detail_renders_intro_html_unescaped(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert '<b>facts</b>' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_renders_rule_title(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'Present Simple' in html
    assert '<b>-s</b>' in html


@pytest.mark.django_db
def test_grammar_category_detail_renders_table(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert '<th>Use</th>' in html
    assert '<td>Fact</td>' in html


@pytest.mark.django_db
def test_grammar_category_detail_renders_examples(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'The sun rises in the east.' in html
    assert 'General fact.' in html
    assert 'Prices are rising.' in html


@pytest.mark.django_db
def test_grammar_category_quiz_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-topic-slug="present-simple-continuous"' in html


@pytest.mark.django_db
def test_grammar_category_quiz_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/category/does-not-exist/quiz/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_category_detail_has_practice_link(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'href="/grammar/category/present-simple-continuous/quiz/"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_quiz_authenticated_flag_set(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert 'data-authenticated="1"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_quiz_authenticated_flag_unset_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/quiz/')
    assert 'data-authenticated="0"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_not_started_for_authenticated_user(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Not started yet' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_shows_best_score(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 60, 'done': False}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Best score: 60%' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_status_shows_mastered(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 90, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/present-simple-continuous/')
    assert 'Mastered' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_detail_no_status_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/category/present-simple-continuous/')
    html = r.content.decode()
    assert 'Not started yet' not in html
    assert 'grammar-topic-detail-status' not in html


@pytest.mark.django_db
def test_grammar_category_list_badge_shows_mastered(topic_articles, regular_user):
    regular_user.grammar_map = {'articles': {'best': 95, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/')
    assert 'grammar-topic-badge-mastered' in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_badge_for_untouched_topic(topic_articles, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/category/')
    assert 'grammar-topic-badge' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_category_list_no_badge_for_guest(topic_articles):
    c = Client()
    r = c.get('/grammar/category/')
    assert 'grammar-topic-badge' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_quiz_play_renders():
    c = Client()
    r = c.get('/grammar/quiz/play/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-mode="test"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_renders():
    c = Client()
    r = c.get('/grammar/quiz/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'name="stage"' in html
    assert 'name="qtype"' in html
    assert 'name="count"' in html
    assert 'action="/grammar/quiz/play/"' in html


@pytest.mark.django_db
def test_grammar_quiz_setup_stage_options_match_model():
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<option value="beginner">Basic</option>' in html
    assert '<option value="independent">Intermediate</option>' in html
    assert '<option value="expert">Advanced</option>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_link_present():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/quiz/"' in html
    assert 'nav.grammarTest">Grammar Test</a>' in html


@pytest.mark.django_db
def test_old_grammar_urls_are_gone():
    c = Client()
    assert c.get('/grammar/').status_code == 200  # now the intro page, not 404
    assert c.get('/grammar/topic/articles/').status_code == 404
    assert c.get('/grammar/topic/articles/quiz/').status_code == 404
    assert c.get('/grammar/test/').status_code == 404
    assert c.get('/grammar/test/play/').status_code == 404


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

- [ ] **Step 12: Append render tests for the 4 Reading/Writing/Listening/Speaking stub pages to `tests/test_pages.py`**

Append to the end of `tests/test_pages.py`:
```python
@pytest.mark.django_db
def test_reading_writing_listening_speaking_stub_pages_render():
    from django.test import Client
    c = Client()
    pages = [
        ('/reading/', 'Section 03 / Reading', 'Reading'),
        ('/writing/', 'Section 04 / Writing', 'Writing'),
        ('/listening/', 'Section 05 / Listening', 'Listening'),
        ('/speaking/', 'Section 06 / Speaking', 'Speaking'),
    ]
    for url, eyebrow, title in pages:
        r = c.get(url)
        assert r.status_code == 200, url
        html = r.content.decode()
        assert eyebrow in html, url
        assert f'<h1>{title}</h1>' in html, url
        assert 'Coming soon.' in html, url
```

- [ ] **Step 13: Update the nav-related tests in `tests/test_pages.py`**

In `tests/test_pages.py`, replace:
```python
@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocab_browse():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="tab" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_quiz_tab_active_on_vocab_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocab/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
    assert '<a class="tab" href="/vocab/" data-i18n="nav.vocabulary">Vocabulary</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_browse():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/" data-i18n="nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_nav_grammar_test_tab_active_on_grammar_test_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/test/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/test/" data-i18n="nav.grammarTest">Grammar Test</a>' in html
```
with:
```python
@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocabulary_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/category/" data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="tab" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_quiz_tab_active_on_vocabulary_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
    assert '<a class="tab" href="/vocabulary/category/" data-i18n="nav.vocabulary">Vocabulary</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/category/" data-i18n="nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_tab_active_on_grammar_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/quiz/" data-i18n="nav.grammarTest">Grammar Test</a>' in html
```

(Note: these 4 tests will be rewritten again in Task 4, once the dropdown nav
replaces this flat-tab structure — that's expected, not a mistake here.)

- [ ] **Step 14: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all tests pass (this project's suite runs via `pytest`, not
`manage.py test` — see project convention).

- [ ] **Step 15: Commit**

```bash
git add config/urls.py config/views.py config/views_vocab.py config/views_grammar.py \
  templates/home.html templates/partials/nav.html \
  templates/vocab/browse.html templates/vocab/category_word_list.html \
  templates/vocab/word_detail.html templates/vocab/quiz_setup.html \
  templates/vocab/home.html templates/vocab/word_list.html \
  templates/grammar/browse.html templates/grammar/topic_detail.html \
  templates/grammar/topic_quiz.html templates/grammar/home.html templates/grammar/word.html \
  templates/grammar/quiz_setup.html templates/grammar/quiz_play.html \
  templates/reading.html templates/writing.html templates/listening.html templates/speaking.html \
  tests/test_vocab_pages.py tests/test_grammar_pages.py tests/test_pages.py
git rm templates/grammar/test_setup.html templates/grammar/test_play.html
git commit -m "feat(vlpe): rename vocab/grammar URLs, add stub Word/R-L-S-W pages"
```

---

### Task 2: Nav active-section context processor

**Files:**
- Create: `config/context_processors.py`
- Modify: `config/settings.py`
- Create: `tests/test_context_processors.py`

**Interfaces:**
- Consumes: nothing from Task 1 (independent — the prefix-matching logic works
  against any `vocabulary_*`/`grammar_*`-named URL, whether or not Task 1 has run).
- Produces: a `nav_active_section` template context variable on every request,
  value one of `'home'`, `'vocabulary'`, `'grammar'`, `'reading'`, `'writing'`,
  `'listening'`, `'speaking'`, or `None`. Consumed by Task 4's `nav.html` rewrite.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_context_processors.py`:

```python
import pytest
from django.test import Client

from config.context_processors import nav_active_section


class _FakeMatch:
    def __init__(self, url_name):
        self.url_name = url_name


class _FakeRequest:
    def __init__(self, resolver_match):
        self.resolver_match = resolver_match


def test_nav_active_section_matches_vocabulary_prefix():
    request = _FakeRequest(_FakeMatch('vocabulary_quiz_setup'))
    assert nav_active_section(request) == {'nav_active_section': 'vocabulary'}


def test_nav_active_section_matches_grammar_prefix():
    request = _FakeRequest(_FakeMatch('grammar_category_detail'))
    assert nav_active_section(request) == {'nav_active_section': 'grammar'}


def test_nav_active_section_matches_flat_section_names():
    for name in ('home', 'reading', 'writing', 'listening', 'speaking'):
        request = _FakeRequest(_FakeMatch(name))
        assert nav_active_section(request) == {'nav_active_section': name}


def test_nav_active_section_none_for_unmatched_url_name():
    request = _FakeRequest(_FakeMatch('account_login'))
    assert nav_active_section(request) == {'nav_active_section': None}


def test_nav_active_section_none_when_resolver_match_is_none():
    request = _FakeRequest(None)
    assert nav_active_section(request) == {'nav_active_section': None}


@pytest.mark.django_db
def test_context_processor_is_wired_into_templates():
    # If config.context_processors.nav_active_section weren't correctly
    # registered in TEMPLATES, this dotted-path lookup would raise
    # ImproperlyConfigured the first time any page renders.
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_context_processors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config.context_processors'`

- [ ] **Step 3: Create `config/context_processors.py`**

```python
_VOCABULARY_PREFIX = 'vocabulary_'
_GRAMMAR_PREFIX = 'grammar_'
_FLAT_SECTIONS = {'home', 'reading', 'writing', 'listening', 'speaking'}


def nav_active_section(request):
    """Which top-level nav section the current page belongs to.

    Derived from the URL name's prefix rather than hand-listed per view,
    so adding a new vocabulary_*/grammar_* page never requires touching
    this function or nav.html's active-state logic.
    """
    match = request.resolver_match
    url_name = match.url_name if match else None
    if url_name is None:
        section = None
    elif url_name in _FLAT_SECTIONS:
        section = url_name
    elif url_name.startswith(_VOCABULARY_PREFIX):
        section = 'vocabulary'
    elif url_name.startswith(_GRAMMAR_PREFIX):
        section = 'grammar'
    else:
        section = None
    return {'nav_active_section': section}
```

- [ ] **Step 4: Register it in `config/settings.py`**

Change:
```python
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
```
to:
```python
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.nav_active_section',
            ],
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_context_processors.py -v`
Expected: PASS (6 passed)

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass — this step is purely additive, nothing consumes
`nav_active_section` yet.

- [ ] **Step 7: Commit**

```bash
git add config/context_processors.py config/settings.py tests/test_context_processors.py
git commit -m "feat(vlpe): add nav_active_section context processor"
```

---

### Task 3: Port production's card/dropdown/mobile-nav/stub CSS and icons

**Files:**
- Modify: `templates/base.html`
- Modify: `static/css/base.css`

**Interfaces:**
- Consumes: nothing (pure CSS/markup addition, no template logic depends on
  Task 1 or Task 2).
- Produces: CSS classes `.home-secs`, `.home-sec`, `.home-sec-ico`,
  `.home-sec-name`, `.home-sec-desc` (intro-page cards, consumed by Task 5);
  `.nav-group`, `.nav-dropdown`, `.nav-dropdown-item` (desktop dropdown,
  consumed by Task 4); `.mobile-nav-chip`, `.mobile-nav-menu`,
  `.mobile-nav-menu-item`, `.mobile-page-switcher`, `.chip` (mobile nav,
  consumed by Task 4 and Task 6); `.page-stub` (stub pages, already referenced
  by Task 1's templates). Icon symbols `#i-menu`, `#i-book`, `#i-target` added
  to the sprite in `base.html` (consumed by Task 4 and Task 5).

This task has no Python-testable surface (pure CSS/markup) — verify via
`node --check`-equivalent (there is no build step, so verify by confirming the
file parses/loads) and the existing suite staying green, since nothing
references these new classes yet.

- [ ] **Step 1: Add 3 new icon symbols to `templates/base.html`**

In the inline `<svg style="display:none">` sprite, change:
```html
  <symbol id="i-grad-cap" viewBox="0 0 24 24"><path d="M22 10v6"/><path d="M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></symbol>
</svg>
```
to:
```html
  <symbol id="i-grad-cap" viewBox="0 0 24 24"><path d="M22 10v6"/><path d="M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></symbol>
  <symbol id="i-menu" viewBox="0 0 24 24"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></symbol>
  <symbol id="i-book" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></symbol>
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
</svg>
```

(These 3 paths are copied verbatim from `VocabLarry/vocablarry.html`'s own
icon sprite, matching this project's "copy production's designs directly"
directive.)

- [ ] **Step 2: Append the new CSS to `static/css/base.css`**

Append to the end of the file:

```css

/* Section-link cards (Vocabulary/Grammar intro pages) — ported from
   production's .home-sec family (vocablarry.html), --vio renamed to
   --violet and rgba(var(--vio),X) converted to rgb(var(--violet) / X)
   per this codebase's established custom-property syntax rule. */
.home-secs{ display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; }
@media (max-width: 700px){ .home-secs{ grid-template-columns: repeat(2,1fr); } }
@media (max-width: 460px){ .home-secs{ grid-template-columns: 1fr; } }
.home-sec{
  background: rgba(22,26,35,.78); border: 1px solid rgb(var(--violet) / .15);
  border-radius: 20px; padding: 22px 20px; backdrop-filter: blur(14px);
  display: flex; flex-direction: column; gap: 7px; position: relative; overflow: hidden;
  transition: transform .45s var(--ease-luxe), border-color .45s var(--ease-luxe), box-shadow .45s var(--ease-luxe);
  text-decoration: none;
}
[data-theme="light"] .home-sec{ background: rgba(255,255,255,.86); }
.home-sec:hover{
  transform: translateY(-4px);
  border-color: rgb(var(--violet) / .45);
  box-shadow: 0 26px 60px rgba(0,0,0,.2), 0 6px 18px rgb(var(--violet) / .08);
}
.home-sec-ico{ font-size: 1.9rem; margin-bottom: 4px; color: rgb(var(--violet)); }
.home-sec-name{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: 1.05rem; font-weight: 800; color: var(--text);
}
.home-sec-desc{ font-size: .82rem; color: var(--muted); line-height: 1.55; }

/* Desktop dropdown nav (Vocabulary/Grammar) — ported from production's
   .nav-group/.nav-dropdown family. */
.nav-group{ position: relative; }
.nav-dropdown{
  display: none; position: absolute; top: calc(100% + 8px); left: 0; min-width: 160px;
  background: rgba(22,26,35,.94); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0,0,0,.4); padding: 12px; z-index: 50; flex-direction: column; gap: 4px;
}
[data-theme="light"] .nav-dropdown{ background: rgba(255,255,255,.94); }
.nav-group.open .nav-dropdown{ display: flex; }
.nav-dropdown-item{
  display: block; width: 100%; text-align: left; font-family: 'Plus Jakarta Sans','Sora',sans-serif;
  font-size: .9rem; font-weight: 600; color: var(--muted); text-decoration: none;
  padding: 10px 14px; border-radius: 10px;
}
.nav-dropdown-item:hover, .nav-dropdown-item.active{ color: var(--text); background: rgb(var(--violet) / .1); }

/* Mobile hamburger nav + in-page Category/Word/Quiz switcher — ported
   from production's .mobile-nav-chip/.mobile-page-switcher family. */
.mobile-nav-chip{ display: none; position: relative; align-items: center; gap: 8px; }
.mobile-nav-chip-label{ font-size: .85rem; font-weight: 600; color: var(--text); cursor: pointer; white-space: nowrap; }
.mobile-nav-chip.open .mobile-nav-menu{ display: flex; }
.mobile-nav-menu{
  display: none; position: absolute; top: calc(100% + 8px); left: 0; min-width: 200px;
  background: rgba(22,26,35,.94); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0,0,0,.4); padding: 12px; z-index: 50; flex-direction: column; gap: 4px;
}
[data-theme="light"] .mobile-nav-menu{ background: rgba(255,255,255,.94); }
.mobile-nav-menu-item{
  display: block; width: 100%; text-align: left; font-family: 'Plus Jakarta Sans','Sora',sans-serif;
  font-size: .9rem; font-weight: 600; color: var(--muted); background: transparent; border: none;
  padding: 10px 14px; border-radius: 10px; cursor: pointer; text-decoration: none;
}
.mobile-nav-menu-item:hover{ color: var(--text); background: rgb(var(--violet) / .1); }
.mobile-page-switcher{ display: none; gap: 8px; margin: 0 0 20px; flex-wrap: wrap; }
.mobile-page-switcher .chip{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: .82rem; font-weight: 600;
  color: var(--muted); background: var(--card-bg); border: 1px solid var(--border);
  border-radius: 999px; padding: 6px 14px; text-decoration: none;
}
.mobile-page-switcher .chip.active{ color: #fff; background: rgb(var(--violet)); border-color: rgb(var(--violet)); }
@media (max-width: 640px){
  .nav-links{ display: none; }
  .mobile-nav-chip{ display: flex; }
  .mobile-page-switcher{ display: flex; }
}

/* Minimal placeholder pages (Reading/Writing/Listening/Speaking, and the
   two not-yet-built Word pages) — matches production's literal
   eyebrow+h1+"Coming soon." shape. */
.page-stub{ padding: 64px 0; display: flex; flex-direction: column; gap: 10px; }
.page-stub h1{ margin: 6px 0 0; font-size: 2rem; }
.page-stub p{ color: var(--muted); }
```

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass unchanged — this task adds no template logic, only CSS and
unreferenced icon symbols.

- [ ] **Step 4: Commit**

```bash
git add templates/base.html static/css/base.css
git commit -m "feat(vlpe): port dropdown/mobile-nav/card/stub CSS from production"
```

---

### Task 4: Nav rewrite — desktop dropdown + mobile hamburger menu

**Files:**
- Modify: `templates/partials/nav.html`
- Create: `static/js/nav.js`
- Modify: `templates/base.html`
- Modify: `static/js/i18n.js`
- Modify: `tests/test_pages.py`
- Modify: `tests/test_vocab_pages.py`
- Modify: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: URL names from Task 1 (`vocabulary_home`, `vocabulary_category_list`,
  `vocabulary_category_detail`, `vocabulary_word_list`, `vocabulary_word_detail`,
  `vocabulary_quiz_setup`, `vocabulary_quiz_play`, `grammar_home`,
  `grammar_category_list`, `grammar_category_detail`, `grammar_category_quiz`,
  `grammar_word`, `grammar_quiz_setup`, `grammar_quiz_play`, `reading`,
  `writing`, `listening`, `speaking`); `nav_active_section` from Task 2; CSS
  classes `.nav-group`/`.nav-dropdown`/`.nav-dropdown-item`/`.mobile-nav-chip`/
  `.mobile-nav-menu`/`.mobile-nav-menu-item` and icon `#i-menu` from Task 3.
- Produces: the final `nav.html` markup shape (dropdown `<li class="nav-group">`
  wrapping a `.nav-dropdown`, `data-nav-toggle` attribute, `#mobileNavChip`/
  `#mobileNavToggle`/`#mobileNavMenu` ids) — consumed by Task 6's mobile chip
  rows (which link back to this same nav via matching `active` semantics) and by
  any future page needing to know the nav's structure.

- [ ] **Step 1: Add `nav.category` and `nav.word` i18n keys**

In `static/js/i18n.js`, change the `en` block:
```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
      "nav.comingSoon": "Coming soon",
```
to:
```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.category": "Category",
      "nav.word": "Word",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
      "nav.reading": "Reading",
      "nav.writing": "Writing",
      "nav.listening": "Listening",
      "nav.speaking": "Speaking",
      "nav.comingSoon": "Coming soon",
```
and the `vi` block:
```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
```
to:
```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.category": "Danh mục",
      "nav.word": "Từ",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
      "nav.reading": "Đọc",
      "nav.writing": "Viết",
      "nav.listening": "Nghe",
      "nav.speaking": "Nói",
      "nav.comingSoon": "Sắp ra mắt",
```

- [ ] **Step 2: Rewrite `templates/partials/nav.html`**

Replace the entire file:

```html
<nav class="site-nav">
  <a class="brand" href="{% url 'home' %}"><svg class="ico ico-mark" aria-hidden="true"><use href="#i-mark"/></svg>Vocab<b>Larry</b></a>
  <ul class="nav-links">
    <li class="nav-group{% if nav_active_section == 'vocabulary' %} active{% endif %}">
      <a class="tab{% if nav_active_section == 'vocabulary' %} active{% endif %}" href="{% url 'vocabulary_home' %}" data-nav-toggle data-i18n="nav.vocabulary">Vocabulary</a>
      <div class="nav-dropdown">
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'vocabulary_category_list' or request.resolver_match.url_name == 'vocabulary_category_detail' %} active{% endif %}" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'vocabulary_word_list' or request.resolver_match.url_name == 'vocabulary_word_detail' %} active{% endif %}" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'vocabulary_quiz_setup' or request.resolver_match.url_name == 'vocabulary_quiz_play' %} active{% endif %}" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
      </div>
    </li>
    <li class="nav-group{% if nav_active_section == 'grammar' %} active{% endif %}">
      <a class="tab{% if nav_active_section == 'grammar' %} active{% endif %}" href="{% url 'grammar_home' %}" data-nav-toggle data-i18n="nav.grammar">Grammar</a>
      <div class="nav-dropdown">
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'grammar_category_list' or request.resolver_match.url_name == 'grammar_category_detail' or request.resolver_match.url_name == 'grammar_category_quiz' %} active{% endif %}" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'grammar_word' %} active{% endif %}" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
        <a class="nav-dropdown-item{% if request.resolver_match.url_name == 'grammar_quiz_setup' or request.resolver_match.url_name == 'grammar_quiz_play' %} active{% endif %}" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
      </div>
    </li>
    <li><a class="tab{% if nav_active_section == 'reading' %} active{% endif %}" href="{% url 'reading' %}" data-i18n="nav.reading">Reading</a></li>
    <li><a class="tab{% if nav_active_section == 'writing' %} active{% endif %}" href="{% url 'writing' %}" data-i18n="nav.writing">Writing</a></li>
    <li><a class="tab{% if nav_active_section == 'listening' %} active{% endif %}" href="{% url 'listening' %}" data-i18n="nav.listening">Listening</a></li>
    <li><a class="tab{% if nav_active_section == 'speaking' %} active{% endif %}" href="{% url 'speaking' %}" data-i18n="nav.speaking">Speaking</a></li>
    {% if user.role == 'staff' or user.role == 'admin' %}
    <li><a href="{% url 'dashboard_index' %}">Dashboard</a></li>
    {% endif %}
  </ul>
  <div class="mobile-nav-chip" id="mobileNavChip">
    <button type="button" class="icon-toggle" id="mobileNavToggle" aria-label="Open navigation menu"><svg class="ico" aria-hidden="true"><use href="#i-menu"/></svg></button>
    <div class="mobile-nav-menu" id="mobileNavMenu">
      <a class="mobile-nav-menu-item" href="{% url 'home' %}" data-i18n="nav.home">Home</a>
      <a class="mobile-nav-menu-item" href="{% url 'vocabulary_home' %}" data-i18n="nav.vocabulary">Vocabulary</a>
      <a class="mobile-nav-menu-item" href="{% url 'grammar_home' %}" data-i18n="nav.grammar">Grammar</a>
      <a class="mobile-nav-menu-item" href="{% url 'reading' %}" data-i18n="nav.reading">Reading</a>
      <a class="mobile-nav-menu-item" href="{% url 'writing' %}" data-i18n="nav.writing">Writing</a>
      <a class="mobile-nav-menu-item" href="{% url 'listening' %}" data-i18n="nav.listening">Listening</a>
      <a class="mobile-nav-menu-item" href="{% url 'speaking' %}" data-i18n="nav.speaking">Speaking</a>
    </div>
  </div>
  <div class="nav-actions">
    <button type="button" class="icon-toggle" data-lang-toggle aria-label="Switch language"><svg class="ico" aria-hidden="true"><use href="#i-globe"/></svg></button>
    <button type="button" class="icon-toggle" data-theme-toggle aria-label="Toggle theme"><svg class="ico" data-theme-icon aria-hidden="true"><use href="#i-moon"/></svg></button>
    {% if user.is_authenticated %}
      <span>{{ user.username }}</span>
      <a class="btn" href="{% url 'account_logout' %}" data-i18n="nav.signOut">Sign Out</a>
    {% else %}
      <a class="btn" href="{% url 'account_login' %}" data-i18n="nav.signIn">Sign In</a>
      <a class="btn btn-primary" href="{% url 'account_signup' %}" data-i18n="nav.signUp">Sign Up</a>
    {% endif %}
  </div>
</nav>
```

Note: `data-i18n="nav.home"` on the mobile "Home" item needs an i18n key —
add it now alongside the other `nav.*` keys from Step 1. In `static/js/i18n.js`
`en` block add `"nav.home": "Home",` and in `vi` block add
`"nav.home": "Trang chủ",` (both right after the `"nav.vocabulary"` line).

- [ ] **Step 3: Create `static/js/nav.js`**

```javascript
(function(){
  document.querySelectorAll("[data-nav-toggle]").forEach(function(link){
    link.addEventListener("click", function(e){
      var group = link.closest(".nav-group");
      if (group && group.classList.contains("active")){
        e.preventDefault();
        group.classList.toggle("open");
      }
    });
  });

  document.addEventListener("click", function(e){
    if (!e.target.closest(".nav-group")){
      document.querySelectorAll(".nav-group.open").forEach(function(g){
        g.classList.remove("open");
      });
    }
    if (!e.target.closest("#mobileNavChip")){
      var chip = document.getElementById("mobileNavChip");
      if (chip) chip.classList.remove("open");
    }
  });

  var mobileToggle = document.getElementById("mobileNavToggle");
  if (mobileToggle){
    mobileToggle.addEventListener("click", function(){
      document.getElementById("mobileNavChip").classList.toggle("open");
    });
  }
})();
```

- [ ] **Step 4: Wire `nav.js` into `templates/base.html`**

Change:
```html
<script src="{% static 'js/i18n.js' %}" defer></script>
<script src="{% static 'js/base.js' %}" defer></script>
```
to:
```html
<script src="{% static 'js/i18n.js' %}" defer></script>
<script src="{% static 'js/base.js' %}" defer></script>
<script src="{% static 'js/nav.js' %}" defer></script>
```

- [ ] **Step 5: Update the 4 nav tests in `tests/test_pages.py` for the dropdown shape**

Replace the 4 tests written in Task 1 Step 12:
```python
@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocabulary_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/category/" data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="tab" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_quiz_tab_active_on_vocabulary_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
    assert '<a class="tab" href="/vocabulary/category/" data-i18n="nav.vocabulary">Vocabulary</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/category/" data-i18n="nav.grammar">Grammar</a>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_tab_active_on_grammar_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/quiz/" data-i18n="nav.grammarTest">Grammar Test</a>' in html
```
with:
```python
@pytest.mark.django_db
def test_nav_vocabulary_tab_active_on_vocabulary_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    # The li wrapper's "active" class is what nav.js reads (via
    # .closest(".nav-group")) to decide toggle-dropdown vs navigate —
    # check it explicitly, not just the inner <a>'s class.
    assert '<li class="nav-group active">' in html
    assert '<a class="tab active" href="/vocabulary/" data-nav-toggle data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="nav-dropdown-item active" href="/vocabulary/category/" data-i18n="nav.category">Category</a>' in html


@pytest.mark.django_db
def test_nav_quiz_dropdown_item_active_on_vocabulary_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="tab active" href="/vocabulary/" data-nav-toggle data-i18n="nav.vocabulary">Vocabulary</a>' in html
    assert '<a class="nav-dropdown-item active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_grammar_tab_active_on_grammar_category_list():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/category/')
    html = r.content.decode()
    assert '<a class="tab active" href="/grammar/" data-nav-toggle data-i18n="nav.grammar">Grammar</a>' in html
    assert '<a class="nav-dropdown-item active" href="/grammar/category/" data-i18n="nav.category">Category</a>' in html


@pytest.mark.django_db
def test_nav_grammar_quiz_dropdown_item_active_on_grammar_quiz_setup():
    from django.test import Client
    c = Client()
    r = c.get('/grammar/quiz/')
    html = r.content.decode()
    assert '<a class="nav-dropdown-item active" href="/grammar/quiz/" data-i18n="nav.quiz">Quiz</a>' in html


@pytest.mark.django_db
def test_nav_reading_writing_listening_speaking_tabs_present():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<a class="tab" href="/reading/" data-i18n="nav.reading">Reading</a>' in html
    assert '<a class="tab" href="/writing/" data-i18n="nav.writing">Writing</a>' in html
    assert '<a class="tab" href="/listening/" data-i18n="nav.listening">Listening</a>' in html
    assert '<a class="tab" href="/speaking/" data-i18n="nav.speaking">Speaking</a>' in html


@pytest.mark.django_db
def test_mobile_nav_menu_lists_all_7_sections():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'id="mobileNavMenu"' in html
    for href in ('/', '/vocabulary/', '/grammar/', '/reading/', '/writing/', '/listening/', '/speaking/'):
        assert f'<a class="mobile-nav-menu-item" href="{href}"' in html


@pytest.mark.django_db
def test_home_hero_ctas_bypass_intro_pages_and_link_to_category():
    # Regression guard: the nav's Vocabulary/Grammar links now point at the
    # intro pages (asserted above), but Home's own hero CTAs must keep
    # pointing directly at Category — this is the one deliberate exception
    # to "everything links to the intro page now".
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<a class="btn btn-primary" href="/vocabulary/category/" data-i18n="hero.start">Start Learning</a>' in html
    assert '<a class="home-btn-outline" href="/grammar/category/" data-i18n="hero.grammar">Practice Grammar</a>' in html
```

- [ ] **Step 6: Update the 2 home-nav-link tests in `tests/test_vocab_pages.py`**

These were written in Task 1 to point at the Category page; the Vocabulary
nav link now points at the intro page instead. Replace:
```python
@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_category_list():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    # Vocabulary becomes a real link. Grammar stays disabled/coming-soon
    # on this same page (separate future sub-project) - don't assert
    # "coming soon" is gone entirely, only that Vocabulary now links out.
    assert 'href="/vocabulary/category/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body
```
with:
```python
@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_home():
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    assert 'href="/vocabulary/"' in body
    assert 'data-i18n="nav.vocabulary">Vocabulary</a>' in body
```
and replace:
```python
@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_quiz():
    c = Client()
    r = c.get('/')
    assert 'href="/vocabulary/quiz/"' in r.content.decode()
```
with:
```python
@pytest.mark.django_db
def test_home_nav_links_to_vocabulary_quiz():
    c = Client()
    r = c.get('/')
    # The Quiz link lives inside the collapsed dropdown markup — still
    # present in the raw HTML even though CSS hides it until opened.
    assert 'href="/vocabulary/quiz/"' in r.content.decode()
```

(The assertion text is unchanged — only the surrounding comment — since the
link is present in the DOM regardless of dropdown open/closed state. This
step exists to confirm the test still passes against the new markup, not to
change its assertion.)

- [ ] **Step 7: Update `test_nav_grammar_link_enabled` and `test_nav_grammar_quiz_link_present` in `tests/test_grammar_pages.py`**

Replace:
```python
@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/category/"' in html
    assert 'nav.grammar">Grammar</a>' in html
```
with:
```python
@pytest.mark.django_db
def test_nav_grammar_link_enabled():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/"' in html
    assert 'nav.grammar">Grammar</a>' in html
```

Replace:
```python
@pytest.mark.django_db
def test_nav_grammar_quiz_link_present():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/quiz/"' in html
    assert 'nav.grammarTest">Grammar Test</a>' in html
```
with:
```python
@pytest.mark.django_db
def test_nav_grammar_quiz_link_present():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/quiz/"' in html
    assert 'nav.quiz">Quiz</a>' in html
```

- [ ] **Step 8: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 9: Manual browser verification (required — real interaction, no Python-testable surface)**

Start the dev server and drive a real Playwright/Chromium session:
- Desktop viewport: load `/vocabulary/category/`, confirm the Vocabulary tab
  shows `active`; click it — dropdown opens (Category/Word/Quiz visible);
  click each dropdown item — navigates to its real URL; click elsewhere on
  the page — dropdown closes. Repeat for Grammar.
- Load `/` (Home, no active section) — confirm neither Vocabulary nor Grammar
  shows `active`, clicking either navigates straight to its intro page (no
  dropdown opens, since neither `nav-group` has the `active` class yet).
- Mobile viewport (e.g. 375px wide): confirm `.nav-links` is hidden and the
  hamburger icon is visible; click it — menu opens listing all 7 sections;
  click "Vocabulary" — navigates to `/vocabulary/`; click outside — menu
  closes.
- Both themes (light/dark): confirm dropdown and mobile-menu backgrounds
  render correctly in each (`[data-theme="light"] .nav-dropdown` /
  `.mobile-nav-menu` overrides).

- [ ] **Step 10: Commit**

```bash
git add templates/partials/nav.html static/js/nav.js templates/base.html \
  static/js/i18n.js tests/test_pages.py tests/test_vocab_pages.py tests/test_grammar_pages.py
git commit -m "feat(vlpe): dropdown nav for Vocabulary/Grammar + mobile hamburger menu"
```

---

### Task 5: Vocabulary & Grammar intro pages (real content)

**Files:**
- Modify: `templates/vocab/home.html`
- Modify: `templates/grammar/home.html`
- Modify: `static/js/i18n.js`
- Modify: `tests/test_vocab_pages.py`
- Modify: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: URL names `vocabulary_category_list`, `vocabulary_word_list`,
  `vocabulary_quiz_setup`, `grammar_category_list`, `grammar_word`,
  `grammar_quiz_setup` from Task 1; `.home-sec`/`.home-secs`/`.home-sec-ico`/
  `.home-sec-name`/`.home-sec-desc` CSS from Task 3; `nav.category`/`nav.word`/
  `nav.quiz` i18n keys from Task 4.
- Produces: real hero+card content on `/vocabulary/` and `/grammar/`,
  replacing Task 1's temporary "Coming soon" placeholders.

- [ ] **Step 1: Add intro-page copy to `static/js/i18n.js`**

In the `en` block, after the `"home.complete"` line, add:
```javascript
      "vocabHome.badge": "5,000 words · 250 categories",
      "vocabHome.title1": "Build your word bank,",
      "vocabHome.title2": "one category at a time.",
      "vocabHome.subtitle": "Browse by topic, look up any word, or test yourself with a quiz — pick where to start below.",
      "vocabHome.descCategory": "Browse every word, grouped by topic and CEFR level.",
      "vocabHome.descWord": "Look up any word across the full dictionary.",
      "vocabHome.descQuiz": "Test yourself with definitions, synonyms, and gap-fills.",
      "grammarHome.badge": "47 topics · 14,100 questions",
      "grammarHome.title1": "Master the rules,",
      "grammarHome.title2": "not just the words.",
      "grammarHome.subtitle": "Browse grammar topics, look up reference tables, or practice with a quiz — pick where to start below.",
      "grammarHome.descCategory": "Browse every topic, from tenses to conditionals.",
      "grammarHome.descWord": "Reference tables for irregular verbs, comparisons, and linkers.",
      "grammarHome.descQuiz": "Practice across every topic at once.",
```
In the `vi` block, after the `"home.complete"` line, add:
```javascript
      "vocabHome.badge": "5.000 từ · 250 danh mục",
      "vocabHome.title1": "Xây dựng vốn từ,",
      "vocabHome.title2": "từng danh mục một.",
      "vocabHome.subtitle": "Duyệt theo chủ đề, tra từ, hoặc tự kiểm tra bằng bài trắc nghiệm — chọn nơi bắt đầu bên dưới.",
      "vocabHome.descCategory": "Duyệt mọi từ, được nhóm theo chủ đề và trình độ CEFR.",
      "vocabHome.descWord": "Tra cứu bất kỳ từ nào trong toàn bộ từ điển.",
      "vocabHome.descQuiz": "Tự kiểm tra với định nghĩa, từ đồng nghĩa và điền khuyết.",
      "grammarHome.badge": "47 chủ đề · 14.100 câu hỏi",
      "grammarHome.title1": "Nắm vững quy tắc,",
      "grammarHome.title2": "không chỉ từ vựng.",
      "grammarHome.subtitle": "Duyệt các chủ đề ngữ pháp, tra bảng tham khảo, hoặc luyện tập bằng bài trắc nghiệm — chọn nơi bắt đầu bên dưới.",
      "grammarHome.descCategory": "Duyệt mọi chủ đề, từ thì động từ đến câu điều kiện.",
      "grammarHome.descWord": "Bảng tham khảo động từ bất quy tắc, so sánh và từ nối.",
      "grammarHome.descQuiz": "Luyện tập trên tất cả chủ đề cùng lúc.",
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_vocab_pages.py`:
```python
@pytest.mark.django_db
def test_vocabulary_home_renders():
    c = Client()
    r = c.get('/vocabulary/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'href="/vocabulary/category/"' in html
    assert 'href="/vocabulary/word/"' in html
    assert 'href="/vocabulary/quiz/"' in html
    assert 'data-i18n="vocabHome.title1"' in html
```

Append to `tests/test_grammar_pages.py`:
```python
@pytest.mark.django_db
def test_grammar_home_renders():
    c = Client()
    r = c.get('/grammar/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'href="/grammar/category/"' in html
    assert 'href="/grammar/word/"' in html
    assert 'href="/grammar/quiz/"' in html
    assert 'data-i18n="grammarHome.title1"' in html
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_pages.py::test_vocabulary_home_renders tests/test_grammar_pages.py::test_grammar_home_renders -v`
Expected: FAIL — both pages still render Task 1's "Coming soon" placeholder,
missing the expected links/attributes.

- [ ] **Step 4: Replace `templates/vocab/home.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Vocabulary — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="home-hero">
  <div class="home-grid-bg"></div>
  <div class="home-glow"></div>
  <div class="home-badge"><svg class="ico" aria-hidden="true"><use href="#i-book"/></svg> <span data-i18n="vocabHome.badge">5,000 words · 250 categories</span></div>
  <h1 class="home-title"><span data-i18n="vocabHome.title1">Build your word bank,</span><br><span class="home-grad" data-i18n="vocabHome.title2">one category at a time.</span></h1>
  <p class="home-sub" data-i18n="vocabHome.subtitle">Browse by topic, look up any word, or test yourself with a quiz — pick where to start below.</p>
</section>
<div class="home-content">
  <div>
    <div class="home-secs">
      <a class="home-sec" href="{% url 'vocabulary_category_list' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-folder"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.category">Category</div>
        <div class="home-sec-desc" data-i18n="vocabHome.descCategory">Browse every word, grouped by topic and CEFR level.</div>
      </a>
      <a class="home-sec" href="{% url 'vocabulary_word_list' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-book"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.word">Word</div>
        <div class="home-sec-desc" data-i18n="vocabHome.descWord">Look up any word across the full dictionary.</div>
      </a>
      <a class="home-sec" href="{% url 'vocabulary_quiz_setup' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-target"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.quiz">Quiz</div>
        <div class="home-sec-desc" data-i18n="vocabHome.descQuiz">Test yourself with definitions, synonyms, and gap-fills.</div>
      </a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Replace `templates/grammar/home.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Grammar — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="home-hero">
  <div class="home-grid-bg"></div>
  <div class="home-glow"></div>
  <div class="home-badge"><svg class="ico" aria-hidden="true"><use href="#i-grad-cap"/></svg> <span data-i18n="grammarHome.badge">47 topics · 14,100 questions</span></div>
  <h1 class="home-title"><span data-i18n="grammarHome.title1">Master the rules,</span><br><span class="home-grad" data-i18n="grammarHome.title2">not just the words.</span></h1>
  <p class="home-sub" data-i18n="grammarHome.subtitle">Browse grammar topics, look up reference tables, or practice with a quiz — pick where to start below.</p>
</section>
<div class="home-content">
  <div>
    <div class="home-secs">
      <a class="home-sec" href="{% url 'grammar_category_list' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-folder"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.category">Category</div>
        <div class="home-sec-desc" data-i18n="grammarHome.descCategory">Browse every topic, from tenses to conditionals.</div>
      </a>
      <a class="home-sec" href="{% url 'grammar_word' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-book"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.word">Word</div>
        <div class="home-sec-desc" data-i18n="grammarHome.descWord">Reference tables for irregular verbs, comparisons, and linkers.</div>
      </a>
      <a class="home-sec" href="{% url 'grammar_quiz_setup' %}">
        <div class="home-sec-ico"><svg class="ico" aria-hidden="true"><use href="#i-target"/></svg></div>
        <div class="home-sec-name" data-i18n="nav.quiz">Quiz</div>
        <div class="home-sec-desc" data-i18n="grammarHome.descQuiz">Practice across every topic at once.</div>
      </a>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_pages.py::test_vocabulary_home_renders tests/test_grammar_pages.py::test_grammar_home_renders -v`
Expected: PASS

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add templates/vocab/home.html templates/grammar/home.html static/js/i18n.js \
  tests/test_vocab_pages.py tests/test_grammar_pages.py
git commit -m "feat(vlpe): real hero+card content for Vocabulary/Grammar intro pages"
```

---

### Task 6: Mobile page-switcher chip row

**Files:**
- Modify: `templates/vocab/browse.html`
- Modify: `templates/vocab/word_list.html`
- Modify: `templates/vocab/quiz_setup.html`
- Modify: `templates/vocab/quiz_play.html`
- Modify: `templates/grammar/browse.html`
- Modify: `templates/grammar/word.html`
- Modify: `templates/grammar/quiz_setup.html`
- Modify: `templates/grammar/quiz_play.html`
- Modify: `tests/test_vocab_pages.py`
- Modify: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: `.mobile-page-switcher`/`.chip` CSS from Task 3; URL names from
  Task 1.
- Produces: nothing consumed by later work — this is this plan's final task.

Per the spec, the chip row appears **only** on these 8 pages: Vocabulary's
Category-list/Word-list/Quiz-setup/Quiz-play, and Grammar's Category-list/
Word/Quiz-setup/Quiz-play. It does **not** appear on drill-in pages
(category detail, word detail, topic detail, per-topic quiz) or the 2 intro
pages.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vocab_pages.py`:
```python
@pytest.mark.django_db
def test_mobile_page_switcher_present_on_vocabulary_landing_pages(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    for url in ('/vocabulary/category/', '/vocabulary/word/', '/vocabulary/quiz/', '/vocabulary/quiz/play/'):
        r = c.get(url)
        assert 'mobile-page-switcher' in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_absent_on_vocabulary_drill_in_pages(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    for url in ('/vocabulary/', f'/vocabulary/category/{category.slug}/', f'/vocabulary/word/{word.pk}/'):
        r = c.get(url)
        assert 'mobile-page-switcher' not in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_marks_active_chip():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<a class="chip active" href="/vocabulary/quiz/" data-i18n="nav.quiz">Quiz</a>' in html
```

Append to `tests/test_grammar_pages.py`:
```python
@pytest.mark.django_db
def test_mobile_page_switcher_present_on_grammar_landing_pages(topic_articles):
    c = Client()
    for url in ('/grammar/category/', '/grammar/word/', '/grammar/quiz/', '/grammar/quiz/play/'):
        r = c.get(url)
        assert 'mobile-page-switcher' in r.content.decode(), url


@pytest.mark.django_db
def test_mobile_page_switcher_absent_on_grammar_drill_in_pages(topic_with_blocks):
    c = Client()
    for url in ('/grammar/', f'/grammar/category/{topic_with_blocks.slug}/', f'/grammar/category/{topic_with_blocks.slug}/quiz/'):
        r = c.get(url)
        assert 'mobile-page-switcher' not in r.content.decode(), url
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_pages.py -k mobile_page_switcher tests/test_grammar_pages.py -k mobile_page_switcher -v`
Expected: FAIL — none of the 8 templates have the chip row yet.

- [ ] **Step 3: Add the chip row to the 4 Vocabulary pages**

`templates/vocab/browse.html` — change:
```html
<section class="vocab-browse">
  <h1>Vocabulary</h1>
  <form method="get" class="vocab-filters">
```
to:
```html
<section class="vocab-browse">
  <h1>Vocabulary</h1>
  <div class="mobile-page-switcher">
    <a class="chip active" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <form method="get" class="vocab-filters">
```

`templates/vocab/word_list.html` — change:
```html
<section class="page-stub">
  <span class="eyebrow">Section 01 / Vocabulary</span>
  <h1>Word</h1>
  <p>Coming soon.</p>
</section>
```
to:
```html
<section class="page-stub">
  <span class="eyebrow">Section 01 / Vocabulary</span>
  <h1>Word</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip active" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <p>Coming soon.</p>
</section>
```

`templates/vocab/quiz_setup.html` — change:
```html
<section class="vocab-quiz-setup">
  <h1>Quiz</h1>
  <p class="vocab-quiz-intro">Test yourself on definitions, synonyms, antonyms, and fill-in-the-blank sentences.</p>
```
to:
```html
<section class="vocab-quiz-setup">
  <h1>Quiz</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <p class="vocab-quiz-intro">Test yourself on definitions, synonyms, antonyms, and fill-in-the-blank sentences.</p>
```

`templates/vocab/quiz_play.html` — the chip row can't go inside
`#quizPlayRoot` since `vocab-quiz.js` replaces that element's entire content
when rendering questions/results, which would wipe the chip row out. Change:
```html
{% block content %}
<section class="vocab-quiz-play" id="quizPlayRoot"></section>
{% endblock %}
```
to:
```html
{% block content %}
<section class="vocab-quiz-play">
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <div id="quizPlayRoot"></div>
</section>
{% endblock %}
```

(This restructure is safe: `vocab-quiz.js` looks up its mount point by
`id="quizPlayRoot"`, which still exists — only its wrapping tag changed from
`<section>` to `<div>` — confirmed by `test_vocabulary_quiz_play_has_mount_point`,
which only asserts the id attribute string is present, not the tag name.)

- [ ] **Step 4: Add the chip row to the 4 Grammar pages**

`templates/grammar/browse.html` — change:
```html
<section class="grammar-browse">
  <h1>Grammar</h1>
  <form method="get" class="grammar-filters">
```
to:
```html
<section class="grammar-browse">
  <h1>Grammar</h1>
  <div class="mobile-page-switcher">
    <a class="chip active" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <form method="get" class="grammar-filters">
```

`templates/grammar/word.html` — change:
```html
<section class="page-stub">
  <span class="eyebrow">Section 02 / Grammar</span>
  <h1>Word</h1>
  <p>Coming soon.</p>
</section>
```
to:
```html
<section class="page-stub">
  <span class="eyebrow">Section 02 / Grammar</span>
  <h1>Word</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip active" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
    <a class="chip" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <p>Coming soon.</p>
</section>
```

`templates/grammar/quiz_setup.html` — change:
```html
<section class="grammar-test-setup">
  <h1>Quiz</h1>
  <p class="grammar-test-intro">Practice across every topic at once — pick a level, question type, and length.</p>
```
to:
```html
<section class="grammar-test-setup">
  <h1>Quiz</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <p class="grammar-test-intro">Practice across every topic at once — pick a level, question type, and length.</p>
```

`templates/grammar/quiz_play.html` — change:
```html
<section class="grammar-test-play">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_category_list' %}">Grammar</a> / Quiz
  </p>
  <div id="grammarQuizRoot" data-mode="test"></div>
</section>
```
to:
```html
<section class="grammar-test-play">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_category_list' %}">Grammar</a> / Quiz
  </p>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'grammar_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'grammar_word' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'grammar_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <div id="grammarQuizRoot" data-mode="test"></div>
</section>
```

(No restructure needed here — `grammarQuizRoot` was already a sibling `<div>`
inside the section, not the section itself.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_pages.py -k mobile_page_switcher tests/test_grammar_pages.py -k mobile_page_switcher -v`
Expected: PASS

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 7: Manual browser verification (required — CSS breakpoint behavior)**

At a mobile viewport (e.g. 375px): confirm the chip row is visible and its
active chip is highlighted on each of the 8 pages; confirm it's absent on the
2 intro pages and the 4 drill-in pages. At a desktop viewport (e.g. 1280px):
confirm the chip row is hidden everywhere (the `@media (max-width: 640px)`
rule from Task 3). Check both themes.

- [ ] **Step 8: Commit**

```bash
git add templates/vocab/browse.html templates/vocab/word_list.html \
  templates/vocab/quiz_setup.html templates/vocab/quiz_play.html \
  templates/grammar/browse.html templates/grammar/word.html \
  templates/grammar/quiz_setup.html templates/grammar/quiz_play.html \
  tests/test_vocab_pages.py tests/test_grammar_pages.py
git commit -m "feat(vlpe): mobile Category/Word/Quiz chip switcher on landing pages"
```
