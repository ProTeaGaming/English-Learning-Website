# VocabLarry Professional Environment — Vocab Quiz Visual Retrofit (design)

## Context

This is the second of four decomposed "visual retrofit" sub-projects (the
first, Vocab Browse/Category/Word, is done and merged), continuing the
user's directive to copy production's (`VocabLarry/vocablarry.html`)
designs directly rather than re-derive VLPE's own visual language.

Scoped to 2 existing VLPE pages: `vocab/quiz_setup.html` (mode/family/
category/CEFR/count selection form) and `vocab/quiz_play.html` +
`static/js/vocab-quiz.js` (the question/answer/results flow, entirely
client-rendered). Both currently use minimal "starter" CSS — plain
`<select>` dropdowns, a bare bordered card for questions, unstyled result
buttons.

Production's equivalents were researched directly from `vocablarry.html`
(read-only — confirmed via a dedicated Explore pass over `#page-test`,
its CSS, and the render functions that build it; nothing in that file was
modified): a glass-panel `.setup-card` containing a prev/next family
cycler (Quiz/Gap/Challenge), a clickable mode-card grid (`.modeCard`)
replacing the current `<select>`, single-value chip filters for category/
CEFR, and a pill-based count selector (`.count-row`) with a custom-number
option; a glass-panel `.q-card` play screen with a gradient progress bar
and color-coded correct/wrong option states; and a glass-panel
`.result-card` with a gradient score number, tiered result copy, and a
styled review-answers list.

**Unrelated bug found during research, fixed as part of this phase:**
`static/js/vocab-quiz.js` hardcodes the pre-rename path `/vocab/quiz/` in
two places (the "no words match" error screen's "Back to setup" link, and
the results screen's "Change Settings" button) — both 404 today, since the
Nav & Routing Skeleton phase renamed this to `/vocabulary/quiz/`. This
slipped through that phase's own verification because it's a JS string
literal in a static file, not a Django `{% url %}` tag, so neither the
route-rename tests (which check rendered HTML) nor a grep for old URL
*names* would have caught it.

## Decisions

- **Word hand-picking ("By Category" vs "By Words" source toggle +
  paginated word-picker) stays out of scope**, deferred again — this is
  the third time this exact feature has been deferred in VLPE's history.
  Production's setup card keeps this toggle; this retrofit only builds the
  "By Category" path (category/CEFR filtering), matching VLPE's existing
  scope.
- **Fix the two hardcoded `/vocab/quiz/` links in `vocab-quiz.js`** to
  `/vocabulary/quiz/` — unrelated to the visual retrofit itself, but
  found during this phase's research and cheap to fix while already in
  the file.
- **Family selector (Quiz/Gap/Challenge) becomes a prev/next cycler**
  (`‹ Quiz ›`), replacing the current 3-way radio group — ported from
  production's `.mode-toggle-row`/`.mode-toggle-btn`/`.mode-toggle-label`.
  The underlying state model is unchanged (still exactly one of
  `"quiz"`/`"gap"`/`"challenge"` selected at a time, still drives which
  field-set is shown/enabled) — only the control's visual/interaction
  shape changes, from "all 3 visible as radios" to "1 visible, cycle with
  ‹/›".
- **Mode selection becomes a clickable card grid** (`.modeCard`/
  `.option-grid`), replacing the `<select id="quizModeSelect">` /
  `<select id="gapModeSelect">` dropdowns — one grid of 5 cards for Quiz's
  modes (Definition Match/Word from Definition/Synonym Match/Antonym
  Match/Mixed Review), a separate grid of 5 cards for Gap's sub-modes
  (Contextual Definition/Lexical Nuance/Collocation & Idiom/Connotation
  Match/Mixed Review), shown/hidden based on the family cycler exactly
  like the current dropdowns are — Challenge shows neither grid (no mode
  choice, matches today). Each card shows a name + one-line description
  (production's own copy, transcribed from its `QUIZ_MODES`/`GAP_MODES`
  data arrays) — VLPE has no such copy today (the current `<option>` text
  IS the mode name, no description), so this genuinely adds new descriptive
  text, not just a new visual shape for existing text.
- **Category and CEFR filters become single-select chip rows**, reusing
  the exact `.chip`/`.filter-row`/`.filters` system already built in
  `base.css` for the category browse page's filter bar — NOT production's
  richer multi-row `.headline-bar` + `.filters` browse-bar (which exists
  because production's version also has the word-picker's own filtering
  needs baked in). A single chip row per field (one for category, one for
  CEFR), each a plain-radio-like single-select (clicking a chip marks it
  active and updates a hidden form field), replacing the two `<select>`
  elements. This is a real interaction-shape change (chips instead of a
  dropdown) but reuses existing CSS/markup patterns rather than porting a
  new system.
  **CEFR chip color-coding needs one small CSS addition, not reuse of the
  browse page's existing rule as-is:** `base.css` currently only defines
  `.chip.active[data-browse-cefr="X"]` (12 rules, one per CEFR level),
  scoped specifically to the browse page's own chips. Production's own
  CSS anticipates exactly this multi-page situation — its real selector
  list is `.chip.active[data-cefr="A1"],.chip.active[data-browse-cefr="A1"],
  .chip.active[data-cat-cefr="A1"]{...}`, one shared rule matching several
  page-specific attribute names. This retrofit's quiz-page CEFR chips get
  their own attribute, `data-quiz-cefr`, added to each of the 12 existing
  rules' selector list (comma-separated, matching production's own
  pattern) — not a reuse of `data-browse-cefr` on a non-browse page, and
  not a duplicated set of 12 new rules.
- **Count selector becomes pill chips** (`.count-row`) — 10/20/30/All as
  chips (matching the category browse page's already-established chip
  interaction) plus a "Custom" chip that reveals an inline number input,
  ported from production's `.custom-chip`/`.custom-count-input`. This is
  new relative to VLPE's own prior precedent (the Grammar Test Mode phase
  explicitly declined a custom-count input, deferring to the fixed
  10/20/30/All set) — but that precedent was about *borrowing* vocab's
  simpler shape for a *different* feature (grammar's cross-topic test);
  here we're retrofitting vocab's own quiz to match vocab's own
  production counterpart, which genuinely has this control, so it's
  in-scope for a "copy production exactly" pass on this specific page.
- **Glass-panel visual design system** (`.setup-card`/`.q-card`/
  `.result-card`, all sharing one blurred dark/light card recipe) ported
  verbatim, with the established `rgba(var(--violet))` → `rgb(var(--violet)
  / X)` conversion.
- **Play screen gains a "Leave" link** at the top (`.back-btn`, ported
  from production) — VLPE currently has no way to exit a quiz mid-play
  except the browser back button. Links to `/vocabulary/quiz/` (the
  setup page).
- **Gap-mode blanks get richer styling** — bold, accent-colored,
  dashed-underline text (production's `.gapblank`), replacing the current
  plain underlined placeholder. The underlying blank-substitution logic
  (`word.gap.replace("___", ...)`) is unchanged; only the inserted
  markup's CSS class and content (5 underscores instead of a text
  placeholder) changes to match production exactly.
- **Card-entrance and score-counter animations get the same visual
  effect as production, implemented without adding GSAP as a new
  dependency.** Production uses GSAP for both (a fade+slide-up on each
  question card render, a tweened 0→score count-up on the results
  screen). VLPE has never loaded GSAP anywhere in this rebuild. Rather
  than pull in a new external library for two small, purely decorative
  animations, this retrofit reproduces the same visual outcome with
  plain CSS (a `@keyframes` fade+translateY animation applied via a CSS
  class added on render) and plain JS (a `setInterval`/
  `requestAnimationFrame`-driven number count-up) — same look, no new
  dependency, consistent with this project's established pattern of
  adapting production's mechanism to VLPE's own architecture rather than
  porting it verbatim when a lighter-weight equivalent achieves the same
  visual result (e.g. the nav dropdown was similarly adapted from
  production's JS page-swap to VLPE's real routing in an earlier phase).
- **Results screen's review-answer list gets styled tags** (`.review-tag
  .correct`/`.review-tag .wrong`, plain ✓/✗ text glyphs per production —
  not SVG icons) replacing the current plain-text-only review items.
- **No i18n content translation** — same exclusion as every prior phase.
  New static chrome labels (mode-card descriptions, "Leave", "Custom",
  tiered result messages) get `data-i18n` attributes + `en`/`vi` entries in
  `static/js/i18n.js`, matching every existing string's dual-entry
  pattern. Question/answer/definition content itself is never translated
  (unchanged — it's sourced from the same `/api/words/` data every other
  vocab page already treats as untranslated).
- **No new models, no new migrations, no new backend/API endpoints.**
  This phase is templates/CSS/JS only — `vocab_quiz_setup`'s view context
  (categories, cefr_levels) is already sufficient for chip rendering; the
  play page's data still comes entirely from the existing `/api/words/`
  and `/api/categories/` endpoints `vocab-quiz.js` already fetches.

## Architecture

```
templates/
  vocab/
    quiz_setup.html          (rewrite — glass-panel setup-card, family
                              cycler, mode-card grids, chip filters,
                              count pills)
    quiz_play.html            (extend — add the "Leave" back-link;
                              #quizPlayRoot itself is populated entirely
                              by JS, no other template change needed)
static/
  js/
    vocab-quiz.js              (rewrite render functions — q-card/
                                progress-bar/options/feedback markup and
                                classes matching production; gapblank
                                class+content; CSS-class-driven card
                                entrance instead of GSAP; count-up
                                animation instead of GSAP; fix the 2
                                hardcoded /vocab/quiz/ paths; family-
                                cycler and mode-card click wiring moves
                                here from quiz_setup.html's old inline
                                script, since the cycler/grid interaction
                                is now richer than a simple family
                                toggle)
    i18n.js                     (add new chrome-label keys: mode-card
                                descriptions, nav.leave, common.custom,
                                tiered result-message keys)
  css/
    vocab.css                   (rewrite/extend — .setup-card/.q-card/
                                .result-card glass-panel family,
                                .mode-toggle-row, .modeCard/.option-grid,
                                .count-row/.custom-chip, .back-btn,
                                richer .q-opt/.gapblank/.review-tag
                                states, CSS-keyframe card-entrance
                                animation — all ported from production
                                with rgba(var(--violet)) converted to
                                rgb(var(--violet) / X))
```

## Components

- **`templates/vocab/quiz_setup.html`** — glass-panel `.setup-card`
  wrapping: the family cycler (`‹ Quiz ›` style, JS-driven, no page
  reload), one of two mode-card grids (Quiz's 5 or Gap's 5, shown per
  family; Challenge shows neither), a category chip row, a CEFR chip row,
  a count-pill row with a custom-number option, and the Start button. The
  underlying `<form method="get" action="{% url 'vocabulary_quiz_play' %}">`
  and its field `name`s (`mode`, `category`, `cefr`, `count`) are
  unchanged from today — only their *rendering* moves from `<select>`/
  radio to card/chip/pill, so `vocabulary_quiz_play`'s query-string
  contract (already consumed by `vocab-quiz.js`) doesn't change at all.
- **`static/js/vocab-quiz.js` (extended, not just the render functions)**
  — gains the family-cycler and mode-card/chip/count-pill click-handling
  logic (moved from `quiz_setup.html`'s old inline `<script>` block, which
  is removed), plus the existing question-generation/scoring logic
  (unchanged) with rewritten `renderQuestion`/`renderResults`/`renderError`
  markup to match production's `.q-card`/`.result-card` shape, and the 2
  hardcoded URL fixes.
- **`templates/vocab/quiz_play.html`** — adds one `.back-btn` "Leave" link
  above `#quizPlayRoot`, linking to `{% url 'vocabulary_quiz_setup' %}`.
- **`static/css/vocab.css`** — the full new visual system for both pages,
  additive/replacing the current `.vocab-quiz-*` rules.

## Data flow

Unchanged end-to-end shape: `GET /vocabulary/quiz/` renders the setup
form (now card/chip/pill-driven, same field names) → submit → `GET
/vocabulary/quiz/play/?mode=...&category=...&cefr=...&count=...` → the
near-empty play page loads → `vocab-quiz.js` fetches `/api/words/` +
`/api/categories/`, builds `state.pool`/questions exactly as today,
renders the new `.q-card` markup, scores answers, and on completion
renders the new `.result-card` markup. No new requests, no new params, no
account writes — this phase changes only how the exact same data flow is
rendered and interacted with visually.

## Error handling

- Empty-pool ("no words match this combination") case: unchanged trigger
  condition, re-styled via the same glass-panel/error-text treatment
  used elsewhere, with the corrected `/vocabulary/quiz/` link (the bug
  fix from Decisions).
- `/api/words/`/`/api/categories/` fetch failure: unchanged generic
  error message, same re-styled treatment.
- Family cycler / mode-card / chip / count-pill state is pure client-side
  UI state until form submission — no server-side validation changes
  needed, since the submitted field values are identical to what the old
  controls already produced (e.g. clicking the "Definition Match" card
  still results in `mode=definition` on submit, exactly as the old
  `<option value="definition">` did).

## Testing

Python tests (extend `tests/test_vocab_pages.py`): quiz setup renders the
family cycler, both mode-card grids (with correct hidden/shown markup
matching the default family), the category/CEFR chip rows (including an
"All" chip and one real chip per seeded category/level), the count-pill
row including the Custom chip and its number input; quiz play renders the
new "Leave" link pointing at `/vocabulary/quiz/`. These are all
render/markup-presence assertions via Django's test `Client` — matching
the existing test style for this page.

No Python-testable surface for: the family cycler's actual cycling
interaction, mode-card/chip/count-pill click-to-select behavior, the
question-generation/scoring/results flow (all pure client-side JS,
unchanged logic — this project's standing precedent from the original
Vocab Quiz phase already established that this file's algorithmic
correctness is verified by tracing the ported logic against production's
source during code review, not by Python tests), the CSS keyframe
card-entrance animation, or the results score count-up animation. The
implementation plan must include a real Playwright click-through: cycle
through all 3 families and confirm the correct mode-card grid (or neither,
for Challenge) shows each time; click a mode card, a category chip, a CEFR
chip, and a count pill (including Custom, confirming the number input
appears and its value is what gets submitted) and confirm the resulting
`/vocabulary/quiz/play/?...` query string matches what was selected;
click "Leave" and confirm it navigates to `/vocabulary/quiz/`; complete a
short real quiz and confirm the question card, option correct/wrong
color states, gap-mode blank styling (for at least one Gap-family run),
and the results screen (score, review list) all render correctly; both
themes.

## Explicitly out of scope for this phase

The "By Category" vs "By Words" source toggle and the paginated
word-picker grid (deferred, third time). Any change to the Grammar pages
(separate future sub-projects). Any change to the actual quiz-generation
algorithm, scoring logic, or the shape of data fetched from `/api/words/`/
`/api/categories/` — this phase is visual/interaction-shape only. Adding
GSAP as a dependency (the same visual outcome is achieved without it, per
Decisions). Vietnamese translation of quiz question/answer content
(unchanged — only new chrome labels get translated).
