# VocabLarry Professional Environment — Grammar Test Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cross-topic Grammar Test to VocabLarry Professional Environment — a practice run drawing questions from many topics at once, filtered by level and question type, entirely separate from mastery tracking.

**Architecture:** `static/js/grammar-quiz.js` (built in the Grammar Topic Quiz sub-project) gains a mode flag distinguishing `"topic"` from `"test"`. All existing rendering/grading functions are reused unchanged; only question sourcing (`state.pool`/`state.drawCount` instead of a single topic's bank) and a few mode-branched links/actions are new. A new setup page mirrors `vocab_quiz_setup`'s exact GET-form → query-string-driven-play pattern.

**Tech Stack:** Django function views (no new models/migrations/endpoints), Django templates, extending the existing vanilla-JS quiz engine, pytest + pytest-django for the server-rendered surface, Playwright for the client-side engine extension (no automated coverage possible for it).

## Global Constraints

- No new models, no new migrations, no new backend endpoints. `/api/grammar/` (existing) already returns every topic's full question bank nested; this feature pools them client-side.
- Topic filtering is **stage only** (`GrammarTopic.STAGES` — `beginner`/`independent`/`expert`), not individual topics. No multi-select topic picker in this pass.
- Mode/count fields are plain `<select>` dropdowns, matching `vocab_quiz_setup.html`'s exact shape — not card UI. Mode values: `mixed` (default)/`mcq`/`gap`/`transform`. Count values: `10`/`20`/`30`/`all` — identical set to Vocab Quiz's own count field, no custom-number input.
- New flat nav entry "Grammar Test", alongside the existing "Grammar" entry — not a dropdown, matching the `Vocabulary`/`Quiz` precedent already in this codebase.
- Setup → play via a GET-submitted form and query-string params (`?stage=&qtype=&count=`), read client-side via `URLSearchParams` — same mechanism `vocab-quiz.js` already uses, not a data attribute.
- **This mode is practice-only and must NEVER touch mastery.** No call to `syncMastery`, no read or write of `grammar_map`, regardless of auth state, under any code path added in this plan.
- No `@ensure_csrf_cookie` needed on the play view — test mode makes no `fetch()` writes at all.
- Results actions in test mode: Try Again (fresh draw, same settings, in place, no navigation), Change Settings (→ `/grammar/test/`), Back to Grammar (→ `/grammar/`). No "Back to Lesson" (no single topic).
- Empty-pool (a stage+qtype combination with zero questions) → the same plain error message pattern `vocab-quiz.js`'s `renderError` already uses.
- No i18n content translation; the new nav entry gets a `data-i18n` key + en/vi dict entries, matching sibling nav items.

---

### Task 1: Grammar Test play page — engine extension

**Files:**
- Create: `templates/grammar/test_play.html`
- Modify: `config/views_grammar.py`
- Modify: `config/urls.py`
- Modify: `static/js/grammar-quiz.js`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Produces: `config.views_grammar.grammar_test_play(request)` — renders `grammar/test_play.html`, no context needed.
- Produces: URL name `grammar_test_play` at `/grammar/test/play/`.
- Produces (for Task 2 to link to): the URL name `grammar_test_play` itself — Task 2's setup form submits to it.
- Consumes: `/api/grammar/` (existing endpoint, response shape `[{id, name, cefr, topics: [{slug, title, ..., quiz: [{qtype, prompt, options, answers, why}, ...]}, ...]}, ...]`), where each top-level `id` is one of `beginner`/`independent`/`expert` — confirmed to match `GrammarTopic.STAGES`' own values exactly.

This task's play page has no setup page to link from yet — verify by navigating directly to `/grammar/test/play/` with hand-typed query strings (Task 2 adds the setup form that does this for real users).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_grammar_pages.py`:

```python
@pytest.mark.django_db
def test_grammar_test_play_renders():
    c = Client()
    r = c.get('/grammar/test/play/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'grammarQuizRoot' in html
    assert 'data-mode="test"' in html
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k test_play
```

Expected: FAIL — `/grammar/test/play/` doesn't resolve yet.

- [ ] **Step 3: Add the view**

In `config/views_grammar.py`, add this function at the end of the file:

```python
def grammar_test_play(request):
    return render(request, 'grammar/test_play.html')
```

- [ ] **Step 4: Wire the URL**

In `config/urls.py`, replace:

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

with:

```python
from config.views_grammar import (
    grammar_browse, grammar_topic_detail, grammar_topic_quiz, grammar_test_play,
)

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
    path('grammar/test/play/', grammar_test_play, name='grammar_test_play'),
```

- [ ] **Step 5: Create the play page template**

Create `templates/grammar/test_play.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Grammar Test — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-test-play">
  <p class="grammar-breadcrumb">
    <a href="{% url 'grammar_browse' %}">Grammar</a> / Test
  </p>
  <div id="grammarQuizRoot" data-mode="test"></div>
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/grammar-quiz.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 6: Run the test to verify it passes**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k test_play
```

Expected: PASS.

- [ ] **Step 7: Extend the quiz engine with a mode flag**

Replace the entire contents of `static/js/grammar-quiz.js` with:

```javascript
(function(){
  var root = document.getElementById("grammarQuizRoot");
  if (!root) return;

  var topicSlug = root.dataset.topicSlug || null;
  var testMode = root.dataset.mode === "test";
  var DRAW_COUNT = 10;
  var PASS_PCT = 80;

  var state = {
    mode: testMode ? "test" : "topic",
    topic: null,
    pool: [],
    drawCount: DRAW_COUNT,
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

  function drawQuestions(){
    return shuffle(state.pool).slice(0, state.drawCount);
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
        var learnMap = data.learn_map || {};
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
          body: JSON.stringify({ grammar_map: grammarMap, learn_map: learnMap }),
        });
      })
      .catch(function(){
        // Best-effort: the results screen is already rendered and fully
        // usable regardless of whether the sync round-trip succeeds.
      });
  }

  function backHref(){
    return state.mode === "test" ? "/grammar/test/" : ("/grammar/topic/" + topicSlug + "/");
  }

  function renderError(message){
    var label = state.mode === "test" ? "Back to Test setup" : "Back to topic";
    root.innerHTML = '<p class="grammar-quiz-error">' + message +
      ' <a href="' + backHref() + '">' + label + '</a></p>';
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
      '<a class="grammar-quiz-leave" href="' + backHref() + '">&larr; Leave</a>' +
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
    if (state.mode === "topic" && root.dataset.authenticated === "1") syncMastery(pct);
    var masteredMsg = state.mode === "topic"
      ? (pct >= PASS_PCT ? "You've mastered this topic!" : "Score " + PASS_PCT + "%+ to master this topic.")
      : "";
    var secondaryAction = state.mode === "topic"
      ? '<a class="btn" href="/grammar/topic/' + topicSlug + '/">Back to Lesson</a>'
      : '<a class="btn" href="/grammar/test/">Change Settings</a>';
    root.innerHTML =
      '<div class="grammar-quiz-results">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="grammar-quiz-score">' + state.score + ' / ' + total + '</div>' +
        '<p class="grammar-quiz-pct">' + pct + '%</p>' +
        (masteredMsg ? '<p class="grammar-quiz-mastered-msg">' + masteredMsg + '</p>' : '') +
        '<div class="grammar-quiz-result-actions">' +
          '<button type="button" class="btn" id="grammarQuizRetryBtn">Try Again</button>' +
          secondaryAction +
          '<a class="btn" href="/grammar/">Back to Grammar</a>' +
        '</div>' +
      '</div>';
    document.getElementById("grammarQuizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.questions = drawQuestions();
      renderQuestion();
    });
  }

  function initTopicMode(){
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
      state.pool = found.quiz;
      state.drawCount = DRAW_COUNT;
      state.questions = drawQuestions();
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  function initTestMode(){
    var params = new URLSearchParams(window.location.search);
    var stageFilter = params.get("stage") || "";
    var qtypeFilter = params.get("qtype") || "mixed";
    var countParam = params.get("count") || "10";
    fetch("/api/grammar/").then(function(r){ return r.json(); }).then(function(stages){
      var pool = [];
      stages.forEach(function(stage){
        if (stageFilter && stage.id !== stageFilter) return;
        stage.topics.forEach(function(topic){
          topic.quiz.forEach(function(q){
            if (qtypeFilter !== "mixed" && q.qtype !== qtypeFilter) return;
            pool.push(q);
          });
        });
      });
      if (!pool.length){
        renderError("No questions match this combination — try different settings.");
        return;
      }
      state.pool = pool;
      state.drawCount = countParam === "all" ? pool.length : Math.min(parseInt(countParam, 10) || 10, pool.length);
      state.questions = drawQuestions();
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  function init(){
    if (testMode) initTestMode(); else initTopicMode();
  }

  init();
})();
```

This is a full-file replacement of the version shipped in the Grammar Topic Quiz sub-project. Every existing function (`shuffle`, `grammarNorm`, `expectedAnswers`, `blankMeansNoAnswer`, `offersBlankGap`, `syncMastery`, `checkMcq`, `checkTyped`, `showFeedback`) is byte-identical to before. What changed: `topicSlug` now falls back to `null`; `drawQuestions()` no longer takes a `topic` argument and reads `state.pool`/`state.drawCount` instead; `renderError`/`renderQuestion`'s Leave link/`renderResults`'s secondary action all route through the new `state.mode`/`backHref()` logic; `init()` now dispatches to `initTopicMode()` (the prior `init()` body, unchanged logic, setting `state.pool`/`state.drawCount` before drawing) or the new `initTestMode()`.

- [ ] **Step 8: Run `node --check` and the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/grammar-quiz.js
python -m pytest -v
```

Expected: `node --check` prints nothing. All tests PASS, including the 1 new one, with no regressions to any existing Grammar Topic Quiz test (the topic-mode code path must behave identically to before this refactor).

- [ ] **Step 9: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

The dev DB has 47 topics: 15 `beginner`-stage (including `articles` and `present-simple-continuous`), 18 `independent`-stage, 14 `expert`-stage (including `inversion-emphasis`, `cleft-sentences`, `subjunctive-unreal-past`) — each topic with exactly 100 mcq/100 gap/100 transform questions. Since there's no setup form yet, type these URLs directly into the address bar:

1. **Regression check (topic mode unaffected):** visit `/grammar/topic/present-simple-continuous/quiz/` — confirm it plays exactly as it did before this refactor (10-question draw, MCQ/typed mix, Leave goes to the topic page, results show "Back to Lesson"/"Back to Grammar", and if you're logged in, mastery still syncs — this is the regression check that the topic-mode code path is unaffected by the generalization).
2. **Test mode, defaults:** visit `/grammar/test/play/` (no query params) — confirm it does NOT error, renders 10 questions, and — since `qtype` defaults to `mixed` — you should see both MCQ (button) and typed (input) question styles across the run (not all one type).
3. **Test mode, MCQ only:** visit `/grammar/test/play/?qtype=mcq&count=10` — click through all 10, confirm every single one is a click-to-answer MCQ question, never a typed input.
4. **Test mode, transform only, stage filter:** visit `/grammar/test/play/?stage=expert&qtype=transform&count=10` — confirm every question is a typed "Rewrite the sentence" prompt (transform), and spot-check that the content reads like advanced-level material (this stage includes `inversion-emphasis`/`cleft-sentences`/`subjunctive-unreal-past` topics).
5. **Count clamping:** visit `/grammar/test/play/?stage=beginner&qtype=gap&count=500` — the beginner stage has 15 topics × 100 gap questions = 1500 available, so 500 should actually draw 500 real questions (not error, not silently cap at some smaller default) — you don't need to click through 500 of them, just confirm the "Question 1 of 500" counter appears correctly, then use the Leave link.
6. **Leave / results actions:** start any test run, click **Leave** mid-question — confirm it navigates to `/grammar/test/` (this will 404 right now since Task 2 hasn't built the setup page yet — that's expected and fine, it proves the link target is correct; Task 2 makes it a real page). Start another run and complete it fully — confirm the results screen shows NO "Mastered" messaging of any kind (this is test mode, not topic mode) and its secondary action button says **Change Settings** (also pointing at `/grammar/test/`, same expected-404-for-now situation) rather than "Back to Lesson". Confirm **Try Again** redraws a fresh set in place without navigating away.
7. **No mastery writes:** while logged in, note your account's current `grammar_map` via `GET /auth/sync/` (open it directly in a second browser tab, or use Django shell: `python manage.py shell -c "from django.contrib.auth import get_user_model; u = get_user_model().objects.get(username='<your username>'); print(u.grammar_map)"`). Complete a full test-mode run scoring well above 80%. Re-check `grammar_map` the same way — confirm it is **byte-for-byte unchanged**, proving no mastery write occurred (contrast this with Grammar Topic Quiz's own manual check, which proved the opposite for topic mode).

Stop the server (Ctrl+C) when done.

- [ ] **Step 10: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/urls.py" "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/test_play.html" "VocabLarry Professional Environment/static/js/grammar-quiz.js" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add cross-topic grammar test play page

grammar-quiz.js gains a mode flag distinguishing topic-scoped quizzes
from cross-topic test runs, generalizing question sourcing to a
state.pool/state.drawCount pair instead of a single topic's bank.
Every existing rendering/grading function is reused unchanged; only
the Leave link and results' secondary action are mode-aware, and
mastery sync never fires in test mode. No setup page yet — this task
is reachable only by hand-typed query strings until the next task
adds the setup form.
EOF
)"
```

---

### Task 2: Grammar Test setup page and nav entry

**Files:**
- Create: `templates/grammar/test_setup.html`
- Modify: `config/views_grammar.py`
- Modify: `config/urls.py`
- Modify: `templates/partials/nav.html`
- Modify: `static/js/i18n.js`
- Modify: `static/css/grammar.css`
- Test: `tests/test_grammar_pages.py`

**Interfaces:**
- Consumes: URL name `grammar_test_play` (Task 1) — this task's setup form submits `GET` to it.
- Consumes: `GrammarTopic.STAGES` (unchanged model attribute, already used by `grammar_browse`).
- Produces: no new interfaces — this is the last task in this sub-project.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_grammar_pages.py`:

```python
@pytest.mark.django_db
def test_grammar_test_setup_renders():
    c = Client()
    r = c.get('/grammar/test/')
    assert r.status_code == 200
    html = r.content.decode()
    assert 'name="stage"' in html
    assert 'name="qtype"' in html
    assert 'name="count"' in html
    assert 'action="/grammar/test/play/"' in html


@pytest.mark.django_db
def test_grammar_test_setup_stage_options_match_model():
    c = Client()
    r = c.get('/grammar/test/')
    html = r.content.decode()
    assert '<option value="beginner">Basic</option>' in html
    assert '<option value="independent">Intermediate</option>' in html
    assert '<option value="expert">Advanced</option>' in html


@pytest.mark.django_db
def test_nav_grammar_test_link_present():
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/grammar/test/"' in html
    assert 'nav.grammarTest">Grammar Test</a>' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_grammar_pages.py -v -k "test_setup or grammar_test_link"
```

Expected: all 3 FAIL — `/grammar/test/` doesn't resolve yet, and the nav link doesn't exist yet.

- [ ] **Step 3: Add the view**

In `config/views_grammar.py`, add this function at the end of the file:

```python
def grammar_test_setup(request):
    return render(request, 'grammar/test_setup.html', {'stages': GrammarTopic.STAGES})
```

- [ ] **Step 4: Wire the URL**

In `config/urls.py`, replace:

```python
from config.views_grammar import (
    grammar_browse, grammar_topic_detail, grammar_topic_quiz, grammar_test_play,
)

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
    path('grammar/test/play/', grammar_test_play, name='grammar_test_play'),
```

with:

```python
from config.views_grammar import (
    grammar_browse, grammar_topic_detail, grammar_topic_quiz,
    grammar_test_setup, grammar_test_play,
)

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
    path('grammar/test/', grammar_test_setup, name='grammar_test_setup'),
    path('grammar/test/play/', grammar_test_play, name='grammar_test_play'),
```

- [ ] **Step 5: Create the setup page template**

Create `templates/grammar/test_setup.html`:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Grammar Test — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/grammar.css' %}">{% endblock %}
{% block content %}
<section class="grammar-test-setup">
  <h1>Grammar Test</h1>
  <p class="grammar-test-intro">Practice across every topic at once — pick a level, question type, and length.</p>
  <form method="get" action="{% url 'grammar_test_play' %}" class="grammar-test-fields">
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
    <button type="submit" class="btn btn-primary">Start Test</button>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 6: Add the nav entry**

In `templates/partials/nav.html`, replace:

```html
    <li><a href="{% url 'grammar_browse' %}" data-i18n="nav.grammar">Grammar</a></li>
  </ul>
```

with:

```html
    <li><a href="{% url 'grammar_browse' %}" data-i18n="nav.grammar">Grammar</a></li>
    <li><a href="{% url 'grammar_test_setup' %}" data-i18n="nav.grammarTest">Grammar Test</a></li>
  </ul>
```

- [ ] **Step 7: Add the i18n dict entries**

In `static/js/i18n.js`, replace:

```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
```

with:

```javascript
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
```

Then, still in the same file, replace:

```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
```

with:

```javascript
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
```

- [ ] **Step 8: Add the setup-page CSS**

Append to `static/css/grammar.css`:

```css
.grammar-test-setup h1{ margin-top: 32px; }
.grammar-test-intro{ color: var(--muted); margin: 8px 0 24px; }
.grammar-test-fields{
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 360px;
}
.grammar-test-field{
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
}
.grammar-test-field select{
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
python -m pytest tests/test_grammar_pages.py -v
```

Expected: every test in the file PASSES.

- [ ] **Step 10: Run the full suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES.

- [ ] **Step 11: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Click "Grammar Test" in the nav — confirm it lands on `/grammar/test/` with a Level/Question type/Questions form, Mixed pre-selected in the Question type field. Submit with every field left at default — confirm it navigates to `/grammar/test/play/?stage=&qtype=mixed&count=10` and a real 10-question mixed run starts. Go back to setup, this time pick Level=Advanced, Question type=Rewrite the Sentence, Questions=20, submit — confirm the URL reflects `stage=expert&qtype=transform&count=20` and every one of the 20 questions is a typed transform prompt. Complete a run and click **Change Settings** — confirm it now correctly returns to `/grammar/test/` (a real page this time, unlike Task 1's expected-404 check). Click **Leave** mid-question on a fresh run — confirm it also correctly returns to `/grammar/test/`. Toggle the language switcher (EN/VI) — confirm the "Grammar Test" nav label and the setup page's own chrome (if any `data-i18n` labels were added — the field labels themselves were written as plain text in this plan, so only the nav entry is expected to translate) switches correctly. Stop the server (Ctrl+C) when done.

- [ ] **Step 12: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/config/urls.py" "VocabLarry Professional Environment/config/views_grammar.py" "VocabLarry Professional Environment/templates/grammar/test_setup.html" "VocabLarry Professional Environment/templates/partials/nav.html" "VocabLarry Professional Environment/static/js/i18n.js" "VocabLarry Professional Environment/static/css/grammar.css" "VocabLarry Professional Environment/tests/test_grammar_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add grammar test setup page and nav entry

grammar_test_setup renders a plain GET form (stage/qtype/count,
Mixed default) submitting to Task 1's already-existing play route —
matching vocab_quiz_setup's exact setup-then-play shape and Vocab
Quiz's own dropdown-only field convention rather than production's
card UI or multi-select topic picker. New flat "Grammar Test" nav
entry alongside "Grammar", matching the existing Vocabulary/Quiz
precedent rather than introducing dropdown nav.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** stage-only filter (Task 2 Step 5's single `<select name="stage">` over `GrammarTopic.STAGES`, no topic multi-select anywhere); plain dropdowns not cards (Task 2 Step 5); flat nav entry not dropdown (Task 2 Step 6); GET-form/query-string setup→play (Task 2 Step 5's form `action`/Task 1's `initTestMode` reading `URLSearchParams`); mode-flagged shared engine reusing all rendering/grading functions unchanged (Task 1 Step 7 — every function except `drawQuestions`/`renderError`/`renderQuestion`/`renderResults`/`init` is byte-identical to the pre-refactor file); mastery never touched in test mode (Task 1 Step 7's `state.mode === "topic"` guard on `syncMastery`, verified live in Task 1 Step 9.7); no `@ensure_csrf_cookie` (neither new view has it, matching "no future write to prepare for"); results actions (Task 1 Step 7's `renderResults` mode branch); empty-pool handling (Task 1 Step 7's `initTestMode`'s `if (!pool.length)` guard); no i18n content translation (only the nav key added, Task 2 Step 7).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code; manual-verification steps name concrete real seed-data facts (stage topic counts, specific topic slugs) rather than generic instructions.
- **Type consistency:** `grammar_test_play(request)`/`grammar_test_setup(request)` signatures match between their Task 1/Task 2 definitions and their `urls.py` registrations. `state.mode`/`state.pool`/`state.drawCount` are introduced once in Task 1 and never redefined in Task 2 (Task 2 adds no JS at all). The URL name `grammar_test_play`, referenced by Task 2's form `action`, matches Task 1's exact registration. Query param names (`stage`/`qtype`/`count`) match exactly between Task 2's form field `name` attributes and Task 1's `initTestMode`'s `params.get(...)` calls — double-checked side by side, no typos (`qtype` not `q_type`, `count` not `qty`).
