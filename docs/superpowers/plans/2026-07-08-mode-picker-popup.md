# Home Hero Mode-Picker Popup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clicking "Start Learning →" or "Quick Test" on the homepage hero opens a mode-picker popup (Vocabulary, Grammar, Reading, Writing, Listening, Speaking) instead of jumping straight to vocab; Vocabulary/Grammar are clickable and route to the right existing page, the other four are visibly disabled.

**Architecture:** One shared modal, styled exactly like the site's existing `.auth-modal-overlay` pattern (e.g. `#deleteOverlay`), added once to the HTML. A single JS function `openModePicker(intent)` sets the modal's title and the two live rows' click targets based on which button opened it, then shows the modal. Closing follows the same backdrop-click + × pattern as the site's other auth modals, plus an Escape handler (matching the precedent set by the debug modal and word modal, the only two modals in this file with Escape support today).

**Tech Stack:** Vanilla JS in the single-file SPA `vocab-master.html`. No backend, no new dependencies.

**Spec:** `docs/superpowers/specs/2026-07-08-mode-picker-popup-design.md`

## Global Constraints

- All changes live in `VocabLarry/Python/Django/vocab-master.html` only. No `.py` files, no new dependencies.
- Popup lists all six sections in this fixed order: Vocabulary, Grammar, Reading, Writing, Listening, Speaking. Only Vocabulary and Grammar are clickable; the other four show a "Soon" pill and are not clickable.
- Titles: **"Choose what to learn"** when opened from Start Learning, **"Choose what to test"** when opened from Quick Test.
- Routing: Vocabulary → `goToPage('list')` for learn intent, `goToPage('test')` for test intent. Grammar → `goToPage('grammar')` for either intent.
- Reuses existing CSS classes/tokens where they already fit: `.auth-modal-overlay`, `.auth-modal`, `.auth-modal-close`, `.auth-modal-title`, `.home-sec-pill.soon` (all already theme-safe across `[data-theme="light"]` — verified no per-theme override is needed for `.home-sec-pill.soon`, it sets its own explicit background/color).
- Icons (already defined as SVG `<symbol>`s in this file): Vocabulary `#i-book`, Grammar `#i-pen`, Reading `#i-book-open`, Writing `#i-file-text`, Listening `#i-headphones`, Speaking `#i-mic`.
- No backend/API changes; no login gating (matches today's behavior — Vocabulary and Grammar need no login to browse).
- Verification in this codebase for frontend-only changes (established in prior sessions, since there is no JS test framework here): `python -m pytest tests -q` must still pass unchanged (confirms no `.py` file was touched and the suite still runs), `node --check` against the concatenated inline `<script>` blocks must pass, and a dev-server smoke test (page returns 200, new element IDs present in served HTML).
- Never push to git; commit only.

---

### Task 1: Mode-picker popup — HTML, CSS, JS, and hero wiring

**Files:**
- Modify: `VocabLarry/Python/Django/vocab-master.html`
  - CSS: insert a new rule block near the existing `.home-sec-pill` rules (~line 1279, right after the `[data-theme="light"] .cat-medal` line, before the next section's comment/rules)
  - HTML (modal markup): insert right after the `profileOverlay` modal's closing `</div>` (~line 1688, immediately before `<main>`)
  - HTML (hero buttons): modify the two existing buttons (~lines 1702-1703)
  - JS: insert `openModePicker`/`closeModePicker` and their wiring right after the existing `closeAuthModal` wiring block (search for `document.getElementById("authOverlay").addEventListener("click", (e) => {` and its matching closing lines, ~4902-4906) so it sits alongside the other modal-wiring code

**Interfaces:**
- Consumes: `goToPage(pageId)` (existing function, `vocab-master.html:4607`) — call with `'list'`, `'test'`, or `'grammar'`.
- Produces: `openModePicker(intent)` where `intent` is the string `'learn'` or `'test'` — called by the two hero buttons. No other task/file depends on this (single-task plan).

- [ ] **Step 1: Add the CSS**

Find this exact block (the last two lines of the `.home-sec-pill` rule group):

```css
[data-theme="light"] .cat-cefr-pill{filter:saturate(1.15) brightness(.78);}
[data-theme="light"] .cat-medal{color:#ca8a04;filter:none;}
```

Insert immediately after it:

```css
/* ---------- Mode-picker popup (home hero) ---------- */
.mode-picker-list{display:flex;flex-direction:column;gap:8px;margin-top:4px;}
.mode-picker-row{
  display:flex;align-items:center;gap:12px;width:100%;box-sizing:border-box;
  padding:12px 14px;border-radius:12px;border:1px solid rgba(var(--vio),.18);
  background:rgba(var(--vio),.06);color:var(--text);font:inherit;font-size:.95rem;font-weight:600;
  text-align:left;cursor:pointer;transition:background .15s ease,border-color .15s ease,transform .15s ease;
}
.mode-picker-row .ico{width:20px;height:20px;flex-shrink:0;}
.mode-picker-name{flex:1;}
button.mode-picker-row:hover{border-color:rgba(var(--vio),.5);background:rgba(var(--vio),.12);transform:translateY(-1px);}
.mode-picker-row-disabled{opacity:.5;cursor:default;}
```

- [ ] **Step 2: Add the modal HTML**

Find this exact block (the end of the `profileOverlay` modal, right before `<main>`):

```html
        <button type="submit" class="auth-submit-btn" id="profileSubmitBtn">Save changes</button>
      </form>
    </div>
  </div>

<main>
```

Insert a new overlay div between `</div>` (closing `profileOverlay`) and `<main>`, so it reads:

```html
        <button type="submit" class="auth-submit-btn" id="profileSubmitBtn">Save changes</button>
      </form>
    </div>
  </div>

<div class="auth-modal-overlay" id="modePickerOverlay">
  <div class="auth-modal" style="max-width:340px;">
    <button class="auth-modal-close" id="modePickerClose" aria-label="Close">&times;</button>
    <h2 class="auth-modal-title" id="modePickerTitle">Choose what to learn</h2>
    <div class="mode-picker-list">
      <button class="mode-picker-row" id="modePickerVocab" type="button">
        <svg class="ico" aria-hidden="true"><use href="#i-book"/></svg>
        <span class="mode-picker-name">Vocabulary</span>
      </button>
      <button class="mode-picker-row" id="modePickerGrammar" type="button">
        <svg class="ico" aria-hidden="true"><use href="#i-pen"/></svg>
        <span class="mode-picker-name">Grammar</span>
      </button>
      <div class="mode-picker-row mode-picker-row-disabled">
        <svg class="ico" aria-hidden="true"><use href="#i-book-open"/></svg>
        <span class="mode-picker-name">Reading</span>
        <span class="home-sec-pill soon">Soon</span>
      </div>
      <div class="mode-picker-row mode-picker-row-disabled">
        <svg class="ico" aria-hidden="true"><use href="#i-file-text"/></svg>
        <span class="mode-picker-name">Writing</span>
        <span class="home-sec-pill soon">Soon</span>
      </div>
      <div class="mode-picker-row mode-picker-row-disabled">
        <svg class="ico" aria-hidden="true"><use href="#i-headphones"/></svg>
        <span class="mode-picker-name">Listening</span>
        <span class="home-sec-pill soon">Soon</span>
      </div>
      <div class="mode-picker-row mode-picker-row-disabled">
        <svg class="ico" aria-hidden="true"><use href="#i-mic"/></svg>
        <span class="mode-picker-name">Speaking</span>
        <span class="home-sec-pill soon">Soon</span>
      </div>
    </div>
  </div>
</div>

<main>
```

- [ ] **Step 3: Wire the hero buttons to open the popup instead of navigating directly**

Find this exact block (~lines 1702-1703):

```html
        <button class="btn" onclick="goToPage('list')">Start Learning →</button>
        <button class="home-btn-outline" onclick="goToPage('test')">Quick Test</button>
```

Replace with:

```html
        <button class="btn" onclick="openModePicker('learn')">Start Learning →</button>
        <button class="home-btn-outline" onclick="openModePicker('test')">Quick Test</button>
```

- [ ] **Step 4: Add the JS — open/close logic and event wiring**

Find this exact block (the `closeAuthModal` wiring — search for `authOverlay").addEventListener`):

```javascript
document.getElementById("authClose").addEventListener("click", closeAuthModal);
document.getElementById("authOverlay").addEventListener("click", (e) => {
  if (e.target.id === "authOverlay") closeAuthModal();
});
```

Insert immediately after it:

```javascript
function openModePicker(intent){
  document.getElementById("modePickerTitle").textContent =
    intent === "test" ? "Choose what to test" : "Choose what to learn";
  document.getElementById("modePickerVocab").onclick = () => {
    closeModePicker();
    goToPage(intent === "test" ? "test" : "list");
  };
  document.getElementById("modePickerGrammar").onclick = () => {
    closeModePicker();
    goToPage("grammar");
  };
  document.getElementById("modePickerOverlay").classList.add("open");
}
function closeModePicker(){
  document.getElementById("modePickerOverlay").classList.remove("open");
}
document.getElementById("modePickerClose").addEventListener("click", closeModePicker);
document.getElementById("modePickerOverlay").addEventListener("click", (e) => {
  if (e.target.id === "modePickerOverlay") closeModePicker();
});
document.addEventListener("keydown", e => {
  if (e.key !== "Escape") return;
  if (document.querySelector(".dbg-overlay")) return;
  if (document.getElementById("modePickerOverlay").classList.contains("open")) closeModePicker();
});
```

The `.dbg-overlay` guard mirrors the existing guard on the word-modal's Escape handler (`vocab-master.html:6762`) — if a debug edit modal is open on top, Escape should close that one first, not reach through to this popup.

- [ ] **Step 5: Verify — JS syntax**

Run (from `VocabLarry/Python/Django/`, using bash or PowerShell as available):

```bash
python - << 'EOF'
import re, subprocess, tempfile, os
html = open('vocab-master.html', encoding='utf-8').read()
blocks = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', html, re.S)
blocks = [b for b in blocks if b.strip()]
js = '\n;\n'.join(blocks)
p = os.path.join(tempfile.gettempdir(), 'vm_check_modepicker.js')
open(p, 'w', encoding='utf-8').write(js)
r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
print('node --check:', 'OK' if r.returncode == 0 else r.stderr[:800])
EOF
```

Expected: `node --check: OK`

- [ ] **Step 6: Verify — backend suite still passes (no `.py` file was touched)**

Run: `python -m pytest tests -q` (from `VocabLarry/Python/Django/`)
Expected: `70 passed` (same count as before this task — confirms nothing broke and no accidental `.py` edits crept in)

- [ ] **Step 7: Verify — dev server smoke test**

Start the server in the background (use your tool's background-run option rather than a shell `&`/`sleep` chain — writing the log to `/tmp/` directly has hit permission errors in this sandbox before; use a path under the current working directory or your scratchpad instead) and check the new markup is served:

```bash
python manage.py runserver 127.0.0.1:8199 --noreload > mp_smoke_server.log 2>&1 &
```

Wait for it to start, then:

```bash
curl -s http://127.0.0.1:8199/ -o mp_smoke.html -w "%{http_code}\n"
grep -c "modePickerOverlay" mp_smoke.html
grep -c "openModePicker" mp_smoke.html
grep -c "mode-picker-row-disabled" mp_smoke.html
```

Expected: `200`, and each `grep -c` returns a count ≥ 1. Then stop the server process and delete `mp_smoke_server.log`/`mp_smoke.html` (they are scratch output, not part of the commit).

- [ ] **Step 8: Manual verification note (cannot be automated — no browser tool)**

Record in the commit message or task report that a manual browser pass is recommended before the user relies on this, covering:
- Click "Start Learning →" → title reads "Choose what to learn"; click Vocabulary → lands on word list page. Reopen, click Grammar → lands on Grammar home.
- Click "Quick Test" → title reads "Choose what to test"; click Vocabulary → lands on vocab quiz setup page. Reopen, click Grammar → lands on Grammar home (same destination as learn intent).
- Reading/Writing/Listening/Speaking rows show a "Soon" pill, are visibly dimmed, and do nothing when clicked.
- Popup closes via the × button, via clicking the dark backdrop, and via pressing Escape.
- Both light and dark themes: rows, title, and Soon pills are all legible (this codebase has twice had readability bugs from CSS assuming a variable/inheritance that didn't exist in one theme — worth a specific look here since this is new modal CSS).

- [ ] **Step 9: Commit**

```bash
git add VocabLarry/Python/Django/vocab-master.html
git commit -m "feat(home): mode-picker popup for Start Learning / Quick Test

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
