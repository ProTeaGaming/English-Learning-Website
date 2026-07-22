# VocabLarry Professional Environment — Vocab Quiz Visual Retrofit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle VocabLarry Professional Environment's Vocab Quiz (`vocab/quiz_setup.html`, `vocab/quiz_play.html`, `vocab-quiz.js`) to visually match production VocabLarry's real quiz design — glass-panel cards, mode-card grids, a family cycler, chip filters, count pills, styled question/result screens — without touching production, and without adding GSAP as a new dependency.

**Architecture:** Four sequential tasks. Task 1 fixes a live 404 bug (hardcoded pre-rename `/vocab/quiz/` links) in isolation. Task 2 lays the CSS foundation (`base.css` CEFR-chip extension + a full rewrite of the quiz-related rules in `vocab.css`) with no markup changes, so it can't regress any existing test. Task 3 rewrites the setup page (template + new setup-page JS in `vocab-quiz.js`). Task 4 rewrites the play/results rendering (`vocab-quiz.js`) and adds the "Leave" link to `quiz_play.html`. Tasks 3 and 4 both touch `vocab-quiz.js` sequentially — each task's step shows the complete resulting file so there is no ambiguity about where new code goes.

**Tech Stack:** Django templates, vanilla JS (no framework, no GSAP), plain CSS (custom properties, `@keyframes`), pytest + Django test client.

## Global Constraints

- Only files under `VocabLarry Professional Environment/` may be modified. `VocabLarry/` (production) is read-only reference material — never edit it.
- `--violet` is a space-separated RGB triplet custom property. Always use `rgb(var(--violet) / X)`, never `rgba(var(--violet), X)` (silent-failure bug class in this codebase).
- VLPE defaults to the **dark** theme (`:root:not([data-theme])`); the light-theme override selector is `[data-theme="light"] .selector{...}` — same selector convention production uses, just VLPE's default is inverted. Port `[data-theme="light"] .selector{...}` blocks verbatim, no flipping needed.
- The underlying form field names (`mode`, `category`, `cefr`, `count`) and the `vocabulary_quiz_play` query-string contract are UNCHANGED — only the rendering/interaction shape changes.
- Category filter stays a `<select>` dropdown (250 real categories in the seed data — a flat chip row is unusable at that scale). Only CEFR becomes a chip row (12 fixed values).
- No GSAP. Card-entrance and score count-up animations are built with plain CSS `@keyframes` and plain JS (`requestAnimationFrame`).
- No new i18n keys — the current setup/play page body content has never used `data-i18n` (only the shared `.mobile-page-switcher`/nav labels do, and those are untouched), and the spec explicitly excludes translating quiz content.
- Word-picker, Grammar pages, quiz-generation algorithm/scoring changes are out of scope.

---

### Task 1: Fix broken `/vocab/quiz/` links in vocab-quiz.js

**Files:**
- Modify: `VocabLarry Professional Environment/static/js/vocab-quiz.js:187,267`
- Test: `VocabLarry Professional Environment/tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new (bug fix only) — later tasks will further rewrite these same functions (`renderError`, the `quizChangeBtn` handler inside `renderResults`), but the corrected URL must survive every later rewrite.

The Nav & Routing Skeleton phase renamed vocab quiz setup from `/vocab/quiz/` to `/vocabulary/quiz/`. Two spots in `vocab-quiz.js` still hardcode the old, now-404 path.

- [ ] **Step 1: Write the failing test**

Add to `VocabLarry Professional Environment/tests/test_vocab_pages.py` (append at end of file):

```python
def test_vocab_quiz_js_has_no_stale_setup_links():
    import pathlib
    js_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'js' / 'vocab-quiz.js'
    content = js_path.read_text(encoding='utf-8')
    assert '/vocab/quiz/' not in content
    assert content.count('/vocabulary/quiz/') >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `VocabLarry Professional Environment/`): `pytest tests/test_vocab_pages.py::test_vocab_quiz_js_has_no_stale_setup_links -v`
Expected: FAIL — `assert '/vocab/quiz/' not in content` fails because the stale links are still present.

- [ ] **Step 3: Fix the two hardcoded links**

In `VocabLarry Professional Environment/static/js/vocab-quiz.js`, line 187 (inside `renderError`):

```js
    root.innerHTML = '<p class="vocab-quiz-error">' + message + ' <a href="/vocab/quiz/">Back to setup</a></p>';
```

becomes:

```js
    root.innerHTML = '<p class="vocab-quiz-error">' + message + ' <a href="/vocabulary/quiz/">Back to setup</a></p>';
```

Line 267 (inside `renderResults`'s `quizChangeBtn` click handler):

```js
      window.location.href = "/vocab/quiz/";
```

becomes:

```js
      window.location.href = "/vocabulary/quiz/";
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_vocab_pages.py::test_vocab_quiz_js_has_no_stale_setup_links -v`
Expected: PASS

- [ ] **Step 5: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass (same count as before, plus the one new test).

- [ ] **Step 6: Commit**

```bash
git add "VocabLarry Professional Environment/static/js/vocab-quiz.js" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "fix(vlpe): correct stale /vocab/quiz/ links in vocab-quiz.js to /vocabulary/quiz/"
```

---

### Task 2: CSS foundation — CEFR chip extension + quiz glass-panel system

**Files:**
- Modify: `VocabLarry Professional Environment/static/css/base.css:441-452`
- Modify: `VocabLarry Professional Environment/static/css/vocab.css` (full-file rewrite)

**Interfaces:**
- Consumes: nothing new.
- Produces: CSS classes that Tasks 3 and 4 will use in markup: `.setup-card`, `.mode-toggle-row`, `.mode-toggle-btn`, `.mode-toggle-label`, `.option-grid`, `.modeCard` (+ `.active`), `.count-row`, `.custom-chip` (+ `.active`), `.custom-count-input` (+ `.bad`), `.custom-count-warn`, `.back-btn`, `.quiz-wrap`, `.progress-bar`, `.progress-fill`, `.q-meta`, `.q-card`, `.q-prompt`, `.q-text`, `.qpos`, `.gapblank`, `.q-options`, `.q-opt` (+ `.correct`/`.wrong`/`:disabled`), `.q-feedback`, `.q-next`, `.result-card`, `.result-score`, `.result-msg`, `.result-actions`, `#testReview`, `.review-item` (+ `.review-correct`/`.review-wrong`), `.review-num`, `.review-body`, `.review-q`, `.review-ans`, `.review-tag` (+ `.correct`/`.wrong`), `@keyframes quizCardEnter`. Also `base.css`'s 12 `.chip.active[data-quiz-cefr="X"]` rules. `.vocab-quiz-setup h1`, `.vocab-quiz-intro`, `.vocab-quiz-error`, `.vocab-quiz-fields`, `.vocab-quiz-field`/`.vocab-quiz-field select` are KEPT unchanged (still used for the setup form's layout and the category `<select>`).
- This task changes no markup, so no existing test's assertions change. It is verified by re-running the full existing suite (must stay green) since there is no automated way to assert CSS content in this codebase's test suite (no prior precedent) — visual correctness for these rules is verified in Tasks 3 and 4 via Playwright once the markup that uses them exists.

- [ ] **Step 1: Extend the 12 CEFR chip rules in base.css to also match `data-quiz-cefr`**

In `VocabLarry Professional Environment/static/css/base.css`, replace lines 441-452:

```css
.chip.active[data-browse-cefr="A1"]{ background: var(--a1); }
.chip.active[data-browse-cefr="A1+"]{ background: var(--a1p); }
.chip.active[data-browse-cefr="A2"]{ background: var(--a2); }
.chip.active[data-browse-cefr="A2+"]{ background: var(--a2p); }
.chip.active[data-browse-cefr="B1"]{ background: var(--b1); }
.chip.active[data-browse-cefr="B1+"]{ background: var(--b1p); }
.chip.active[data-browse-cefr="B2"]{ background: var(--b2); }
.chip.active[data-browse-cefr="B2+"]{ background: var(--b2p); }
.chip.active[data-browse-cefr="C1"]{ background: var(--c1); }
.chip.active[data-browse-cefr="C1+"]{ background: var(--c1p); }
.chip.active[data-browse-cefr="C2"]{ background: var(--c2); }
.chip.active[data-browse-cefr="C2+"]{ background: var(--c2p); }
```

with:

```css
.chip.active[data-browse-cefr="A1"],.chip.active[data-quiz-cefr="A1"]{ background: var(--a1); }
.chip.active[data-browse-cefr="A1+"],.chip.active[data-quiz-cefr="A1+"]{ background: var(--a1p); }
.chip.active[data-browse-cefr="A2"],.chip.active[data-quiz-cefr="A2"]{ background: var(--a2); }
.chip.active[data-browse-cefr="A2+"],.chip.active[data-quiz-cefr="A2+"]{ background: var(--a2p); }
.chip.active[data-browse-cefr="B1"],.chip.active[data-quiz-cefr="B1"]{ background: var(--b1); }
.chip.active[data-browse-cefr="B1+"],.chip.active[data-quiz-cefr="B1+"]{ background: var(--b1p); }
.chip.active[data-browse-cefr="B2"],.chip.active[data-quiz-cefr="B2"]{ background: var(--b2); }
.chip.active[data-browse-cefr="B2+"],.chip.active[data-quiz-cefr="B2+"]{ background: var(--b2p); }
.chip.active[data-browse-cefr="C1"],.chip.active[data-quiz-cefr="C1"]{ background: var(--c1); }
.chip.active[data-browse-cefr="C1+"],.chip.active[data-quiz-cefr="C1+"]{ background: var(--c1p); }
.chip.active[data-browse-cefr="C2"],.chip.active[data-quiz-cefr="C2"]{ background: var(--c2); }
.chip.active[data-browse-cefr="C2+"],.chip.active[data-quiz-cefr="C2+"]{ background: var(--c2p); }
```

- [ ] **Step 2: Rewrite vocab.css**

Replace the ENTIRE content of `VocabLarry Professional Environment/static/css/vocab.css` with:

```css
.vocab-browse h1{ margin-top: 32px; }

.vocab-empty{ color: var(--muted); padding: 24px 0; }

.vocab-breadcrumb{ color: var(--muted); font-size: 0.9rem; margin: 24px 0 4px; }
.vocab-breadcrumb a{ color: var(--muted); }

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
.learn-state-btn, .card-toggle{
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-weight: 700;
  cursor: pointer;
}
.learn-state-btn[data-state="little"], .card-toggle[data-state="little"]{
  background: #f59e0b; border-color: #f59e0b; color: #1c1917;
}
.learn-state-btn[data-state="learned"], .card-toggle[data-state="learned"]{
  background: #22c55e; border-color: #22c55e; color: #fff;
}

.vocab-quiz-setup h1{ margin-top: 32px; }
.vocab-quiz-intro{ color: var(--muted); margin: 8px 0 24px; }
.vocab-quiz-error{ color: var(--muted); padding: 40px 0; }

.vocab-quiz-fields{
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.vocab-quiz-field{
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  text-align: left;
  margin-bottom: 16px;
}
.vocab-quiz-field select{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 400;
  width: 100%;
}

/* Setup card — glass panel, ported from production's .setup-card
   (rgba(var(--vio)) converted to rgb(var(--violet) / X) per this
   codebase's known rgba(var()) silent-failure gotcha). */
.setup-card{
  max-width: 680px; margin: 0 auto;
  background: rgba(22,26,35,.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 24px; padding: 32px; text-align: center;
  box-shadow: 0 16px 48px rgba(0,0,0,.35);
}
[data-theme="light"] .setup-card{ background: rgba(255,255,255,.88); }

/* Family cycler — ported from production's .mode-toggle-row/.mode-toggle-btn */
.mode-toggle-row{ display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 20px; }
.mode-toggle-btn{
  display: flex; align-items: center; justify-content: center; width: 36px; height: 36px;
  border-radius: 999px; border: 1px solid rgb(var(--violet) / .25); background: rgb(var(--violet) / .08);
  font-size: 1rem; line-height: 1; cursor: pointer; transition: border-color .18s ease, background .18s ease; color: var(--text);
}
.mode-toggle-btn:hover{ border-color: rgb(var(--violet)); background: rgb(var(--violet) / .16); }
.mode-toggle-label{ font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 700; min-width: 120px; }

/* Mode cards — ported from production's .option-grid/.modeCard */
.option-grid{ display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 10px; margin-bottom: 22px; }
.modeCard{
  background: rgb(var(--violet) / .06); border: 1.5px solid rgb(var(--violet) / .18); border-radius: 14px; padding: 14px;
  cursor: pointer; transition: border-color .18s ease, background .18s ease, transform .2s cubic-bezier(.25,.46,.45,.94); text-align: left;
}
.modeCard:hover{ border-color: rgb(var(--violet) / .45); transform: translateY(-2px); }
.modeCard.active{ border-color: rgb(var(--violet)); background: rgb(var(--violet) / .14); box-shadow: 0 0 0 3px rgb(var(--violet) / .1); }
.modeCard h3{ font-size: .95rem; margin-bottom: 4px; }
.modeCard p{ font-size: .78rem; color: var(--muted); line-height: 1.35; }

/* Count pills — ported from production's .count-row/.custom-chip */
.count-row{ display: flex; justify-content: center; gap: 10px; margin-top: 20px; margin-bottom: 24px; flex-wrap: wrap; align-items: center; }
.custom-chip{
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 999px; cursor: pointer;
  background: rgb(var(--violet) / .06); border: 1px solid rgb(var(--violet) / .18); color: var(--muted);
  font-size: .82rem; font-weight: 600; font-family: 'Plus Jakarta Sans','Inter',sans-serif; line-height: 1;
  transition: color .15s ease, border-color .15s ease, background .15s ease, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.custom-chip:hover{ color: var(--text); border-color: rgb(var(--violet) / .5); background: rgb(var(--violet) / .1); transform: translateY(-1px); }
.custom-chip.active{ background: rgb(var(--violet)); border-color: transparent; color: #fff; box-shadow: 0 4px 14px rgb(var(--violet) / .35); }
.custom-count-input{
  width: 36px; padding: 3px 4px; border-radius: 6px; text-align: center;
  background: #fff; border: none;
  color: #6366f1; font-size: .82rem; font-weight: 700; font-family: inherit;
  -moz-appearance: textfield;
}
.custom-count-input::-webkit-outer-spin-button,
.custom-count-input::-webkit-inner-spin-button{ -webkit-appearance: none; }
.custom-count-input:focus{ outline: none; box-shadow: 0 0 0 2px rgba(255,255,255,0.8); }
.custom-count-input.bad{ background: #fca5a5; color: #7f1d1d; }
.custom-count-warn{ display: none; font-size: .78rem; color: #f87171; margin-top: -16px; margin-bottom: 8px; text-align: center; }

/* Leave link — ported from production's .back-btn */
.back-btn{
  font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-size: .88rem; font-weight: 600; color: var(--muted);
  background: none; border: none; padding: 0; cursor: pointer; margin-bottom: 12px; display: block;
  text-decoration: none; transition: color .15s ease;
}
.back-btn:hover{ color: rgb(var(--violet)); }

/* Question screen — ported from production's .progress-bar/.q-card family */
.quiz-wrap{ max-width: 680px; margin: 0 auto; }
.progress-bar{ height: 4px; background: var(--surface2); border-radius: 99px; overflow: hidden; margin-bottom: 18px; }
.progress-fill{
  height: 100%; border-radius: 99px; transition: width .4s ease;
  background: linear-gradient(90deg,#7c3aed 0%,#a855f7 100%);
}
.q-meta{ display: flex; justify-content: space-between; font-size: .85rem; color: var(--muted); margin-bottom: 14px; font-weight: 600; font-family: 'JetBrains Mono',monospace; }
.q-card{
  background: rgba(22,26,35,.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 24px; padding: 32px;
  box-shadow: 0 16px 48px rgba(0,0,0,.3);
  animation: quizCardEnter .35s cubic-bezier(.25,.46,.45,.94);
}
[data-theme="light"] .q-card{ background: rgba(255,255,255,.88); }
.q-prompt{ font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; font-weight: 700; margin-bottom: 10px; font-family: 'JetBrains Mono',monospace; }
.q-text{ font-size: 1.25rem; font-weight: 700; font-family: 'Plus Jakarta Sans','Sora',sans-serif; margin-bottom: 24px; line-height: 1.5; }
.q-text .qpos{ font-size: .7em; color: var(--muted); font-weight: 400; font-style: italic; }
.q-text .gapblank{ color: var(--accent); font-weight: 800; border-bottom: 2px dashed var(--accent); padding: 0 4px; }
.q-options{ display: flex; flex-direction: column; gap: 10px; }
.q-opt{
  text-align: left; background: rgb(var(--violet) / .06); border: 1px solid rgb(var(--violet) / .18); color: var(--text);
  padding: 13px 18px; border-radius: 14px; font-size: .95rem; cursor: pointer;
  font-family: 'Plus Jakarta Sans','Inter',sans-serif;
  transition: border-color .15s ease, background .15s ease, box-shadow .15s ease, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.q-opt:hover{ border-color: rgb(var(--violet) / .5); background: rgb(var(--violet) / .1); box-shadow: 0 0 0 3px rgb(var(--violet) / .1); transform: translateY(-1px); }
.q-opt.correct{ background: rgba(34,197,94,.18); border-color: #22c55e; color: #86efac; transform: none; }
.q-opt.wrong{ background: rgba(239,68,68,.18); border-color: #ef4444; color: #fca5a5; transform: none; }
[data-theme="light"] .q-opt.correct{ color: #15803d; }
[data-theme="light"] .q-opt.wrong{ color: #b91c1c; }
.q-opt:disabled{ cursor: default; }
.q-opt:disabled:hover{ border-color: rgb(var(--violet) / .18); background: rgb(var(--violet) / .06); box-shadow: none; transform: none; }
.q-feedback{ margin-top: 18px; font-size: .88rem; color: var(--muted); min-height: 20px; }
.q-feedback b{ color: var(--text); }
.q-next{ display: flex; justify-content: flex-end; margin-top: 18px; }

@keyframes quizCardEnter{
  from{ opacity: 0; transform: translateY(16px) scale(.98); }
  to{ opacity: 1; transform: translateY(0) scale(1); }
}

/* Result screen — ported from production's .result-card family */
.result-card{
  max-width: 560px; margin: 0 auto; text-align: center;
  background: rgba(22,26,35,.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 24px; padding: 40px;
  box-shadow: 0 16px 48px rgba(0,0,0,.35);
  animation: quizCardEnter .35s cubic-bezier(.25,.46,.45,.94);
}
[data-theme="light"] .result-card{ background: rgba(255,255,255,.88); }
.result-card h2{ font-size: 1.3rem; color: var(--muted); margin-bottom: 8px; }
.result-score{
  font-size: 3.5rem; font-weight: 800; font-family: 'Plus Jakarta Sans','Sora',sans-serif; margin: 8px 0;
  background: linear-gradient(135deg,#7c3aed,#a855f7,#4ade80); -webkit-background-clip: text; background-clip: text; color: transparent;
}
.result-msg{ color: var(--muted); margin-bottom: 28px; font-size: .95rem; }
.result-actions{ display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 24px; }
#testReview{ margin-top: 8px; display: flex; flex-direction: column; gap: 8px; text-align: left; }
.review-item{ display: flex; gap: 12px; padding: 12px 14px; border-radius: 12px; border: 1px solid rgb(var(--violet) / .15); background: rgb(var(--violet) / .05); }
.review-item.review-correct{ border-color: rgba(52,211,153,.35); }
.review-item.review-wrong{ border-color: rgba(248,113,113,.35); }
.review-num{ font-size: .75rem; font-weight: 700; color: var(--muted); min-width: 20px; padding-top: 2px; }
.review-body{ flex: 1; display: flex; flex-direction: column; gap: 6px; }
.review-q{ font-size: .88rem; color: var(--text); font-weight: 500; }
.review-ans{ display: flex; flex-wrap: wrap; gap: 6px; }
.review-tag{ font-size: .78rem; font-weight: 600; padding: 3px 10px; border-radius: 999px; }
.review-tag.correct{ background: rgba(52,211,153,.15); color: #34d399; }
.review-tag.wrong{ background: rgba(248,113,113,.15); color: #f87171; }

/* Category browse — .cat-card family, ported from production */
.cat-grid{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(270px,1fr)); padding-bottom: 48px; }
.cat-card{
  position: relative; border: 1px solid var(--border); border-radius: 20px; padding: 18px;
  background: var(--card-bg); text-decoration: none; color: var(--text);
  cursor: pointer; display: flex; flex-direction: column; gap: 14px;
  transition: transform .4s var(--ease-luxe), box-shadow .4s var(--ease-luxe), border-color .4s var(--ease-luxe);
}
.cat-card:hover{
  transform: translateY(-4px); border-color: rgb(var(--violet) / .5);
  box-shadow: 0 24px 60px rgba(0,0,0,.18), 0 6px 18px rgb(var(--violet) / .08);
}
.cat-card-top{ display: flex; align-items: center; gap: 8px; }
.cat-tag{
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'JetBrains Mono', monospace; font-size: .58rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .12em; padding: 4px 10px; border-radius: 999px;
  color: var(--accent-c, rgb(var(--violet)));
  background: rgb(var(--violet) / .1); border: 1px solid rgb(var(--violet) / .38);
}
.cat-tag .ico{ font-size: .85rem; }
.cat-arrow{ margin-left: auto; font-size: 1rem; color: var(--muted); opacity: .5; flex-shrink: 0; transition: color .3s var(--ease-luxe), opacity .3s var(--ease-luxe), transform .45s var(--ease-luxe); }
.cat-card:hover .cat-arrow{ color: var(--accent-c, rgb(var(--violet))); opacity: 1; transform: translate(2px,-2px); }
.cat-medal{ font-size: 1.15rem; width: 1.15rem; height: 1.15rem; color: #eab308; flex-shrink: 0; filter: drop-shadow(0 0 6px rgba(234,179,8,.35)); }
[data-theme="light"] .cat-medal{ color: #ca8a04; filter: none; }
.cat-name{ font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 800; font-size: 1.02rem; line-height: 1.3; color: var(--accent-c, var(--text)); letter-spacing: -.01em; }
.cat-pbar-row{ display: flex; align-items: center; gap: 10px; }
.cat-pbar{ flex: 1; height: 2.5px; border-radius: 99px; background: var(--border); overflow: hidden; position: relative; }
.cat-pfill{ height: 100%; border-radius: 99px; background: var(--accent-c, rgb(var(--violet))); transition: width .4s ease; }
.cat-pfill-little{ height: 100%; border-radius: 99px 0 0 99px; background: var(--c1); transition: width .4s ease; opacity: .7; }
.cat-plabel{ font-size: .66rem; color: var(--muted); white-space: nowrap; font-family: 'JetBrains Mono', monospace; }

/* Word grid within a category — .word-card family, ported from production */
.card-grid{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px,1fr)); gap: 16px; margin: 20px 0; }
.word-card{
  position: relative; border: 1px solid rgb(var(--violet) / .15); border-radius: 18px;
  background: var(--card-bg); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  padding: 16px; min-height: 120px; overflow: hidden;
  border-top: 3px solid rgb(var(--violet));
  transition: transform .24s cubic-bezier(.25,.46,.45,.94), box-shadow .24s cubic-bezier(.25,.46,.45,.94);
}
.word-card:hover{
  transform: translateY(-5px);
  box-shadow: 0 20px 48px rgba(0,0,0,.45), 0 0 0 1px rgb(var(--violet) / .5), 0 4px 16px rgb(var(--violet) / .15);
}
.word-card .face{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.word-card .word a{ font-size: 1.1rem; font-weight: 700; font-family: 'Plus Jakarta Sans','Sora',sans-serif; letter-spacing: -.01em; line-height: 1.25; color: var(--text); text-decoration: none; }
.word-card .word a:hover{ color: rgb(var(--violet)); }
.word-card .pos{ font-size: .75rem; color: var(--muted); margin-top: 2px; font-style: italic; }
.word-card .reveal{
  position: absolute; inset: 0;
  background: linear-gradient(160deg, var(--card-bg) 0%, var(--card-bg) 100%);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  padding: 14px 16px; opacity: 0; transform: translateY(8px);
  transition: opacity .2s cubic-bezier(.4,0,.2,1), transform .2s cubic-bezier(.4,0,.2,1);
  overflow-y: auto; display: flex; flex-direction: column; gap: 6px; font-size: .82rem;
  pointer-events: none;
}
.word-card:hover .reveal{ opacity: 1; transform: translateY(0); pointer-events: auto; }
.reveal .rdef{ font-weight: 600; line-height: 1.4; color: var(--text); }
.reveal .rrow{ color: var(--muted); line-height: 1.4; }
.reveal .rrow b{ color: var(--text); font-weight: 600; }
.reveal .rex{ color: var(--muted); font-style: italic; line-height: 1.4; margin-top: auto; padding-top: 6px; border-top: 1px solid var(--border); }
.reveal .learn-state-row{ margin: 6px 0 0; }
.word-card.learned{ box-shadow: 0 0 0 2px #22c55e inset; }
.word-card.learned::before{
  content: "✓"; position: absolute; top: 10px; right: 10px; width: 20px; height: 20px;
  background: #22c55e; color: #fff; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: .7rem; font-weight: 800; z-index: 2;
}
.word-card.little{ box-shadow: 0 0 0 2px #f59e0b inset; }
.word-card.little::before{
  content: "~"; position: absolute; top: 10px; right: 10px; width: 20px; height: 20px;
  background: #f59e0b; color: #1c1917; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: .85rem; font-weight: 900; z-index: 2;
}

/* Numbered pagination — ported from production's .pagination/.page-btn */
.pagination{ display: flex; gap: 6px; align-items: center; justify-content: center; margin: 24px 0; flex-wrap: wrap; }
.page-btn{
  min-width: 36px; height: 36px; padding: 0 10px; border-radius: 9px; border: 1px solid rgb(var(--violet) / .18);
  background: rgb(var(--violet) / .06); color: var(--muted); font-family: 'JetBrains Mono', monospace;
  font-size: .82rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; justify-content: center;
  transition: background .15s, color .15s, border-color .15s, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.page-btn:hover:not(.disabled){ border-color: rgb(var(--violet) / .5); color: rgb(var(--violet)); transform: translateY(-1px); }
.page-btn.active{ background: rgb(var(--violet)); border-color: rgb(var(--violet)); color: #fff; box-shadow: 0 4px 12px rgb(var(--violet) / .35); }
.page-btn.disabled{ opacity: .4; pointer-events: none; }
.page-ellipsis{ color: var(--muted); font-size: .9rem; padding: 0 4px; font-family: 'JetBrains Mono', monospace; }

/* Category bulk actions — ported from production's .cat-bulk-actions */
.cat-bulk-actions{ display: flex; gap: 10px; justify-content: center; margin: 24px 0 8px; flex-wrap: wrap; }
.cat-bulk-btn{
  font-size: .82rem; font-weight: 700; font-family: 'Plus Jakarta Sans','Sora',sans-serif; padding: 9px 20px;
  border-radius: 12px; border: none; background: #22c55e; color: #fff; text-decoration: none;
  cursor: pointer; box-shadow: 0 4px 14px rgba(34,197,94,.35);
  transition: transform .2s cubic-bezier(.25,.46,.45,.94), box-shadow .2s ease;
}
.cat-bulk-btn:hover{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(34,197,94,.45); }
.cat-bulk-btn-secondary{ background: rgb(var(--violet) / .1); border: 1px solid rgb(var(--violet) / .2); color: var(--text); box-shadow: none; }
.cat-bulk-btn-secondary:hover{ background: rgb(var(--violet) / .16); box-shadow: none; }

/* Word detail — card container matching production's modal content */
.word-detail-card{
  position: relative; max-width: 480px; margin: 24px 0 48px;
  background: var(--card-bg); border-radius: 24px; overflow: hidden;
  border-top: 4px solid var(--accent-c, rgb(var(--violet)));
  border-left: 1px solid rgb(var(--violet) / .25); border-right: 1px solid rgb(var(--violet) / .25);
  border-bottom: 1px solid rgb(var(--violet) / .25);
  box-shadow: 0 32px 80px rgba(0,0,0,.25);
  padding: 24px 24px 28px;
}
.word-detail-header{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.word-detail-header h1{ font-size: 1.8rem; font-weight: 800; font-family: 'Plus Jakarta Sans','Sora',sans-serif; color: var(--accent-c, rgb(var(--violet))); line-height: 1.1; margin: 0; }
.word-xref{ color: rgb(var(--violet)); font-weight: 700; text-decoration: underline; text-decoration-style: dotted; text-underline-offset: 2px; }
.word-xref:hover{ text-decoration-style: solid; }
```

- [ ] **Step 3: Run the full test suite to confirm no regressions**

Run (from `VocabLarry Professional Environment/`): `pytest`
Expected: all tests pass, same count as after Task 1 (this task changed no markup, so no test assertion is affected).

- [ ] **Step 4: Commit**

```bash
git add "VocabLarry Professional Environment/static/css/base.css" "VocabLarry Professional Environment/static/css/vocab.css"
git commit -m "feat(vlpe): port production's quiz glass-panel CSS system into vocab.css"
```

---

### Task 3: Setup page retrofit — glass-panel card, family cycler, mode-card grids, CEFR chips, count pills

**Files:**
- Modify: `VocabLarry Professional Environment/templates/vocab/quiz_setup.html` (full-file rewrite)
- Modify: `VocabLarry Professional Environment/static/js/vocab-quiz.js` (adds a new `initSetupPage()` block; the existing play/results engine below it is untouched in this task)
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py` (update tests that assert old markup, add tests for new markup)

**Interfaces:**
- Consumes: CSS classes from Task 2 (`.setup-card`, `.mode-toggle-row`, `.mode-toggle-btn`, `.mode-toggle-label`, `.option-grid`, `.modeCard`, `.count-row`, `.custom-chip`, `.custom-count-input`, `.custom-count-warn`, `.chip`/`.filters`/`.filter-row`/`.filter-label` from `base.css`), and the corrected URLs from Task 1.
- Produces: the query-string contract on submit is unchanged (`mode`, `category`, `cefr`, `count` — same names/values as before). `FAMILIES`, `FAMILY_LABELS`, `QUIZ_MODES`, `GAP_MODES` are now defined at the top of `vocab-quiz.js`; Task 4 reuses `FAMILY_LABELS` for the result screen's title.

The setup page becomes a single `.setup-card` glass panel containing: a family cycler (prev/next arrows + label, cycling Quiz → Fill the Gap → Challenge), a JS-rendered mode-card grid (5 cards for Quiz, 5 for Gap, none for Challenge), the existing category `<select>` (unchanged control, restyled chrome only — 250 categories don't fit a chip row), a CEFR chip row (new), and count pills with a "Custom" chip + number input. All interactivity moves out of the old inline `<script>` and into `vocab-quiz.js`, which now runs on both the setup and play pages.

- [ ] **Step 1: Write the failing/changed tests**

In `VocabLarry Professional Environment/tests/test_vocab_pages.py`, replace these five tests:

```python
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
```

with:

```python
@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_family_cycler():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="familyPrev"' in html
    assert 'id="familyNext"' in html
    assert 'id="familyLabel"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_mode_grids():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="quizModeGrid"' in html
    assert 'id="gapModeGrid"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_hidden_mode_input():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="modeInput"' in html
    assert 'name="mode"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_loads_quiz_js():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert 'vocab-quiz.js' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_setup_card():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    assert 'class="setup-card"' in r.content.decode()
```

Also add three new tests directly after `test_vocabulary_quiz_setup_lists_cefr_levels`:

```python
@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_cefr_chips(cefr_a1):
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'data-quiz-cefr="A1"' in html
    assert 'name="cefr"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_has_count_row():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert 'id="countRow"' in html
    assert 'data-count="10"' in html
    assert 'data-count="all"' in html
    assert 'id="customCountInput"' in html
    assert 'name="count"' in html


@pytest.mark.django_db
def test_vocabulary_quiz_setup_still_has_category_select():
    c = Client()
    r = c.get('/vocabulary/quiz/')
    html = r.content.decode()
    assert '<select name="category">' in html
```

- [ ] **Step 2: Run the changed/new tests to verify they fail**

Run: `pytest tests/test_vocab_pages.py -k "quiz_setup" -v`
Expected: FAIL on the new/changed tests (old markup doesn't have `familyPrev`/`quizModeGrid`/`setup-card`/`data-quiz-cefr`/`countRow` etc. yet); the unrelated `quiz_setup_lists_categories`/`quiz_setup_lists_cefr_levels`/`quiz_setup_renders` tests still pass (untouched markup).

- [ ] **Step 3: Rewrite quiz_setup.html**

Replace the ENTIRE content of `VocabLarry Professional Environment/templates/vocab/quiz_setup.html` with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-quiz-setup">
  <h1>Quiz</h1>
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <p class="vocab-quiz-intro">Test yourself on definitions, synonyms, antonyms, and fill-in-the-blank sentences.</p>

  <div class="setup-card">
    <div class="mode-toggle-row">
      <button type="button" class="mode-toggle-btn" id="familyPrev" aria-label="Previous test mode">‹</button>
      <span class="mode-toggle-label" id="familyLabel">Quiz</span>
      <button type="button" class="mode-toggle-btn" id="familyNext" aria-label="Next test mode">›</button>
    </div>

    <form method="get" action="{% url 'vocabulary_quiz_play' %}" class="vocab-quiz-fields" id="quizSetupForm">
      <input type="hidden" name="mode" id="modeInput" value="definition">
      <input type="hidden" name="cefr" id="cefrInput" value="">
      <input type="hidden" name="count" id="countInput" value="10">

      <div class="option-grid" id="quizModeGrid"></div>
      <div class="option-grid" id="gapModeGrid" hidden></div>

      <label class="vocab-quiz-field">
        <span>Category</span>
        <select name="category">
          <option value="">All categories</option>
          {% for category in categories %}
            <option value="{{ category.slug }}">{{ category.name }}</option>
          {% endfor %}
        </select>
      </label>

      <div class="filters">
        <div class="filter-row">
          <span class="filter-label">CEFR</span>
          <button type="button" class="chip active" data-quiz-cefr="all">All levels</button>
          {% for level in cefr_levels %}
            <button type="button" class="chip" data-quiz-cefr="{{ level.code }}">{{ level.code }}</button>
          {% endfor %}
        </div>
      </div>

      <div class="count-row" id="countRow">
        <button type="button" class="chip active" data-count="10">10</button>
        <button type="button" class="chip" data-count="20">20</button>
        <button type="button" class="chip" data-count="30">30</button>
        <button type="button" class="chip" data-count="all">All</button>
        <span class="custom-chip" id="customCountChip">
          <span>Custom</span>
          <input type="number" min="1" class="custom-count-input" id="customCountInput" value="15" hidden>
        </span>
      </div>
      <span class="custom-count-warn" id="customCountWarn">Enter a number greater than 0.</span>

      <button type="submit" class="btn btn-primary">Start Quiz</button>
    </form>
  </div>
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/vocab-quiz.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 4: Add the setup-page JS block to vocab-quiz.js**

In `VocabLarry Professional Environment/static/js/vocab-quiz.js`, the file currently starts with:

```js
(function(){
  var root = document.getElementById("quizPlayRoot");
  if (!root) return;
```

Replace those three lines with:

```js
(function(){
  var FAMILIES = ["quiz", "gap", "challenge"];
  var FAMILY_LABELS = { quiz: "Quiz", gap: "Fill the Gap", challenge: "Challenge" };

  var QUIZ_MODES = [
    { id: "definition", name: "Definition Match", desc: "See a word — choose its correct definition." },
    { id: "word", name: "Word from Definition", desc: "Read a definition — choose the matching word." },
    { id: "synonym", name: "Synonym Match", desc: "See a word — choose a word with a similar meaning." },
    { id: "antonym", name: "Antonym Match", desc: "See a word — choose a word with the opposite meaning." },
    { id: "mixed", name: "Mixed Review", desc: "A random mix of every question type." }
  ];

  var GAP_MODES = [
    { id: "gap-context", name: "Contextual Definition", desc: "The sentence provides context clues — use them to find the missing word." },
    { id: "gap-nuance", name: "Lexical Nuance", desc: "Near-synonyms are the distractors — only one word is precisely correct." },
    { id: "gap-collocation", name: "Collocation & Idiom", desc: "The blank requires a specific fixed word partnership or collocation." },
    { id: "gap-connotation", name: "Connotation Match", desc: "Choose the word whose tone — positive, negative or formal — fits the sentence." },
    { id: "gap-mixed", name: "Mixed Review", desc: "A random mix of all four gap fill types." }
  ];

  function initSetupPage(){
    var form = document.getElementById("quizSetupForm");
    if (!form) return;

    var modeInput = document.getElementById("modeInput");
    var cefrInput = document.getElementById("cefrInput");
    var countInput = document.getElementById("countInput");
    var familyLabel = document.getElementById("familyLabel");
    var quizGrid = document.getElementById("quizModeGrid");
    var gapGrid = document.getElementById("gapModeGrid");
    var countRow = document.getElementById("countRow");
    var customChip = document.getElementById("customCountChip");
    var customInput = document.getElementById("customCountInput");
    var customWarn = document.getElementById("customCountWarn");

    var familyIdx = 0;

    function renderModeGrid(container, modes){
      container.innerHTML = modes.map(function(m, i){
        return '<button type="button" class="modeCard' + (i === 0 ? ' active' : '') + '" data-mode="' + m.id + '">' +
          '<h3>' + m.name + '</h3><p>' + m.desc + '</p></button>';
      }).join("");
      container.querySelectorAll(".modeCard").forEach(function(card){
        card.addEventListener("click", function(){
          container.querySelectorAll(".modeCard").forEach(function(c){ c.classList.remove("active"); });
          card.classList.add("active");
          modeInput.value = card.dataset.mode;
        });
      });
    }

    function applyFamily(){
      var family = FAMILIES[familyIdx];
      familyLabel.textContent = FAMILY_LABELS[family];
      quizGrid.hidden = family !== "quiz";
      gapGrid.hidden = family !== "gap";
      if (family === "quiz"){
        modeInput.value = QUIZ_MODES[0].id;
      } else if (family === "gap"){
        modeInput.value = GAP_MODES[0].id;
      } else {
        modeInput.value = "challenge";
      }
    }

    renderModeGrid(quizGrid, QUIZ_MODES);
    renderModeGrid(gapGrid, GAP_MODES);

    document.getElementById("familyPrev").addEventListener("click", function(){
      familyIdx = (familyIdx - 1 + FAMILIES.length) % FAMILIES.length;
      applyFamily();
    });
    document.getElementById("familyNext").addEventListener("click", function(){
      familyIdx = (familyIdx + 1) % FAMILIES.length;
      applyFamily();
    });
    applyFamily();

    form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(chip){
      chip.addEventListener("click", function(){
        form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(c){ c.classList.remove("active"); });
        chip.classList.add("active");
        cefrInput.value = chip.dataset.quizCefr === "all" ? "" : chip.dataset.quizCefr;
      });
    });

    function setCount(value){
      countInput.value = value;
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){
        c.classList.toggle("active", c.dataset.count === String(value));
      });
      customChip.classList.remove("active");
      customInput.hidden = true;
      customWarn.style.display = "none";
    }

    countRow.querySelectorAll(".chip[data-count]").forEach(function(chip){
      chip.addEventListener("click", function(){ setCount(chip.dataset.count); });
    });

    customChip.addEventListener("click", function(){
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){ c.classList.remove("active"); });
      customChip.classList.add("active");
      customInput.hidden = false;
      customInput.focus();
      var val = parseInt(customInput.value, 10);
      if (val > 0) countInput.value = val;
    });

    customInput.addEventListener("click", function(e){ e.stopPropagation(); });
    customInput.addEventListener("input", function(){
      var val = parseInt(customInput.value, 10);
      if (val > 0){
        customInput.classList.remove("bad");
        customWarn.style.display = "none";
        countInput.value = val;
      } else {
        customInput.classList.add("bad");
        customWarn.style.display = "block";
      }
    });
  }

  initSetupPage();

  var root = document.getElementById("quizPlayRoot");
  if (!root) return;
```

Everything below that (`var params = new URLSearchParams(...)` through the closing `init(); })();`) is untouched by this task — it is exactly the file as Task 1 left it.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_vocab_pages.py -k "quiz_setup or mobile_page_switcher" -v`
Expected: PASS — all `quiz_setup` tests, plus `test_mobile_page_switcher_present_on_vocabulary_landing_pages` and `test_mobile_page_switcher_marks_active_chip` (the `.mobile-page-switcher` markup is untouched).

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run: `pytest`
Expected: all tests pass.

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be verified by the Python test suite (client-side interaction). Using a browser (or Playwright), navigate to `/vocabulary/quiz/` and confirm:
- The family cycler starts on "Quiz" with 5 mode cards showing (Definition Match active by default); clicking `›` cycles to "Fill the Gap" (5 gap cards shown, quiz cards hidden) then "Challenge" (no cards shown) then wraps back to "Quiz"; `‹` cycles backward.
- Clicking a mode card sets it active (others deactivate) — inspect the hidden `#modeInput` value updates to match `data-mode`.
- Clicking a CEFR chip sets it active with the correct CEFR color (matching `.cefr-badge`/`--a1`..`--c2p` colors) and deactivates the others; `#cefrInput` updates (empty string for "All levels").
- Clicking a count chip (10/20/30/All) sets it active and deactivates "Custom"; clicking "Custom" reveals the number input, focuses it, and typing a value updates `#countInput`; typing 0 or a negative number shows the red warning text and turns the input's background red.
- Submitting the form (Start Quiz) navigates to `/vocabulary/quiz/play/?mode=...&category=...&cefr=...&count=...` with the expected query string for whatever was selected.
- Both dark (default) and light theme render the `.setup-card` glass panel correctly (light theme: `rgba(255,255,255,.88)` background, not the dark glass).

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/templates/vocab/quiz_setup.html" "VocabLarry Professional Environment/static/js/vocab-quiz.js" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): retrofit quiz setup page with glass-panel card, family cycler, mode-card grids, CEFR chips, count pills"
```

---

### Task 4: Play/Results screen retrofit — glass-panel question/result cards, Leave link, count-up animation

**Files:**
- Modify: `VocabLarry Professional Environment/templates/vocab/quiz_play.html`
- Modify: `VocabLarry Professional Environment/static/js/vocab-quiz.js` (full-file rewrite of the play/results engine below `initSetupPage()`)
- Modify: `VocabLarry Professional Environment/tests/test_vocab_pages.py` (add one test)

**Interfaces:**
- Consumes: CSS classes from Task 2 (`.quiz-wrap`, `.progress-bar`, `.progress-fill`, `.q-meta`, `.q-card`, `.q-prompt`, `.q-text`, `.qpos`, `.gapblank`, `.q-options`, `.q-opt`, `.q-feedback`, `.q-next`, `.result-card`, `.result-score`, `.result-msg`, `.result-actions`, `#testReview`, `.review-item`, `.review-num`, `.review-body`, `.review-q`, `.review-ans`, `.review-tag`, `.back-btn`), `FAMILY_LABELS` from Task 3's block in the same file, and the corrected `/vocabulary/quiz/` URLs from Task 1.
- Produces: no new interfaces consumed elsewhere — this is the terminal rendering layer.

The play screen gets a static "Leave" link (bails out to setup, independent of JS state) and the question/results rendering is rewritten to use the new glass-panel classes, with a `qpos`-wrapped part-of-speech tag, a `gapblank`-styled blank (renamed from `vocab-quiz-blank`), a family-aware result title, generic tiered result copy, and a plain-JS score count-up animation on the results screen.

- [ ] **Step 1: Write the failing test**

Add to `VocabLarry Professional Environment/tests/test_vocab_pages.py`, directly after `test_vocabulary_quiz_play_loads_script`:

```python
@pytest.mark.django_db
def test_vocabulary_quiz_play_has_leave_link():
    c = Client()
    r = c.get('/vocabulary/quiz/play/')
    html = r.content.decode()
    assert 'class="back-btn"' in html
    assert 'href="/vocabulary/quiz/"' in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_vocab_pages.py::test_vocabulary_quiz_play_has_leave_link -v`
Expected: FAIL — `quiz_play.html` doesn't have a `.back-btn` element yet.

- [ ] **Step 3: Add the Leave link to quiz_play.html**

Replace the ENTIRE content of `VocabLarry Professional Environment/templates/vocab/quiz_play.html` with:

```html
{% extends "base.html" %}
{% load static %}
{% block title %}Quiz — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-quiz-play">
  <div class="mobile-page-switcher">
    <a class="chip" href="{% url 'vocabulary_category_list' %}" data-i18n="nav.category">Category</a>
    <a class="chip" href="{% url 'vocabulary_word_list' %}" data-i18n="nav.word">Word</a>
    <a class="chip active" href="{% url 'vocabulary_quiz_setup' %}" data-i18n="nav.quiz">Quiz</a>
  </div>
  <div class="quiz-wrap">
    <a href="{% url 'vocabulary_quiz_setup' %}" class="back-btn">Leave</a>
    <div id="quizPlayRoot"></div>
  </div>
</section>
{% endblock %}
{% block extra_body %}
<script src="{% static 'js/vocab-quiz.js' %}" defer></script>
{% endblock %}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_vocab_pages.py::test_vocabulary_quiz_play_has_leave_link -v`
Expected: PASS

- [ ] **Step 5: Rewrite the play/results engine in vocab-quiz.js**

Replace the ENTIRE content of `VocabLarry Professional Environment/static/js/vocab-quiz.js` with:

```js
(function(){
  var FAMILIES = ["quiz", "gap", "challenge"];
  var FAMILY_LABELS = { quiz: "Quiz", gap: "Fill the Gap", challenge: "Challenge" };

  var QUIZ_MODES = [
    { id: "definition", name: "Definition Match", desc: "See a word — choose its correct definition." },
    { id: "word", name: "Word from Definition", desc: "Read a definition — choose the matching word." },
    { id: "synonym", name: "Synonym Match", desc: "See a word — choose a word with a similar meaning." },
    { id: "antonym", name: "Antonym Match", desc: "See a word — choose a word with the opposite meaning." },
    { id: "mixed", name: "Mixed Review", desc: "A random mix of every question type." }
  ];

  var GAP_MODES = [
    { id: "gap-context", name: "Contextual Definition", desc: "The sentence provides context clues — use them to find the missing word." },
    { id: "gap-nuance", name: "Lexical Nuance", desc: "Near-synonyms are the distractors — only one word is precisely correct." },
    { id: "gap-collocation", name: "Collocation & Idiom", desc: "The blank requires a specific fixed word partnership or collocation." },
    { id: "gap-connotation", name: "Connotation Match", desc: "Choose the word whose tone — positive, negative or formal — fits the sentence." },
    { id: "gap-mixed", name: "Mixed Review", desc: "A random mix of all four gap fill types." }
  ];

  function initSetupPage(){
    var form = document.getElementById("quizSetupForm");
    if (!form) return;

    var modeInput = document.getElementById("modeInput");
    var cefrInput = document.getElementById("cefrInput");
    var countInput = document.getElementById("countInput");
    var familyLabel = document.getElementById("familyLabel");
    var quizGrid = document.getElementById("quizModeGrid");
    var gapGrid = document.getElementById("gapModeGrid");
    var countRow = document.getElementById("countRow");
    var customChip = document.getElementById("customCountChip");
    var customInput = document.getElementById("customCountInput");
    var customWarn = document.getElementById("customCountWarn");

    var familyIdx = 0;

    function renderModeGrid(container, modes){
      container.innerHTML = modes.map(function(m, i){
        return '<button type="button" class="modeCard' + (i === 0 ? ' active' : '') + '" data-mode="' + m.id + '">' +
          '<h3>' + m.name + '</h3><p>' + m.desc + '</p></button>';
      }).join("");
      container.querySelectorAll(".modeCard").forEach(function(card){
        card.addEventListener("click", function(){
          container.querySelectorAll(".modeCard").forEach(function(c){ c.classList.remove("active"); });
          card.classList.add("active");
          modeInput.value = card.dataset.mode;
        });
      });
    }

    function applyFamily(){
      var family = FAMILIES[familyIdx];
      familyLabel.textContent = FAMILY_LABELS[family];
      quizGrid.hidden = family !== "quiz";
      gapGrid.hidden = family !== "gap";
      if (family === "quiz"){
        modeInput.value = QUIZ_MODES[0].id;
      } else if (family === "gap"){
        modeInput.value = GAP_MODES[0].id;
      } else {
        modeInput.value = "challenge";
      }
    }

    renderModeGrid(quizGrid, QUIZ_MODES);
    renderModeGrid(gapGrid, GAP_MODES);

    document.getElementById("familyPrev").addEventListener("click", function(){
      familyIdx = (familyIdx - 1 + FAMILIES.length) % FAMILIES.length;
      applyFamily();
    });
    document.getElementById("familyNext").addEventListener("click", function(){
      familyIdx = (familyIdx + 1) % FAMILIES.length;
      applyFamily();
    });
    applyFamily();

    form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(chip){
      chip.addEventListener("click", function(){
        form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(c){ c.classList.remove("active"); });
        chip.classList.add("active");
        cefrInput.value = chip.dataset.quizCefr === "all" ? "" : chip.dataset.quizCefr;
      });
    });

    function setCount(value){
      countInput.value = value;
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){
        c.classList.toggle("active", c.dataset.count === String(value));
      });
      customChip.classList.remove("active");
      customInput.hidden = true;
      customWarn.style.display = "none";
    }

    countRow.querySelectorAll(".chip[data-count]").forEach(function(chip){
      chip.addEventListener("click", function(){ setCount(chip.dataset.count); });
    });

    customChip.addEventListener("click", function(){
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){ c.classList.remove("active"); });
      customChip.classList.add("active");
      customInput.hidden = false;
      customInput.focus();
      var val = parseInt(customInput.value, 10);
      if (val > 0) countInput.value = val;
    });

    customInput.addEventListener("click", function(e){ e.stopPropagation(); });
    customInput.addEventListener("input", function(){
      var val = parseInt(customInput.value, 10);
      if (val > 0){
        customInput.classList.remove("bad");
        customWarn.style.display = "none";
        countInput.value = val;
      } else {
        customInput.classList.add("bad");
        customWarn.style.display = "block";
      }
    });
  }

  initSetupPage();

  var root = document.getElementById("quizPlayRoot");
  if (!root) return;

  var params = new URLSearchParams(window.location.search);
  var categorySlug = params.get("category") || "";
  var cefrCode = params.get("cefr") || "";
  var requestedCount = params.get("count") || "10";
  var mode = params.get("mode") || "definition";
  var family = mode === "challenge" ? "challenge" : (mode.indexOf("gap-") === 0 ? "gap" : "quiz");

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
      text = word.word + ' <span class="qpos">(' + word.pos + ')</span>';
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else if (qMode === "antonym"){
      var ants = word.antonyms || [];
      correct = capitalize(ants[Math.floor(Math.random() * ants.length)]);
      prompt = "Choose a word with the opposite meaning:";
      text = word.word + ' <span class="qpos">(' + word.pos + ')</span>';
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else {
      prompt = "Choose the correct definition:";
      text = word.word + ' <span class="qpos">(' + word.pos + ')</span>';
      correct = word.definition;
      options = buildOptions(correct, others, function(w){ return w.definition; });
    }
    return { prompt: prompt, text: text, options: options, correct: correct, word: word };
  }

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
    var text = word.gap.replace("___", '<span class="gapblank">_____</span>');
    return {
      type: "gap",
      prompt: GAP_PROMPTS[subMode],
      text: text,
      options: options,
      correct: word.word,
      word: word
    };
  }

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
      if (mode === "challenge") return buildHybridQuestion(word);
      if (mode.indexOf("gap-") === 0) return buildGapQuestion(word, mode);
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }

  function renderError(message){
    root.innerHTML = '<p class="vocab-quiz-error">' + message + ' <a href="/vocabulary/quiz/">Back to setup</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    root.innerHTML =
      '<div class="progress-bar"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="q-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="q-card">' +
        '<div class="q-prompt">' + q.prompt + '</div>' +
        '<div class="q-text">' + q.text + '</div>' +
        '<div class="q-options">' +
          q.options.map(function(opt){ return '<button type="button" class="q-opt">' + opt + '</button>'; }).join("") +
        '</div>' +
        '<div class="q-feedback"></div>' +
        '<div class="q-next" style="display:none;"><button type="button" class="btn" id="quizNextBtn"></button></div>' +
      '</div>';
    root.querySelectorAll(".q-opt").forEach(function(btn){
      btn.addEventListener("click", function(){ handleAnswer(btn, q); });
    });
  }

  function handleAnswer(selectedBtn, q){
    var isCorrect = selectedBtn.textContent === q.correct;
    root.querySelectorAll(".q-opt").forEach(function(btn){
      btn.disabled = true;
      if (btn.textContent === q.correct) btn.classList.add("correct");
      else if (btn === selectedBtn) btn.classList.add("wrong");
    });
    if (isCorrect) state.score++;
    state.answers.push({ question: q, selected: selectedBtn.textContent, isCorrect: isCorrect });
    var feedback = root.querySelector(".q-feedback");
    var feedbackText = (isCorrect ? "<b>Correct!</b> " : "<b>Not quite.</b> The answer is " + q.correct + ". ") +
      q.word.word + " — " + q.word.definition;
    if (q.type === "gap" && q.word.example){
      feedbackText += "<br>" + stripEmTags(q.word.example);
    }
    feedback.innerHTML = feedbackText;
    root.querySelector(".q-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".q-next");
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

  function resultMessage(pct){
    if (pct === 100) return "Perfect score! Outstanding vocabulary mastery.";
    if (pct >= 80) return "Excellent work — you know these words well.";
    if (pct >= 60) return "Good effort — a bit more practice and you'll nail it.";
    return "Keep practising — review the word list and try again.";
  }

  function animateScore(el, target, total, duration){
    var start = null;
    function step(ts){
      if (start === null) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      el.textContent = Math.round(progress * target) + " / " + total;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    var resultTitle = FAMILY_LABELS[family] + " Complete";
    root.innerHTML =
      '<div class="result-card">' +
        '<h2>' + resultTitle + '</h2>' +
        '<div class="result-score" id="resultScoreDisplay">0 / ' + total + '</div>' +
        '<p class="result-msg">' + resultMessage(pct) + '</p>' +
        '<div class="result-actions">' +
          '<button type="button" class="btn" id="quizRetryBtn">Try Again</button>' +
          '<button type="button" class="btn" id="quizChangeBtn">Change Settings</button>' +
          '<button type="button" class="btn" id="quizReviewBtn">Review Answers</button>' +
        '</div>' +
        '<div id="testReview" style="display:none;"></div>' +
      '</div>';
    animateScore(document.getElementById("resultScoreDisplay"), state.score, total, 700);
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
      window.location.href = "/vocabulary/quiz/";
    });
    document.getElementById("quizReviewBtn").addEventListener("click", function(){
      var panel = document.getElementById("testReview");
      if (panel.style.display === "flex"){ panel.style.display = "none"; return; }
      panel.innerHTML = state.answers.map(function(a, i){
        var tags = '<span class="review-tag correct">✓ ' + a.question.correct + '</span>';
        if (!a.isCorrect){
          tags += '<span class="review-tag wrong">✗ Your answer: ' + a.selected + '</span>';
        }
        return '<div class="review-item ' + (a.isCorrect ? "review-correct" : "review-wrong") + '">' +
          '<span class="review-num">' + (i + 1) + '</span>' +
          '<div class="review-body">' +
            '<div class="review-q">' + a.question.word.word + '</div>' +
            '<div class="review-ans">' + tags + '</div>' +
          '</div>' +
        '</div>';
      }).join("");
      panel.style.display = "flex";
    });
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

- [ ] **Step 6: Run the full test suite to confirm no regressions**

Run (from `VocabLarry Professional Environment/`): `pytest`
Expected: all tests pass.

- [ ] **Step 7: Manual/Playwright verification**

This step cannot be verified by the Python test suite (client-side rendering and algorithmic correctness). Using a browser (or Playwright):
- Start a quiz from `/vocabulary/quiz/` with each family (Quiz, Fill the Gap, Challenge) and confirm the `.q-card` glass panel, progress bar, part-of-speech `.qpos` styling, and (for Gap/Challenge) the bold accent-colored dashed-underline `.gapblank` render correctly.
- Answer a question correctly and incorrectly; confirm `.q-opt.correct`/`.q-opt.wrong` styling and the feedback text.
- Complete a full quiz; confirm the `.result-card` renders, the score visibly counts up from 0 to the final value, the result title matches the family ("Quiz Complete" / "Fill the Gap Complete" / "Challenge Complete"), and the message text matches the scored percentage tier.
- Click "Review Answers"; confirm the `.review-item` list renders with ✓/✗ `.review-tag`s, and toggling collapses/expands it.
- Click "Change Settings"; confirm it navigates to `/vocabulary/quiz/` (not the old 404 `/vocab/quiz/`).
- Click "Leave" during an active question; confirm it navigates to `/vocabulary/quiz/`.
- Confirm both dark (default) and light theme render `.q-card`/`.result-card` correctly (light theme: `rgba(255,255,255,.88)` background).
- Confirm the `.q-card`/`.result-card` entrance animation (fade + slight rise) plays on each new question and on the results screen, without a GSAP dependency being added anywhere (check `package.json`/template `<script>` tags — none should reference GSAP).

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry Professional Environment/templates/vocab/quiz_play.html" "VocabLarry Professional Environment/static/js/vocab-quiz.js" "VocabLarry Professional Environment/tests/test_vocab_pages.py"
git commit -m "feat(vlpe): retrofit quiz play/results screens with glass-panel cards, Leave link, and score count-up animation"
```
