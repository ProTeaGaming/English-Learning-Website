# Grammar Restyle & Stage Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename grammar stage display labels to Basic/Intermediate/Advanced, add a vocab-style stage filter bar to the grammar home, and replace the bright stage colours with a muted grammar-scoped palette.

**Architecture:** Display-label-only rename in `api/views.py` + `vocab/models.py` (stage ids unchanged, no data migration). All UI work is three anchored edits in the single-file SPA `vocab-master.html`: new `--gram-*` CSS vars + class-based chip/fill/bar/medal styling, a static `headline-bar` in `#grammarHome` wired once at module init, and a filter-aware `renderGrammarHome`.

**Tech Stack:** Django 5 + SQLite, pytest-django, vanilla JS single-file SPA.

**Spec:** `docs/superpowers/specs/2026-07-06-grammar-restyle-filter-design.md`

## Global Constraints

- All Django commands run from `D:\IT RELATED\CLAUDE BOMBASTIC AI\ielts-vocab-master\Python\Django`.
- Tests: `python -m pytest <file> -v`; full suite must stay green: `python -m pytest` (currently 42 tests).
- Git: commit after every task. NEVER push (and never to `origin`).
- Django product only — do not touch `Python/Flask/`, `PHP/`, or `React-Native/`.
- Stage **ids** stay exactly `beginner`, `independent`, `expert` everywhere (DB, JSON, URLs, JS state). Only human-visible labels become `Basic`, `Intermediate`, `Advanced`.
- No emoji; icons via the inline SVG sprite (`#i-sprout`, `#i-trend-up`, `#i-grad-cap` — all already in the file).
- Vocab pages must be pixel-identical: do not modify `CEFR_COLORS`, `cefrPillHtml`, `.headline-btn` base rules, or any `data-headline` CSS.
- `vocab-master.html` is ~5,200 lines. Anchor edits on unique code snippets, not line numbers.
- Muted palette (exact values): dark theme `--gram-basic:#8fbf9f`, `--gram-inter:#95aed6`, `--gram-adv:#cfa36b`, `--gram-done:#7aab8f`; light theme `--gram-basic:#5b8a6e`, `--gram-inter:#5872a8`, `--gram-adv:#a1743e`, `--gram-done:#3f7a5f`.

---

### Task 1: Backend label rename (API + model + migration)

**Files:**
- Modify: `ielts-vocab-master/Python/Django/api/views.py` (GRAMMAR_STAGES)
- Modify: `ielts-vocab-master/Python/Django/vocab/models.py` (GrammarTopic.STAGES)
- Create: `ielts-vocab-master/Python/Django/vocab/migrations/XXXX_alter_grammartopic_stage.py` (generated, no-op AlterField)
- Test: `ielts-vocab-master/Python/Django/tests/test_grammar_api.py` (update assertion)

**Interfaces:**
- Consumes: existing `GET /api/grammar/` view and `GrammarTopic` model.
- Produces: API stage objects with `name` = `Basic`/`Intermediate`/`Advanced` (ids unchanged). Task 3's filter buttons carry these labels as static text; the SPA group headers render the API `name` so they need no SPA change.

- [ ] **Step 1: Update the test to expect the new label (failing first)**

In `tests/test_grammar_api.py`, change the assertion line:

```python
    assert beginner['name'] == 'Basic'
```

(was `== 'Beginner'`; the `[s['id'] for s in data] == ['beginner', 'independent', 'expert']` assertion stays unchanged — ids don't move.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_grammar_api.py -v`
Expected: FAIL — `assert 'Beginner' == 'Basic'`

- [ ] **Step 3: Rename the labels**

In `api/views.py` replace:

```python
GRAMMAR_STAGES = [
    ('beginner', 'Beginner', 'A1–A2'),
    ('independent', 'Independent', 'B1–B2'),
    ('expert', 'Expert', 'C1–C2'),
]
```

with:

```python
GRAMMAR_STAGES = [
    ('beginner', 'Basic', 'A1–A2'),
    ('independent', 'Intermediate', 'B1–B2'),
    ('expert', 'Advanced', 'C1–C2'),
]
```

In `vocab/models.py` replace:

```python
    STAGES = [
        ('beginner', 'Beginner'),
        ('independent', 'Independent'),
        ('expert', 'Expert'),
    ]
```

with:

```python
    STAGES = [
        ('beginner', 'Basic'),
        ('independent', 'Intermediate'),
        ('expert', 'Advanced'),
    ]
```

- [ ] **Step 4: Generate and apply the (no-op) migration**

Run: `python manage.py makemigrations vocab`
Expected: `Alter field stage on grammartopic`
Run: `python manage.py migrate`
Expected: `OK` (choices changes don't touch SQLite data)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_grammar_api.py -v`
Expected: 3 passed
Run: `python -m pytest`
Expected: 42 passed (dashboard tests filter by stage *value*, so no other assertion changes)

- [ ] **Step 6: Commit**

```powershell
git add api/views.py vocab/models.py vocab/migrations/ tests/test_grammar_api.py
git commit -m "feat(grammar): rename stage labels to Basic/Intermediate/Advanced"
```

---

### Task 2: SPA muted stage palette (vars + chip/fill/bar/medal classes)

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (4 edits: two var blocks, grammar CSS block, two JS functions)

No JS test runner exists; verification is `node --check` + served-page greps (browser pass in Task 4).

**Interfaces:**
- Consumes: existing `:root` / `[data-theme="light"]` var blocks; the `/* ── Grammar section ── */` CSS block; `cefrRangePillHtml`, `renderGrammarStage` in the GRAMMAR SECTION JS module.
- Produces: CSS vars `--gram-basic/--gram-inter/--gram-adv/--gram-done` (both themes); classes `gram-chip`, `gram-s-basic/inter/adv`, `gram-done`; JS map `GRAMMAR_STAGE_KEY` (`{beginner:'basic', independent:'inter', expert:'adv'}`). Task 3's active-button CSS uses the same vars.

- [ ] **Step 1: Add the palette vars to both theme blocks**

In the `:root` block (dark default), find the line:

```css
  --vio:124,58,237;
```

and insert immediately BEFORE it:

```css
  --gram-basic:#8fbf9f; --gram-inter:#95aed6; --gram-adv:#cfa36b; --gram-done:#7aab8f;
```

In the `[data-theme="light"]` block, find the line:

```css
  --card-bg:#ffffff; --card-border:#dcd7cc;
```

and insert immediately BEFORE it:

```css
  --gram-basic:#5b8a6e; --gram-inter:#5872a8; --gram-adv:#a1743e; --gram-done:#3f7a5f;
```

- [ ] **Step 2: Add the class rules to the grammar CSS block**

Find the rule `.gram-card-blurb{...}` (start of the `/* ── Grammar section ── */` block) and insert immediately BEFORE it:

```css
.gram-chip{background:color-mix(in srgb, var(--muted) 14%, transparent);border:1px solid color-mix(in srgb, var(--muted) 35%, transparent);color:var(--muted);}
.gram-chip.gram-s-basic{background:color-mix(in srgb, var(--gram-basic) 14%, transparent);border-color:color-mix(in srgb, var(--gram-basic) 35%, transparent);color:var(--gram-basic);}
.gram-chip.gram-s-inter{background:color-mix(in srgb, var(--gram-inter) 14%, transparent);border-color:color-mix(in srgb, var(--gram-inter) 35%, transparent);color:var(--gram-inter);}
.gram-chip.gram-s-adv{background:color-mix(in srgb, var(--gram-adv) 14%, transparent);border-color:color-mix(in srgb, var(--gram-adv) 35%, transparent);color:var(--gram-adv);}
#grammarStages .cat-pfill.gram-s-basic{background:var(--gram-basic);}
#grammarStages .cat-pfill.gram-s-inter{background:var(--gram-inter);}
#grammarStages .cat-pfill.gram-s-adv{background:var(--gram-adv);}
#grammarStages .cat-pfill.gram-done{background:var(--gram-done);}
#grammarStages .cat-medal{color:var(--gram-done);}
#grammarStages .section-block.gram-s-basic .section-block-pfill{background:var(--gram-basic);}
#grammarStages .section-block.gram-s-inter .section-block-pfill{background:var(--gram-inter);}
#grammarStages .section-block.gram-s-adv .section-block-pfill{background:var(--gram-adv);}
```

- [ ] **Step 3: Switch the chip function to classes**

Replace the whole function:

```js
function cefrRangePillHtml(label){
  const first = String(label).split('–')[0];
  const c = CEFR_COLORS[first] || '#888';
  return `<span class="cat-cefr-pill" style="background:${c}1c;border:1px solid ${c}55;color:${c}">${label}</span>`;
}
```

with:

```js
const GRAMMAR_STAGE_KEY = { beginner: 'basic', independent: 'inter', expert: 'adv' };
const GRAMMAR_CEFR_KEY  = { 'A1': 'basic', 'B1': 'inter', 'C1': 'adv' };

function cefrRangePillHtml(label){
  const key = GRAMMAR_CEFR_KEY[String(label).split('–')[0]];
  return `<span class="cat-cefr-pill gram-chip${key ? ` gram-s-${key}` : ''}">${label}</span>`;
}
```

(Unknown prefixes fall back to the neutral `gram-chip` styling — per spec.)

- [ ] **Step 4: Class the stage group and the card fill**

In `renderGrammarStage`, replace:

```js
  wrap.className = 'section-block open';
```

with:

```js
  const stageKey = GRAMMAR_STAGE_KEY[stage.id] || '';
  wrap.className = `section-block open${stageKey ? ` gram-s-${stageKey}` : ''}`;
```

and replace the card fill line:

```js
        <div class="cat-pbar"><div class="cat-pfill" style="width:${best}%;${done ? 'background:#10b981;' : ''}"></div></div>
```

with:

```js
        <div class="cat-pbar"><div class="cat-pfill ${done ? 'gram-done' : `gram-s-${stageKey}`}" style="width:${best}%"></div></div>
```

- [ ] **Step 5: Verify**

Run (from the Django dir): `python -m pytest` — Expected: 42 passed (guard against file corruption).
Extract the main `<script>` block and run `node --check` on it — Expected: clean parse.
Grep the file: `grep -c "gram-s-" vocab-master.html` — Expected: ≥ 20 occurrences (CSS + JS).

- [ ] **Step 6: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): muted stage palette for chips, fills, bars and medal"
```

---

### Task 3: SPA stage filter bar

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (3 edits: markup, CSS, JS)

**Interfaces:**
- Consumes: `renderGrammarHome`, `renderGrammarStage`, the `#grammarHome` markup, `.headline-bar`/`.headline-btn` base CSS, sprite icons `#i-sprout`/`#i-trend-up`/`#i-grad-cap`, vars from Task 2.
- Produces: `let grammarStageFilter` (`'all' | 'beginner' | 'independent' | 'expert'`), `#grammarFilterBar` markup, filter-aware `renderGrammarHome`. Nothing downstream consumes these — leaf feature.

- [ ] **Step 1: Insert the filter bar markup**

In the `#grammarHome` markup, replace:

```html
      </div>
      <div id="grammarStages"></div>
```

with:

```html
      </div>
      <div class="headline-bar" id="grammarFilterBar">
        <button class="headline-btn active" data-grammar-stage="all">All</button>
        <button class="headline-btn" data-grammar-stage="beginner"><svg class="ico" aria-hidden="true"><use href="#i-sprout"/></svg> Basic</button>
        <button class="headline-btn" data-grammar-stage="independent"><svg class="ico" aria-hidden="true"><use href="#i-trend-up"/></svg> Intermediate</button>
        <button class="headline-btn" data-grammar-stage="expert"><svg class="ico" aria-hidden="true"><use href="#i-grad-cap"/></svg> Advanced</button>
      </div>
      <div id="grammarStages"></div>
```

(The anchor pair is unique: it is the only `</div>` directly followed by `<div id="grammarStages"></div>`.)

- [ ] **Step 2: Add the active-state CSS**

Immediately after the `.gram-chip.gram-s-adv{...}` rule added in Task 2, insert:

```css
.headline-btn.active[data-grammar-stage="all"]{background:var(--accent);border-color:var(--accent);color:#fff;}
.headline-btn.active[data-grammar-stage="beginner"]{background:var(--gram-basic);border-color:var(--gram-basic);color:#fff;}
.headline-btn.active[data-grammar-stage="independent"]{background:var(--gram-inter);border-color:var(--gram-inter);color:#fff;}
.headline-btn.active[data-grammar-stage="expert"]{background:var(--gram-adv);border-color:var(--gram-adv);color:#fff;}
```

- [ ] **Step 3: Add the filter state and wiring; make `renderGrammarHome` filter-aware**

In the GRAMMAR SECTION JS module, find:

```js
let GRAMMAR_STAGES_DATA = null;   // fetched once per session
```

and insert immediately AFTER it:

```js
let grammarStageFilter = 'all';   // 'all' | stage id; resets on reload
```

Replace, inside `renderGrammarHome`, the lines:

```js
    wrap.innerHTML = '';
    stages.forEach((stage, i) => wrap.appendChild(renderGrammarStage(stage, i + 1)));
```

with:

```js
    wrap.innerHTML = '';
    stages.forEach((stage, i) => {
      if (grammarStageFilter !== 'all' && stage.id !== grammarStageFilter) return;
      wrap.appendChild(renderGrammarStage(stage, i + 1));
    });
```

(`i + 1` keeps the canonical 01/02/03 numbering even when filtered.)

Then find the closing stub comment boundary of the module — the line:

```js
/* ════ NAVIGATION ════ */
```

and insert immediately BEFORE it:

```js
document.querySelectorAll('#grammarFilterBar .headline-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    grammarStageFilter = btn.dataset.grammarStage;
    document.querySelectorAll('#grammarFilterBar .headline-btn').forEach(b =>
      b.classList.toggle('active', b === btn));
    renderGrammarHome();
  });
});
```

(The script sits after the page markup, so `#grammarFilterBar` exists when this runs; wiring once at module init means no duplicate listeners across re-renders.)

- [ ] **Step 4: Verify**

Run: `python -m pytest` — Expected: 42 passed.
`node --check` on the extracted main script — Expected: clean parse.
Start the dev server; `curl http://localhost:8000/` and confirm the response contains `grammarFilterBar`, `data-grammar-stage="independent"`, and `grammarStageFilter`. Stop the server.

- [ ] **Step 5: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): stage filter bar (All/Basic/Intermediate/Advanced)"
```

---

### Task 4: Verification pass

**Files:** none (fix-forward if issues found)

- [ ] **Step 1: Full backend suite**

Run: `python -m pytest`
Expected: 42 passed.

- [ ] **Step 2: API and dashboard labels**

Run: `python manage.py shell -c "import json; from django.test import Client; d=json.loads(Client(HTTP_HOST='localhost').get('/api/grammar/').content); print([ (s['id'], s['name']) for s in d ])"`
Expected: `[('beginner', 'Basic'), ('independent', 'Intermediate'), ('expert', 'Advanced')]`
Dashboard: `get_stage_display` now yields the new labels (covered by the model change; spot-check via the list page if a staff session is available).

- [ ] **Step 3: Browser checklist (manual, user or controller with a browser)**

- Grammar home: filter bar present, All active by default, three groups titled Basic/Intermediate/Advanced.
- Click Basic/Intermediate/Advanced: only that group remains, canonical number kept; All restores all three.
- Chips, card fills, stage bars, medal use the muted palette; mastered bar is calm green; check BOTH themes.
- Vocab Browse page unchanged (bright CEFR pills still bright there).
- Complete one quiz ≥80%: card shows muted done bar + medal tint.

- [ ] **Step 4: Commit any fixes**

```powershell
git add vocab-master.html
git commit -m "fix(grammar): restyle polish from verification"
```
