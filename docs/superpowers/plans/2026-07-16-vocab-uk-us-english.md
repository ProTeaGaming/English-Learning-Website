# Vocabulary US/UK English Variant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let learners pick English (UK) instead of English (US) in the existing language switcher, showing British spelling for the ~40 vocabulary words that genuinely differ (colour/favourite/sceptical/etc.), while leaving the other 4,960 words and all identity/progress-tracking keys untouched.

**Architecture:** Follows the existing Vietnamese i18n pattern exactly: a static override dict (`WORD_GB`, keyed by word pk) plus small per-field accessor functions (`wordHeadword`/`wordDef`/`wordExample`/`wordSynonyms`/`wordAntonyms`) that return the UK text when `state.lang === "en-gb"` and an override exists, else the original. Every render/quiz-generation call site that currently reads the raw field is routed through the matching accessor — but only where the value is *displayed*; keys used for `learnMap`/`VOCAB_BY_WORD`/`selectedWords` identity stay on the raw canonical field so progress-tracking and MCQ grading never break across a language switch.

**Tech Stack:** Vanilla JS in a single HTML file (`VocabLarry/vocablarry.html`), Django dev server for manual/Playwright verification, no build step, no JS test runner (this codebase verifies frontend changes via `node --check` on the extracted `<script>` plus a live Playwright click-through, not unit tests — there is no JS unit test framework here).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-16-vocab-uk-us-english-design.md` — read it if anything below is ambiguous.
- Only edit `VocabLarry/vocablarry.html` (this project's rule: only `VocabLarry/` is the live product; `IELTS-Vocab/` is frozen legacy — never touch it).
- No backend/API/model changes. `WORD_GB` is static client-side data, same as `WORD_DEF_VI`.
- Never commit-and-push to `elw` without the user explicitly asking in this session — commit locally after each task, but hold the push until asked.
- Do not touch Grammar content (lesson prose, quiz questions) — that is Phase 2, a separate future spec/plan.
- `state.lang` values in play: `"en"` (US, default), `"en-gb"` (UK, new), `"vi"` (unchanged). Persisted via `localStorage.ivm_lang`, same key as today.
- Every code snippet below is the exact current text in `VocabLarry/vocablarry.html` as of commit `0b5f980` — if a `Modify` step's "before" text doesn't match exactly, stop and re-read the file around that line before editing; don't guess.

---

### Task 1: Language switcher — split "English" into English (US) / English (UK)

**Files:**
- Modify: `VocabLarry/vocablarry.html` (`#langMenu` markup, ~line 1544)

**Interfaces:**
- Consumes: nothing new — the existing generic `data-lang` click handler (`document.querySelectorAll("#langMenu [data-lang]")...`, ~line 3491) already sets `state.lang = row.dataset.lang` and persists it for *any* value, no code change needed there.
- Produces: `state.lang` can now be `"en-gb"`, selectable from the UI. Tasks 2-4 depend on this value existing.

- [ ] **Step 1: Edit the langMenu markup**

In `VocabLarry/vocablarry.html`, find:

```html
        <div class="lang-menu" id="langMenu">
          <button class="mode-picker-row" data-lang="en" type="button">
            <span class="mode-picker-name">English</span>
          </button>
          <button class="mode-picker-row" data-lang="vi" type="button">
            <span class="mode-picker-name">Tiếng Việt</span>
          </button>
```

Replace with:

```html
        <div class="lang-menu" id="langMenu">
          <button class="mode-picker-row" data-lang="en" type="button">
            <span class="mode-picker-name">English (US)</span>
          </button>
          <button class="mode-picker-row" data-lang="en-gb" type="button">
            <span class="mode-picker-name">English (UK)</span>
          </button>
          <button class="mode-picker-row" data-lang="vi" type="button">
            <span class="mode-picker-name">Tiếng Việt</span>
          </button>
```

- [ ] **Step 2: Start the dev server**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python manage.py runserver 8000` (background/separate terminal — leave it running for this and all later tasks' verification steps).

- [ ] **Step 3: Verify with Playwright**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.click("#langToggle")
    rows = page.locator("#langMenu .mode-picker-row .mode-picker-name").all_inner_texts()
    assert rows[0] == "English (US)", rows
    assert rows[1] == "English (UK)", rows
    assert rows[2] == "Tiếng Việt", rows
    page.click("#langMenu [data-lang='en-gb']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en-gb"
    assert "active" in page.locator("#langMenu [data-lang='en-gb']").get_attribute("class")
    page.click("#langToggle")
    page.click("#langMenu [data-lang='en']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en"
    b.close()
print("Task 1 verified OK")
```

Expected output: `Task 1 verified OK`, no assertion errors.

- [ ] **Step 4: Commit**

```bash
git add "VocabLarry/vocablarry.html"
git commit -m "feat(lang): split English into English (US) / English (UK) rows"
```

---

### Task 2: WORD_GB override data + accessor functions

**Files:**
- Modify: `VocabLarry/vocablarry.html` (right after the existing `wordDef()` function, ~line 8531; `loadVocab()`'s `VOCAB_BY_WORD` construction, ~line 14471)

**Interfaces:**
- Consumes: `state.lang` (Task 1).
- Produces: `wordHeadword(word)`, `wordDef(word)` (extended), `wordExample(word)`, `wordSynonyms(word)`, `wordAntonyms(word)` — each takes a `VOCAB_DATA`-shaped object (`{w, pos, def, syn, ant, ex, gap, cefr, cat, pk, ...}`) and returns the display-ready value for the current `state.lang`. Tasks 3-4 call these instead of reading `.w`/`.def`/`.ex`/`.syn`/`.ant` directly wherever text is *displayed* (not for `learnMap`/`VOCAB_BY_WORD`/`selectedWords` keys, which stay on the raw field).

This task's `WORD_GB` content is final — reviewed by hand against every occurrence of each ambiguous term (story/check/program/practice/license/curb/tire) in the current 5,000-word dataset. Do not regenerate it from a fresh script run; paste it exactly as given below.

- [ ] **Step 1: Add `WORD_GB` and the accessor functions**

In `VocabLarry/vocablarry.html`, find:

```js
/* Returns the Vietnamese definition when available and Vietnamese is
   active, else the original English definition unchanged. */
function wordDef(word){
  return (state.lang === "vi" && WORD_DEF_VI[word.pk]) || word.def;
}
```

Replace with:

```js
/* Returns the Vietnamese definition when available and Vietnamese is
   active, else the original English definition unchanged. */
function wordDef(word){
  if (state.lang === "vi" && WORD_DEF_VI[word.pk]) return WORD_DEF_VI[word.pk];
  const gb = ukOverride(word);
  if (gb && gb.def) return gb.def;
  return word.def;
}

/* English (UK) spelling variant data. Only the ~40 words (of 5,000) whose
   headword, definition, example, synonyms, or antonyms actually contain a
   genuine US/UK spelling difference get an entry here — reviewed by hand
   against every occurrence of context-ambiguous terms (story/storey,
   check/cheque, program/programme, practice/practise, license/licence,
   curb/kerb, tire/tyre all turned out to have zero genuine matches in this
   dataset's actual usage and are deliberately NOT included; see the design
   spec's audit section). Each entry holds only the fields that differ. */
const WORD_GB = {
  4961: { "example": "She was <em>elated</em> when she found out she had been accepted to the programme." },
  5227: { "word": "sceptical", "example": "Many investors remain <em>sceptical</em> about the company's growth forecasts." },
  5560: { "synonyms": ["distrustful", "sceptical", "jaded", "pessimistic"] },
  5599: { "word": "instalment", "example": "She paid for the laptop in monthly <em>instalments</em> over a year." },
  5606: { "synonyms": ["endurance", "staying power", "resilience", "vigour"] },
  5692: { "antonyms": ["critic", "sceptic", "disinterested party"] },
  7023: { "example": "The report analysed <em>macroeconomic</em> trends across the region." },
  7029: { "def": "Relating to the economic behaviour of individuals or firms." },
  7334: { "def": "Treating serious issues with inappropriate humour." },
  7647: { "example": "The programme pairs new employees with senior staff for <em>mentorship</em>." },
  7654: { "example": "The city centre is closed to <em>vehicular</em> traffic on weekends." },
  7669: { "example": "The new <em>condominium</em> offers stunning views of the harbour." },
  7705: { "def": "The act of offering money or favours to influence someone's actions." },
  7718: { "antonyms": ["defence"] },
  7732: { "example": "The rumour was clearly <em>malicious</em> in intent." },
  7740: { "example": "The <em>jovial</em> innkeeper welcomed every traveller with a joke." },
  7895: { "def": "The branch of theology concerned with death, judgement, and final destiny." },
  7907: { "synonyms": ["scepticism"] },
  7917: { "antonyms": ["clarity", "directness", "candour"] },
  7935: { "example": "The resort caters to travellers with <em>epicurean</em> tastes." },
  7954: { "example": "The university launched a programme to encourage student <em>entrepreneurship</em>." },
  8063: { "example": "You should <em>take that rumour with a grain of salt</em>." },
  8113: { "def": "A judgement that a person is not guilty of a crime." },
  8383: { "example": "The government launched an <em>afforestation</em> programme to combat erosion." },
  8526: { "example": "The town centre benefited from a wave of <em>revitalization</em>." },
  8696: { "example": "<em>Offshoring</em> helped the company reduce labour costs." },
  8732: { "word": "endeavour", "example": "The team will <em>endeavour</em> to finish the project on time." },
  8830: { "example": "The new road was built to <em>bypass</em> the city centre." },
  8920: { "example": "A <em>seasoned</em> traveller, she packed light and moved quickly through customs." },
  9110: { "synonyms": ["skilful", "talented", "expert"] },
  9282: { "word": "flavour", "example": "The soup had a strong <em>flavour</em> of garlic." },
  9283: { "synonyms": ["flavour"] },
  9624: { "word": "catalyse", "example": "The new policy helped <em>catalyse</em> economic reform." },
  9782: { "synonyms": ["minor fault", "indiscretion", "misdemeanour", "foible"] },
  9787: { "antonyms": ["wellbeing", "vigour", "contentment"] },
  9788: { "antonyms": ["vigour", "energy", "alertness"] },
  9789: { "antonyms": ["vigour", "energy", "liveliness"] },
  9804: { "synonyms": ["endless struggle", "never-ending labour"] },
  9846: { "synonyms": ["favourable", "helpful", "beneficial", "supportive"], "antonyms": ["detrimental", "unfavourable", "hindering"] },
  9874: { "antonyms": ["comfortable", "relaxed", "cosy"] }
};

/* Returns this word's WORD_GB override object when English (UK) is active
   and one exists, else undefined. Internal helper for the wordX()
   accessors below — never read the returned object's absence as "this
   word has no UK spelling", since most words genuinely don't differ. */
function ukOverride(word){
  return state.lang === "en-gb" ? WORD_GB[word.pk] : undefined;
}
/* Display-only accessors: use these wherever the word/example/synonyms/
   antonyms are shown to the user or matched against a search box. Do NOT
   use these for learnMap/VOCAB_BY_WORD/selectedWords keys — those must
   stay on the raw word.w/word.ex/etc. fields so progress tracking and
   quiz-option identity survive a language switch mid-session. */
function wordHeadword(word){
  const gb = ukOverride(word);
  return (gb && gb.word) || word.w;
}
function wordExample(word){
  const gb = ukOverride(word);
  return (gb && gb.example) || word.ex;
}
function wordSynonyms(word){
  const gb = ukOverride(word);
  return (gb && gb.synonyms) || word.syn;
}
function wordAntonyms(word){
  const gb = ukOverride(word);
  return (gb && gb.antonyms) || word.ant;
}
```

- [ ] **Step 2: Add the `VOCAB_BY_WORD` alias-key fix**

`linkedWordsHtml()` looks up synonym/antonym cross-reference links via `VOCAB_BY_WORD.get(text.toLowerCase())`. Five words get a headword spelling change in `WORD_GB` (flavour, sceptical, instalment, endeavour, catalyse) — without this fix, a synonym/antonym list showing one of these words' UK spelling (e.g. "sceptical" in word 5692's antonyms) would fail to resolve as a clickable cross-reference in UK mode, since `VOCAB_BY_WORD` is only keyed by the raw US spelling ("skeptical").

In `VocabLarry/vocablarry.html`, find:

```js
    CAT_MAP       = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));
    ALL_CATEGORIES = [...CATEGORIES, ...CEFR_CATEGORIES];
    VOCAB_BY_WORD = new Map(VOCAB_DATA.map(w => [w.w.toLowerCase(), w]));
```

Replace with:

```js
    CAT_MAP       = Object.fromEntries(CATEGORIES.map(c => [c.id, c]));
    ALL_CATEGORIES = [...CATEGORIES, ...CEFR_CATEGORIES];
    VOCAB_BY_WORD = new Map(VOCAB_DATA.map(w => [w.w.toLowerCase(), w]));
    // Also alias each word's UK-spelling headword (if it has one) to the
    // same object, so cross-reference links resolve regardless of which
    // spelling variant is currently displayed as synonym/antonym text.
    VOCAB_DATA.forEach(w => {
      const gb = WORD_GB[w.pk];
      if (gb && gb.word) VOCAB_BY_WORD.set(gb.word.toLowerCase(), w);
    });
```

- [ ] **Step 3: Syntax-check the script**

Run:

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry"
python -c "
import re
html = open('vocablarry.html', encoding='utf-8').read()
scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
open('_script_check.js', 'w', encoding='utf-8').write('\n'.join(scripts))
"
node --check _script_check.js
rm _script_check.js
```

Expected: no output (silent success means valid syntax).

- [ ] **Step 4: Verify accessors and the alias fix with Playwright**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("window.VOCAB_DATA && VOCAB_DATA.length > 0")
    page.evaluate("state.lang = 'en-gb'")
    result = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 9282); // flavor/flavour
        return {
            headword: wordHeadword(w),
            example: wordExample(w),
            aliasHit: VOCAB_BY_WORD.get('flavour') === w,
            rawStillUS: w.w,
        };
    }""")
    assert result["headword"] == "flavour", result
    assert "flavour" in result["example"], result
    assert result["aliasHit"] is True, result
    assert result["rawStillUS"] == "flavor", result
    page.evaluate("state.lang = 'en'")
    assert page.evaluate("wordHeadword(VOCAB_DATA.find(x => x.pk === 9282))") == "flavor"
    b.close()
print("Task 2 verified OK")
```

Expected output: `Task 2 verified OK`.

- [ ] **Step 5: Commit**

```bash
git add "VocabLarry/vocablarry.html"
git commit -m "feat(vocab): add WORD_GB UK spelling overrides + display accessors"
```

---

### Task 3: Wire accessors into vocabulary display and search

**Files:**
- Modify: `VocabLarry/vocablarry.html` — `matchesFilters()` (~line 9741), `renderWordGrid()` (~lines 14943-14983), Word/Examples page render (~lines 15227-15236), `openWordModal()` (~lines 15925-15938), `renderWordPicker()` (~lines 15549-15587), `testSelectAllWords` handler (~line 16037)

**Interfaces:**
- Consumes: `wordHeadword`, `wordDef`, `wordExample`, `wordSynonyms`, `wordAntonyms` (Task 2).
- Produces: nothing new for later tasks — this task only changes what's rendered/searched.

- [ ] **Step 1: `matchesFilters()` search predicate**

Find:

```js
  if (f.learned === "learned" && !isLearned(word.w)) return false;
  if (f.learned === "little"  && !isLittle(word.w)) return false;
  if (f.learned === "unlearned" && isAnyLearned(word.w)) return false;
  if (f.search){
    const q = f.search.toLowerCase();
    const hay = [word.w, wordDef(word), ...(word.syn||[]), ...(word.ant||[])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
```

Replace with (learned-state checks stay on raw `word.w` — they're `learnMap` keys, not display):

```js
  if (f.learned === "learned" && !isLearned(word.w)) return false;
  if (f.learned === "little"  && !isLittle(word.w)) return false;
  if (f.learned === "unlearned" && isAnyLearned(word.w)) return false;
  if (f.search){
    const q = f.search.toLowerCase();
    const hay = [wordHeadword(word), wordDef(word), ...(wordSynonyms(word)||[]), ...(wordAntonyms(word)||[])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
```

- [ ] **Step 2: `renderWordGrid()` inline filter + card markup**

Find:

```js
  const allWords = baseWords.filter(w => {
    if (f.cefr !== "all" && w.cefr !== f.cefr) return false;
    if (f.learned === "learned" && !isLearned(w.w)) return false;
    if (f.learned === "little"  && !isLittle(w.w)) return false;
    if (f.learned === "unlearned" && isAnyLearned(w.w)) return false;
    if (f.search){
      const q = f.search.toLowerCase();
      const hay = [w.w, wordDef(w), ...(w.syn||[]), ...(w.ant||[])].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
```

Replace with:

```js
  const allWords = baseWords.filter(w => {
    if (f.cefr !== "all" && w.cefr !== f.cefr) return false;
    if (f.learned === "learned" && !isLearned(w.w)) return false;
    if (f.learned === "little"  && !isLittle(w.w)) return false;
    if (f.learned === "unlearned" && isAnyLearned(w.w)) return false;
    if (f.search){
      const q = f.search.toLowerCase();
      const hay = [wordHeadword(w), wordDef(w), ...(wordSynonyms(w)||[]), ...(wordAntonyms(w)||[])].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
```

Then find:

```js
      <div class="face">
        <div>
          <div class="word">${word.w}</div>
          <div class="pos">${word.pos}</div>
        </div>
        <span class="cefr-badge ${word.cefr}">${word.cefr}</span>
      </div>
      <div class="reveal">
        <span class="dbg-ctl" data-dbg-word-ctl>
          <button type="button" class="dbg-edit-word">✎</button>
          <button type="button" class="dbg-delete-word">✕</button>
        </span>
        <div class="rdef">${wordDef(word)}</div>
        ${word.syn && word.syn.length ? `<div class="rrow"><b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(word.syn)}</div>` : ""}
        ${word.ant && word.ant.length ? `<div class="rrow"><b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(word.ant)}</div>` : ""}
        <div class="rex">${word.ex}</div>
```

Replace with:

```js
      <div class="face">
        <div>
          <div class="word">${wordHeadword(word)}</div>
          <div class="pos">${word.pos}</div>
        </div>
        <span class="cefr-badge ${word.cefr}">${word.cefr}</span>
      </div>
      <div class="reveal">
        <span class="dbg-ctl" data-dbg-word-ctl>
          <button type="button" class="dbg-edit-word">✎</button>
          <button type="button" class="dbg-delete-word">✕</button>
        </span>
        <div class="rdef">${wordDef(word)}</div>
        ${word.syn && word.syn.length ? `<div class="rrow"><b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(wordSynonyms(word))}</div>` : ""}
        ${word.ant && word.ant.length ? `<div class="rrow"><b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(wordAntonyms(word))}</div>` : ""}
        <div class="rex">${wordExample(word)}</div>
```

(The `word.syn && word.syn.length` / `word.ant && word.ant.length` existence checks stay on the raw array — `WORD_GB` never changes an array's length, only its content, so the raw check is equivalent and simpler.)

- [ ] **Step 3: Word/Examples page markup**

Find:

```js
      <div class="ex-head">
        <span class="ex-word">${word.w}</span>
        <span class="ex-pos">${word.pos}</span>
        <span class="cefr-badge ${word.cefr}">${word.cefr}</span>
      </div>
      <div class="ex-sentence">${word.ex}</div>`;
    item.classList.add("interactive");
    item.insertAdjacentHTML("beforeend", `<div class="ex-reveal">
      <div class="rdef">${wordDef(word)}</div>
      ${word.syn && word.syn.length ? `<div class="rrow"><b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(word.syn)}</div>` : ""}
      ${word.ant && word.ant.length ? `<div class="rrow"><b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(word.ant)}</div>` : ""}
    </div>`);
```

Replace with:

```js
      <div class="ex-head">
        <span class="ex-word">${wordHeadword(word)}</span>
        <span class="ex-pos">${word.pos}</span>
        <span class="cefr-badge ${word.cefr}">${word.cefr}</span>
      </div>
      <div class="ex-sentence">${wordExample(word)}</div>`;
    item.classList.add("interactive");
    item.insertAdjacentHTML("beforeend", `<div class="ex-reveal">
      <div class="rdef">${wordDef(word)}</div>
      ${word.syn && word.syn.length ? `<div class="rrow"><b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(wordSynonyms(word))}</div>` : ""}
      ${word.ant && word.ant.length ? `<div class="rrow"><b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(wordAntonyms(word))}</div>` : ""}
    </div>`);
```

- [ ] **Step 4: Word detail modal (`openWordModal`)**

Find:

```js
  document.getElementById("modal-word").textContent = word.w;
  document.getElementById("modal-pos").textContent = word.pos;
  const cefrEl = document.getElementById("modal-cefr");
  cefrEl.textContent = word.cefr; cefrEl.className = `cefr-badge ${word.cefr}`;
  document.getElementById("modal-def").textContent = wordDef(word);
  const synEl = document.getElementById("modal-syn");
  synEl.innerHTML = word.syn && word.syn.length ? `<b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(word.syn)}` : "";
  synEl.style.display = word.syn && word.syn.length ? "" : "none";
  wireWordXrefs(synEl);
  const antEl = document.getElementById("modal-ant");
  antEl.innerHTML = word.ant && word.ant.length ? `<b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(word.ant)}` : "";
  antEl.style.display = word.ant && word.ant.length ? "" : "none";
  wireWordXrefs(antEl);
  document.getElementById("modal-ex").innerHTML = word.ex;
```

Replace with:

```js
  document.getElementById("modal-word").textContent = wordHeadword(word);
  document.getElementById("modal-pos").textContent = word.pos;
  const cefrEl = document.getElementById("modal-cefr");
  cefrEl.textContent = word.cefr; cefrEl.className = `cefr-badge ${word.cefr}`;
  document.getElementById("modal-def").textContent = wordDef(word);
  const synEl = document.getElementById("modal-syn");
  synEl.innerHTML = word.syn && word.syn.length ? `<b>${t("vocab.synonyms")}:</b> ${linkedWordsHtml(wordSynonyms(word))}` : "";
  synEl.style.display = word.syn && word.syn.length ? "" : "none";
  wireWordXrefs(synEl);
  const antEl = document.getElementById("modal-ant");
  antEl.innerHTML = word.ant && word.ant.length ? `<b>${t("vocab.antonyms")}:</b> ${linkedWordsHtml(wordAntonyms(word))}` : "";
  antEl.style.display = word.ant && word.ant.length ? "" : "none";
  wireWordXrefs(antEl);
  document.getElementById("modal-ex").innerHTML = wordExample(word);
```

- [ ] **Step 5: `renderWordPicker()` search predicate + chip label**

Find:

```js
  const allWords = VOCAB_DATA.filter(w => {
    if (!wordMatchesHeadline(w.cefr, hl)) return false;
    if (wc !== "all" && w.cefr !== wc) return false;
    const cat = CAT_MAP[w.cat];
    if (ws !== "all" && (!cat || cat.section !== ws)) return false;
    if (wcat !== "all" && w.cat !== wcat) return false;
    if (wl === "learned" && !isLearned(w.w)) return false;
    if (wl === "unlearned" && isAnyLearned(w.w)) return false;
    if (!q) return true;
    return [w.w, wordDef(w), ...(w.syn||[]), ...(w.ant||[])].join(" ").toLowerCase().includes(q);
  });
```

Replace with:

```js
  const allWords = VOCAB_DATA.filter(w => {
    if (!wordMatchesHeadline(w.cefr, hl)) return false;
    if (wc !== "all" && w.cefr !== wc) return false;
    const cat = CAT_MAP[w.cat];
    if (ws !== "all" && (!cat || cat.section !== ws)) return false;
    if (wcat !== "all" && w.cat !== wcat) return false;
    if (wl === "learned" && !isLearned(w.w)) return false;
    if (wl === "unlearned" && isAnyLearned(w.w)) return false;
    if (!q) return true;
    return [wordHeadword(w), wordDef(w), ...(wordSynonyms(w)||[]), ...(wordAntonyms(w)||[])].join(" ").toLowerCase().includes(q);
  });
```

Then find:

```js
    const sel = state.test.selectedWords.has(w.w);
    btn.className = "chip" + (sel ? " active" : "");
    btn.innerHTML = `${w.w} <span class="cefr-badge ${w.cefr}" style="font-size:.6rem;padding:1px 5px;margin-left:3px;vertical-align:middle;">${w.cefr}</span>`;
```

Replace with (Set membership stays on raw `w.w` — it's the selection identity key):

```js
    const sel = state.test.selectedWords.has(w.w);
    btn.className = "chip" + (sel ? " active" : "");
    btn.innerHTML = `${wordHeadword(w)} <span class="cefr-badge ${w.cefr}" style="font-size:.6rem;padding:1px 5px;margin-left:3px;vertical-align:middle;">${w.cefr}</span>`;
```

- [ ] **Step 6: `testSelectAllWords` search predicate**

Find:

```js
    if (wl === "learned" && !isLearned(w.w)) return false;
    if (wl === "unlearned" && isAnyLearned(w.w)) return false;
    if (!q) return true;
    return [w.w, wordDef(w), ...(w.syn||[]), ...(w.ant||[])].join(" ").toLowerCase().includes(q);
  }).forEach(w => state.test.selectedWords.add(w.w));
```

Replace with:

```js
    if (wl === "learned" && !isLearned(w.w)) return false;
    if (wl === "unlearned" && isAnyLearned(w.w)) return false;
    if (!q) return true;
    return [wordHeadword(w), wordDef(w), ...(wordSynonyms(w)||[]), ...(wordAntonyms(w)||[])].join(" ").toLowerCase().includes(q);
  }).forEach(w => state.test.selectedWords.add(w.w));
```

- [ ] **Step 7: Verify with Playwright**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("window.VOCAB_DATA && VOCAB_DATA.length > 0")
    page.evaluate("state.lang = 'en-gb'; localStorage.setItem('ivm_lang','en-gb')")
    page.reload()
    page.wait_for_function("window.VOCAB_DATA && VOCAB_DATA.length > 0")
    # flavor/flavour is category "food-and-drink" or similar — open its word modal directly
    page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 9282);
        openWordModal(w);
    }""")
    modal_word = page.locator("#modal-word").text_content()
    modal_ex = page.locator("#modal-ex").inner_html()
    assert modal_word == "flavour", modal_word
    assert "flavour" in modal_ex, modal_ex
    # Cross-ref: word 5692 "enthusiast" has antonym "sceptic" (unchanged form,
    # since WORD_GB only overrides its own antonyms list to ["critic","sceptic",...]
    # — confirm the antonym cross-ref list renders and, for a word whose synonym
    # IS a UK-renamed headword (5560 "cynical" -> synonym "sceptical"), the
    # cross-ref link resolves via the VOCAB_BY_WORD alias.
    page.evaluate("""() => { openWordModal(VOCAB_DATA.find(x => x.pk === 5560)); }""")
    xref = page.locator("#modal-syn .word-xref", has_text="sceptical")
    assert xref.count() == 1, "sceptical cross-ref link missing (alias fix not working)"
    b.close()
print("Task 3 verified OK")
```

Expected output: `Task 3 verified OK`.

- [ ] **Step 8: Run the pytest suite (regression check — this task is frontend-only, should be unaffected)**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests -q`
Expected: `85 passed`

- [ ] **Step 9: Commit**

```bash
git add "VocabLarry/vocablarry.html"
git commit -m "feat(vocab): show UK spelling in word cards, search, and word detail modal"
```

---

### Task 4: Wire accessors into vocab quiz generation and grading

**Files:**
- Modify: `VocabLarry/vocablarry.html` — `buildQuestion()` (~line 15396), `buildGapQuestion()` (~line 15432), quiz feedback rendering (~line 15818)

**Interfaces:**
- Consumes: `wordHeadword`, `wordDef`, `wordExample`, `wordSynonyms`, `wordAntonyms` (Task 2).
- Produces: nothing new for later tasks.

Quiz grading here is MCQ-based: `isCorrect = selectedBtn.textContent === q.correct`, and both `q.correct` and `q.options` are built from the same word in the same function call. As long as both go through the same accessor consistently, grading stays correct regardless of which language is active — this task is about display consistency, not grading logic changes. Distractor-pool *selection* logic (which other words are eligible distractors) intentionally stays on raw fields — it doesn't matter which spelling is used internally to pick candidates, only what's shown matters.

- [ ] **Step 1: `buildQuestion()`**

Find:

```js
function buildQuestion(word, mode){
  const others = VOCAB_DATA.filter(w => w.w !== word.w);
  // promptKey, not the translated text itself, is stored on the question —
  // all of this test's questions are built once up front at test-start, so
  // a baked-in string would stay frozen in whatever language was active at
  // that moment; renderTestQuestion() resolves it fresh via t() every
  // render, so a mid-quiz language switch actually takes effect.
  let promptKey, text, correct, options;
  switch(mode){
    case "word":
      promptKey = "qPrompt.word";
      text = wordDef(word);
      correct = word.w;
      options = buildOptions(correct, others, w => w.w);
      break;
    case "synonym":
      promptKey = "qPrompt.synonym";
      text = `${word.w} <span class="qpos">(${word.pos})</span>`;
      correct = capitalize(word.syn[Math.floor(Math.random()*word.syn.length)]);
      options = buildOptions(correct, others.filter(w => w.w !== correct), w => w.w);
      break;
    case "antonym":
      promptKey = "qPrompt.antonym";
      text = `${word.w} <span class="qpos">(${word.pos})</span>`;
      correct = capitalize(word.ant[Math.floor(Math.random()*word.ant.length)]);
      options = buildOptions(correct, others.filter(w => w.w !== correct), w => w.w);
      break;
    default:
      promptKey = "qPrompt.definition";
      text = `${word.w} <span class="qpos">(${word.pos})</span>`;
      correct = wordDef(word);
      options = buildOptions(correct, others, w => wordDef(w));
  }
  return {promptKey, text, options, correct, word};
}
```

Replace with:

```js
function buildQuestion(word, mode){
  const others = VOCAB_DATA.filter(w => w.w !== word.w);
  // promptKey, not the translated text itself, is stored on the question —
  // all of this test's questions are built once up front at test-start, so
  // a baked-in string would stay frozen in whatever language was active at
  // that moment; renderTestQuestion() resolves it fresh via t() every
  // render, so a mid-quiz language switch actually takes effect.
  let promptKey, text, correct, options;
  switch(mode){
    case "word":
      promptKey = "qPrompt.word";
      text = wordDef(word);
      correct = wordHeadword(word);
      options = buildOptions(correct, others, w => wordHeadword(w));
      break;
    case "synonym":
      promptKey = "qPrompt.synonym";
      text = `${wordHeadword(word)} <span class="qpos">(${word.pos})</span>`;
      correct = capitalize(wordSynonyms(word)[Math.floor(Math.random()*wordSynonyms(word).length)]);
      options = buildOptions(correct, others.filter(w => wordHeadword(w) !== correct), w => wordHeadword(w));
      break;
    case "antonym":
      promptKey = "qPrompt.antonym";
      text = `${wordHeadword(word)} <span class="qpos">(${word.pos})</span>`;
      correct = capitalize(wordAntonyms(word)[Math.floor(Math.random()*wordAntonyms(word).length)]);
      options = buildOptions(correct, others.filter(w => wordHeadword(w) !== correct), w => wordHeadword(w));
      break;
    default:
      promptKey = "qPrompt.definition";
      text = `${wordHeadword(word)} <span class="qpos">(${word.pos})</span>`;
      correct = wordDef(word);
      options = buildOptions(correct, others, w => wordDef(w));
  }
  return {promptKey, text, options, correct, word};
}
```

- [ ] **Step 2: `buildGapQuestion()` — only its final two lines change**

Find:

```js
  const options = buildOptions(word.w, distractorPool, w => w.w);
  const text = word.gap.replace("___", `<span class="gapblank">_____</span>`);
  return {text, options, correct:word.w, word, promptKey};
```

Replace with (`word.gap` itself has zero UK overrides in the current dataset — confirmed by the audit — so it's left as-is; no `wordGap()` accessor exists or is needed for Phase 1):

```js
  const options = buildOptions(wordHeadword(word), distractorPool, w => wordHeadword(w));
  const text = word.gap.replace("___", `<span class="gapblank">_____</span>`);
  return {text, options, correct: wordHeadword(word), word, promptKey};
```

- [ ] **Step 3: Quiz feedback message**

Find:

```js
  if (q.type === "gap"){
    const fullEx = q.word.ex.replace(/<\/?em>/g, "");
    feedback = isCorrect
      ? `<b>${t("testUi.correct")}</b> ${q.word.w} — ${wordDef(q.word)}<br>${fullEx}`
      : `<b>${t("testUi.notQuite")}</b> ${t("testUi.theAnswerIs").replace("{answer}", q.correct)} — ${wordDef(q.word)}<br>${fullEx}`;
  } else {
    feedback = isCorrect
      ? `<b>${t("testUi.correct")}</b> ${q.word.w} — ${wordDef(q.word)}`
      : `<b>${t("testUi.notQuite")}</b> ${q.word.w} — ${wordDef(q.word)}`;
  }
```

Replace with:

```js
  if (q.type === "gap"){
    const fullEx = wordExample(q.word).replace(/<\/?em>/g, "");
    feedback = isCorrect
      ? `<b>${t("testUi.correct")}</b> ${wordHeadword(q.word)} — ${wordDef(q.word)}<br>${fullEx}`
      : `<b>${t("testUi.notQuite")}</b> ${t("testUi.theAnswerIs").replace("{answer}", q.correct)} — ${wordDef(q.word)}<br>${fullEx}`;
  } else {
    feedback = isCorrect
      ? `<b>${t("testUi.correct")}</b> ${wordHeadword(q.word)} — ${wordDef(q.word)}`
      : `<b>${t("testUi.notQuite")}</b> ${wordHeadword(q.word)} — ${wordDef(q.word)}`;
  }
```

- [ ] **Step 4: Verify with Playwright — run a "word" mode quiz question in UK mode on a headword-changed word**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("window.VOCAB_DATA && VOCAB_DATA.length > 0")
    page.evaluate("state.lang = 'en-gb'")
    q = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 9282); // flavor/flavour
        return buildQuestion(w, 'word');
    }""")
    assert q["correct"] == "flavour", q
    assert "flavour" in q["options"], q
    assert "flavor" not in q["options"], q  # no leftover US spelling mixed in
    gq = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 8732); // endeavor/endeavour, has a .gap sentence? check first
        return w.gap ? buildGapQuestion(w) : null;
    }""")
    b.close()
print("Task 4 verified OK, sample question:", q)
```

Expected output: `Task 4 verified OK, ...` with no assertion errors. (The `gq` check is informational only — not every word has a `.gap` sentence; if `gq` is `None` for pk 8732, that's expected and fine.)

- [ ] **Step 5: Run the pytest suite (regression check)**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests -q`
Expected: `85 passed`

- [ ] **Step 6: Commit**

```bash
git add "VocabLarry/vocablarry.html"
git commit -m "feat(vocab): show UK spelling in vocab quiz questions and feedback"
```

---

### Task 5: Full end-to-end verification pass

**Files:** none (verification only)

**Interfaces:**
- Consumes: everything from Tasks 1-4.
- Produces: nothing — this is the spec's acceptance-criteria checkpoint before the feature is considered done.

- [ ] **Step 1: Run the full Playwright acceptance script**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("window.VOCAB_DATA && VOCAB_DATA.length > 0")

    # 1. Switch to English (UK) via the real UI, not page.evaluate
    page.click("#langToggle")
    page.click("#langMenu [data-lang='en-gb']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en-gb"

    # 2. A headword-changed word (flavour) shows correctly via search on
    #    the Vocabulary > Category > browse search box
    page.evaluate("goToPage('list')")
    page.wait_for_selector("#page-list.active", state="attached")

    # 3. Word detail modal for an example/def-only change (macroeconomic, pk 7023)
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 7023))")
    assert "analysed" in page.locator("#modal-ex").inner_html()
    page.evaluate("closeWordModal()")

    # 4. An ambiguous-pair word (protagonist, pk 5712, "story" sense) must NOT
    #    have been changed to "storey" — confirms the hand-reviewed decision held.
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 5712))")
    def_text = page.locator("#modal-def").text_content()
    assert "storey" not in def_text, def_text
    assert "story" in def_text, def_text
    page.evaluate("closeWordModal()")

    # 5. "check" ambiguous word (pk 9040, verb sense) must stay "check", not "cheque"
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9040))")
    assert page.locator("#modal-word").text_content() == "check"
    page.evaluate("closeWordModal()")

    # 6. "program" word that DOES change (mentorship, pk 7647)
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 7647))")
    assert "programme" in page.locator("#modal-ex").inner_html()
    page.evaluate("closeWordModal()")

    # 7. "program" word that must NOT change (codec, pk 8521 - computing sense)
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 8521))")
    assert "programme" not in page.locator("#modal-def").text_content()
    page.evaluate("closeWordModal()")

    # 8. Quiz: headword-changed word accepted correctly in UK mode
    q = page.evaluate("buildQuestion(VOCAB_DATA.find(x => x.pk === 9282), 'word')")
    assert q["correct"] == "flavour"

    # 9. Switch back to English (US): everything reverts
    page.click("#langToggle")
    page.click("#langMenu [data-lang='en']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en"
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9282))")
    assert page.locator("#modal-word").text_content() == "flavor"
    page.evaluate("closeWordModal()")

    # 10. Vietnamese mode is unaffected by any of this
    page.click("#langToggle")
    page.click("#langMenu [data-lang='vi']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "vi"

    b.close()
print("Task 5 — full acceptance pass OK")
```

Expected output: `Task 5 — full acceptance pass OK`, no assertion errors.

- [ ] **Step 2: Run the full pytest suite one more time**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests -q`
Expected: `85 passed`

- [ ] **Step 3: Stop the dev server**

Find and kill whatever process is listening on port 8000 (started in Task 1, Step 2).

- [ ] **Step 4: Report status — do not push**

This plan's commits are local only. Per this project's standing rule, do not `git push elw main` and do not regenerate `VocabLarry/vocablarry-deploy.zip` until the user explicitly asks for it in the conversation where this plan is executed.
