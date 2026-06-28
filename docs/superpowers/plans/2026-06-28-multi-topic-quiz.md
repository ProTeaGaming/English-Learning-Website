# Multi-Topic Quiz Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to select multiple topic categories simultaneously on the quiz setup screen; questions are drawn from the combined word pool of all selected categories.

**Architecture:** All changes are confined to `vocab-master.html`. The test filter object switches `cat: string` to `cats: Set<string>`. `matchesFilters` gains a Set-aware branch that activates only when `f.cats` is present, leaving Browse/Examples pages unchanged. `buildCategoryChips` detects which mode it's in (`f.cats` vs `f.cat`) and toggles vs replaces accordingly.

**Tech Stack:** Vanilla JS, inline HTML file — no build step, no framework.

## Global Constraints

- One file only: `ielts-vocab-master/Python/Django/vocab-master.html`
- Do NOT change Browse or Examples filter objects — they keep `f.cat: string`
- Do NOT add new dependencies or CSS classes
- Verify in browser by running `python manage.py runserver` from `ielts-vocab-master/Python/Django/` and opening `http://127.0.0.1:8000`

---

### Task 1: State initialisation and applyBrowseFiltersToTest

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html:3061` (state.test.filters)
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html:3127,3134` (applyBrowseFiltersToTest)

**Interfaces:**
- Produces: `state.test.filters.cats` — a `Set<string>` (empty = all categories); `f.cat` is removed from `state.test.filters`

- [ ] **Step 1: Update `state.test` initialisation**

Find this block (around line 3057):
```js
state.test = {
  mode: "quiz",
  quizMode: "definition",
  count: 10,
  filters: {headline:"all", section:"all", cat:"all", cefr:"all", learned:"all"},
  questions: [], idx: 0, score: 0,
};
```

Replace with:
```js
state.test = {
  mode: "quiz",
  quizMode: "definition",
  count: 10,
  filters: {headline:"all", section:"all", cats: new Set(), cefr:"all", learned:"all"},
  questions: [], idx: 0, score: 0,
};
```

- [ ] **Step 2: Update `applyBrowseFiltersToTest`**

Find this function (around line 3121):
```js
function applyBrowseFiltersToTest(){
  if (catState.cat){
    const cat = ALL_CATEGORIES.find(c => c.id === catState.cat);
    const hl = cat ? (SECTION_HEADLINES[cat.section] || "all") : "all";
    state.test.filters.headline = hl;
    state.test.filters.section = hl === "cefr" ? "all" : (cat && cat.section ? cat.section : "all");
    state.test.filters.cat = catState.cat;
    state.test.filters.cefr = catState.cefr;
    state.test.filters.learned = catState.learned === "little" ? "unlearned" : catState.learned;
  } else {
    state.test.filters.headline = browseState.headline;
    state.test.filters.section = browseState.headline === "cefr" ? "all" : browseState.section;
    state.test.filters.cefr = browseState.cefr;
    state.test.filters.cat = "all";
    state.test.filters.learned = "all";
  }
}
```

Replace with:
```js
function applyBrowseFiltersToTest(){
  if (catState.cat){
    const cat = ALL_CATEGORIES.find(c => c.id === catState.cat);
    const hl = cat ? (SECTION_HEADLINES[cat.section] || "all") : "all";
    state.test.filters.headline = hl;
    state.test.filters.section = hl === "cefr" ? "all" : (cat && cat.section ? cat.section : "all");
    state.test.filters.cats = new Set([catState.cat]);
    state.test.filters.cefr = catState.cefr;
    state.test.filters.learned = catState.learned === "little" ? "unlearned" : catState.learned;
  } else {
    state.test.filters.headline = browseState.headline;
    state.test.filters.section = browseState.headline === "cefr" ? "all" : browseState.section;
    state.test.filters.cefr = browseState.cefr;
    state.test.filters.cats = new Set();
    state.test.filters.learned = "all";
  }
}
```

- [ ] **Step 3: Verify no console errors**

Start the server and open `http://127.0.0.1:8000`. Open DevTools → Console. Navigate to the Quiz page. Confirm no errors. The quiz pool count should still show (the filter renders before Task 2 is done, so numbers may be off — that's expected).

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/Python/Django/vocab-master.html
git commit -m "feat: replace cat string with cats Set in test filters"
```

---

### Task 2: matchesFilters — Set-aware category check

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html:1683-1702`

**Interfaces:**
- Consumes: `state.test.filters.cats` — `Set<string>` from Task 1
- Produces: `matchesFilters(word, f)` — returns `false` when `f.cats` is non-empty and `word.cat` is not in the set (handles CEFR virtual cats too)

- [ ] **Step 1: Update `matchesFilters`**

Find this block (around line 1683):
```js
function matchesFilters(word, f){
  const cat = CAT_MAP[word.cat];
  if (f.section !== "all" && cat && cat.section !== f.section) return false;
  if (f.cat !== "all"){
    const cefrLevel = CEFR_CAT_LEVEL[f.cat];
    if (cefrLevel){
      if (word.cefr !== cefrLevel) return false;
    } else if (word.cat !== f.cat) return false;
  }
  if (f.cefr !== "all" && word.cefr !== f.cefr) return false;
  if (f.learned === "learned" && !isLearned(word.w)) return false;
  if (f.learned === "little"  && !isLittle(word.w)) return false;
  if (f.learned === "unlearned" && isAnyLearned(word.w)) return false;
  if (f.search){
    const q = f.search.toLowerCase();
    const hay = [word.w, word.def, ...(word.syn||[]), ...(word.ant||[])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}
```

Replace with:
```js
function matchesFilters(word, f){
  const cat = CAT_MAP[word.cat];
  if (f.section !== "all" && cat && cat.section !== f.section) return false;
  if (f.cats) {
    // Test page: multi-select Set (empty = all)
    if (f.cats.size > 0) {
      let matched = false;
      for (const catId of f.cats) {
        const cefrLevel = CEFR_CAT_LEVEL[catId];
        if (cefrLevel ? word.cefr === cefrLevel : word.cat === catId) { matched = true; break; }
      }
      if (!matched) return false;
    }
  } else if (f.cat !== "all") {
    // Browse/Examples pages: single-select string
    const cefrLevel = CEFR_CAT_LEVEL[f.cat];
    if (cefrLevel){
      if (word.cefr !== cefrLevel) return false;
    } else if (word.cat !== f.cat) return false;
  }
  if (f.cefr !== "all" && word.cefr !== f.cefr) return false;
  if (f.learned === "learned" && !isLearned(word.w)) return false;
  if (f.learned === "little"  && !isLittle(word.w)) return false;
  if (f.learned === "unlearned" && isAnyLearned(word.w)) return false;
  if (f.search){
    const q = f.search.toLowerCase();
    const hay = [word.w, word.def, ...(word.syn||[]), ...(word.ant||[])].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  return true;
}
```

- [ ] **Step 2: Verify filter count is correct**

Reload `http://127.0.0.1:8000`, go to Quiz. The filter count should show the full word pool (since `cats` is an empty Set = all). Browse and Examples pages should still filter correctly by single category.

- [ ] **Step 3: Commit**

```bash
git add ielts-vocab-master/Python/Django/vocab-master.html
git commit -m "feat: matchesFilters supports f.cats Set for multi-topic test filter"
```

---

### Task 3: Toggle chips UI and clear button

**Files:**
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html:1770-1802` (buildCategoryChips)
- Modify: `ielts-vocab-master/Python/Django/vocab-master.html:1849-1852` (clear button in initTopicFilters)

**Interfaces:**
- Consumes: `f.cats` Set from Task 1, `matchesFilters` from Task 2
- Produces: Category chips that toggle on/off when clicked on the quiz page; "All Categories" chip clears the Set; Browse/Examples pages unchanged

- [ ] **Step 1: Update `buildCategoryChips` for toggle behaviour**

Find this function (around line 1770):
```js
function buildCategoryChips(container, f, onChange){
  const hl = f.headline;
  let cats;
  if (hl === "cefr"){
    cats = CEFR_CATEGORIES;
  } else {
    cats = hl === undefined || hl === "all"
      ? CATEGORIES
      : CATEGORIES.filter(c => SECTION_HEADLINES[c.section] === hl);
    cats = cats.filter(c => f.section==="all" || c.section===f.section);
  }
  const allChip = document.createElement("button");
  allChip.className = "chip" + (f.cat==="all" ? " active" : "");
  allChip.dataset.cat = "all";
  allChip.textContent = "All Categories";

  const optionChips = cats.map(c => {
    const chip = document.createElement("button");
    chip.className = `chip t-${c.theme}` + (f.cat===c.id ? " active" : "");
    chip.dataset.cat = c.id;
    chip.textContent = `${c.icon} ${c.name}`;
    return chip;
  });

  [allChip, ...optionChips].forEach(chip => {
    chip.addEventListener("click", () => {
      f.cat = chip.dataset.cat;
      onChange();
    });
  });

  renderExpandableChips(container, allChip, optionChips);
}
```

Replace with:
```js
function buildCategoryChips(container, f, onChange){
  const hl = f.headline;
  const multiSelect = f.cats !== undefined;
  let cats;
  if (hl === "cefr"){
    cats = CEFR_CATEGORIES;
  } else {
    cats = hl === undefined || hl === "all"
      ? CATEGORIES
      : CATEGORIES.filter(c => SECTION_HEADLINES[c.section] === hl);
    cats = cats.filter(c => f.section==="all" || c.section===f.section);
  }
  const allChip = document.createElement("button");
  allChip.className = "chip" + (multiSelect ? (f.cats.size===0 ? " active" : "") : (f.cat==="all" ? " active" : ""));
  allChip.dataset.cat = "all";
  allChip.textContent = "All Categories";

  const optionChips = cats.map(c => {
    const chip = document.createElement("button");
    chip.className = `chip t-${c.theme}` + (multiSelect ? (f.cats.has(c.id) ? " active" : "") : (f.cat===c.id ? " active" : ""));
    chip.dataset.cat = c.id;
    chip.textContent = `${c.icon} ${c.name}`;
    return chip;
  });

  [allChip, ...optionChips].forEach(chip => {
    chip.addEventListener("click", () => {
      if (multiSelect) {
        if (chip.dataset.cat === "all") {
          f.cats = new Set();
        } else {
          if (f.cats.has(chip.dataset.cat)) f.cats.delete(chip.dataset.cat);
          else f.cats.add(chip.dataset.cat);
        }
      } else {
        f.cat = chip.dataset.cat;
      }
      onChange();
    });
  });

  renderExpandableChips(container, allChip, optionChips);
}
```

- [ ] **Step 2: Update the clear button in `initTopicFilters`**

Find this block (around line 1849):
```js
  document.getElementById(`${prefix}ClearFilters`).addEventListener("click", () => {
    f.section = "all"; f.cat = "all"; f.cefr = "all"; f.learned = "all";
    if (f.headline !== undefined) f.headline = "all";
    renderTopicFilters(prefix, f, getPool, unitLabel);
  });
```

Replace with:
```js
  document.getElementById(`${prefix}ClearFilters`).addEventListener("click", () => {
    f.section = "all"; f.cefr = "all"; f.learned = "all";
    if (f.headline !== undefined) f.headline = "all";
    if (f.cats !== undefined) f.cats = new Set();
    else f.cat = "all";
    renderTopicFilters(prefix, f, getPool, unitLabel);
  });
```

- [ ] **Step 3: Manual verification — multi-select**

Reload `http://127.0.0.1:8000` and go to the Quiz page.

Check each behaviour:
1. Click one category chip → it highlights, word count updates to that topic's words only
2. Click a second category chip → both highlight, word count = combined pool of both topics
3. Click a highlighted chip again → it deselects, count drops back
4. Click "All Categories" → all chips deselect, count returns to full pool
5. Click "Clear filters" → same as All Categories (everything resets)
6. Navigate to Browse → single-select still works normally on Browse/Examples pages
7. Start a quiz with 2 topics selected → questions span both topics

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/Python/Django/vocab-master.html
git commit -m "feat: multi-topic quiz selection via toggle chips"
```
