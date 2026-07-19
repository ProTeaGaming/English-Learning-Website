# VocabLarry Professional Environment — Grammar Topic Quiz Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a playable per-topic Grammar quiz to VocabLarry Professional Environment — a 10-question random draw from a topic's question bank (MCQ + strict-typed gap/transform), with a results screen, and account-persisted mastery tracking shown back on the topic and browse pages.

**Architecture:** A new near-empty Django page (`/grammar/topic/<slug>/quiz/`) is driven entirely by a new client-side JS module (`static/js/grammar-quiz.js`) that fetches the already-existing `/api/grammar/` endpoint and does all question sampling, rendering, and scoring in the browser — mirroring `static/js/vocab-quiz.js`'s architecture exactly. Mastery persistence reuses the already-existing `/auth/sync/` endpoint and `CustomUser.grammar_map` field via the same GET-then-merge-then-POST pattern `static/js/vocab-word.js` already established.

**Tech Stack:** Django function views (no new models/migrations/endpoints), Django templates, one new vanilla-JS module, pytest + pytest-django for the server-rendered surface, Playwright for the client-side quiz engine (no automated test coverage is possible for it).

## Global Constraints

- No new models, no new migrations, no new backend endpoints. `GrammarQuestion` already has every field needed (`qtype`, `prompt`, `options`, `answers`, `why`); `/api/grammar/` already returns each topic's questions nested; `CustomUser.grammar_map` and `/auth/sync/` already exist and already merge correctly (POSTing `{grammar_map: ...}` never touches `learn_map`, and vice versa).
- Quiz question sampling, rendering, and scoring happen entirely in `static/js/grammar-quiz.js`, fetching `/api/grammar/` client-side — no server-rendered question data, no new JSON endpoint.
- No setup step. A "Practice" link on the topic detail page launches the quiz directly: always a fresh random draw of 10 questions (`DRAW_COUNT = 10`) from the topic's question bank.
- Typed answers (`gap`/`transform` question types) are graded **strictly**: only curly-vs-straight apostrophe normalization and outer trim happen before comparison — capitalization, internal spacing, and final punctuation all count as mistakes. Do not add leniency.
- A `gap` question whose `prompt` starts with `"___"` expects its answer capitalized (first letter uppercased) even though some historical data may store it lowercase.
- Once any question in the *current 10-question draw* has an answer matching `/^\(?no article\)?$|^-$/i` (case/apostrophe-normalized), an empty typed submission is accepted as a real answer choice on every `gap` question in that draw (not just the one it applies to), and the input shows a placeholder hint.
- `why` is shown after every answered question, correct or not.
- Mastery persistence: on the results screen, if the page was rendered for an authenticated user, sync `grammar_map[slug] = {best: max(prev.best, pct), done: prev.done || pct >= 80}` to `/auth/sync/` via GET-then-merge-then-POST (never POST a partial map — it fully replaces the top-level key). Guests get the full quiz experience with nothing persisted.
- Topic detail page: authenticated users see a status line ("Not started yet" / "Best score: N%" / "Mastered ✓"); guests see none.
- Browse grid: authenticated users see a small badge **only when there's progress to report** ("Best: N%" or "Mastered") — a never-attempted topic shows no badge at all, same as a guest sees it. This is the one place this feature does not show all three states.
- Results screen actions, matching production: **Try Again** (fresh random 10, restarts in place, no navigation), **Back to Lesson** (→ topic detail), **Back to Grammar** (→ browse). A **Leave** link during play (→ topic detail) has no confirmation dialog — nothing is persisted until results are reached.
- Unknown topic slug at the quiz route → standard Django 404 via `get_object_or_404`.
- No i18n work — question content renders exactly as stored (English).
- Any view whose page will grow a `fetch()`-based write must get `@ensure_csrf_cookie` in the same task that first renders that page, not deferred to whichever task adds the write.

---

### Task 1: Grammar topic quiz page — playable engine

**Files:**
- Modify: `config/urls.py`
- Modify: `config/views_grammar.py`
- Create: `templates/grammar/topic_quiz.html`
- Modify: `templates/grammar/topic_detail.html`
- Create: `static/js/grammar-quiz.js`
- Modify: `static/css/grammar.css`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Produces: `config.views_grammar.grammar_topic_quiz(request, slug)` — renders `grammar/topic_quiz.html`, context key `topic`.
- Produces: URL name `grammar_topic_quiz` at `/grammar/topic/<slug:slug>/quiz/`.
- Produces (JS globals inside the `grammar-quiz.js` IIFE, referenced by Task 2's diff instructions): `state` (object with `topic`, `questions`, `idx`, `score`), `topicSlug`, `PASS_PCT`, `renderResults()`.
- Consumes: `/api/grammar/` (existing endpoint) — response shape `[{id, name, cefr, topics: [{id, slug, title, ..., quiz: [{id, order, qtype, prompt, options, answers, why}, ...]}, ...]}, ...]`.

This task has a Python-testable server-rendered surface (Steps 1–4) and a client-side engine with no Python-testable surface (Steps 5–8, verified by hand in Step 9).

- [ ] **Step 1: Write the failing server-rendered tests**

Add to `tests/test_grammar_pages.py`:

```python
@pytest.mark.django_db
def test_grammar_topic_quiz_renders(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/quiz/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-topic-slug="present-simple-continuous"' in html


@pytest.mark.django_db
def test_grammar_topic_quiz_unknown_slug_404():
    c = Client()
    r = c.get('/grammar/topic/does-not-exist/quiz/')
    assert r.status_code == 404


@pytest.mark.django_db
def test_grammar_topic_detail_has_practice_link(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert 'href="/grammar/topic/present-simple-continuous/quiz/"' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k "topic_quiz or practice_link"
```

Expected: all 3 FAIL — `/grammar/topic/.../quiz/` doesn't resolve yet, and the Practice link doesn't exist yet.

- [ ] **Step 3: Add the view**

In `config/views_grammar.py`, add `ensure_csrf_cookie` to the imports and add the new view. Replace:

```python
from django.shortcuts import get_object_or_404, render

from vocab.models import GrammarTopic
```

with:

```python
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from vocab.models import GrammarTopic
```

Then add this function at the end of the file:

```python
@ensure_csrf_cookie
def grammar_topic_quiz(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    return render(request, 'grammar/topic_quiz.html', {'topic': topic})
```

(The `@ensure_csrf_cookie` decorator is added now, in this task, even though the mastery-sync `fetch()` POST that needs the cookie isn't added until Task 2 — this guarantees the cookie exists on first load of this page regardless of which page a user lands on first, matching this project's established convention.)

- [ ] **Step 4: Wire the URL and add the Practice link**

In `config/urls.py`, replace:

```python
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
```

with:

```python
from config.views_grammar import grammar_browse, grammar_topic_detail, grammar_topic_quiz

urlpatterns = [
    path('', home, name='home'),
    path('vocab/', vocab_browse, name='vocab_browse'),
    path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
    path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
    path('vocab/quiz/', vocab_quiz_setup, name='vocab_quiz_setup'),
    path('vocab/quiz/play/', vocab_quiz_play, name='vocab_quiz_play'),
    path('grammar/', grammar_browse, name='grammar_browse'),
    path('grammar/topic/<slug:slug>/', grammar_topic_detail, name='grammar_topic_detail'),
    path('grammar/topic/<slug:slug>/quiz/', grammar_topic_quiz, name='grammar_topic_quiz'),
```

In `templates/grammar/topic_detail.html`, replace:

```html
  <p class="grammar-topic-detail-blurb">{{ topic.blurb }}</p>
  {% for block in blocks %}
```

with:

```html
  <p class="grammar-topic-detail-blurb">{{ topic.blurb }}</p>
  <a class="btn grammar-topic-detail-practice" href="{% url 'grammar_topic_quiz' topic.slug %}">Practice this topic</a>
  {% for block in blocks %}
```

- [ ] **Step 5: Create the quiz page template**

Create `templates/grammar/topic_quiz.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Practice: {{ topic.title }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-topic-quiz">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_browse' %}">Grammar</a> /
    <a href="{% url 'grammar_topic_detail' topic.slug %}">{{ topic.title }}</a> / Practice
  </p>
  <div id="grammarQuizRoot" data-topic-slug="{{ topic.slug }}"></div>
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/grammar-quiz.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 6: Run the server-rendered tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k "topic_quiz or practice_link"
```

Expected: all 3 PASS.

- [ ] **Step 7: Write the quiz engine**

Create `static/js/grammar-quiz.js`:

```javascript
(function(){
  var root = document.getElementById("grammarQuizRoot");
  if (!root) return;

  var topicSlug = root.dataset.topicSlug;
  var DRAW_COUNT = 10;
  var PASS_PCT = 80;

  var state = {
    topic: null,
    questions: [],
    idx: 0,
    score: 0,
  };

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function grammarNorm(s){
    return String(s).replace(/[’‘]/g, "'").trim();
  }

  function expectedAnswers(q){
    if (q.qtype !== "gap" || q.prompt.indexOf("___") !== 0) return q.answers;
    return q.answers.map(function(a){
      return a.charAt(0).toUpperCase() + a.slice(1);
    });
  }

  function blankMeansNoAnswer(q){
    return q.qtype === "gap" && q.answers.some(function(a){
      return /^\(?no article\)?$|^-$/i.test(grammarNorm(a));
    });
  }

  function offersBlankGap(){
    return state.questions.some(function(qq){ return blankMeansNoAnswer(qq); });
  }

  function drawQuestions(topic){
    return shuffle(topic.quiz).slice(0, DRAW_COUNT);
  }

  function renderError(message){
    root.innerHTML = '<p class="grammar-quiz-error">' + message +
      ' <a href="/grammar/topic/' + topicSlug + '/">Back to topic</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    var isTyped = q.qtype !== "mcq";
    var promptLabel = q.qtype === "mcq" ? "Choose the correct option:"
      : q.qtype === "gap" ? "Fill in the blank:" : "Rewrite the sentence:";
    var gapPlaceholder = q.qtype === "gap" && offersBlankGap() ? "(leave blank if nothing goes here)" : "";
    root.innerHTML =
      '<a class="grammar-quiz-leave" href="/grammar/topic/' + topicSlug + '/">&larr; Leave</a>' +
      '<div class="grammar-quiz-progress"><div class="grammar-quiz-progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="grammar-quiz-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="grammar-quiz-card">' +
        '<div class="grammar-quiz-prompt">' + promptLabel + '</div>' +
        '<div class="grammar-quiz-text">' + q.prompt + '</div>' +
        (isTyped
          ? '<div class="grammar-quiz-typed-row">' +
              '<input type="text" class="grammar-quiz-input" id="grammarQuizInput" autocomplete="off" spellcheck="false" placeholder="' + gapPlaceholder + '">' +
              '<button type="button" class="btn" id="grammarQuizCheckBtn">Check</button>' +
            '</div>'
          : '<div class="grammar-quiz-options">' +
              q.options.map(function(opt, i){
                return '<button type="button" class="grammar-quiz-opt" data-i="' + i + '">' + opt + '</button>';
              }).join("") +
            '</div>') +
        '<div class="grammar-quiz-feedback"></div>' +
        '<div class="grammar-quiz-next" style="display:none;"><button type="button" class="btn" id="grammarQuizNextBtn"></button></div>' +
      '</div>';
    if (isTyped){
      var input = document.getElementById("grammarQuizInput");
      document.getElementById("grammarQuizCheckBtn").addEventListener("click", function(){ checkTyped(q, input); });
      input.addEventListener("keydown", function(e){ if (e.key === "Enter") checkTyped(q, input); });
      input.focus();
    } else {
      root.querySelectorAll(".grammar-quiz-opt").forEach(function(btn){
        btn.addEventListener("click", function(){ checkMcq(q, btn); });
      });
    }
  }

  function showFeedback(isCorrect, feedbackHtml){
    if (isCorrect) state.score++;
    root.querySelector(".grammar-quiz-feedback").innerHTML = feedbackHtml;
    root.querySelector(".grammar-quiz-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".grammar-quiz-next");
    var nextBtn = document.getElementById("grammarQuizNextBtn");
    var isLast = state.idx + 1 === state.questions.length;
    nextBtn.textContent = isLast ? "See Results" : "Next Question";
    nextWrap.style.display = "flex";
    nextBtn.addEventListener("click", function(){
      state.idx++;
      if (state.idx < state.questions.length) renderQuestion();
      else renderResults();
    });
  }

  function checkMcq(q, selectedBtn){
    var correctIdx = q.answers[0];
    var selectedIdx = Number(selectedBtn.dataset.i);
    var isCorrect = selectedIdx === correctIdx;
    root.querySelectorAll(".grammar-quiz-opt").forEach(function(btn){
      btn.disabled = true;
      if (Number(btn.dataset.i) === correctIdx) btn.classList.add("correct");
      else if (btn === selectedBtn) btn.classList.add("wrong");
    });
    var feedback = "<b>" + (isCorrect ? "Correct!" : "Not quite.") + "</b> " + q.why;
    showFeedback(isCorrect, feedback);
  }

  function checkTyped(q, input){
    if (input.disabled) return;
    var typed = grammarNorm(input.value);
    var acceptsBlank = blankMeansNoAnswer(q);
    var blankIsAnswerChoice = q.qtype === "gap" && offersBlankGap();
    if (!typed && !acceptsBlank && !blankIsAnswerChoice){
      root.querySelector(".grammar-quiz-feedback").innerHTML = "Type an answer first, or check the hint if the blank can be left empty.";
      return;
    }
    var expected = expectedAnswers(q);
    var isCorrect = typed ? expected.some(function(a){ return grammarNorm(a) === typed; }) : acceptsBlank;
    input.disabled = true;
    document.getElementById("grammarQuizCheckBtn").disabled = true;
    input.classList.add(isCorrect ? "correct" : "wrong");
    var feedback = isCorrect
      ? "<b>Correct!</b> " + q.why
      : "<b>Not quite.</b> The answer is \"" + expected[0] + "\". " + q.why;
    showFeedback(isCorrect, feedback);
  }

  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    var masteredMsg = pct >= PASS_PCT
      ? "You've mastered this topic!"
      : "Score " + PASS_PCT + "%+ to master this topic.";
    root.innerHTML =
      '<div class="grammar-quiz-results">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="grammar-quiz-score">' + state.score + ' / ' + total + '</div>' +
        '<p class="grammar-quiz-pct">' + pct + '%</p>' +
        '<p class="grammar-quiz-mastered-msg">' + masteredMsg + '</p>' +
        '<div class="grammar-quiz-result-actions">' +
          '<button type="button" class="btn" id="grammarQuizRetryBtn">Try Again</button>' +
          '<a class="btn" href="/grammar/topic/' + topicSlug + '/">Back to Lesson</a>' +
          '<a class="btn" href="/grammar/">Back to Grammar</a>' +
        '</div>' +
      '</div>';
    document.getElementById("grammarQuizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.questions = drawQuestions(state.topic);
      renderQuestion();
    });
  }

  function init(){
    fetch("/api/grammar/").then(function(r){ return r.json(); }).then(function(stages){
      var found = null;
      stages.forEach(function(stage){
        stage.topics.forEach(function(t){
          if (t.slug === topicSlug) found = t;
        });
      });
      if (!found || !found.quiz || !found.quiz.length){
        renderError("This topic doesn't have any quiz questions yet.");
        return;
      }
      state.topic = found;
      state.questions = drawQuestions(found);
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  init();
})();
```

- [ ] **Step 8: Add the quiz engine CSS**

Append to `static/css/grammar.css`:

```css
.grammar-topic-detail-practice{ display: inline-block; margin-bottom: 24px; }

.grammar-quiz-leave{
  display: inline-block;
  margin-bottom: 16px;
  color: var(--muted);
  text-decoration: none;
  font-size: 0.9rem;
}
.grammar-quiz-progress{
  height: 6px;
  border-radius: 999px;
  background: var(--border);
  overflow: hidden;
  margin-bottom: 12px;
}
.grammar-quiz-progress-fill{
  height: 100%;
  background: rgb(var(--violet));
}
.grammar-quiz-meta{
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 0.85rem;
  margin-bottom: 16px;
}
.grammar-quiz-card{
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  background: var(--card-bg);
}
.grammar-quiz-prompt{ font-weight: 700; margin-bottom: 8px; }
.grammar-quiz-text{ font-size: 1.15rem; margin-bottom: 20px; }
.grammar-quiz-options{ display: grid; gap: 10px; }
.grammar-quiz-opt{
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  text-align: left;
  font-size: 0.95rem;
  cursor: pointer;
}
.grammar-quiz-opt.correct{ border-color: #22c55e; background: rgba(34,197,94,0.12); }
.grammar-quiz-opt.wrong{ border-color: #dc2626; background: rgba(220,38,38,0.12); }
.grammar-quiz-typed-row{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.grammar-quiz-input{
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--text);
  font-size: 0.95rem;
  flex: 1;
  min-width: 200px;
}
.grammar-quiz-input.correct{ border-color: #22c55e; }
.grammar-quiz-input.wrong{ border-color: #dc2626; }
.grammar-quiz-feedback{ margin-top: 16px; color: var(--muted); }
.grammar-quiz-next{ margin-top: 20px; }
.grammar-quiz-error{ color: var(--muted); padding: 40px 0; }
.grammar-quiz-results{ text-align: center; padding: 40px 0; }
.grammar-quiz-score{ font-size: 3rem; font-weight: 800; color: rgb(var(--violet)); }
.grammar-quiz-pct{ color: var(--muted); margin-bottom: 8px; }
.grammar-quiz-mastered-msg{ margin-bottom: 24px; }
.grammar-quiz-result-actions{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
```

- [ ] **Step 9: Run `node --check` and the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/grammar-quiz.js
python -m pytest -v
```

Expected: `node --check` prints nothing (syntax OK). All Python tests PASS, including the 3 new ones.

- [ ] **Step 10: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

The dev DB already has the full production dataset (47 topics × 300 questions each — confirmed via `GrammarTopic.objects.count()` / `GrammarQuestion.objects.count()`), so real content is available for every check below.

Navigate to `/grammar/topic/present-simple-continuous/`. Confirm a "Practice this topic" button/link is present and goes to `/grammar/topic/present-simple-continuous/quiz/`. On the quiz page, confirm: a progress bar and "Question 1 of 10" appear, a question renders (you'll see a mix of MCQ option-buttons and typed gap/transform inputs across the run — this topic's bank includes real examples like the MCQ prompt *"Water ___ at 100°C at sea level."* with options `boils/boil/is boiling/boiled`, and the transform prompt starting *"Rewrite in the present continuous..."* whose expected answer is `"The population is increasing every year."`). For an MCQ question, click an option — confirm correct turns green, a wrong pick turns red, `why` text appears, and a Next/See Results button appears. For a typed question, type the answer **exactly** as printed above (case and punctuation matching) — confirm it's marked correct; then reload and deliberately type it in the wrong case (e.g. lowercase when the real answer is capitalized, or vice versa) to confirm the strict comparison marks it wrong, proving leniency was NOT added. Click through all 10 questions, confirming score increments only on correct answers and the progress bar advances. On the last question, confirm the button reads "See Results" and clicking it shows the results screen: score, percentage, a mastered/not-mastered message, and 3 actions. Click **Try Again** — confirm a fresh question renders in place (no page navigation, no confirm dialog) with score reset to 0. Complete it again and click **Back to Lesson** — confirm it navigates to the topic detail page. Go back to the quiz, mid-question click the **Leave** link — confirm it navigates to the topic detail page with no confirmation prompt. Separately, visit `/grammar/topic/does-not-exist/quiz/` and confirm a 404 page.

Note: two data-driven edge cases (the sentence-start capitalization rule, and the "leave blank" no-answer rule) exist in this codebase's real seed data — e.g. topic `articles` has a gap question whose accepted answers include `"(no article)"`/`"no article"`/`"-"` — but hitting the exact question that exercises either rule depends on this run's random 10-question draw, so they can't be reliably forced through normal clicking. Treat these as verified by inspection against production's `grammarExpectedAnswers`/`grammarBlankMeansNoAnswer`/`grammarQuizOffersBlankGap` (which this task's `expectedAnswers`/`blankMeansNoAnswer`/`offersBlankGap` port line-for-line), not by live observation. If you want a live check anyway, retry the quiz a few times on the `articles` topic specifically (`/grammar/topic/articles/quiz/`) until a "no article"-type question is drawn, then confirm submitting an empty answer is graded correct and the input shows the "(leave blank if nothing goes here)" placeholder hint.

Stop the server (Ctrl+C) when done.

- [ ] **Step 11: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/urls.py" "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/topic_quiz.html" "VocabLarry Professional Environment/templates/grammar/topic_detail.html" "VocabLarry Professional Environment/static/js/grammar-quiz.js" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add playable per-topic grammar quiz

grammar_topic_quiz renders a near-empty page; static/js/grammar-quiz.js
fetches the existing /api/grammar/ endpoint client-side and does all
question sampling/rendering/scoring, faithfully porting production's
strict typed-answer comparison (grammarNorm), the sentence-start
capitalization rule, and the "leave blank" no-answer rule. No mastery
persistence yet — this task is fully playable but ephemeral, matching
this sub-project's task split (engine first, persistence next). Topic
detail page gains a "Practice this topic" link. @ensure_csrf_cookie
added now so the cookie is guaranteed present before Task 2's sync POST
needs it.
EOF
)"
```

---

### Task 2: Mastery persistence and status display

**Files:**
- Modify: `config/views_grammar.py`
- Modify: `templates/grammar/topic_quiz.html`
- Modify: `templates/grammar/topic_detail.html`
- Modify: `templates/grammar/browse.html`
- Modify: `static/js/grammar-quiz.js`
- Modify: `static/css/grammar.css`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: `state`, `topicSlug`, `PASS_PCT`, `renderResults()` from Task 1 — all unchanged in signature, `renderResults()`'s body is extended.
- Consumes: `GrammarTopic` (unchanged), `request.user.grammar_map` (existing `CustomUser` field), `/auth/sync/` (existing endpoint, GET returns `{learn_map, grammar_map}`, POST accepts `{grammar_map: {...}}` without touching `learn_map`).
- Produces: no new interfaces — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_grammar_pages.py`:

```python
@pytest.mark.django_db
def test_grammar_topic_quiz_authenticated_flag_set(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/topic/present-simple-continuous/quiz/')
    assert 'data-authenticated="1"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_quiz_authenticated_flag_unset_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/quiz/')
    assert 'data-authenticated="0"' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_status_not_started_for_authenticated_user(topic_with_blocks, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert 'Not started yet' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_status_shows_best_score(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 60, 'done': False}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert 'Best score: 60%' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_status_shows_mastered(topic_with_blocks, regular_user):
    regular_user.grammar_map = {'present-simple-continuous': {'best': 90, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/topic/present-simple-continuous/')
    assert 'Mastered' in r.content.decode()


@pytest.mark.django_db
def test_grammar_topic_detail_no_status_for_guest(topic_with_blocks):
    c = Client()
    r = c.get('/grammar/topic/present-simple-continuous/')
    html = r.content.decode()
    assert 'Not started yet' not in html
    assert 'grammar-topic-detail-status' not in html


@pytest.mark.django_db
def test_grammar_browse_badge_shows_mastered(topic_articles, regular_user):
    regular_user.grammar_map = {'articles': {'best': 95, 'done': True}}
    regular_user.save(update_fields=['grammar_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/')
    assert 'grammar-topic-badge-mastered' in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_no_badge_for_untouched_topic(topic_articles, regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/grammar/')
    assert 'grammar-topic-badge' not in r.content.decode()


@pytest.mark.django_db
def test_grammar_browse_no_badge_for_guest(topic_articles):
    c = Client()
    r = c.get('/grammar/')
    assert 'grammar-topic-badge' not in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k "authenticated_flag or status or badge"
```

Expected: all 8 FAIL — none of this context/markup exists yet.

- [ ] **Step 3: Pass grammar status into the views**

In `config/views_grammar.py`, replace:

```python
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
```

with:

```python
def grammar_browse(request):
    query = request.GET.get('q', '').strip()
    stage_filter = request.GET.get('stage', '').strip()
    topics = GrammarTopic.objects.order_by('order')
    if query:
        topics = topics.filter(title__icontains=query)
    if stage_filter:
        topics = topics.filter(stage=stage_filter)
    topics = list(topics)
    grammar_map = request.user.grammar_map if request.user.is_authenticated else {}
    for topic in topics:
        topic.grammar_status = grammar_map.get(topic.slug)
    return render(request, 'grammar/browse.html', {
        'topics': topics,
        'stages': GrammarTopic.STAGES,
        'query': query,
        'stage_filter': stage_filter,
    })
```

Then, still in the same file, replace:

```python
def grammar_topic_detail(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    blocks = topic.blocks.order_by('order')
    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'blocks': blocks,
    })
```

with:

```python
def grammar_topic_detail(request, slug):
    topic = get_object_or_404(GrammarTopic, slug=slug)
    blocks = topic.blocks.order_by('order')
    grammar_status = None
    if request.user.is_authenticated:
        grammar_status = request.user.grammar_map.get(topic.slug)
    return render(request, 'grammar/topic_detail.html', {
        'topic': topic,
        'blocks': blocks,
        'grammar_status': grammar_status,
    })
```

- [ ] **Step 4: Add the status line and the authenticated flag to templates**

In `templates/grammar/topic_detail.html`, replace:

```html
  <p class="grammar-topic-detail-blurb">{{ topic.blurb }}</p>
  <a class="btn grammar-topic-detail-practice" href="{% url 'grammar_topic_quiz' topic.slug %}">Practice this topic</a>
```

with:

```html
  <p class="grammar-topic-detail-blurb">{{ topic.blurb }}</p>
  {% if grammar_status.done %}
    <p class="grammar-topic-detail-status grammar-topic-detail-status-mastered">Mastered ✓</p>
  {% elif grammar_status %}
    <p class="grammar-topic-detail-status">Best score: {{ grammar_status.best }}%</p>
  {% elif user.is_authenticated %}
    <p class="grammar-topic-detail-status grammar-topic-detail-status-new">Not started yet</p>
  {% endif %}
  <a class="btn grammar-topic-detail-practice" href="{% url 'grammar_topic_quiz' topic.slug %}">Practice this topic</a>
```

In `templates/grammar/browse.html`, replace:

```html
    <a class="grammar-topic-card" href="{% url 'grammar_topic_detail' topic.slug %}">
      <span class="grammar-topic-tag">{{ topic.tag }}</span>
      <span class="grammar-topic-title">{{ topic.title }}</span>
      <span class="grammar-topic-cefr">{{ topic.cefr_label }}</span>
      <span class="grammar-topic-blurb">{{ topic.blurb }}</span>
    </a>
```

with:

```html
    <a class="grammar-topic-card" href="{% url 'grammar_topic_detail' topic.slug %}">
      <span class="grammar-topic-tag">{{ topic.tag }}</span>
      {% if topic.grammar_status.done %}
        <span class="grammar-topic-badge grammar-topic-badge-mastered">Mastered</span>
      {% elif topic.grammar_status %}
        <span class="grammar-topic-badge">Best: {{ topic.grammar_status.best }}%</span>
      {% endif %}
      <span class="grammar-topic-title">{{ topic.title }}</span>
      <span class="grammar-topic-cefr">{{ topic.cefr_label }}</span>
      <span class="grammar-topic-blurb">{{ topic.blurb }}</span>
    </a>
```

In `templates/grammar/topic_quiz.html`, replace:

```html
  <div id="grammarQuizRoot" data-topic-slug="{{ topic.slug }}"></div>
```

with:

```html
  <div id="grammarQuizRoot" data-topic-slug="{{ topic.slug }}" data-authenticated="{{ user.is_authenticated|yesno:'1,0' }}"></div>
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v
```

Expected: every test in the file PASSES (Task 1's 3 plus this task's 8, plus every test carried over from Grammar Browse + Topic).

- [ ] **Step 6: Add the mastery sync to the quiz engine**

In `static/js/grammar-quiz.js`, replace:

```javascript
  function drawQuestions(topic){
    return shuffle(topic.quiz).slice(0, DRAW_COUNT);
  }
```

with:

```javascript
  function drawQuestions(topic){
    return shuffle(topic.quiz).slice(0, DRAW_COUNT);
  }

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function syncMastery(pct){
    fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){ return res.json(); })
      .then(function(data){
        var grammarMap = data.grammar_map || {};
        var prev = grammarMap[topicSlug] || { best: 0, done: false };
        var best = Math.max(prev.best, pct);
        grammarMap[topicSlug] = { best: best, done: prev.done || best >= PASS_PCT };
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ grammar_map: grammarMap }),
        });
      })
      .catch(function(){
        // Best-effort: the results screen is already rendered and fully
        // usable regardless of whether the sync round-trip succeeds.
      });
  }
```

Then, still in the same file, replace:

```javascript
  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    var masteredMsg = pct >= PASS_PCT
      ? "You've mastered this topic!"
      : "Score " + PASS_PCT + "%+ to master this topic.";
```

with:

```javascript
  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    if (root.dataset.authenticated === "1") syncMastery(pct);
    var masteredMsg = pct >= PASS_PCT
      ? "You've mastered this topic!"
      : "Score " + PASS_PCT + "%+ to master this topic.";
```

- [ ] **Step 7: Add the badge and status-line CSS**

Append to `static/css/grammar.css`:

```css
.grammar-topic-badge{
  align-self: flex-start;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(34,197,94,0.12);
  color: #16a34a;
}
.grammar-topic-badge-mastered{ background: rgba(234,179,8,0.15); color: #b45309; }

.grammar-topic-detail-status{ font-weight: 600; margin-bottom: 16px; }
.grammar-topic-detail-status-mastered{ color: #b45309; }
.grammar-topic-detail-status-new{ color: var(--muted); font-weight: 400; }
```

- [ ] **Step 8: Run `node --check` and the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/grammar-quiz.js
python -m pytest -v
```

Expected: `node --check` prints nothing. Every test PASSES.

- [ ] **Step 9: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Sign up or log in as a test account (or use Django admin to check/set state afterward). While logged in, visit `/grammar/topic/present-simple-continuous/` — confirm the status line reads "Not started yet". Click Practice, complete the 10-question run scoring **below 80%** on purpose (answer some wrong), reach the results screen. Navigate back to the topic detail page — confirm the status line now reads "Best score: N%" matching what the results screen showed. Return to `/grammar/` — confirm this topic's card now shows a "Best: N%" badge, and confirm a topic you haven't touched yet shows no badge at all. Take the quiz again on the same topic, this time scoring **80% or above** on purpose (answer all or nearly all correctly) — confirm the results screen shows the mastered message, the topic detail status line now reads "Mastered ✓", and the browse card's badge switches to "Mastered". Take the quiz a third time and score lower than your previous best — confirm the status still shows the earlier (higher) best score/Mastered state, not the lower one (proving `best = max(prev, pct)` and `done` staying sticky once true). Log out and repeat a single quiz run as a guest — confirm the quiz fully works (plays, scores, shows results) but no status line appears on the topic page and no badge appears on the browse grid. Stop the server (Ctrl+C) when done.

- [ ] **Step 10: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/topic_quiz.html" "VocabLarry Professional Environment/templates/grammar/topic_detail.html" "VocabLarry Professional Environment/templates/grammar/browse.html" "VocabLarry Professional Environment/static/js/grammar-quiz.js" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): persist grammar quiz mastery and show status

On the results screen, an authenticated user's grammar_map[slug] is
synced via the existing /auth/sync/ endpoint using the same
GET-then-merge-then-POST pattern vocab-word.js already established for
learn_map (best = max(prev, pct), done sticky once true). Topic detail
shows a status line (Not started/Best score/Mastered) for logged-in
users; the browse grid shows a badge only when there's progress to
report (Mastered/Best:N%) — a never-attempted topic shows no badge,
avoiding 40+ repeated "Not started" badges on the grid. Guests get the
full quiz experience with nothing persisted and no status UI.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** client-side engine fetching `/api/grammar/`, no new backend (Task 1 Steps 3–7); no setup step, Practice link launches directly (Task 1 Step 4); strict typed comparison + both data-driven edge cases (Task 1 Step 7, `grammarNorm`/`expectedAnswers`/`blankMeansNoAnswer`/`offersBlankGap`); `why` always shown (Task 1 Step 7, `checkMcq`/`checkTyped`); mastery persistence via GET-then-merge-then-POST (Task 2 Step 6); topic detail status line, 3 states (Task 2 Step 4); browse badge, progress-only (Task 2 Step 4, confirmed by Step 1's `test_grammar_browse_no_badge_for_untouched_topic`); results screen 3 actions + Leave link (Task 1 Step 7); 404 on unknown slug (Task 1 Step 3, `get_object_or_404`); `@ensure_csrf_cookie` added in the same task that first renders the page, not deferred (Task 1 Step 3).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code; both manual-verification steps name concrete real seed-data question examples (verified live against the actual dev DB) rather than generic instructions.
- **Type consistency:** `grammar_topic_quiz(request, slug)`'s signature is introduced once in Task 1 and never changed. `state`/`topicSlug`/`PASS_PCT`/`renderResults()` names Task 2 depends on match Task 1's actual code exactly (checked by re-reading Task 1 Step 7 line-by-line against Task 2 Steps 4 and 6). `grammar_status` (a dict or `None`) is used identically in both the view (Task 2 Step 3) and template (Task 2 Step 4) — `.done`/`.best` keys match `grammar_map`'s existing stored shape from `accounts/views.py`'s `sync` endpoint. `topic.grammar_status` (browse) and `grammar_status` (topic detail, a separate unprefixed context variable) are intentionally different names for different views — not a typo, each view computes its own independently.
