# Mobile Hamburger Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Below 640px, replace the wrapping nav-tab row with a hamburger-triggered dropdown for top-level navigation, and move each section's Category/Word/Test switcher into the page content as a button row.

**Architecture:** Pure additive changes to the single-file SPA `VocabLarry/vocab-master.html` — new markup (hamburger button + panel, per-page switcher bars) gated by one CSS media query, plus JS that reuses the *existing* `.nav-dropdown-item` click handlers and `goToPage()` active-state logic rather than duplicating navigation behavior. No backend/Python changes.

**Tech Stack:** Vanilla JS, CSS custom properties (`[data-theme]`), the existing `positionDropdown()` helper (added earlier this session for `#langMenu`/`#userMenu`), Playwright (Python) for verification — this project has no JS unit-test framework; verification throughout is a Playwright script asserting real rendered/computed state, matching the pattern already used all session.

## Global Constraints

- Single breakpoint: `@media (max-width: 640px)`. No intermediate states.
- Tablet (768px+) and desktop nav, and everything in `.topbar-right` (theme/language/progress/profile/sign-in), are unchanged at every width — do not touch their markup, CSS, or JS.
- No new navigation logic may be written for page transitions — new UI must trigger the existing `.nav-dropdown-item` click handlers (`vocab-master.html:13216-13225`) and `goToPage()` (`vocab-master.html:13192-13214`) so behavior (including the Test page's `applyBrowseFiltersToTest()` special case) can never drift between desktop and phone.
- Reuse the existing `.chip` class (`vocab-master.html:366`) for switcher buttons and the existing `positionDropdown()` helper (`vocab-master.html:13285`) for the hamburger panel — do not reinvent either.
- Every new interactive element that shows English text must carry a `data-i18n` attribute pointing at an **existing** key (`nav.home`, `nav.vocabulary`, `nav.grammar`, `nav.reading`, `nav.writing`, `nav.listening`, `nav.speaking`, `nav.category`, `nav.word`, `nav.test`) — no new i18n keys needed, `applyI18n()` already sweeps all `[data-i18n]` elements on the page.
- Verify every task with a Playwright script run against the local dev server (`http://127.0.0.1:8000/`, already running throughout this session) — take exact selectors/coordinates from real output, not assumptions.
- After all tasks pass, run `pytest` (backend regression) and the `node --check`-equivalent script-parse check used all session.

---

### Task 1: Hamburger icon, button, and hiding the tab row below 640px

**Files:**
- Modify: `VocabLarry/vocab-master.html:1342` (icon sprite — add new `<symbol>` right after `i-mark`)
- Modify: `VocabLarry/vocab-master.html:1470-1471` (topbar-left — insert hamburger button after `.brand`)
- Modify: `VocabLarry/vocab-master.html:98` (`.tabs` rule — add hide-below-640px)

**Interfaces:**
- Produces: `#mobileNavToggle` button (exists in DOM at every width; visible only <640px), `<symbol id="i-menu">` in the icon sprite.

- [ ] **Step 1: Write the verification script (expect it to fail — element doesn't exist yet)**

Create `C:\Users\TGC\AppData\Local\Temp\claude\D--IT-RELATED-CLAUDE-BOMBASTIC-AI\c5842d5d-621d-4808-9b92-e792d93bc19b\scratchpad\verify_task1_hamburger_visibility.py`:

```python
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    toggle = page.query_selector("#mobileNavToggle")
    assert toggle is not None, "FAIL: #mobileNavToggle does not exist"
    assert page.eval_on_selector("#mobileNavToggle", "el => getComputedStyle(el).display") != "none", \
        "FAIL: #mobileNavToggle should be visible at 375px"
    assert page.eval_on_selector(".tabs", "el => getComputedStyle(el).display") == "none", \
        "FAIL: .tabs should be hidden at 375px"
    print("PASS: 375px — hamburger visible, tabs hidden")
    page.close()

    page2 = browser.new_page(viewport={"width": 768, "height": 1024})
    page2.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    assert page2.eval_on_selector("#mobileNavToggle", "el => getComputedStyle(el).display") == "none", \
        "FAIL: #mobileNavToggle should be hidden at 768px"
    assert page2.eval_on_selector(".tabs", "el => getComputedStyle(el).display") != "none", \
        "FAIL: .tabs should be visible at 768px"
    print("PASS: 768px — hamburger hidden, tabs visible")
    page2.close()

    browser.close()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python <path>/verify_task1_hamburger_visibility.py`
Expected: `AssertionError: FAIL: #mobileNavToggle does not exist`

- [ ] **Step 3: Add the hamburger icon symbol**

In `VocabLarry/vocab-master.html`, immediately after line 1342 (`<symbol id="i-mark" ...>`), insert:

```html
  <symbol id="i-menu" viewBox="0 0 24 24"><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/></symbol>
```

- [ ] **Step 4: Add the hamburger button markup**

In `VocabLarry/vocab-master.html`, replace:

```html
      <div class="brand"><svg class="ico ico-mark" aria-hidden="true"><use href="#i-mark"/></svg><span class="brand-name">Vocab<b>Larry</b></span></div>
      <nav class="tabs">
```

with:

```html
      <div class="brand"><svg class="ico ico-mark" aria-hidden="true"><use href="#i-mark"/></svg><span class="brand-name">Vocab<b>Larry</b></span></div>
      <div class="mobile-nav-chip" id="mobileNavChip">
        <button class="theme-toggle" id="mobileNavToggle" title="Menu" aria-label="Open navigation menu" type="button"><svg class="ico" aria-hidden="true"><use href="#i-menu"/></svg></button>
      </div>
      <nav class="tabs">
```

- [ ] **Step 5: Add the CSS — hide tabs, show hamburger, only below 640px**

In `VocabLarry/vocab-master.html`, find line 98 (`.tabs{display:flex; gap:3px; flex-wrap:wrap;}`) and add immediately after it:

```css
.mobile-nav-chip{display:none; position:relative;}
@media (max-width:640px){
  .tabs{display:none;}
  .mobile-nav-chip{display:block;}
}
```

- [ ] **Step 6: Run the verification script to confirm it passes**

Run: `python <path>/verify_task1_hamburger_visibility.py`
Expected:
```
PASS: 375px — hamburger visible, tabs hidden
PASS: 768px — hamburger hidden, tabs visible
```

- [ ] **Step 7: Parse-check and commit**

```bash
node -e "const fs=require('fs');const html=fs.readFileSync('VocabLarry/vocab-master.html','utf-8');const scripts=[...html.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);let ok=true;scripts.forEach((s,i)=>{try{new Function(s);}catch(e){ok=false;console.log('Error',i,e.message);}});console.log('parsed ok:',ok);"
git add VocabLarry/vocab-master.html
git commit -m "feat(mobile-nav): add hamburger button, hide tab row below 640px"
```

---

### Task 2: Hamburger panel — markup, open/close, positioning, navigation

**Files:**
- Modify: `VocabLarry/vocab-master.html` (panel markup inside `#mobileNavChip`, added in Task 1)
- Modify: `VocabLarry/vocab-master.html` (CSS block near `.mobile-nav-chip`, from Task 1)
- Modify: `VocabLarry/vocab-master.html:~13276` (JS, right after `applyI18n();` and before the existing `langChip` listener — same area `positionDropdown()` already lives)

**Interfaces:**
- Consumes: `positionDropdown(chipId, menuId)` — `vocab-master.html:13285`, signature `(chipId: string, menuId: string) => void`, already reads `document.getElementById(chipId).classList.contains("open")` and positions `menuId` as `position:fixed`. `NAV_SECTIONS` — `vocab-master.html:13174`, `{ [section]: string[] }` mapping each section to its ordered page-id list. `goToPage(pageId: string)` — `vocab-master.html:13192`. `closeNavDropdowns()` — `vocab-master.html:13188`.
- Produces: `#mobileNavMenu` panel with 7 items (`[data-section-btn]`), toggled via `#mobileNavChip.open`.

- [ ] **Step 1: Write the verification script (expect it to fail)**

Create `verify_task2_hamburger_panel.py` in the same scratchpad directory:

```python
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)

    page.click("#mobileNavToggle")
    time.sleep(0.4)
    menu = page.query_selector("#mobileNavMenu")
    assert menu is not None, "FAIL: #mobileNavMenu does not exist"

    items = page.eval_on_selector_all("#mobileNavMenu [data-section-btn]", "els => els.map(e => e.dataset.sectionBtn)")
    expected = ["home", "vocabulary", "grammar", "reading", "writing", "listening", "speaking"]
    assert items == expected, f"FAIL: expected {expected}, got {items}"
    print("PASS: all 7 sections present in order")

    box = page.eval_on_selector("#mobileNavMenu", "el => { const r = el.getBoundingClientRect(); return {left:r.left, right:r.right}; }")
    assert box["left"] >= 0 and box["right"] <= 375, f"FAIL: menu off-screen: {box}"
    print("PASS: menu stays within 375px viewport:", box)

    page.click("#mobileNavMenu [data-section-btn='vocabulary']")
    time.sleep(0.4)
    active_page = page.eval_on_selector(".page.active", "el => el.id")
    assert active_page == "page-list", f"FAIL: expected page-list, got {active_page}"
    print("PASS: tapping Vocabulary navigated to page-list")

    is_open = page.eval_on_selector("#mobileNavChip", "el => el.classList.contains('open')")
    assert not is_open, "FAIL: panel should have closed after selection"
    print("PASS: panel closed after selection")

    browser.close()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python <path>/verify_task2_hamburger_panel.py`
Expected: `AssertionError: FAIL: #mobileNavMenu does not exist`

- [ ] **Step 3: Add the panel markup**

Replace the `#mobileNavChip` block from Task 1:

```html
      <div class="mobile-nav-chip" id="mobileNavChip">
        <button class="theme-toggle" id="mobileNavToggle" title="Menu" aria-label="Open navigation menu" type="button"><svg class="ico" aria-hidden="true"><use href="#i-menu"/></svg></button>
      </div>
```

with:

```html
      <div class="mobile-nav-chip" id="mobileNavChip">
        <button class="theme-toggle" id="mobileNavToggle" title="Menu" aria-label="Open navigation menu" type="button"><svg class="ico" aria-hidden="true"><use href="#i-menu"/></svg></button>
        <div class="mobile-nav-menu" id="mobileNavMenu">
          <button class="mobile-nav-menu-item" data-section-btn="home" data-i18n="nav.home" type="button">Home</button>
          <button class="mobile-nav-menu-item" data-section-btn="vocabulary" data-i18n="nav.vocabulary" type="button">Vocabulary</button>
          <button class="mobile-nav-menu-item" data-section-btn="grammar" data-i18n="nav.grammar" type="button">Grammar</button>
          <button class="mobile-nav-menu-item" data-section-btn="reading" data-i18n="nav.reading" type="button">Reading</button>
          <button class="mobile-nav-menu-item" data-section-btn="writing" data-i18n="nav.writing" type="button">Writing</button>
          <button class="mobile-nav-menu-item" data-section-btn="listening" data-i18n="nav.listening" type="button">Listening</button>
          <button class="mobile-nav-menu-item" data-section-btn="speaking" data-i18n="nav.speaking" type="button">Speaking</button>
        </div>
      </div>
```

- [ ] **Step 4: Add the panel CSS**

Replace the CSS added in Task 1:

```css
.mobile-nav-chip{display:none; position:relative;}
@media (max-width:640px){
  .tabs{display:none;}
  .mobile-nav-chip{display:block;}
}
```

with:

```css
.mobile-nav-chip{display:none; position:relative;}
.mobile-nav-chip.open .mobile-nav-menu{display:flex;}
.mobile-nav-menu{
  display:none; position:absolute; top:calc(100% + 8px); left:0; min-width:200px;
  background:rgba(22,26,35,.94); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  border:1px solid rgba(var(--vio),.22); border-radius:16px;
  box-shadow:0 16px 48px rgba(0,0,0,.4); padding:12px; z-index:50; flex-direction:column; gap:4px;
}
[data-theme="light"] .mobile-nav-menu{background:rgba(255,255,255,.94);}
.mobile-nav-menu-item{
  display:block; width:100%; text-align:left; font-family:'Plus Jakarta Sans','Sora',sans-serif;
  font-size:.9rem; font-weight:600; color:var(--muted); background:transparent; border:none;
  padding:10px 14px; border-radius:10px; cursor:pointer;
}
.mobile-nav-menu-item:hover{color:var(--text); background:rgba(var(--vio),.1);}
@media (max-width:640px){
  .tabs{display:none;}
  .mobile-nav-chip{display:block;}
}
```

- [ ] **Step 5: Add the JS — open/close, positioning, item navigation**

In `VocabLarry/vocab-master.html`, find (this is the `positionDropdown()` helper + its resize listener, added earlier this session for `#langMenu`/`#userMenu` — confirmed still at this exact adjacency to `langChip`'s listener as of this plan being written):

```js
window.addEventListener("resize", () => {
  positionDropdown("langChip", "langMenu");
  positionDropdown("userChip", "userMenu");
});
document.getElementById("langChip").addEventListener("click", (e) => {
```

and insert immediately before that `langChip` listener (right after the `resize` listener's closing `});`):

```js
document.getElementById("mobileNavToggle").addEventListener("click", (e) => {
  e.stopPropagation();
  document.getElementById("mobileNavChip").classList.toggle("open");
  positionDropdown("mobileNavChip", "mobileNavMenu");
});
document.querySelectorAll("#mobileNavMenu [data-section-btn]").forEach(item => {
  item.addEventListener("click", (e) => {
    e.stopPropagation();
    goToPage(NAV_SECTIONS[item.dataset.sectionBtn][0]);
    closeNavDropdowns();
    document.getElementById("mobileNavChip").classList.remove("open");
  });
});
document.addEventListener("click", (e) => {
  if (!e.target.closest("#mobileNavChip")) document.getElementById("mobileNavChip")?.classList.remove("open");
});
```

**Note:** `positionDropdown` and `NAV_SECTIONS`/`goToPage`/`closeNavDropdowns` must already be defined by this point in the script for these listeners to resolve them at call-time (not at parse-time, since they're only invoked inside click handlers) — `positionDropdown` is defined earlier in the same script block (line 13285 pre-Task-1, function declarations are hoisted regardless of position), so this is safe.

- [ ] **Step 6: Run the verification script to confirm it passes**

Run: `python <path>/verify_task2_hamburger_panel.py`
Expected:
```
PASS: all 7 sections present in order
PASS: menu stays within 375px viewport: {...}
PASS: tapping Vocabulary navigated to page-list
PASS: panel closed after selection
```

- [ ] **Step 7: Verify Vietnamese labels (manual check, no new i18n keys needed)**

```python
import time
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
    page.evaluate("localStorage.setItem('ivm_lang','vi')")
    page.reload(wait_until="networkidle")
    time.sleep(1)
    page.click("#mobileNavToggle")
    time.sleep(0.3)
    labels = page.eval_on_selector_all("#mobileNavMenu [data-section-btn]", "els => els.map(e => e.textContent.trim())")
    print(labels)
    browser.close()
```

Expected: `['Trang chủ', 'Từ vựng', 'Ngữ pháp', 'Đọc', 'Viết', 'Nghe', 'Nói']`

- [ ] **Step 8: Parse-check and commit**

```bash
node -e "const fs=require('fs');const html=fs.readFileSync('VocabLarry/vocab-master.html','utf-8');const scripts=[...html.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);let ok=true;scripts.forEach((s,i)=>{try{new Function(s);}catch(e){ok=false;console.log('Error',i,e.message);}});console.log('parsed ok:',ok);"
git add VocabLarry/vocab-master.html
git commit -m "feat(mobile-nav): hamburger panel with 7-section dropdown navigation"
```

---

### Task 3: Category/Word/Test switcher bar — markup on all 6 pages

**Files:**
- Modify: `VocabLarry/vocab-master.html:1924-1929` (`#page-list` page-head)
- Modify: `VocabLarry/vocab-master.html:2031-2036` (`#page-examples` page-head)
- Modify: `VocabLarry/vocab-master.html:2076-2081` (`#page-test` page-head)
- Modify: `VocabLarry/vocab-master.html:2192-2197` (`#page-grammar` page-head)
- Modify: `VocabLarry/vocab-master.html:2245-2250` (`#page-gramword` page-head)
- Modify: `VocabLarry/vocab-master.html:2312-2317` (`#page-gramtest` page-head)
- Modify: `VocabLarry/vocab-master.html` (new CSS rule near `.chip` definition, line 366)

**Interfaces:**
- Consumes: `.chip` class (`vocab-master.html:366`, generic pill button with `.active` state).
- Produces: `.mobile-page-switcher` container (3 `.chip[data-page]` buttons each) on all 6 pages, visible only <640px. Not yet wired to navigation — that's Task 4.

**Note on line numbers:** each `Modify` below inserts *after* an existing, uniquely-matchable `</div>` that closes that page's `.page-head` block — use the surrounding text shown, not the line number alone, since earlier edits in this plan shift subsequent line numbers.

- [ ] **Step 1: Write the verification script (expect it to fail)**

Create `verify_task3_switcher_markup.py`:

```python
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"
PAGES = ["page-list", "page-examples", "page-test", "page-grammar", "page-gramword", "page-gramtest"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    for pid in PAGES:
        count = page.eval_on_selector_all(f"#{pid} .mobile-page-switcher .chip", "els => els.length")
        assert count == 3, f"FAIL: {pid} has {count} switcher buttons, expected 3"
    print("PASS: all 6 pages have a 3-button switcher in the DOM")

    visible = page.eval_on_selector("#page-list .mobile-page-switcher", "el => getComputedStyle(el).display")
    assert visible != "none", "FAIL: switcher should be visible at 375px"
    print("PASS: switcher visible at 375px")
    page.close()

    page2 = browser.new_page(viewport={"width": 768, "height": 1024})
    page2.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    hidden = page2.eval_on_selector("#page-list .mobile-page-switcher", "el => getComputedStyle(el).display")
    assert hidden == "none", "FAIL: switcher should be hidden at 768px"
    print("PASS: switcher hidden at 768px")
    page2.close()

    browser.close()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python <path>/verify_task3_switcher_markup.py`
Expected: `AssertionError: FAIL: page-list has 0 switcher buttons, expected 3`

- [ ] **Step 3: Add the switcher CSS**

In `VocabLarry/vocab-master.html`, find line 366 (`.chip{`) and insert immediately before it:

```css
.mobile-page-switcher{display:none; gap:8px; margin:0 0 20px; flex-wrap:wrap;}
@media (max-width:640px){ .mobile-page-switcher{display:flex;} }
```

- [ ] **Step 4: Add the switcher markup to `#page-list`**

Replace:

```html
  <section id="page-list" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 data-i18n="nav.category">Category</h1>
      <p data-i18n="vocab.categoryPageDesc">5,000 essential words, organised by section and category — click one to begin.</p>
    </div>
```

with:

```html
  <section id="page-list" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 data-i18n="nav.category">Category</h1>
      <p data-i18n="vocab.categoryPageDesc">5,000 essential words, organised by section and category — click one to begin.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="list" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="examples" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="test" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 5: Add the switcher markup to `#page-examples`**

Replace:

```html
  <section id="page-examples" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 data-i18n="nav.word">Word</h1>
      <p data-i18n="vocab.wordPageDesc">Every word, used correctly in a full sentence.</p>
    </div>
```

with:

```html
  <section id="page-examples" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 data-i18n="nav.word">Word</h1>
      <p data-i18n="vocab.wordPageDesc">Every word, used correctly in a full sentence.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="list" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="examples" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="test" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 6: Add the switcher markup to `#page-test`**

Replace:

```html
  <section id="page-test" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 id="testTitle">Quiz</h1>
      <p id="testDesc">Test your knowledge with multiple question types.</p>
    </div>
```

with:

```html
  <section id="page-test" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="vocab.eyebrow">Section 01 / Vocabulary</span>
      <h1 id="testTitle">Quiz</h1>
      <p id="testDesc">Test your knowledge with multiple question types.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="list" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="examples" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="test" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 7: Add the switcher markup to `#page-grammar`**

Replace:

```html
  <section id="page-grammar" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.category">Category</h1>
      <p data-i18n="grammar.categoryDesc">From first tenses to advanced structures — a lesson and a practice set for every stage.</p>
    </div>
```

with:

```html
  <section id="page-grammar" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.category">Category</h1>
      <p data-i18n="grammar.categoryDesc">From first tenses to advanced structures — a lesson and a practice set for every stage.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="grammar" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="gramword" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="gramtest" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 8: Add the switcher markup to `#page-gramword`**

Replace:

```html
  <section id="page-gramword" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.word">Word</h1>
      <p data-i18n="grammar.wordDesc">The reference shelf — irregular verb forms, plural nouns, comparison forms, linking words and idioms, searchable.</p>
    </div>
```

with:

```html
  <section id="page-gramword" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.word">Word</h1>
      <p data-i18n="grammar.wordDesc">The reference shelf — irregular verb forms, plural nouns, comparison forms, linking words and idioms, searchable.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="grammar" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="gramword" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="gramtest" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 9: Add the switcher markup to `#page-gramtest`**

Replace:

```html
  <section id="page-gramtest" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.test">Test</h1>
      <p data-i18n="gramtest.pageDesc">Practice questions drawn from any mix of grammar topics.</p>
    </div>
```

with:

```html
  <section id="page-gramtest" class="page">
    <div class="page-head">
      <span class="eyebrow" data-i18n="grammar.eyebrow">Section 02 / Grammar</span>
      <h1 data-i18n="nav.test">Test</h1>
      <p data-i18n="gramtest.pageDesc">Practice questions drawn from any mix of grammar topics.</p>
    </div>
    <div class="mobile-page-switcher">
      <button class="chip" data-page="grammar" data-i18n="nav.category" type="button">Category</button>
      <button class="chip" data-page="gramword" data-i18n="nav.word" type="button">Word</button>
      <button class="chip" data-page="gramtest" data-i18n="nav.test" type="button">Test</button>
    </div>
```

- [ ] **Step 10: Run the verification script to confirm it passes**

Run: `python <path>/verify_task3_switcher_markup.py`
Expected:
```
PASS: all 6 pages have a 3-button switcher in the DOM
PASS: switcher visible at 375px
PASS: switcher hidden at 768px
```

- [ ] **Step 11: Parse-check and commit**

```bash
node -e "const fs=require('fs');const html=fs.readFileSync('VocabLarry/vocab-master.html','utf-8');const scripts=[...html.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);let ok=true;scripts.forEach((s,i)=>{try{new Function(s);}catch(e){ok=false;console.log('Error',i,e.message);}});console.log('parsed ok:',ok);"
git add VocabLarry/vocab-master.html
git commit -m "feat(mobile-nav): add Category/Word/Test switcher bar markup to 6 pages"
```

---

### Task 4: Wire switcher buttons to real navigation + sync active state

**Files:**
- Modify: `VocabLarry/vocab-master.html:13192-13214` (`goToPage()` — change 2 active-class queries from single-match to multi-match)
- Modify: `VocabLarry/vocab-master.html` (new JS block, placed right after the existing `.nav-dropdown-item` listener at line 13216-13225)

**Interfaces:**
- Consumes: `.mobile-page-switcher .chip[data-page]` (from Task 3). `.nav-dropdown-item[data-page]` (existing).
- Produces: clicking any switcher button fires the same navigation as its matching desktop dropdown item; `goToPage()` now keeps every `.mobile-page-switcher .chip` in sync with `.active` state, not just the one `.nav-dropdown-item`.

- [ ] **Step 1: Write the verification script (expect it to fail)**

Create `verify_task4_switcher_navigation.py`:

```python
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)

    # Navigate to the Category page (default) then tap "Word" in the switcher
    page.click("#page-list .mobile-page-switcher .chip[data-page='examples']")
    time.sleep(0.4)
    active_page = page.eval_on_selector(".page.active", "el => el.id")
    assert active_page == "page-examples", f"FAIL: expected page-examples, got {active_page}"
    print("PASS: switcher 'Word' button navigated to page-examples")

    active_count = page.eval_on_selector_all(
        ".mobile-page-switcher .chip[data-page='examples'].active", "els => els.length")
    assert active_count == 3, f"FAIL: expected 3 synced active switcher buttons (one per vocab page), got {active_count}"
    print("PASS: all 3 vocab pages' switcher bars show 'Word' as active")

    # Tap "Test" and confirm the Test-page special-case filter sync still fires
    page.click("#page-examples .mobile-page-switcher .chip[data-page='test']")
    time.sleep(0.6)
    active_page2 = page.eval_on_selector(".page.active", "el => el.id")
    assert active_page2 == "page-test", f"FAIL: expected page-test, got {active_page2}"
    pool_len = page.evaluate("testPool().length")
    assert pool_len > 0, "FAIL: testPool() should be non-empty after applyBrowseFiltersToTest() ran"
    print("PASS: switcher 'Test' button navigated to page-test and testPool() populated:", pool_len)

    browser.close()
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python <path>/verify_task4_switcher_navigation.py`
Expected: `playwright._impl._errors.TimeoutError` on the first click (button has no listener yet, but more importantly the active-page never changes) — or an `AssertionError` if the click resolves but nothing happens. Either failure mode confirms the wiring doesn't exist yet.

- [ ] **Step 3: Update `goToPage()` to sync switcher buttons**

In `VocabLarry/vocab-master.html`, replace:

```js
function goToPage(pageId){
  document.querySelectorAll(".nav-group > .tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-dropdown-item").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));

  const section = sectionOfPage(pageId);
  document.querySelector(`.tab[data-section-btn="${section}"]`).classList.add("active");
  const dropdownItem = document.querySelector(`.nav-dropdown-item[data-page="${pageId}"]`);
  if (dropdownItem) dropdownItem.classList.add("active");
```

with:

```js
function goToPage(pageId){
  document.querySelectorAll(".nav-group > .tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".nav-dropdown-item, .mobile-page-switcher .chip").forEach(i => i.classList.remove("active"));
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));

  const section = sectionOfPage(pageId);
  document.querySelector(`.tab[data-section-btn="${section}"]`).classList.add("active");
  document.querySelectorAll(`.nav-dropdown-item[data-page="${pageId}"], .mobile-page-switcher .chip[data-page="${pageId}"]`)
    .forEach(el => el.classList.add("active"));
```

- [ ] **Step 4: Wire the switcher buttons to trigger real navigation**

In `VocabLarry/vocab-master.html`, find:

```js
document.querySelectorAll(".nav-dropdown-item").forEach(item => {
  item.addEventListener("click", () => {
    if (item.dataset.page === "test"){
      applyBrowseFiltersToTest();
      renderTestMode();
    }
    goToPage(item.dataset.page);
    closeNavDropdowns();
  });
});
```

and insert immediately after it:

```js
document.querySelectorAll(".mobile-page-switcher .chip[data-page]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelector(`.nav-dropdown-item[data-page="${btn.dataset.page}"]`).click();
  });
});
```

- [ ] **Step 5: Run the verification script to confirm it passes**

Run: `python <path>/verify_task4_switcher_navigation.py`
Expected:
```
PASS: switcher 'Word' button navigated to page-examples
PASS: all 3 vocab pages' switcher bars show 'Word' as active
PASS: switcher 'Test' button navigated to page-test and testPool() populated: 5000
```

- [ ] **Step 6: Parse-check, run pytest regression, and commit**

```bash
node -e "const fs=require('fs');const html=fs.readFileSync('VocabLarry/vocab-master.html','utf-8');const scripts=[...html.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);let ok=true;scripts.forEach((s,i)=>{try{new Function(s);}catch(e){ok=false;console.log('Error',i,e.message);}});console.log('parsed ok:',ok);"
cd VocabLarry && python -m pytest tests -q && cd ..
git add VocabLarry/vocab-master.html
git commit -m "feat(mobile-nav): wire switcher buttons to real navigation, sync active state"
```

---

### Task 5: Full breakpoint + regression sweep

**Files:** none (verification only)

**Interfaces:** none — this task only runs assertions against everything built in Tasks 1-4 plus the pre-existing desktop nav and `#langMenu`/`#userMenu` fix from earlier this session.

- [ ] **Step 1: Write and run the full sweep script**

Create `verify_task5_full_sweep.py`:

```python
import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000/"
WIDTHS = [320, 375, 414, 639, 640, 768, 900, 1024, 1440]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for w in WIDTHS:
        page = browser.new_page(viewport={"width": w, "height": 900})
        page.goto(BASE, wait_until="networkidle")
        time.sleep(0.5)
        hamburger_visible = page.eval_on_selector("#mobileNavToggle", "el => getComputedStyle(el).display") != "none"
        tabs_visible = page.eval_on_selector(".tabs", "el => getComputedStyle(el).display") != "none"
        expected_mobile = w <= 640
        assert hamburger_visible == expected_mobile, f"FAIL at {w}px: hamburger_visible={hamburger_visible}, expected {expected_mobile}"
        assert tabs_visible != expected_mobile, f"FAIL at {w}px: tabs_visible={tabs_visible}, expected {not expected_mobile}"
        print(f"PASS {w}px: hamburger={hamburger_visible} tabs={tabs_visible}")
        page.close()

    # Desktop dropdown hover behavior unaffected
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.5)
    page.hover("[data-section-btn='vocabulary']")
    time.sleep(0.3)
    dropdown_visible = page.eval_on_selector(
        "[data-section='vocabulary'] .nav-dropdown", "el => getComputedStyle(el).display") != "none"
    assert dropdown_visible, "FAIL: desktop hover-dropdown regression"
    print("PASS: desktop hover-dropdown still works")
    page.close()

    # #langMenu / #userMenu positioning fix (earlier this session) still holds
    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.5)
    page.click("#langChip")
    time.sleep(0.3)
    box = page.eval_on_selector("#langMenu", "el => { const r = el.getBoundingClientRect(); return {left:r.left, right:r.right}; }")
    assert box["left"] >= 0 and box["right"] <= 375, f"FAIL: langMenu regression: {box}"
    print("PASS: #langMenu positioning fix still holds")
    page.close()

    browser.close()
```

Run: `python <path>/verify_task5_full_sweep.py`
Expected: every line prints `PASS`, no `AssertionError`.

- [ ] **Step 2: Run the backend test suite (regression safety, unaffected by this frontend-only change)**

```bash
cd VocabLarry && python -m pytest tests -q && cd ..
```

Expected: `85 passed`

- [ ] **Step 3: Final parse-check and push**

```bash
node -e "const fs=require('fs');const html=fs.readFileSync('VocabLarry/vocab-master.html','utf-8');const scripts=[...html.matchAll(/<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]);let ok=true;scripts.forEach((s,i)=>{try{new Function(s);}catch(e){ok=false;console.log('Error',i,e.message);}});console.log('parsed ok:',ok);"
git push elw main
```

Note: this is a `vocab-master.html`-only change, so per the established workflow this session, updating production is the fast path (no deploy zip needed):

```bash
# on the PythonAnywhere Bash console
cd ~/VocabLarry
curl -s -o vocab-master.html "https://raw.githubusercontent.com/ProTeaGaming/English-Learning-Website/main/VocabLarry/vocab-master.html"
wc -c vocab-master.html   # compare against: wc -c VocabLarry/vocab-master.html locally
```

Then Reload on the Web tab.
