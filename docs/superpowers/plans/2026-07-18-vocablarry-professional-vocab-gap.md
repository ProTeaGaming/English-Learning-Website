# VocabLarry Professional Environment — Vocab Gap Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Gap mode (fill-the-blank multiple-choice quiz, 4 sub-modes + Mixed Review) to the existing Vocab Quiz feature — a Quiz/Gap family toggle on the setup page, and gap question generation/rendering/feedback on the play page — reusing the existing routes, views, and JSON API with no new backend.

**Architecture:** `templates/vocab/quiz_setup.html` gains a Quiz/Gap radio toggle that swaps between two `<select name="mode">` elements (only the visible one is enabled, so the form still submits one `mode` value). `static/js/vocab-quiz.js` gains a `buildGapQuestion()` function, ported from `vocablarry.html`, dispatched whenever `mode` starts with `gap-`; it reuses the existing `buildOptions()` helper and plugs into the existing render/answer/results flow untouched.

**Tech Stack:** Django templates (no new views/URLs), vanilla JS (`fetch`, no framework), pytest + pytest-django for the setup page's server-rendered surface.

## Global Constraints

- No new models, no new migrations, no new backend endpoints, no new URLs — reuses the existing `/vocab/quiz/` and `/vocab/quiz/play/` routes/views and the existing `/api/words/`, `/api/categories/` JSON endpoints (already serving `gap` and `example` fields) from the Vocab Quiz (Quiz mode) sub-project.
- Gap question generation is a faithful port of `vocablarry.html`'s `buildGapQuestion` — same 4 distractor-pool strategies (Contextual Definition/Lexical Nuance/Collocation & Idiom/Connotation Match) with the same same-part-of-speech fallback thresholds (3 for nuance/collocation, 2 for connotation, 3 for context), and the same per-question random resolution for Mixed Review.
- The target word pool for any `gap-*` mode is filtered to words whose `gap` field is non-empty and contains the literal `___` placeholder. The distractor pool is always the full unfiltered word list (`state.allWords` minus the target) — matches Quiz mode's existing `others` behavior exactly, do not filter distractors by gap-eligibility.
- `mode` stays a single query-string param. Gap sub-modes are represented as `gap-context`, `gap-nuance`, `gap-collocation`, `gap-connotation`, `gap-mixed`, dispatched via a `mode.indexOf('gap-') === 0` check. No new URL params.
- Question count clamps silently to the eligible pool size, matching Quiz mode's existing `Math.min(requested, pool.length)` behavior in `pickTargetWords()` — no new validation UI on the setup page.
- No score/progress persistence anywhere — matches Quiz mode, purely ephemeral client-side session state.
- There is no server-side equivalent of gap question-generation logic to unit test — verified via `node --check` plus manual browser testing per task, matching the precedent set by Quiz mode's question-generation task.
- Test with `pytest`, using `from django.test import Client; c = Client()` per-test, extending `tests/test_vocab_pages.py` (not creating a new test file) — matches that file's existing convention. Reuse its existing `cefr_a1`/`cefr_b1` fixtures — do not redefine them.

---

### Task 1: Setup page — Quiz/Gap family toggle

**Files:**
- Modify: `templates/vocab/quiz_setup.html`
- Modify: `static/css/vocab.css`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: existing context keys `categories`, `cefr_levels` from `vocab_quiz_setup` (unchanged, `config/views_vocab.py`) — this task touches the template only, not the view.
- Produces: the form still submits a single `mode` query param to `vocab_quiz_play` — Quiz family values unchanged (`definition`/`word`/`synonym`/`antonym`/`mixed`); Gap family values are new (`gap-context`/`gap-nuance`/`gap-collocation`/`gap-connotation`/`gap-mixed`). Task 2 consumes these exact string values.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_vocab_pages.py`, right after the existing `test_vocab_quiz_setup_lists_cefr_levels` test:

```python
@pytest.mark.django_db
def test_vocab_quiz_setup_has_family_toggle():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'name="family"' in html
    assert 'value="quiz"' in html
    assert 'value="gap"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_lists_gap_submodes():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="gap-context"' in html
    assert 'value="gap-nuance"' in html
    assert 'value="gap-collocation"' in html
    assert 'value="gap-connotation"' in html
    assert 'value="gap-mixed"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_quiz_modes_still_present():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="definition"' in html
    assert 'value="word"' in html
    assert 'value="synonym"' in html
    assert 'value="antonym"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k "test_vocab_quiz_setup_has_family_toggle or test_vocab_quiz_setup_lists_gap_submodes or test_vocab_quiz_setup_quiz_modes_still_present"
```

Expected: `test_vocab_quiz_setup_has_family_toggle` and `test_vocab_quiz_setup_lists_gap_submodes` FAIL (no `family` radio or `gap-*` options exist yet); `test_vocab_quiz_setup_quiz_modes_still_present` PASSES already (the existing 5 Quiz options).

- [ ] **Step 3: Replace the setup template's Mode field with a family toggle**

Replace the entire contents of `templates/vocab/quiz_setup.html` with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-quiz-setup">
  <h1>Quiz</h1>
  <p class="vocab-quiz-intro">Test yourself on definitions, synonyms, antonyms, and fill-in-the-blank sentences.</p>
  <form method="get" action="{% url 'vocab_quiz_play' %}" class="vocab-quiz-form">
    <div class="vocab-quiz-field">
      <span>Mode family</span>
      <div class="vocab-quiz-family-toggle">
        <label><input type="radio" name="family" value="quiz" id="familyQuiz" checked> Quiz</label>
        <label><input type="radio" name="family" value="gap" id="familyGap"> Gap</label>
      </div>
    </div>
    <label class="vocab-quiz-field" id="quizModeField">
      <span>Mode</span>
      <select name="mode" id="quizModeSelect">
        <option value="definition">Definition Match</option>
        <option value="word">Word from Definition</option>
        <option value="synonym">Synonym Match</option>
        <option value="antonym">Antonym Match</option>
        <option value="mixed">Mixed Review</option>
      </select>
    </label>
    <label class="vocab-quiz-field" id="gapModeField" hidden>
      <span>Gap sub-mode</span>
      <select name="mode" id="gapModeSelect" disabled>
        <option value="gap-context">Contextual Definition</option>
        <option value="gap-nuance">Lexical Nuance</option>
        <option value="gap-collocation">Collocation &amp; Idiom</option>
        <option value="gap-connotation">Connotation Match</option>
        <option value="gap-mixed">Mixed Review</option>
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
{% block extra_body %}
<script>
(function(){
  var quizField = document.getElementById("quizModeField");
  var gapField = document.getElementById("gapModeField");
  var quizSelect = document.getElementById("quizModeSelect");
  var gapSelect = document.getElementById("gapModeSelect");
  function applyFamily(family){
    var isGap = family === "gap";
    quizField.hidden = isGap;
    gapField.hidden = !isGap;
    quizSelect.disabled = isGap;
    gapSelect.disabled = !isGap;
  }
  document.querySelectorAll('input[name="family"]').forEach(function(radio){
    radio.addEventListener("change", function(){ applyFamily(radio.value); });
  });
  applyFamily("quiz");
})();
</script>
{% endblock %}
```

Note: a `disabled` `<select>` is excluded from form submission by the browser natively, so only the active family's `mode` value is ever sent — no extra JS needed to prevent double-submission.

- [ ] **Step 4: Add the family-toggle CSS**

Append to `static/css/vocab.css`:

```css
.vocab-quiz-family-toggle{ display: flex; gap: 16px; font-weight: 400; }
.vocab-quiz-family-toggle label{ display: flex; align-items: center; gap: 6px; cursor: pointer; }
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all tests in the file PASS, including the 3 new ones and every pre-existing test (setup/play rendering, category/CEFR listing, nav link, mount point, script tag).

- [ ] **Step 6: Manually verify the toggle in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Navigate to `/vocab/quiz/`. Confirm the Quiz mode dropdown is visible by default. Click the "Gap" radio — confirm the Quiz dropdown hides and the Gap sub-mode dropdown (5 options: Contextual Definition/Lexical Nuance/Collocation & Idiom/Connotation Match/Mixed Review) appears. Click back to "Quiz" — confirm it reverts. With "Gap" selected and "Lexical Nuance" chosen, click Start Quiz — confirm the browser navigates to `/vocab/quiz/play/?...&mode=gap-nuance&...` (the play page itself will not render a real gap question yet — that's Task 2; a broken/blank question card here is expected for now). Stop the server (Ctrl+C).

- [ ] **Step 7: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/templates/vocab/quiz_setup.html" "VocabLarry Professional Environment/static/css/vocab.css" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add Quiz/Gap family toggle to quiz setup page

quiz_setup.html now shows a Quiz/Gap radio toggle above the mode
select; only the active family's select is enabled, so the form still
submits a single `mode` value. Gap sub-modes are gap-prefixed
(gap-context/gap-nuance/gap-collocation/gap-connotation/gap-mixed) so
the play page's existing single-mode dispatch can branch on them
without a second URL param. Question generation for these values is
implemented in the next task.
EOF
)"
```

---

### Task 2: Play page — gap question generation, rendering, and feedback

**Files:**
- Modify: `static/js/vocab-quiz.js`
- Modify: `static/css/vocab.css`

**Interfaces:**
- Consumes: `mode` values `gap-context`/`gap-nuance`/`gap-collocation`/`gap-connotation`/`gap-mixed` from the query string, produced by Task 1's setup form (existing `var mode = params.get("mode") || "definition";` already captures whatever string is submitted — no change needed to that line).
- Consumes: existing `state.allWords` (each word object has `id`, `word`, `pos`, `definition`, `synonyms`, `antonyms`, `example`, `gap`, `category_id`, `cefr_code` — from `/api/words/`, unchanged), existing `buildOptions(correct, othersPool, getValue)` helper, unchanged.
- Produces: no new interfaces for later tasks — this is the last task in this sub-project. Challenge mode (a future sub-project) will read this file's `mode.indexOf('gap-') === 0` dispatch pattern and `buildGapQuestion` as reusable precedent, the same way it will reuse `buildQuestion`.

This task has no Python-testable surface — verify via `node --check` (Step 5) and manual browser testing (Step 6).

- [ ] **Step 1: Add gap-eligibility filtering to `buildPool()`**

In `static/js/vocab-quiz.js`, replace:

```javascript
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
```

with:

```javascript
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
    } else if (mode.indexOf("gap-") === 0){
      pool = pool.filter(function(w){ return w.gap && w.gap.indexOf("___") !== -1; });
    }
    return pool;
  }
```

- [ ] **Step 2: Add `buildGapQuestion` and its helpers, right after `buildQuestion`**

In `static/js/vocab-quiz.js`, find the end of the existing `buildQuestion` function (it ends with `return { prompt: prompt, text: text, options: options, correct: correct, word: word };\n  }`) and insert immediately after it:

```javascript

  var GAP_PROMPTS = {
    context: "Choose the word that best completes the sentence.",
    nuance: "Near-synonyms are the options — only one word is precisely correct.",
    collocation: "The blank requires a specific fixed word partnership.",
    connotation: "Choose the word whose tone fits the sentence."
  };

  function stripEmTags(s){
    return (s || "").replace(/<\/?em>/g, "");
  }

  function buildGapQuestion(word, gapMode){
    if (gapMode === "gap-mixed"){
      var concrete = ["gap-context", "gap-nuance", "gap-collocation", "gap-connotation"];
      return buildGapQuestion(word, concrete[Math.floor(Math.random() * concrete.length)]);
    }
    var others = state.allWords.filter(function(w){ return w.id !== word.id; });
    var samePos = others.filter(function(w){ return w.pos === word.pos; });
    var distractorPool, subMode;
    if (gapMode === "gap-nuance"){
      subMode = "nuance";
      var synSet = {};
      (word.synonyms || []).forEach(function(s){ synSet[s.toLowerCase()] = true; });
      var synPool = others.filter(function(w){
        return w.synonyms && w.synonyms.some(function(s){ return synSet[s.toLowerCase()]; });
      });
      distractorPool = synPool.length >= 3 ? synPool : samePos;
    } else if (gapMode === "gap-collocation"){
      subMode = "collocation";
      var sameCat = others.filter(function(w){ return w.category_id === word.category_id; });
      distractorPool = sameCat.length >= 3 ? sameCat : samePos;
    } else if (gapMode === "gap-connotation"){
      subMode = "connotation";
      var antSet = {};
      (word.antonyms || []).forEach(function(a){ antSet[a.toLowerCase()] = true; });
      var antPool = others.filter(function(w){ return antSet[w.word.toLowerCase()]; });
      distractorPool = antPool.length >= 2
        ? antPool.concat(samePos.filter(function(w){ return !antSet[w.word.toLowerCase()]; }))
        : samePos;
    } else {
      subMode = "context";
      distractorPool = samePos.length >= 3 ? samePos : others;
    }
    var options = buildOptions(word.word, distractorPool, function(w){ return w.word; });
    var text = word.gap.replace("___", '<span class="vocab-quiz-blank">_____</span>');
    return {
      type: "gap",
      prompt: GAP_PROMPTS[subMode],
      text: text,
      options: options,
      correct: word.word,
      word: word
    };
  }
```

- [ ] **Step 3: Dispatch to `buildGapQuestion` in `generateQuestions()`**

Replace:

```javascript
  function generateQuestions(){
    var pool = buildPool();
    var targets = pickTargetWords(pool);
    state.questions = targets.map(function(word){
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }
```

with:

```javascript
  function generateQuestions(){
    var pool = buildPool();
    var targets = pickTargetWords(pool);
    state.questions = targets.map(function(word){
      if (mode.indexOf("gap-") === 0) return buildGapQuestion(word, mode);
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }
```

- [ ] **Step 4: Show the full example sentence in gap-question feedback**

In `handleAnswer()`, replace:

```javascript
    var feedback = root.querySelector(".vocab-quiz-feedback");
    feedback.innerHTML = (isCorrect ? "<b>Correct!</b> " : "<b>Not quite.</b> The answer is " + q.correct + ". ") +
      q.word.word + " — " + q.word.definition;
```

with:

```javascript
    var feedback = root.querySelector(".vocab-quiz-feedback");
    var feedbackText = (isCorrect ? "<b>Correct!</b> " : "<b>Not quite.</b> The answer is " + q.correct + ". ") +
      q.word.word + " — " + q.word.definition;
    if (q.type === "gap" && q.word.example){
      feedbackText += "<br>" + stripEmTags(q.word.example);
    }
    feedback.innerHTML = feedbackText;
```

- [ ] **Step 5: Check JS syntax**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/vocab-quiz.js
```

Expected: no output, exit code 0.

- [ ] **Step 6: Add the blank-span CSS**

Append to `static/css/vocab.css`:

```css
.vocab-quiz-blank{
  display: inline-block;
  min-width: 64px;
  border-bottom: 2px solid rgb(var(--violet));
  font-weight: 700;
}
```

- [ ] **Step 7: Run the full pytest suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES (this task touches no Python, but confirms Task 1's changes are still intact and nothing else broke).

- [ ] **Step 8: Manually verify all 5 gap sub-modes in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

From `/vocab/quiz/`, select "Gap" family and, one at a time, each of the 5 sub-modes (Contextual Definition, Lexical Nuance, Collocation & Idiom, Connotation Match, Mixed Review), leaving category/CEFR/count at defaults, and click Start Quiz for each. Confirm: a sentence renders with an underlined blank in place of `___`, 4 word options appear, clicking an option scores correctly (correct option turns green; a wrong pick turns red and the correct one is still highlighted), and the feedback line shows the word, its definition, and the full example sentence with no literal `<em>`/`</em>` text visible. For Mixed Review, click through several questions and confirm the underlying question style visibly varies (not always the same sub-mode). Then test the zero-pool case: pick a category/CEFR combination you expect has no words with a `gap` field (or temporarily use browser devtools to confirm via `/api/words/` which ones do), and confirm the existing "No words available for this combination — try different settings" message renders instead of a broken question. Finally, finish a gap quiz and confirm Try Again and Change Settings both still work exactly as they do for Quiz mode. Stop the server (Ctrl+C) when done.

- [ ] **Step 9: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/static/js/vocab-quiz.js" "VocabLarry Professional Environment/static/css/vocab.css"
git commit -m "$(cat <<'EOF'
feat(vlpe): implement gap-mode question generation and feedback

buildGapQuestion() ports vocablarry.html's gap distractor-pool logic
(context/nuance/collocation/connotation, with the same fallback
thresholds) faithfully, dispatched from generateQuestions() whenever
mode starts with "gap-". buildPool() now filters the target pool to
gap-eligible words (non-empty gap field containing "___") for these
modes while distractors keep drawing from the full word list, matching
Quiz mode's existing behavior. Gap-question feedback additionally
shows the word's full example sentence.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** every spec bullet has a corresponding step — family toggle (Task 1), gap-prefixed `mode` values (Task 1 + Task 2), gap-eligible pool filter (Task 2 Step 1), all 4 distractor strategies + Mixed Review (Task 2 Step 2), blank rendering (Task 2 Step 2), enhanced feedback (Task 2 Step 4), silent count clamping (unchanged `pickTargetWords`, already covered by existing code, explicitly called out in Global Constraints), static count label (no step needed — nothing changes it), no persistence (no step touches storage), testing approach (Task 1 Step 1/2/5, Task 2 Step 5/7/8).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code.
- **Type consistency:** `mode` values (`gap-context` etc.) match exactly between Task 1's `<option value="...">` and Task 2's `mode.indexOf("gap-")` checks and `GAP_PROMPTS` keys (which strip the `gap-` prefix internally via `subMode`, consistently). `buildGapQuestion(word, gapMode)`'s signature and `{type, prompt, text, options, correct, word}` return shape match what `renderQuestion`/`handleAnswer` already consume unchanged from Quiz mode.
