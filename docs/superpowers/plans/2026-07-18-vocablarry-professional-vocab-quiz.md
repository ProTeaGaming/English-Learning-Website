# VocabLarry Professional Environment — Vocab Quiz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a working Quiz-mode vocabulary quiz to VocabLarry Professional Environment — a server-rendered setup form (category/CEFR/mode/count) and a client-driven play page (question generation, scoring, results, review) — reusing the existing JSON API, no new backend.

**Architecture:** Two Django views render static template shells (`/vocab/quiz/` setup, `/vocab/quiz/play/` play). All question generation, scoring, and the play flow live entirely in `static/js/vocab-quiz.js`, which reads its configuration from the URL query string and fetches word/category data from the existing `/api/words/` and `/api/categories/` JSON endpoints.

**Tech Stack:** Django function views (no new models/migrations/endpoints), vanilla JS (`fetch`, no framework), pytest + pytest-django for the server-side surface.

## Global Constraints

- No new models, no new migrations, no new backend endpoints — reuses `vocab.models.Category`/`CEFRLevel` (server-side, for the setup form's selects) and the existing `/api/words/`, `/api/categories/` JSON endpoints (client-side, for question data).
- Question generation is a faithful port of `vocablarry.html`'s `buildQuestion`/`buildOptions`/`randomMixedMode` — same distractor-sampling algorithm, same Mixed-mode logic (Synonym/Antonym only offered when the word actually has them).
- Distractors are sampled from the **full** fetched word dataset, not the category/CEFR-filtered target pool — matches production's `others = VOCAB_DATA.filter(...)` behavior exactly.
- Selecting Synonym Match or Antonym Match filters the **target pool** to only words that have at least one synonym/antonym respectively (words without are excluded before random selection, not skipped one-by-one).
- No score/progress persistence anywhere — matches production, purely ephemeral client-side session state.
- Test with `pytest`, using `from django.test import Client; c = Client()` per-test, matching `tests/test_vocab_pages.py`'s existing convention. Extend that same file rather than creating a new one.
- There is no server-side equivalent of the question-generation/scoring logic to unit test — per the design spec, JS correctness is verified through manual browser testing per task, not automated tests.
- Reuse `conftest.py`'s existing `regular_user`/`staff_user`/`User` fixtures and `tests/test_vocab_pages.py`'s existing `cefr_a1`/`cefr_b1` fixtures — do not redefine them.

---

### Task 1: Quiz setup page

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `config/urls.py`
- Create: `templates/vocab/quiz_setup.html`
- Modify: `templates/partials/nav.html`
- Modify: `static/js/i18n.js`
- Modify: `static/css/vocab.css`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Produces: `config.views_vocab.vocab_quiz_setup(request)` — renders `vocab/quiz_setup.html`, context keys `categories` (queryset), `cefr_levels` (queryset).
- Produces: URL name `vocab_quiz_setup` at `/vocab/quiz/`.
- Produces: the setup form submits via plain `GET` to `vocab_quiz_play` (Task 2's URL, registered as a stub in this task — see Step 4) with query params `category`, `cefr`, `count`, `mode`.

- [ ] **Step 1: Write the failing tests**

Extend `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocab_quiz_setup_renders():
    c = Client()
    r = c.get('/vocab/quiz/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_categories(cefr_a1):
    Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get('/vocab/quiz/')
    assert 'Animals' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_cefr_levels(cefr_a1):
    c = Client()
    r = c.get('/vocab/quiz/')
    assert '>A1<' in r.content.decode()


@pytest.mark.django_db
def test_home_nav_links_to_vocab_quiz():
    c = Client()
    r = c.get('/')
    assert 'href="/vocab/quiz/"' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k "vocab_quiz_setup or test_home_nav_links_to_vocab_quiz"
```

Expected: all 4 FAIL — `/vocab/quiz/` doesn't resolve yet, and the nav has no Quiz link.

- [ ] **Step 3: Add the view**

The `category_word_list.html`/`word_detail.html` forward-reference lesson from the Vocab Browse + Word sub-project applies here too: this task's `quiz_setup.html` form action points at `{% url 'vocab_quiz_play' %}` (Task 2's view), a plain `<a>`-free `<form action=...>` attribute — Django's `{% url %}` tag is evaluated whenever the template renders, regardless of whether the form is ever submitted, so `vocab_quiz_play` must be registered (at minimum as a stub) in this task, exactly like Vocab Browse + Word's `vocab_category`/`vocab_word_detail` stubs.

Add to `config/views_vocab.py`:

```python
from django.http import HttpResponse


def vocab_quiz_setup(request):
    categories = Category.objects.order_by('order')
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/quiz_setup.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
    })


def vocab_quiz_play(request):
    # Stub for Task 2 — real implementation replaces only this function
    # body. Registered now, at the exact path Task 2 specifies, because
    # quiz_setup.html's <form action="{% url 'vocab_quiz_play' %}"> is
    # evaluated at render time regardless of whether the form is submitted.
    return HttpResponse('Quiz play page coming in Task 2', status=501)
```

- [ ] **Step 4: Wire the URLs**

Modify `config/urls.py`:

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

- [ ] **Step 5: Create `templates/vocab/quiz_setup.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-quiz-setup">
  <h1>Quiz</h1>
  <p class="vocab-quiz-intro">Test yourself on definitions, synonyms, and antonyms.</p>
  <form method="get" action="{% url 'vocab_quiz_play' %}" class="vocab-quiz-form">
    <label class="vocab-quiz-field">
      <span>Mode</span>
      <select name="mode">
        <option value="definition">Definition Match</option>
        <option value="word">Word from Definition</option>
        <option value="synonym">Synonym Match</option>
        <option value="antonym">Antonym Match</option>
        <option value="mixed">Mixed Review</option>
      </select>
    </label>
    <label class="vocab-quiz-field">
      <span>Category</span>
      <select name="category">
        <option value="">All categories</option>
        {% for category in categories %}
          <option value="{{ category.slug }}">{{ category.name }}</option>
        {% endfor %}
      </select>
    </label>
    <label class="vocab-quiz-field">
      <span>CEFR level</span>
      <select name="cefr">
        <option value="">All levels</option>
        {% for level in cefr_levels %}
          <option value="{{ level.code }}">{{ level.code }}</option>
        {% endfor %}
      </select>
    </label>
    <label class="vocab-quiz-field">
      <span>Questions</span>
      <select name="count">
        <option value="10">10 questions</option>
        <option value="20">20 questions</option>
        <option value="30">30 questions</option>
        <option value="all">All words</option>
      </select>
    </label>
    <button type="submit" class="btn btn-primary">Start Quiz</button>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 6: Wire the nav**

Modify `templates/partials/nav.html` — add a Quiz link between Vocabulary and Grammar:

```html
    <li><a href="{% url 'vocab_browse' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
```

becomes:

```html
    <li><a href="{% url 'vocab_browse' %}" data-i18n="nav.vocabulary">Vocabulary</a></li>
    <li><a href="{% url 'vocab_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a></li>
```

- [ ] **Step 7: Add the i18n key**

Modify `static/js/i18n.js` — add `"nav.quiz"` to both dictionaries:

```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
```

```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
```

(Insert each line right after the corresponding `"nav.vocabulary"` line in its dictionary — the rest of each dictionary is unchanged.)

- [ ] **Step 8: Create the setup-form CSS**

Append to `static/css/vocab.css`:

```css
.vocab-quiz-setup h1{ margin-top: 32px; }
.vocab-quiz-intro{ color: var(--muted); margin: 8px 0 24px; }
.vocab-quiz-form{
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 360px;
}
.vocab-quiz-field{
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}
.vocab-quiz-field select{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 400;
}
```

- [ ] **Step 9: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k "vocab_quiz_setup or test_home_nav_links_to_vocab_quiz"
```

Expected: all 4 PASS.

- [ ] **Step 10: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `116 passed` (112 from Vocab Browse + Word + 4 new).

- [ ] **Step 11: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add vocab quiz setup page

GET /vocab/quiz/ renders a form (mode/category/CEFR/count), submitting
via GET to the play page's query string. New nav entry for Quiz
alongside Vocabulary. vocab_quiz_play is stubbed (501) at this point -
Task 2 replaces it with the real page.
EOF
)"
```

---

### Task 2: Quiz play page shell

**Files:**
- Modify: `config/views_vocab.py`
- Create: `templates/vocab/quiz_play.html`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Produces: `config.views_vocab.vocab_quiz_play(request)` — renders `vocab/quiz_play.html` with no context. Replaces the 501 stub Task 1 registered; the URL name/route doesn't change.
- Produces: an empty `<section id="quizPlayRoot">` mount point and a `<script src=".../vocab-quiz.js">` tag — Task 3 creates that file; this task only wires up the empty page shell that will load it.

- [ ] **Step 1: Write the failing tests**

Extend `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocab_quiz_play_renders():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_play_has_mount_point():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert 'id="quizPlayRoot"' in r.content.decode()


@pytest.mark.django_db
def test_vocab_quiz_play_loads_script():
    c = Client()
    r = c.get('/vocab/quiz/play/')
    assert 'vocab-quiz.js' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k vocab_quiz_play
```

Expected: `test_vocab_quiz_play_renders` FAILS on status code (501, not 200 — the Task 1 stub). The other two FAIL because the stub's placeholder text contains neither `id="quizPlayRoot"` nor `vocab-quiz.js`.

- [ ] **Step 3: Replace the stub view**

Replace the `# Stub for Task 2...` function in `config/views_vocab.py` with:

```python
def vocab_quiz_play(request):
    return render(request, 'vocab/quiz_play.html')
```

Remove the `from django.http import HttpResponse` import added in Task 1 (confirm nothing else in the file uses `HttpResponse` before removing it — `vocab_quiz_setup`/`vocab_browse`/`vocab_category`/`vocab_word_detail` all use `render`/`get_object_or_404`, not `HttpResponse`, so it should be safe).

- [ ] **Step 4: Create `templates/vocab/quiz_play.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-quiz-play" id="quizPlayRoot"></section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/vocab-quiz.js' %}" defer></script>
{% endblock %}
```

Note: `static/js/vocab-quiz.js` doesn't exist yet — Task 3 creates it. Until then, this page's `<script>` tag 404s harmlessly (the browser logs a failed request, nothing on the page depends on the script having loaded to render the empty shell) — this task's own tests only check the tag is present in the HTML, not that the file actually exists yet.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k vocab_quiz_play
```

Expected: all 3 PASS.

- [ ] **Step 6: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `119 passed`.

- [ ] **Step 7: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add vocab quiz play page shell

GET /vocab/quiz/play/ now renders a real page with an empty mount
point and loads static/js/vocab-quiz.js (created in the next task).
EOF
)"
```

---

### Task 3: Question generation and single-question play flow

**Files:**
- Create: `static/js/vocab-quiz.js`
- Modify: `static/css/vocab.css`

**Interfaces:**
- Consumes: `/api/words/` (returns a JSON array of `{id, word, pos, definition, synonyms, antonyms, example, gap, category_id, cefr_code, order}` per word — `api/views.py:words`, unchanged), `/api/categories/` (returns `{id, slug, name, icon, cefr_code, cefr_level_id, bg_hex, color_id, text_hex, order}` per category — `api/views.py:categories`, unchanged).
- Consumes: query string params `category` (slug), `cefr` (code), `count` (`"10"`/`"20"`/`"30"`/`"all"`), `mode` (`"definition"`/`"word"`/`"synonym"`/`"antonym"`/`"mixed"`) from `window.location.search`.
- Consumes: `#quizPlayRoot` mount point from Task 2's `quiz_play.html`.
- Produces: `renderResults()` — an intentionally empty stub function. Task 4 replaces only this function's body; nothing else in this file changes. Calling it (which happens when the user finishes the last question) does nothing yet — that's expected for this task, not a bug.

This task has no Python-testable surface (per the plan's Global Constraints) — verify entirely by hand per Step 3 below.

- [ ] **Step 1: Create `static/js/vocab-quiz.js`**

```javascript
(function(){
  var root = document.getElementById("quizPlayRoot");
  if (!root) return;

  var params = new URLSearchParams(window.location.search);
  var categorySlug = params.get("category") || "";
  var cefrCode = params.get("cefr") || "";
  var requestedCount = params.get("count") || "10";
  var mode = params.get("mode") || "definition";

  var state = {
    allWords: [],
    categoriesBySlug: {},
    questions: [],
    idx: 0,
    score: 0,
    answers: [],
  };

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function capitalize(s){
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  }

  function buildOptions(correct, othersPool, getValue){
    var opts = [correct];
    var pool = shuffle(othersPool);
    var i = 0;
    while (opts.length < 4 && i < pool.length){
      var candidate = getValue(pool[i]);
      if (candidate && opts.indexOf(candidate) === -1) opts.push(candidate);
      i++;
    }
    return shuffle(opts);
  }

  function randomMixedMode(word){
    var options = ["definition", "word"];
    if (word.synonyms && word.synonyms.length) options.push("synonym");
    if (word.antonyms && word.antonyms.length) options.push("antonym");
    return options[Math.floor(Math.random() * options.length)];
  }

  function buildQuestion(word, qMode){
    var others = state.allWords.filter(function(w){ return w.id !== word.id; });
    var prompt, text, correct, options;
    if (qMode === "word"){
      prompt = "Which word matches this definition?";
      text = word.definition;
      correct = word.word;
      options = buildOptions(correct, others, function(w){ return w.word; });
    } else if (qMode === "synonym"){
      var syns = word.synonyms || [];
      correct = capitalize(syns[Math.floor(Math.random() * syns.length)]);
      prompt = "Choose a word with a similar meaning:";
      text = word.word + " (" + word.pos + ")";
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else if (qMode === "antonym"){
      var ants = word.antonyms || [];
      correct = capitalize(ants[Math.floor(Math.random() * ants.length)]);
      prompt = "Choose a word with the opposite meaning:";
      text = word.word + " (" + word.pos + ")";
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else {
      prompt = "Choose the correct definition:";
      text = word.word + " (" + word.pos + ")";
      correct = word.definition;
      options = buildOptions(correct, others, function(w){ return w.definition; });
    }
    return { prompt: prompt, text: text, options: options, correct: correct, word: word };
  }

  function buildPool(){
    var pool = state.allWords;
    if (categorySlug){
      var catId = state.categoriesBySlug[categorySlug];
      if (catId) pool = pool.filter(function(w){ return w.category_id === catId; });
    }
    if (cefrCode){
      pool = pool.filter(function(w){ return w.cefr_code === cefrCode; });
    }
    if (mode === "synonym"){
      pool = pool.filter(function(w){ return w.synonyms && w.synonyms.length; });
    } else if (mode === "antonym"){
      pool = pool.filter(function(w){ return w.antonyms && w.antonyms.length; });
    }
    return pool;
  }

  function pickTargetWords(pool){
    var shuffled = shuffle(pool);
    if (requestedCount === "all") return shuffled;
    var n = parseInt(requestedCount, 10) || 10;
    return shuffled.slice(0, Math.min(n, shuffled.length));
  }

  function generateQuestions(){
    var pool = buildPool();
    var targets = pickTargetWords(pool);
    state.questions = targets.map(function(word){
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }

  function renderError(message){
    root.innerHTML = '<p class="vocab-quiz-error">' + message + ' <a href="/vocab/quiz/">Back to setup</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    root.innerHTML =
      '<div class="vocab-quiz-progress"><div class="vocab-quiz-progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="vocab-quiz-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="vocab-quiz-card">' +
        '<div class="vocab-quiz-prompt">' + q.prompt + '</div>' +
        '<div class="vocab-quiz-text">' + q.text + '</div>' +
        '<div class="vocab-quiz-options">' +
          q.options.map(function(opt){ return '<button type="button" class="vocab-quiz-opt">' + opt + '</button>'; }).join("") +
        '</div>' +
        '<div class="vocab-quiz-feedback"></div>' +
        '<div class="vocab-quiz-next" style="display:none;"><button type="button" class="btn" id="quizNextBtn"></button></div>' +
      '</div>';
    root.querySelectorAll(".vocab-quiz-opt").forEach(function(btn){
      btn.addEventListener("click", function(){ handleAnswer(btn, q); });
    });
  }

  function handleAnswer(selectedBtn, q){
    var isCorrect = selectedBtn.textContent === q.correct;
    root.querySelectorAll(".vocab-quiz-opt").forEach(function(btn){
      btn.disabled = true;
      if (btn.textContent === q.correct) btn.classList.add("correct");
      else if (btn === selectedBtn) btn.classList.add("wrong");
    });
    if (isCorrect) state.score++;
    state.answers.push({ question: q, selected: selectedBtn.textContent, isCorrect: isCorrect });
    var feedback = root.querySelector(".vocab-quiz-feedback");
    feedback.innerHTML = (isCorrect ? "<b>Correct!</b> " : "<b>Not quite.</b> The answer is " + q.correct + ". ") +
      q.word.word + " — " + q.word.definition;
    root.querySelector(".vocab-quiz-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".vocab-quiz-next");
    var nextBtn = document.getElementById("quizNextBtn");
    var isLast = state.idx + 1 === state.questions.length;
    nextBtn.textContent = isLast ? "See Results" : "Next Question";
    nextWrap.style.display = "flex";
    nextBtn.addEventListener("click", function(){
      state.idx++;
      if (state.idx < state.questions.length) renderQuestion();
      else renderResults();
    });
  }

  function renderResults(){
    // Replaced in Task 4 — until then, finishing the last question does
    // nothing (the "See Results" button click has no visible effect).
  }

  function init(){
    Promise.all([
      fetch("/api/words/").then(function(r){ return r.json(); }),
      fetch("/api/categories/").then(function(r){ return r.json(); }),
    ]).then(function(results){
      state.allWords = results[0];
      results[1].forEach(function(c){ state.categoriesBySlug[c.slug] = c.id; });
      generateQuestions();
      if (state.questions.length === 0){
        renderError("No words available for this combination — try different settings.");
        return;
      }
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  init();
})();
```

- [ ] **Step 2: Append the play-screen CSS**

Append to `static/css/vocab.css`:

```css
.vocab-quiz-progress{
  height: 6px;
  border-radius: 999px;
  background: var(--border);
  margin: 24px 0 16px;
  overflow: hidden;
}
.vocab-quiz-progress-fill{
  height: 100%;
  background: rgb(var(--violet));
}
.vocab-quiz-meta{
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 0.9rem;
  margin-bottom: 16px;
}
.vocab-quiz-card{
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  background: var(--card-bg);
}
.vocab-quiz-prompt{ font-weight: 700; margin-bottom: 8px; }
.vocab-quiz-text{ font-size: 1.2rem; margin-bottom: 20px; }
.vocab-quiz-options{
  display: grid;
  gap: 10px;
}
.vocab-quiz-opt{
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  text-align: left;
  font-size: 0.95rem;
  cursor: pointer;
}
.vocab-quiz-opt.correct{ border-color: #22c55e; background: rgba(34,197,94,0.12); }
.vocab-quiz-opt.wrong{ border-color: #dc2626; background: rgba(220,38,38,0.12); }
.vocab-quiz-feedback{ margin-top: 16px; color: var(--muted); }
.vocab-quiz-next{ margin-top: 20px; }
.vocab-quiz-error{ color: var(--muted); padding: 40px 0; }
```

- [ ] **Step 3: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Navigate to `/vocab/quiz/`, leave every field at its default, click Start Quiz. Confirm: the play page loads, a progress bar and "Question 1 of 10" appear, a Definition Match question renders with 4 options. Click an option — confirm the correct option turns green, a wrong pick (if you chose wrong) turns red, feedback text appears below with the word and its definition, and a "Next Question" button appears. Click through several questions, confirming the score in the top-right increments only on correct answers and the progress bar advances. On the last question, click "See Results" — confirm nothing happens yet (expected, Task 4 implements this). Then test the other 3 real modes (`?mode=word`, `?mode=synonym`, `?mode=antonym` via the setup form) and Mixed, and test a category + CEFR filter combination to confirm the target pool actually narrows (try a combination you know has very few matching words, and confirm the question count doesn't exceed the pool size). Also test the zero-pool case (e.g. Antonym Match on a category where nothing has antonyms) — confirm the "No words available..." message renders instead of a broken question. Stop the server (Ctrl+C) when done.

- [ ] **Step 4: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): implement quiz question generation and single-question flow

static/js/vocab-quiz.js ports vocablarry.html's buildQuestion/
buildOptions/randomMixedMode algorithms faithfully: distractors sampled
from the full word dataset, target pool filtered by category/CEFR (and,
for Synonym/Antonym modes, by synonym/antonym availability). Handles
one question through to the next; the results screen is an intentional
no-op stub, replaced in the next task.
EOF
)"
```

---

### Task 4: Results screen, review, and retry

**Files:**
- Modify: `static/js/vocab-quiz.js`
- Modify: `static/css/vocab.css`

**Interfaces:**
- Consumes: `state.questions`, `state.score`, `state.answers`, `generateQuestions()`, `renderQuestion()`, `renderError()` from Task 3 — all unchanged.
- Produces: no new interfaces for later tasks — this is the last task in this sub-project.

This task has no Python-testable surface — verify entirely by hand per Step 2 below.

- [ ] **Step 1: Replace the `renderResults` stub**

In `static/js/vocab-quiz.js`, replace:

```javascript
  function renderResults(){
    // Replaced in Task 4 — until then, finishing the last question does
    // nothing (the "See Results" button click has no visible effect).
  }
```

with:

```javascript
  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    root.innerHTML =
      '<div class="vocab-quiz-results">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="vocab-quiz-score">' + state.score + ' / ' + total + '</div>' +
        '<p class="vocab-quiz-pct">' + pct + '%</p>' +
        '<div class="vocab-quiz-result-actions">' +
          '<button type="button" class="btn" id="quizRetryBtn">Try Again</button>' +
          '<button type="button" class="btn" id="quizChangeBtn">Change Settings</button>' +
          '<button type="button" class="btn" id="quizReviewBtn">Review Answers</button>' +
        '</div>' +
        '<div class="vocab-quiz-review" id="quizReview" style="display:none;"></div>' +
      '</div>';
    document.getElementById("quizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.answers = [];
      generateQuestions();
      if (state.questions.length === 0){
        renderError("No words available for this combination — try different settings.");
        return;
      }
      renderQuestion();
    });
    document.getElementById("quizChangeBtn").addEventListener("click", function(){
      window.location.href = "/vocab/quiz/";
    });
    document.getElementById("quizReviewBtn").addEventListener("click", function(){
      var panel = document.getElementById("quizReview");
      if (panel.style.display === "block"){ panel.style.display = "none"; return; }
      panel.innerHTML = state.answers.map(function(a, i){
        return '<div class="vocab-quiz-review-item ' + (a.isCorrect ? "correct" : "wrong") + '">' +
          '<span class="vocab-quiz-review-num">' + (i + 1) + '</span>' +
          '<span class="vocab-quiz-review-word">' + a.question.word.word + '</span>' +
          '<span class="vocab-quiz-review-answer">Your answer: ' + a.selected + '</span>' +
          (a.isCorrect ? '' : '<span class="vocab-quiz-review-correct">Correct: ' + a.question.correct + '</span>') +
        '</div>';
      }).join("");
      panel.style.display = "block";
    });
  }
```

- [ ] **Step 2: Append the results/review CSS**

Append to `static/css/vocab.css`:

```css
.vocab-quiz-results{ text-align: center; padding: 40px 0; }
.vocab-quiz-score{ font-size: 3rem; font-weight: 800; color: rgb(var(--violet)); }
.vocab-quiz-pct{ color: var(--muted); margin-bottom: 24px; }
.vocab-quiz-result-actions{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.vocab-quiz-review{ text-align: left; margin-top: 32px; display: flex; flex-direction: column; gap: 10px; }
.vocab-quiz-review-item{
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.vocab-quiz-review-item.correct{ border-color: #22c55e; }
.vocab-quiz-review-item.wrong{ border-color: #dc2626; }
.vocab-quiz-review-num{ font-weight: 700; color: var(--muted); }
.vocab-quiz-review-correct{ color: #dc2626; font-weight: 600; }
```

- [ ] **Step 3: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Start a 10-question quiz and answer all 10 (mix of correct/incorrect on purpose). On the last question, click "See Results" — confirm a results screen renders with your actual score (e.g. "7 / 10") and percentage. Click "Review Answers" — confirm a list of all 10 questions appears, each showing the word, your answer, and (for wrong answers only) the correct answer, with correct/wrong ones visually distinguished. Click "Review Answers" again — confirm it collapses. Click "Try Again" — confirm a fresh question set starts (different random distractor order — you likely won't get the exact same questions back-to-back since selection is random), score reset to 0. Complete it again, click "Change Settings" this time — confirm it navigates back to `/vocab/quiz/` with the setup form. Stop the server (Ctrl+C) when done.

- [ ] **Step 4: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): add quiz results, review, and retry

renderResults() now shows the final score/percentage, a per-question
review list (word, your answer, correct answer when wrong), a Try
Again button that regenerates a fresh question set from the same
filters, and Change Settings back to the setup form. Completes the
Quiz-mode vertical slice - Gap and Challenge modes are separate future
sub-projects building on this same architecture.
EOF
)"
```

---

## Definition of Done

- `python -m pytest tests -q` is fully green (119 tests).
- `manage.py check` is clean.
- Manual browser check confirms: setup form → play (all 5 modes: Definition/Word/Synonym/Antonym/Mixed) → answer feedback → results → review → Try Again → Change Settings, all working, plus the zero-pool error case and a category/CEFR filter actually narrowing the question pool.
- Home hero/nav still correctly link Vocabulary + Quiz; Grammar remains disabled.
- Gap mode, Challenge mode, word hand-picking, learned-state filtering, section grouping, content i18n, dialect substitution, and score persistence remain explicitly out of scope, unaffected by this work.
