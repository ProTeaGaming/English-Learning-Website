# IELTS Vocab Master — Build Plan & Log

> Read this file before making changes to either `vocab-app/` (React/Vite) or
> `vocab-master.html` (standalone single-file app). After finishing a unit of
> work, append a new entry to the **Build Log** below so future work can pick
> up the context quickly.

## Project shape

- `vocab-app/` — React + Vite + Tailwind. Source in `src/`.
- `vocab-master.html` — standalone single-file app (vanilla HTML/CSS/JS),
  mirrors the same features/UI as `vocab-app`.
- **Both versions must stay in feature parity** unless told otherwise — when
  a UI/UX change is requested, implement it in both.

## Build Log

### 2026-06-13 — Light/Dark theme + Vocabulary/Reading nav restructure

**Request:**
- Add light/dark mode to the site.
- Regroup pages into sections with hover dropdowns:
  - **Vocabulary**: Word List, Examples
  - **Reading**: Quiz, Fill the Gap, Challenge
- Hovering a section reveals a dropdown to jump straight to a sub-page.
- Apply to **both** `vocab-app` and `vocab-master.html`.

**vocab-app (React) changes:**
- `tailwind.config.js` — converted theme colors (`bg`, `surface`, `surface2`,
  `line`, `ink`, `muted`, `accent`, `b1`, `b2`, `c1`, `c2`, `c2p`) to
  `rgb(var(--color-x) / <alpha-value>)` so they work with Tailwind opacity
  modifiers and CSS-variable theming. Topic colors (tb, tv, tp, etc.) left as
  static hex.
- `src/index.css` — added dark (`:root`) and `[data-theme="light"]` variable
  sets, updated `body`/`.reveal` to use the variables, added light-mode
  overrides for `.q-opt.correct` / `.q-opt.wrong`, and added new component
  classes: `.nav-caret`, `.nav-dropdown`, `.nav-dropdown-item`,
  `.theme-toggle`.
- `src/hooks/useTheme.js` (new) — theme state hook (mirrors `useLearned.js`),
  persists to `localStorage["ivm_theme"]`, falls back to
  `prefers-color-scheme`, sets `data-theme` on `<html>`.
- `src/components/Navbar.jsx` — rewritten: `SECTIONS` config (Vocabulary →
  list/examples, Reading → quiz/gap/challenge) rendered as hover/click
  dropdowns with click-outside-to-close, plus the theme toggle button.
- `src/App.jsx` — wired `useTheme()` into `Navbar`.

**vocab-master.html changes:**
- Mirrored the same `:root` / `[data-theme="light"]` CSS variables, nav
  dropdown styles (`.nav-group`, `.nav-dropdown`, `.nav-dropdown-item`,
  `.nav-caret`), and `.theme-toggle` styles.
- Added an early inline `<script>` (before `</head>`) to apply the saved/
  preferred theme before first paint (avoids flash of wrong theme).
- Rewrote `<header class="topbar">` nav markup into Vocabulary/Reading
  `.nav-group` blocks with dropdowns.
- Replaced the old flat tab-click JS with `NAV_SECTIONS`, `goToPage()`,
  dropdown click handlers, section-tab click handlers (toggle dropdown if
  already active, else navigate to first sub-page), click-outside-to-close,
  and theme-toggle click handler (persists to `localStorage["ivm_theme"]`).

**Verification (Playwright, both apps):**
- vocab-app: dev server on `http://localhost:5173`, eslint clean. Verified
  dropdowns open/navigate correctly, active-state highlighting correct,
  theme toggle works and persists across reload (`ivm_theme` in
  localStorage), no console errors.
- vocab-master.html: served via a local static server. Verified dark theme
  on load, Vocabulary/Reading dropdowns open on hover and navigate correctly,
  active state correct on both the section tab and the dropdown item, theme
  toggle switches `data-theme` + persists across reload, no console errors.

**Outcome:** Both apps now have full light/dark theming and the
Vocabulary/Reading hover-dropdown navigation, verified working.

---

### 2026-06-13 — "View All" / "Hide All" toggle for filter chip rows

**Request:**
- For long filter option lists (Sections, Categories), truncate to a default
  count (5) with a "View All" underlined link.
- Clicking "View All" expands to show all options and the link becomes
  "Hide All"; clicking it again collapses back to the default count.
- Apply consistently across all filter sections in both apps.

**vocab-app (React) changes:**
- `src/components/ExpandableChips.jsx` (new) — reusable component taking
  `items` + `renderItem`, truncates to `visibleCount` (default 5), renders a
  `.view-all-link` toggle button when `items.length > visibleCount`.
- `src/index.css` — added `.view-all-link` (underlined accent text link)
  style.
- `src/components/Filters.jsx` and `src/components/TopicCefrFilter.jsx` —
  wrapped the Sections row (`SECTION_ORDER`) and Categories row
  (`visibleCats`) option chips in `<ExpandableChips>`. The pinned "All
  Sections"/"All Categories" chip always stays visible.

**vocab-master.html changes:**
- Added `.view-all-link` CSS (mirrors the React styling).
- Added `renderExpandableChips(container, pinnedChip, optionChips,
  defaultCount=5)` helper that truncates `optionChips` and appends a
  "View All"/"Hide All" toggle button; expanded state is persisted on
  `container.dataset.expanded` so it survives re-renders triggered by other
  filter changes.
- Refactored `buildSectionChips` and `buildCategoryChips` to build the pinned
  chip + option chip arrays and delegate rendering to
  `renderExpandableChips`. These two functions are shared by all filter rows
  (Word List, Examples, Quiz, Fill the Gap, Challenge), so the toggle applies
  universally.

**Verification (Playwright, both apps):**
- vocab-app: lint clean (`npm run lint`), production build succeeds
  (`npm run build`). Sections row: 6 chips collapsed (All Sections + 5) →
  11 expanded (All Sections + 10), link toggles "View All" ↔ "Hide All" and
  collapses back correctly.
- vocab-master.html: Sections row 6 → 11, Categories row 6 → 44 on expand;
  expanded state persists after selecting a different category chip
  (re-render). No console errors in either app. CEFR (5 levels) and Progress
  (2 options) rows stay under the default count, so no toggle appears there
  — matches the "long lists only" requirement.

**Outcome:** Both apps now show truncated filter chip rows with a
"View All"/"Hide All" toggle, applied consistently across all
section/category filter rows.

---

### 2026-06-13 — Centre the topbar content in vocab-master.html

**Request:** in `vocab-master.html`, centre the topbar (brand, nav, theme
toggle, stats) like `vocab-app`'s navbar, leaving the search bar and
everything below it unchanged.

**Changes:**
- `.topbar` now only handles the sticky bar (position, padding, background,
  border) — layout responsibilities moved to a new `.topbar-inner` wrapper
  (`max-width:1280px; margin:0 auto; display:flex; justify-content:space-
  between`), matching `<main>`'s 1280px max-width so the topbar edges align
  with the page content below.
- `.tabs` no longer has `flex:1` (was stretching to fill the full-width bar).
- New `.topbar-right` wraps the theme toggle + "Learned: x/500" stat so
  `.topbar-inner` has exactly 3 children (brand / nav / right group) for
  `space-between`, mirroring `vocab-app`'s `Navbar.jsx` structure.
- Mobile media query: moved the `gap:12px` from `.topbar` to
  `.topbar-inner`.

**Verification (Playwright):** at 1920px viewport, `.topbar-inner` is 1280px
wide with equal 320px margins on each side, exactly matching `<main>`'s
left/right edges. Nav hover-dropdown still works. Mobile (375px) layout
wraps correctly. No console errors.

**Outcome:** vocab-master.html's topbar content is now centred and aligned
with the page content, matching the vocab-app navbar's look. Search bar and
everything below were untouched.

---

### 2026-06-13 — Group Vocabulary/Reading nav next to the brand

**Request:** move the "Vocabulary"/"Reading" nav buttons slightly left so
they sit closer to the logo, matching vocab-app's grouped navbar feel.

**Changes:**
- `.topbar-inner`: removed `justify-content:space-between` (was centering
  the nav roughly in the middle of the bar with large symmetric gaps).
- `.topbar-right`: added `margin-left:auto` so it's pushed to the far right
  edge while brand + nav now sit together on the left with the normal
  `gap:24px`.

**Verification (Playwright, 1920px):** brand-to-nav gap is now a flat 24px
(nav starts right after the brand) and the right group (theme toggle +
"Learned" stat) remains flush against the right edge. Checked at 1920px,
768px, and 375px — nav dropdown still opens correctly, no console errors.

**Outcome:** "Vocabulary"/"Reading" now sit right next to the "IELTS Vocab
Master" brand on the left, with the theme toggle/stats anchored to the far
right — matching vocab-app's grouped-left navbar look.

---

⚠️ Note: an earlier `COPY_PLAN.md` existed in this directory before this
entry but was accidentally deleted (along with `yee-universe/COPY_PLAN.md`)
during cleanup of unrelated test files. Its original contents could not be
recovered. This file was recreated from session context starting
2026-06-13.

---

### 2026-06-13 — Mirror nav grouping in vocab-app + full responsive pass

**Request:**
- Apply the same "Vocabulary"/"Reading" nav-grouping (next to the brand,
  with theme toggle/stats on the far right) to `vocab-app`'s `Navbar.jsx`,
  matching the layout just done in `vocab-master.html`.
- Make the whole site (both apps) compatible with phones, tablets, and other
  devices.

**vocab-app (React) changes:**
- `src/components/Navbar.jsx` — restored `justify-between` on the outer
  header row; brand + nav are now wrapped together in a
  `<div className="flex items-center gap-6 flex-wrap">` (mirrors
  `.topbar-left`), and the theme-toggle + "Learned" stat group is the second
  top-level flex child (no more `ml-auto`). This avoids an awkward empty gap
  when the right-hand group wraps to its own line on narrow screens —
  `justify-content:space-between` falls back to `flex-start` for a
  single-item wrapped line, so the group left-aligns instead of floating with
  empty space before it.
- `src/components/Filters.jsx` — the search input row (`#searchInput` +
  "N words" count) now stacks vertically on small screens
  (`flex flex-col sm:flex-row gap-2.5 sm:items-center`, input
  `min-w-0 sm:min-w-[200px]`). Previously, on a 375px viewport the "500 words"
  label squeezed the search input down to ~228px, truncating the placeholder
  text to "Search words, definit…". Now the input takes the full row width on
  mobile and the count sits on its own line below; side-by-side layout is
  unchanged at `sm:` (640px) and up.

**vocab-master.html changes:**
- `.topbar-inner` restored `justify-content:space-between`; brand + `<nav
  class="tabs">` wrapped in new `.topbar-left{display:flex; align-items:center;
  gap:24px; flex-wrap:wrap;}`; `.topbar-right` no longer uses
  `margin-left:auto`. Same mobile-wrap-gap fix as `Navbar.jsx` above.
- `@media (max-width:640px)` — added `.search-row{flex-direction:column;
  align-items:stretch;}` and `#searchInput, #exSearchInput{min-width:0;}` so
  the search input takes full width and the result count drops below it on
  mobile, fixing the same placeholder-truncation issue as in `Filters.jsx`.

**Verification (Playwright, both apps, phone 375px / tablet 768px / desktop
1280px, all 5 pages: Word List, Examples, Quiz, Fill the Gap, Challenge):**
- No horizontal overflow (`scrollWidth === clientWidth`) in any of the 30
  page/viewport combinations across both apps.
- No console errors in either app at any viewport.
- Mobile nav: brand → nav buttons → theme/stats now stack cleanly with no
  empty-gap artifact; desktop nav: "Vocabulary"/"Reading" sit right next to
  the brand, theme toggle/stats anchored to the far right.
- Nav dropdowns (hover + click) still open/navigate/highlight correctly at
  all three viewports.
- Search bar: full-width on mobile with "N words"/"N sentences match" below
  it; unchanged side-by-side layout on tablet/desktop.
- Spot-checked active Quiz and Challenge question screens, and the Word List
  card grid, at phone/tablet/desktop — option cards, topic/level chip rows,
  and result cards all wrap/reflow without overflow.

**Outcome:** `vocab-app`'s navbar now matches `vocab-master.html`'s grouped
left-nav / right-stats layout, and both apps are verified overflow-free and
console-error-free across phone, tablet, and desktop viewports, with the
search bar fixed for narrow screens.

---

### 2026-06-14 — Add 500 new words (1000 total) to both apps

**Request:** add 500 new vocabulary entries (50 new categories across
`data-part7.js`–`data-part11.js`) on top of the original 500, with zero
duplicates against the existing words, then bring `vocab-master.html` up to
parity (it still only had the original 500 words / 43 categories).

**vocab-app (React) changes:**
- Added `src/data/data-part7.js` … `data-part11.js` (50 new categories, 500
  new words, verified zero duplicates vs. the original 500 and internally).
  Required words ("Proliferation", "Deliberate", "Coin" verb sense,
  "Compensate", "Comprehend", "Fathom", "Hesitation") all included.
- `src/data/vocab-data.js` — added `PART7`–`PART11` imports, extended
  `ALL_PARTS`, added 50 new `SECTIONS` entries grouped into 14 new section
  headings, extended `SECTION_ORDER`. Header comment updated to "85
  categories, 1000 words total".
- `src/components/WordList.jsx` — "500 essential words" → "1000 essential
  words".

**vocab-master.html changes:**
- Mirrored the same 50 category blocks (500 words) into the inline
  `ALL_PARTS` array, the 50 `SECTIONS` entries (same 14 groupings), and the
  14 new `SECTION_ORDER` entries — done via a one-off Node script
  (`merge-html.cjs`, removed after use) that copied the category-block text
  directly from `data-part7.js`–`data-part11.js` to guarantee byte-identical
  data between the two apps.
- Updated word-count text: `<title>`, the "Learned: 0/500" stat, and the
  Word List page description → 1000. (The unrelated "500" in the Google
  Fonts `wght@...500...` URL was left untouched.)

**Verification:**
- `grep -o '{w:"' vocab-master.html` → 1000; duplicate-word and
  duplicate-category-id scans both empty.
- Extracted the inline `<script>` and ran `node --check` → syntax OK.
- `npm run build` in `vocab-app` succeeds.

**Outcome:** both apps now have 1000 words across 93 categories / 24 section
groupings, in full data parity.

---

### 2026-06-14 — Remove all A2-level words, replace with C1/C2/C2+

**Request:** remove the 11 A2-level words (too easy for this app) and replace
them with more advanced vocabulary, including a few C2+ words.

**Changes (both `vocab-app` and `vocab-master.html`, kept identical):**
- "Hesitation" (decision-making) — kept (it was a required word and the
  category is literally named after it), but its CEFR was corrected from A2
  to B1, which is a more accurate level for this word anyway.
- The other 10 A2 words were replaced in-place, keeping each new word in the
  same category/theme:
  - `research-inquiry`: Investigate → **Extrapolate** (C2)
  - `growth-expansion`: Expand → **Burgeon** (C2)
  - `money-shopping`: Refund → **Levy** (C1)
  - `tech-digital-life`: Offline → **Deprecated** (C2)
  - `climate-weather`: Forecast → **Inclement** (C1)
  - `travel-experiences`: Souvenir → **Wanderlust** (C1)
  - `lifestyle-habits`: Routine → **Perfunctory** (C2+)
  - `comparison-contrast`: Identical → **Antithetical** (C2)
  - `sound-light`: Flash → **Cacophony** (C2+)
  - `work-tasks`: Chore → **Onerous** (C1)

**Verification:**
- `grep -c 'cefr:"A2"'` → 0 in both files.
- Word count still 1000 in both, duplicate-word scan empty in both.
- New CEFR distribution (both files): B1 173, B2 449, C1 327, C2 43, C2+ 8.
- `node --check` on the extracted vocab-master.html inline script → OK.
- `npm run build` in `vocab-app` succeeds.

**Outcome:** no A2-level words remain in either app; the 10 replacements are
C1/C2/C2+, with "Perfunctory" and "Cacophony" added at C2+.

---

### 2026-06-16 — Navbar restructure + merged Test page

**Request:**
- Restructure nav: Vocabulary dropdown gains "Test"; add Grammar, Reading, Writing as flat
  nav tabs (no dropdown) navigating to "Coming soon" placeholder pages.
- Merge the three separate Quiz / Fill the Gap / Challenge pages into one "Test" page
  with a `‹ Mode ›` toggle that cycles between modes with wraparound.
- Grammar/Reading/Writing placeholder pages show a "🚧 Under construction" card.

**vocab-app (React) changes:**
- `src/utils/quiz.js` — removed `QUIZ_COUNTS`/`GAP_COUNTS`/`CHALLENGE_COUNTS`;
  added `TEST_MODE_ORDER`, `TEST_COUNTS`, and `TEST_MODE_META` (per-mode config map
  with toggleLabel, pageTitle, pageDesc, setupTitle, setupSub, poolUnit, countLabel,
  startLabel, resultTitle, resultMessage, secondaryButtonLabel).
- `src/index.css` — added `.mode-toggle-row`, `.mode-toggle-btn`, `.mode-toggle-label`.
- `src/components/Test.jsx` (new) — merged Quiz/Fill the Gap/Challenge page; `testMode`
  cycles via `TEST_MODE_ORDER`; QUIZ_MODES grid shown only in quiz mode; GSAP card
  entrance + score counter animations; per-mode pool filtering (GAP_POOL vs VOCAB_DATA).
- `src/components/ComingSoon.jsx` (new) — placeholder page used for Grammar/Reading/Writing.
- `src/components/Navbar.jsx` — SECTIONS updated (Vocabulary dropdown gains Test;
  Grammar/Reading/Writing added as flat `{id, label, page}` entries rendered without
  dropdown caret via `if (!section.pages)` guard).
- `src/App.jsx` — imports Test/ComingSoon; routes `test`/`grammar`/`reading`/`writing`.
- Deleted: `src/components/Quiz.jsx`, `FillGap.jsx`, `Challenge.jsx`.

**vocab-master.html changes:**
- CSS: added `.mode-toggle-row`/`.mode-toggle-btn`/`.mode-toggle-label`.
- Nav markup: Vocabulary dropdown gains "Test"; Grammar/Reading/Writing added as flat
  `.nav-group` tabs (no `.nav-dropdown`).
- Page sections: removed `#page-quiz`/`#page-gap`/`#page-challenge`; added `#page-test`
  (with `testTitle`/`testDesc`/`testModeLabel` dynamic IDs), `#page-grammar`,
  `#page-reading`, `#page-writing`.
- JS: `NAV_SECTIONS` updated; `goToPage` null-checks dropdown-item lookup for flat tabs;
  `renderTopicFilters` accepts function-or-string `unitLabel`; entire Quiz/Gap/Challenge
  JS block (~330 lines) replaced with consolidated Test block (`TEST_MODE_META`,
  `testPool`, `buildTestQuestion`, `renderTestModes/Counts/SetupCopy`, `cycleTestMode`,
  `renderTestQuestion`, `handleTestAnswer`, `showTestResult`); INIT updated.

**Verification:**
- `npm run lint` + `npm run build` in `vocab-app`: clean, build succeeds.
- `node --check` on extracted vocab-master.html inline script: OK.
- Grep confirms zero old `page-quiz`/`page-gap`/`page-challenge` section IDs remain;
  zero old `state.quiz`/`quizPool`/`QUIZ_COUNTS` references remain.

**Outcome:** Both apps now have a single "Test" page with Quiz/Fill the Gap/Challenge
mode cycling; Grammar/Reading/Writing are placeholder pages with active-tab highlighting;
full feature parity maintained between vocab-app and vocab-master.html.
