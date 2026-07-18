# VocabLarry Professional Environment — Vocab Challenge Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Challenge mode (a random per-question mix of every existing question type, across both Quiz and Gap families) to the existing Vocab Quiz feature — a third family option on the setup page (no sub-mode picker), and a `buildHybridQuestion` function on the play page that reuses every question-generation and rendering code path Quiz and Gap modes already built, with no new backend.

**Architecture:** `templates/vocab/quiz_setup.html`'s existing Quiz/Gap radio toggle gains a third `value="challenge"` option; since Challenge has no visible sub-mode picker, a hidden `<input type="hidden" name="mode" value="challenge">` (enabled only when Challenge is selected) carries the `mode` value instead of a `<select>`. `static/js/vocab-quiz.js` gains one new function, `buildHybridQuestion(word)`, which picks a question type per word (from `definition`/`word`/`synonym`?/`antonym`?/`gap`?, guarding each conditional type the same way `randomMixedMode` already does) and delegates to the existing `buildQuestion`/`buildGapQuestion` functions unmodified — so `renderQuestion()`, `handleAnswer()`, and `renderResults()` need zero changes.

**Tech Stack:** Django templates (no new views/URLs), vanilla JS (`fetch`, no framework), pytest + pytest-django for the setup page's server-rendered surface.

## Global Constraints

- No new models, no new migrations, no new backend endpoints, no new URLs — reuses the existing `/vocab/quiz/` and `/vocab/quiz/play/` routes/views and the existing `/api/words/`, `/api/categories/` JSON endpoints from the Quiz and Gap mode sub-projects.
- `mode` stays a single query-string param. Challenge's value is the flat string `challenge` (no sub-mode suffix, unlike Gap's `gap-*` values) — dispatched via a plain `mode === "challenge"` check.
- **No change to `buildPool()`** — `"challenge"` doesn't match any of the existing `synonym`/`antonym`/`gap-`-prefix branches, so it already falls through to the plain category/CEFR-filtered pool (the same pool Quiz mode uses). Do not add a new branch for it.
- `buildHybridQuestion(word)`'s candidate list always includes `definition` and `word` unconditionally; `synonym`/`antonym` are added only if the word has at least one (same guard as `randomMixedMode`); `gap` is added only if `word.gap` is non-empty and contains `___` (this is a deliberate improvement over production, which includes `gap` unconditionally and can render a blank-text question — see the design spec's Context section for why). When the pick is `gap`, choose uniformly among all 4 concrete gap sub-modes (`gap-context`/`gap-nuance`/`gap-collocation`/`gap-connotation`) — full variety, not production's context-only default.
- `buildHybridQuestion` returns exactly what `buildGapQuestion`/`buildQuestion` already return, with no wrapping — no changes to `renderQuestion()`, `handleAnswer()`, or `renderResults()` are needed or permitted in this plan.
- No score/progress persistence anywhere — matches Quiz and Gap modes.
- There is no server-side equivalent of `buildHybridQuestion` to unit test — verified via `node --check` plus manual browser testing, matching the precedent set by Quiz and Gap modes' question-generation tasks.
- Test with `pytest`, using `from django.test import Client; c = Client()` per-test, extending `tests/test_vocab_pages.py` (not creating a new test file) — matches that file's existing convention. Reuse its existing `cefr_a1`/`cefr_b1` fixtures — do not redefine them.

---

### Task 1: Setup page — Challenge family option

**Files:**
- Modify: `templates/vocab/quiz_setup.html`
- Test: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: existing context keys `categories`, `cefr_levels` from `vocab_quiz_setup` (unchanged) — this task touches the template only.
- Produces: the form can now submit `mode=challenge` (in addition to the pre-existing Quiz and Gap values) to `vocab_quiz_play`. Task 2 consumes this exact string value.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_vocab_pages.py`, right after the existing `test_vocab_quiz_setup_quiz_modes_still_present` test:

```python
@pytest.mark.django_db
def test_vocab_quiz_setup_has_challenge_family_radio():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'value="challenge" id="familyChallenge"' in html


@pytest.mark.django_db
def test_vocab_quiz_setup_has_challenge_mode_input():
    c = Client()
    r = c.get('/vocab/quiz/')
    html = r.content.decode()
    assert 'id="challengeModeInput"' in html
    assert 'name="mode" value="challenge"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v -k "test_vocab_quiz_setup_has_challenge_family_radio or test_vocab_quiz_setup_has_challenge_mode_input"
```

Expected: both FAIL (no `familyChallenge` radio or `challengeModeInput` exist yet).

- [ ] **Step 3: Add the Challenge family radio and hidden mode input**

In `templates/vocab/quiz_setup.html`, replace:

```html
      <div class="vocab-quiz-family-toggle">
        <label><input type="radio" name="family" value="quiz" id="familyQuiz" checked> Quiz</label>
        <label><input type="radio" name="family" value="gap" id="familyGap"> Gap</label>
      </div>
```

with:

```html
      <div class="vocab-quiz-family-toggle">
        <label><input type="radio" name="family" value="quiz" id="familyQuiz" checked> Quiz</label>
        <label><input type="radio" name="family" value="gap" id="familyGap"> Gap</label>
        <label><input type="radio" name="family" value="challenge" id="familyChallenge"> Challenge</label>
      </div>
```

Then, still in the same file, replace:

```html
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
```

with:

```html
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
      <input type="hidden" name="mode" value="challenge" id="challengeModeInput" disabled>
      <label class="vocab-quiz-field">
        <span>Category</span>
```

- [ ] **Step 4: Update the family-toggle script to handle a 3-way switch**

In the same file, replace:

```javascript
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
```

with:

```javascript
(function(){
  var quizField = document.getElementById("quizModeField");
  var gapField = document.getElementById("gapModeField");
  var quizSelect = document.getElementById("quizModeSelect");
  var gapSelect = document.getElementById("gapModeSelect");
  var challengeModeInput = document.getElementById("challengeModeInput");
  function applyFamily(family){
    var isGap = family === "gap";
    var isChallenge = family === "challenge";
    quizField.hidden = family !== "quiz";
    gapField.hidden = !isGap;
    quizSelect.disabled = family !== "quiz";
    gapSelect.disabled = !isGap;
    challengeModeInput.disabled = !isChallenge;
  }
  document.querySelectorAll('input[name="family"]').forEach(function(radio){
    radio.addEventListener("change", function(){ applyFamily(radio.value); });
  });
  applyFamily("quiz");
})();
```

Note: this reuses the existing `.vocab-quiz-family-toggle label` CSS already shipped in the Gap mode sub-project — no new CSS is needed for the third radio.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_vocab_pages.py -v
```

Expected: all tests in the file PASS, including the 2 new ones and every pre-existing test.

- [ ] **Step 6: Manually verify the 3-way toggle in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Navigate to `/vocab/quiz/`. Confirm the Quiz mode dropdown is visible by default. Click "Gap" — confirm the Quiz dropdown hides and the Gap sub-mode dropdown appears (as before). Click "Challenge" — confirm BOTH the Quiz and Gap dropdowns are hidden and nothing replaces them. Click back to "Quiz" — confirm it reverts correctly. With "Challenge" selected, click Start Quiz — confirm the browser navigates to `/vocab/quiz/play/?...&mode=challenge&...` with no `family=` param present (the play page itself will not generate a real hybrid question yet — that's Task 2; a broken/blank question card here is expected for now). Stop the server (Ctrl+C).

- [ ] **Step 7: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/templates/vocab/quiz_setup.html" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "$(cat <<'EOF'
feat(vlpe): add Challenge family option to quiz setup page

quiz_setup.html's Quiz/Gap toggle now has a third "Challenge" radio.
Challenge has no sub-mode picker (matches production), so a hidden
<input name="mode" value="challenge"> carries the mode value instead
of a <select> — enabled/disabled by the same script that already
manages the Quiz and Gap selects, so exactly one mode-carrying element
is ever active. Question generation for mode=challenge is implemented
in the next task.
EOF
)"
```

---

### Task 2: Play page — hybrid question generation

**Files:**
- Modify: `static/js/vocab-quiz.js`

**Interfaces:**
- Consumes: `mode` value `"challenge"` from the query string, produced by Task 1's setup form (existing `var mode = params.get("mode") || "definition";` already captures it — no change needed to that line).
- Consumes: existing `state.allWords`, `buildQuestion(word, qMode)`, `buildGapQuestion(word, gapMode)` — unchanged, reused exactly as Quiz and Gap modes already call them.
- Produces: no new interfaces — this is the last sub-project in the Quiz/Gap/Challenge family trio; remaining future sub-projects (Grammar, Dashboard) don't touch this file.

This task has no Python-testable surface — verify via `node --check` (Step 3) and manual browser testing (Step 4).

- [ ] **Step 1: Add `buildHybridQuestion`, right after `buildGapQuestion`**

In `static/js/vocab-quiz.js`, find the end of `buildGapQuestion` (it ends with the `return { type: "gap", ... };\n  }` block, immediately followed by the start of `function buildPool(){`) and insert this new function between them:

```javascript

  function buildHybridQuestion(word){
    var candidates = ["definition", "word"];
    if (word.synonyms && word.synonyms.length) candidates.push("synonym");
    if (word.antonyms && word.antonyms.length) candidates.push("antonym");
    if (word.gap && word.gap.indexOf("___") !== -1) candidates.push("gap");
    var pick = candidates[Math.floor(Math.random() * candidates.length)];
    if (pick === "gap"){
      var gapSubModes = ["gap-context", "gap-nuance", "gap-collocation", "gap-connotation"];
      return buildGapQuestion(word, gapSubModes[Math.floor(Math.random() * gapSubModes.length)]);
    }
    return buildQuestion(word, pick);
  }
```

- [ ] **Step 2: Dispatch to `buildHybridQuestion` in `generateQuestions()`**

Replace:

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

with:

```javascript
  function generateQuestions(){
    var pool = buildPool();
    var targets = pickTargetWords(pool);
    state.questions = targets.map(function(word){
      if (mode === "challenge") return buildHybridQuestion(word);
      if (mode.indexOf("gap-") === 0) return buildGapQuestion(word, mode);
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }
```

Do not modify `buildPool()` — per the plan's Global Constraints, `"challenge"` correctly falls through to the plain category/CEFR-filtered pool without any new branch.

- [ ] **Step 3: Check JS syntax**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
node --check static/js/vocab-quiz.js
```

Expected: no output, exit code 0.

- [ ] **Step 4: Run the full pytest suite (regression check)**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest -v
```

Expected: every test PASSES (this task touches no Python, but confirms Task 1's changes are still intact and nothing else broke).

- [ ] **Step 5: Manually verify Challenge mode in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

From `/vocab/quiz/`, select "Challenge" family, leave category/CEFR/count at defaults (or pick "All words" for count to maximize variety), and click Start Quiz. Click through at least 15-20 questions and confirm: the question style visibly varies from question to question (some show a plain definition/word prompt, some show a blank-sentence gap prompt with an underlined blank — given ~20% of words have gap sentences, you should see at least a few gap-style questions in a run of this size), scoring is correct for both styles (green/red highlighting, running score increments only on correct answers), and gap-style questions show the extra example-sentence feedback line while non-gap questions don't. Then pick a category you expect has few or no words with synonyms/antonyms/gap sentences and confirm Challenge still produces valid definition/word questions there (never a broken or blank question). Finish the quiz and confirm Try Again and Change Settings both work exactly as they do for Quiz and Gap modes. Stop the server (Ctrl+C) when done.

- [ ] **Step 6: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment/static/js/vocab-quiz.js"
git commit -m "$(cat <<'EOF'
feat(vlpe): implement Challenge-mode hybrid question generation

buildHybridQuestion() picks one question type per word from
definition/word (always available) plus synonym/antonym/gap when the
word actually supports them, then delegates to the existing
buildQuestion/buildGapQuestion unchanged. Gap picks use full sub-mode
variety rather than production's context-only default. generateQuestions()
dispatches mode="challenge" to this new function; buildPool() is
untouched since challenge already falls through to the plain
category/CEFR-filtered pool.
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** every spec bullet has a corresponding step — third family radio + hidden mode input (Task 1 Step 3), 3-way toggle script (Task 1 Step 4), `buildPool()` explicitly left untouched (Task 2 Step 2's instruction), candidate-list guards and gap full-variety (Task 2 Step 1), no `renderQuestion`/`handleAnswer`/`renderResults` changes (none scheduled — correct, per spec), testing approach (Task 1 Steps 1/2/5/6, Task 2 Steps 3/4/5).
- **Placeholder scan:** no TBD/TODO; every step has complete, exact code.
- **Type consistency:** `mode === "challenge"` matches exactly between Task 1's hidden `<input value="challenge">` and Task 2's `generateQuestions()` check. `buildHybridQuestion(word)`'s signature and return value (delegated entirely to `buildGapQuestion`/`buildQuestion`'s existing shapes) require no new fields anywhere else in the file.
