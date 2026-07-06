# Grammar Thematic Sections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the grammar home's three stage groups with 11 curated thematic sections (vocab-Browse style), keeping the stage filter as a cross-section card filter.

**Architecture:** Pure client-side regrouping in the single-file SPA: a slug→section map + section order list, a flatten/filter/group pipeline in `renderGrammarHome`, and `renderGrammarSection` replacing `renderGrammarStage`. No backend, API, model, or seed changes.

**Tech Stack:** Vanilla JS single-file SPA (`vocab-master.html`), Django backend untouched.

**Spec:** `docs/superpowers/specs/2026-07-06-grammar-sections-design.md`

## Global Constraints

- All Django commands run from `D:\IT RELATED\CLAUDE BOMBASTIC AI\ielts-vocab-master\Python\Django`.
- Full suite must stay green: `python -m pytest` (42 tests). No backend files change in this plan.
- Git: commit after every task. NEVER push.
- Django product only; `vocab-master.html` is ~5,200 lines — anchor edits on unique snippets, not line numbers.
- The section taxonomy, order, and slug assignments are EXACTLY the spec's table — 11 sections, 36 slugs, counts 4+3+4+3+2+4+2+4+2+4+4.
- Stage ids stay `beginner`/`independent`/`expert`; the filter bar markup/wiring and all card/chip/palette styling from the previous plans are NOT modified except where this plan says so.

---

### Task 1: Regroup grammar home into thematic sections

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html` (3 edits: CSS removal, section maps + `renderGrammarHome` rework, `renderGrammarStage` → `renderGrammarSection`)

**Interfaces:**
- Consumes: `loadGrammar()` (memoised, returns the 3-stage array), `grammarStageFilter`, `grammarTopicDone`, `loadGrammarProgress`, `cefrRangePillHtml`, `openGrammarTopic`, `GRAMMAR_STAGE_KEY`, existing `section-block` / `cat-*` / `gram-*` CSS.
- Produces: `GRAMMAR_SECTION_ORDER` (11 names), `GRAMMAR_SECTIONS` (36 slug→name), `renderGrammarSection(name, topics, num)`; `renderGrammarStage` is removed. Nothing else consumes these — leaf feature.

- [ ] **Step 1: Remove the stage-coloured section-bar CSS**

Delete these three lines (they colour the group progress bar per stage; sections now mix stages):

```css
#grammarStages .section-block.gram-s-basic .section-block-pfill{background:var(--gram-basic);}
#grammarStages .section-block.gram-s-inter .section-block-pfill{background:var(--gram-inter);}
#grammarStages .section-block.gram-s-adv .section-block-pfill{background:var(--gram-adv);}
```

- [ ] **Step 2: Add the section maps**

In the GRAMMAR SECTION JS module, find:

```js
const GRAMMAR_STAGE_KEY = { beginner: 'basic', independent: 'inter', expert: 'adv' };
```

and insert immediately BEFORE it:

```js
const GRAMMAR_SECTION_ORDER = [
  'Tenses',
  'Questions & Reported Speech',
  'Nouns, Pronouns & Determiners',
  'Adjectives & Adverbs',
  'Word Forms & Prepositions',
  'Verb Patterns & Modals',
  'Voice',
  'Conditionals & Unreal Forms',
  'Clauses',
  'Emphasis & Sentence Focus',
  'Cohesion & Academic Style',
];
const GRAMMAR_SECTIONS = {
  'present-simple-continuous': 'Tenses',
  'past-simple-continuous':    'Tenses',
  'future-forms':              'Tenses',
  'perfect-tenses':            'Tenses',
  'question-forms':            'Questions & Reported Speech',
  'reported-speech':           'Questions & Reported Speech',
  'question-tags-indirect':    'Questions & Reported Speech',
  'nouns-plurals':             'Nouns, Pronouns & Determiners',
  'pronouns-possessives':      'Nouns, Pronouns & Determiners',
  'articles':                  'Nouns, Pronouns & Determiners',
  'quantifiers':               'Nouns, Pronouns & Determiners',
  'comparatives-superlatives': 'Adjectives & Adverbs',
  'gradable-adjectives':       'Adjectives & Adverbs',
  'adverbs-word-order':        'Adjectives & Adverbs',
  'word-forms':                'Word Forms & Prepositions',
  'prepositions-time-place':   'Word Forms & Prepositions',
  'gerunds-infinitives':       'Verb Patterns & Modals',
  'used-to':                   'Verb Patterns & Modals',
  'modal-verbs':               'Verb Patterns & Modals',
  'advanced-modality':         'Verb Patterns & Modals',
  'passive-voice':             'Voice',
  'causatives':                'Voice',
  'conditionals':              'Conditionals & Unreal Forms',
  'mixed-conditionals':        'Conditionals & Unreal Forms',
  'wish-if-only':              'Conditionals & Unreal Forms',
  'subjunctive-unreal-past':   'Conditionals & Unreal Forms',
  'relative-clauses':          'Clauses',
  'participle-clauses':        'Clauses',
  'inversion-emphasis':        'Emphasis & Sentence Focus',
  'cleft-sentences':           'Emphasis & Sentence Focus',
  'fronting-ever-clauses':     'Emphasis & Sentence Focus',
  'dummy-subjects':            'Emphasis & Sentence Focus',
  'linking-words':             'Cohesion & Academic Style',
  'ellipsis-substitution':     'Cohesion & Academic Style',
  'nominalisation':            'Cohesion & Academic Style',
  'hedging-academic-tone':     'Cohesion & Academic Style',
};
const GRAMMAR_STAGE_RANK = { beginner: 0, independent: 1, expert: 2 };
```

- [ ] **Step 3: Rework `renderGrammarHome`'s success path**

Replace, inside `renderGrammarHome`, the lines:

```js
    wrap.innerHTML = '';
    stages.forEach((stage, i) => {
      if (grammarStageFilter !== 'all' && stage.id !== grammarStageFilter) return;
      wrap.appendChild(renderGrammarStage(stage, i + 1));
    });
```

with:

```js
    wrap.innerHTML = '';
    const topics = [];
    stages.forEach(stage => stage.topics.forEach(t => topics.push({ ...t, stageId: stage.id })));
    const grouped = new Map();
    topics.forEach(t => {
      const section = GRAMMAR_SECTIONS[t.slug] || t.tag;
      if (!grouped.has(section)) grouped.set(section, []);
      grouped.get(section).push(t);
    });
    const names = [...GRAMMAR_SECTION_ORDER.filter(n => grouped.has(n)),
                   ...[...grouped.keys()].filter(n => !GRAMMAR_SECTION_ORDER.includes(n))];
    let rendered = 0;
    names.forEach((name, i) => {
      const inSection = grouped.get(name)
        .filter(t => grammarStageFilter === 'all' || t.stageId === grammarStageFilter)
        .sort((a, b) => (GRAMMAR_STAGE_RANK[a.stageId] ?? 3) - (GRAMMAR_STAGE_RANK[b.stageId] ?? 3));
      if (!inSection.length) return;
      wrap.appendChild(renderGrammarSection(name, inSection, i + 1));
      rendered++;
    });
    if (!rendered){
      wrap.innerHTML = `<p class="sub" style="text-align:center;">No grammar topics yet.</p>`;
    }
```

Notes for the implementer: `Array.prototype.sort` is stable, so API order is preserved within a stage rank. `names` is built from the FULL grouped map (before stage filtering), so `i + 1` is the canonical section number and stays stable when the filter empties earlier sections.

- [ ] **Step 4: Replace `renderGrammarStage` with `renderGrammarSection`**

Replace the whole `renderGrammarStage` function with:

```js
function renderGrammarSection(name, topics, num){
  const progress = loadGrammarProgress();
  const doneCnt = topics.filter(t => grammarTopicDone(t.slug)).length;
  const pct = topics.length ? Math.round(doneCnt / topics.length * 100) : 0;
  const wrap = document.createElement('div');
  wrap.className = 'section-block open';
  wrap.innerHTML = `
    <div class="section-block-header">
      <div class="section-block-num">${String(num).padStart(2, '0')}</div>
      <div class="section-block-info">
        <div class="section-block-name">${name}</div>
        <div class="section-block-meta">${topics.length} topic${topics.length !== 1 ? 's' : ''}</div>
      </div>
      <div class="section-block-right">
        <div class="section-block-prog">
          <div class="section-block-pbar"><div class="section-block-pfill" style="width:${pct}%"></div></div>
          <div class="section-block-pct">${doneCnt}/${topics.length}</div>
        </div>
        <span class="section-block-chevron">›</span>
      </div>
    </div>
    <div class="section-block-divider"></div>
    <div class="section-block-body">
      <div class="section-block-body-inner"><div class="cat-grid"></div></div>
    </div>`;
  const header = wrap.querySelector('.section-block-header');
  const body = wrap.querySelector('.section-block-body');
  body.style.maxHeight = 'none';
  header.addEventListener('click', () => {
    const opening = !wrap.classList.contains('open');
    wrap.classList.toggle('open', opening);
    body.style.maxHeight = opening ? body.scrollHeight + 'px' : '0';
  });
  const grid = wrap.querySelector('.cat-grid');
  topics.forEach(t => {
    const stageKey = GRAMMAR_STAGE_KEY[t.stageId] || '';
    const done = grammarTopicDone(t.slug);
    const best = (progress[t.slug] || {}).best || 0;
    const card = document.createElement('div');
    card.className = 'cat-card t-tv';
    card.innerHTML = `
      <div class="cat-card-top">
        <span class="cat-tag">${t.tag}</span>
        ${cefrRangePillHtml(t.cefr)}
        <svg class="ico cat-arrow" aria-hidden="true"><use href="#i-arrow-up-right"/></svg>
      </div>
      <div class="cat-name">${t.title}</div>
      <div class="gram-card-blurb">${t.blurb}</div>
      <div class="cat-pbar-row">
        <div class="cat-pbar"><div class="cat-pfill ${done ? 'gram-done' : `gram-s-${stageKey}`}" style="width:${best}%"></div></div>
        ${done
          ? '<svg class="ico cat-medal" aria-label="Mastered"><use href="#i-medal"/></svg>'
          : `<span class="cat-plabel">${best ? `best ${best}%` : 'not started'}</span>`}
      </div>`;
    card.addEventListener('click', () => openGrammarTopic(t));
    grid.appendChild(card);
  });
  return wrap;
}
```

(Card markup is identical to the old per-stage version except `stageKey` derives from the topic's attached `stageId` and the stage-group class on the block root is gone. The old function's `const stageKey = ...` line inside `renderGrammarStage`'s header section, and any `gram-s-` class on `wrap.className`, must not survive.)

- [ ] **Step 5: Verify**

Run (from the Django dir): `python -m pytest` — Expected: 42 passed.
`node --check` on the extracted main `<script>` block — Expected: clean parse.
Map-coverage sanity (from the Django dir):

```powershell
python -c "import json,re; html=open('vocab-master.html',encoding='utf-8').read(); m=re.search(r'const GRAMMAR_SECTIONS = \{(.*?)\};', html, re.S); mapped=set(re.findall(r\"'([a-z0-9-]+)':\", m.group(1))); seed={t['slug'] for t in json.load(open('grammar-content.json',encoding='utf-8'))}; print('missing:', sorted(seed-mapped) or 'none'); print('extra:', sorted(mapped-seed) or 'none')"
```

Expected: `missing: none` and `extra: none`.
Confirm `renderGrammarStage` no longer exists: `grep -c "renderGrammarStage" vocab-master.html` — Expected: 0.
Start the dev server, `curl http://localhost:8000/` must contain `GRAMMAR_SECTION_ORDER` and `renderGrammarSection`; stop it if you started it.

- [ ] **Step 6: Commit**

```powershell
git add vocab-master.html
git commit -m "feat(grammar): regroup home into 11 thematic sections"
```

---

### Task 2: Verification pass

**Files:** none (fix-forward if issues found)

- [ ] **Step 1: Full backend suite**

Run: `python -m pytest`
Expected: 42 passed (nothing backend changed).

- [ ] **Step 2: Data-driven section check**

Run this from the Django dir — it simulates the SPA's grouping against the live API:

```powershell
python manage.py shell -c "
import json, re
from django.test import Client
html = open('vocab-master.html', encoding='utf-8').read()
m = re.search(r'const GRAMMAR_SECTIONS = \{(.*?)\};', html, re.S)
mapping = dict(re.findall(r\"'([a-z0-9-]+)':\s*'([^']+)'\", m.group(1)))
order = re.findall(r\"^  '([^']+)',$\", re.search(r'const GRAMMAR_SECTION_ORDER = \[(.*?)\];', html, re.S).group(1), re.M)
data = json.loads(Client(HTTP_HOST='localhost').get('/api/grammar/').content)
from collections import Counter
counts = Counter(mapping[t['slug']] for s in data for t in s['topics'])
print([(n, counts[n]) for n in order])
assert sum(counts.values()) == 36
"
```

Expected: the 11 sections in canonical order with counts `[4, 3, 4, 3, 2, 4, 2, 4, 2, 4, 4]`.

- [ ] **Step 3: Browser checklist (manual)**

- Grammar home shows 11 numbered sections in spec order, counts matching Step 2.
- Basic filter leaves only sections 01–05; Advanced leaves 04, 06, 08–11; All restores everything; numbers stay canonical.
- Cards inside a section are ordered Basic → Intermediate → Advanced; chips/fills still vocab-palette; mastered card shows green bar + gold medal; section bars use the default accent.
- Lesson and quiz flows still work from a card click; both themes look right.

- [ ] **Step 4: Commit any fixes**

```powershell
git add vocab-master.html
git commit -m "fix(grammar): section regroup polish from verification"
```
