# IELTS Vocab Master — Navbar Restructure + Merged "Test" Page

## Context

`ielts-vocab-master` ships two parity-kept implementations: `vocab-app/`
(React + Vite) and `vocab-master.html` (standalone single-file app). Both
currently use a two-section nav:

- **Vocabulary**: Word List, Examples
- **Reading**: Quiz, Fill the Gap, Challenge

This spec restructures the nav into four top-level groups and merges the
three quiz-style pages (Quiz / Fill the Gap / Challenge) into a single
"Test" page with a mode-cycling toggle, since all three already share the
same topic/CEFR/category filters and count options.

## 1. Navigation structure

New top-level nav order, left to right:

**Vocabulary** (dropdown) → **Grammar** → **Reading** → **Writing**

- **Vocabulary** dropdown: Word List, Examples, **Test** (replaces the old
  Quiz / Fill the Gap / Challenge entries with one "Test" entry).
- **Grammar**, **Reading**, **Writing**: flat nav buttons — no dropdown
  caret, each is a single page. Clicking navigates to a placeholder page
  (e.g. "Grammar — Coming soon") with normal active-tab highlighting, same
  as any other page. Content for these pages is out of scope for this spec
  beyond the placeholder.

## 2. Merged "Test" page

One page replaces the separate Quiz / Fill the Gap / Challenge pages.

### Setup screen

- **Mode toggle** at the top: `‹  Quiz  ›`-style control with prev/next
  buttons. Clicking cycles `Quiz → Fill the Gap → Challenge → Quiz → ...`
  and the reverse direction, wrapping at both ends (Quiz ‹ wraps to
  Challenge; Challenge › wraps to Quiz).
- When mode = **Quiz**: the existing 5-option question-type grid
  (Definition Match, Word from Definition, Synonym Match, Antonym Match,
  Mixed Review) appears below the toggle, exactly as today, with its own
  `quizMode` state.
- When mode = **Fill the Gap** or **Challenge**: that grid is hidden.
  `quizMode` state is retained (not reset) so switching back to Quiz
  restores the previous selection.
- **Count row** (10 / 20 / 30 / All) — shared `count` state across all
  three modes (the option values are already identical:
  `QUIZ_COUNTS === GAP_COUNTS === CHALLENGE_COUNTS === [10, 20, 30, "all"]`).
  Label wording adapts: "questions" for Quiz/Challenge, "sentences" for
  Fill the Gap.
- **Filters & categories** (`TopicCefrFilter` / topic-cefr filter chips) —
  shared `filters` state, persists when switching modes.
- **Start button** — label adapts per mode: "Start Quiz" / "Start
  Exercise" / "Start Challenge".
- Pool source per mode: Quiz/Challenge use `VOCAB_DATA` filtered by
  `matchesFilters`; Fill the Gap uses `GAP_POOL` (the subset of
  `VOCAB_DATA` with fill-in-the-blank sentences) filtered the same way.

### Play screen

Each mode keeps its existing question-building logic:
- Quiz: `buildQuestion(word, quizMode === "mixed" ? randomMixedMode(word) : quizMode)`
- Fill the Gap: `buildGapQuestion(word)`
- Challenge: `buildHybridQuestion(word)`

Existing per-mode play UI (progress bar, score, gap-sentence rendering,
correct/wrong option highlighting) is preserved as-is, just routed through
the shared page.

### Result screen

Per-mode copy is preserved:
- Quiz: "Quiz Complete", existing `resultMessage`, buttons "Try Again" /
  "Change Mode".
- Fill the Gap: "Exercise Complete", existing `resultMessage`, button "Try
  Again" only.
- Challenge: "Challenge Complete", existing `resultMessage`, buttons "Try
  Again" / "Change Setup".

"Change Mode"/"Change Setup"/"Try Again" return to the Test setup screen
with the current `testMode`, `quizMode`, `filters`, and `count` retained.

## 3. Implementation approach

### vocab-app (React)

- New `src/components/Test.jsx` replaces `Quiz.jsx`, `FillGap.jsx`,
  `Challenge.jsx`. Holds:
  - `testMode` state (`"quiz" | "gap" | "challenge"`), cycled by prev/next
    buttons with wraparound.
  - Shared `filters` (`DEFAULT_TOPIC_FILTERS`) and `count` state.
  - `quizMode` state (only relevant/shown when `testMode === "quiz"`).
  - A per-mode config map providing: pool source, question builder, page
    title/description, count-row label noun, start-button label,
    result-screen title/message/buttons.
- New `src/components/ComingSoon.jsx` — simple placeholder page (title +
  "Coming soon" message), used for Grammar/Reading/Writing.
- `Navbar.jsx`: `SECTIONS` config updated —
  - `vocabulary` section's `pages` becomes `list`, `examples`, `test`.
  - `grammar`, `reading`, `writing` become flat single-page nav items
    (no `pages` array / no dropdown caret) that navigate directly.
- `App.jsx`: routing updated — `test` → `<Test>`, `grammar`/`reading`/
  `writing` → `<ComingSoon title="..."/>`.
- `utils/quiz.js`: no functional changes required (counts already
  identical across modes); may add small per-mode label/config constants
  used by `Test.jsx`.

### vocab-master.html

- Consolidate `#page-quiz`, `#page-gap`, `#page-challenge` into one
  `#page-test` section containing the mode-toggle + shared setup/play/
  result markup, with per-mode copy swapped in via JS.
- Add `#page-grammar`, `#page-reading`, `#page-writing` placeholder
  sections ("Coming soon").
- Update `NAV_SECTIONS` and the nav markup:
  - `vocabulary` dropdown items: `list`, `examples`, `test`.
  - `grammar`, `reading`, `writing` become flat tab buttons (no dropdown),
    each its own "section" of one page.
- Refactor the existing quiz/gap/challenge render & start logic (filter
  rendering, pool computation, question building, result rendering) into
  shared functions parameterized by mode, mirroring the React config map.

## 4. Verification

Playwright pass on both apps, desktop (1280px) and mobile (375px):
- Nav order is Vocabulary / Grammar / Reading / Writing; Vocabulary
  dropdown shows Word List / Examples / Test; active-tab highlighting
  correct for all pages including Grammar/Reading/Writing placeholders.
- Test page: mode toggle cycles forward and backward through Quiz / Fill
  the Gap / Challenge with wraparound at both ends; Quiz-only
  question-type grid shows/hides correctly per mode.
- Filters, categories, and count selection persist when switching test
  modes.
- Each mode's play/result flow still produces correct questions and
  scoring (spot-check one run per mode).
- Grammar/Reading/Writing pages render "Coming soon" placeholders with
  correct nav highlighting.
- No console errors in either app at any viewport.

## Out of scope

- Actual content for Grammar/Reading/Writing pages (placeholders only).
- Any changes to vocabulary data, word counts, or CEFR levels.
