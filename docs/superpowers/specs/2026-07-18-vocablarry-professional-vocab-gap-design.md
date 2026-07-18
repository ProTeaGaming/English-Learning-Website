# VocabLarry Professional Environment — Vocab Quiz (Gap mode) (design)

## Context

This is sub-project 2c of the VocabLarry Professional Environment rebuild
(see `docs/superpowers/specs/2026-07-17-vocablarry-professional-foundation-design.md`,
`docs/superpowers/specs/2026-07-17-vocablarry-professional-vocab-browse-word-design.md`,
and `docs/superpowers/specs/2026-07-18-vocablarry-professional-vocab-quiz-design.md`
for parent context and locked-in architecture decisions). Foundation, Vocab
Browse + Word, and Vocab Quiz (Quiz mode: Definition Match, Word from
Definition, Synonym Match, Antonym Match, Mixed Review) are all merged to
`main`.

The production `VocabLarry/` SPA's Test page has 3 top-level modes — Quiz,
Gap (fill-the-blank), Challenge (random mix of everything). This spec
covers **Gap mode only**: Contextual Definition, Lexical Nuance,
Collocation & Idiom, Connotation Match, and Mixed Review (which randomly
picks one of the other four per question). Challenge mode remains a
separate future sub-project.

In production, Gap mode is **not free-typed input** — it is
multiple-choice, structurally identical to Quiz mode's answer mechanism
(`buildOptions()`, same `textContent === correct` scoring). The only
differences are: the question text is a sentence with a blank instead of
a headword/definition, and each sub-mode selects its distractor pool
differently. The `Word` model already has a dedicated `gap` field (a
sentence containing the literal placeholder `___`, separate from
`example`), and it's already serialized by the existing `/api/words/`
endpoint used by Quiz mode — so, like Quiz mode, this needs **no new
backend**.

## Decisions

- **No new backend, no new URLs.** Gap mode is added to the *existing*
  `/vocab/quiz/` setup page and `/vocab/quiz/play/` play page — same
  routes, same views, same `/api/words/` / `/api/categories/` /
  `/api/cefr-levels/` data source as Quiz mode. No new models, no new
  migrations, no new API surface.
- **Setup page gets a Quiz/Gap family toggle.** The single flat `<select
  name="mode">` from the Quiz-only build becomes two selects, one per
  family, shown/hidden by a Quiz/Gap radio toggle (small inline script —
  no new JS module). Only the active family's select is enabled, so the
  form still submits a single `mode` value. This introduces the
  family-toggle shape production uses (Quiz/Gap/Challenge) without
  building Challenge yet — the toggle just has two options for now, and
  Challenge slots in as a third later without re-touching this structure.
- **`mode` stays a single query param, gap values are `gap`-prefixed.**
  Quiz family values are unchanged (`definition`, `word`, `synonym`,
  `antonym`, `mixed`). Gap family values are `gap-context`, `gap-nuance`,
  `gap-collocation`, `gap-connotation`, `gap-mixed`. The play page's JS
  branches on `mode.indexOf('gap-') === 0` to route into gap question
  generation — same single-param dispatch shape `vocab-quiz.js` already
  uses, no second `family` param needed.
- **Target pool requires a usable gap sentence.** `buildPool()` adds a
  filter — `word.gap && word.gap.includes('___')` — applied whenever the
  selected mode is any `gap-*` value, on top of the existing
  category/CEFR filters. Not every word has a written gap sentence, so
  this excludes ineligible words from being the *asked-about* word.
  **Distractor options are still drawn from the full unfiltered word
  list** (matching Quiz mode's existing behavior and production's
  `buildGapQuestion`) — distractors only need a headword, not their own
  gap sentence.
- **Question count clamps silently**, same as Quiz mode's existing
  `Math.min(requested, pool.length)` — if a category/CEFR filter leaves
  fewer gap-eligible words than requested, the quiz just runs shorter, no
  validation message on the setup page.
- **Gap question generation is ported faithfully from `vocablarry.html`'s
  `buildGapQuestion`**, not redesigned. For all sub-modes, the "correct"
  answer is always the target word's headword, and `others` (the
  distractor source) is always the full word list minus the target:
  - **Contextual Definition** (`gap-context`, default): distractor pool
    is same-part-of-speech words; falls back to the full word list if
    fewer than 3 same-POS matches exist.
  - **Lexical Nuance** (`gap-nuance`): distractor pool is words sharing
    at least one synonym with the target word; falls back to
    same-part-of-speech if fewer than 3 matches.
  - **Collocation & Idiom** (`gap-collocation`): distractor pool is words
    in the same category as the target; falls back to same-part-of-speech
    if fewer than 3 matches.
  - **Connotation Match** (`gap-connotation`): distractor pool is the
    target's listed antonyms, plus same-part-of-speech words that aren't
    already in that antonym list; falls back to same-part-of-speech alone
    if fewer than 2 antonym matches exist.
  - **Mixed Review** (`gap-mixed`): per question, randomly picks one of
    the four concrete sub-modes above and generates that kind of
    question (same per-question-random shape as Quiz mode's existing
    Mixed Review).
- **Blank rendering**: the target word's `gap` sentence has its first
  `___` replaced with a `<span class="vocab-quiz-blank">_____</span>`,
  shown in the same prompt/text slot Quiz mode's question card already
  uses. Prompt copy above it is a hardcoded English string per sub-mode
  (e.g. "Choose the word that best completes the sentence.") — matches
  Quiz mode's existing hardcoded English prompts; this project's i18n
  only covers nav/chrome, not quiz content.
- **Answer feedback is enhanced for gap questions**: in addition to the
  existing word + definition line, gap feedback also shows the target
  word's full `example` sentence with `<em>`/`</em>` tags stripped —
  matching production's richer gap feedback. Quiz-mode feedback is
  unchanged. `example` is already fetched via `/api/words/`, no new data
  needed.
- **No score/progress persistence** — same as Quiz mode, purely ephemeral
  client-side session state.
- **Count field label stays static** ("Questions") rather than switching
  to production's "sentences" unit-label for Gap — each gap question is
  inherently one sentence already, so the distinction adds no real
  clarity here and isn't worth extra JS.
- **No dialect substitution, no Vietnamese content translation** — same
  exclusions as prior phases; gap sentences render whatever their stored
  `gap`/`example` fields say.

## Architecture

```
templates/
  vocab/
    quiz_setup.html   (add Quiz/Gap family toggle + Gap sub-mode select)
static/
  js/vocab-quiz.js     (add buildGapQuestion + gap-mode dispatch/rendering)
  css/vocab.css         (append: family toggle, .vocab-quiz-blank)
```

No changes to `config/urls.py`, `config/views_vocab.py`, or `quiz_play.html`
— both existing routes/views are reused unmodified; `quiz_play.html`'s
mount point and script tag already work for any `mode` value.

## Components

- **`quiz_setup.html`** — the existing single mode `<select>` is replaced
  with: a Quiz/Gap radio toggle, a Quiz sub-mode `<select>` (unchanged 5
  options), and a new Gap sub-mode `<select>` (Contextual Definition /
  Lexical Nuance / Collocation & Idiom / Connotation Match / Mixed
  Review). An inline script toggles `hidden`/`disabled` on the two
  selects based on the radio choice, so the form always submits exactly
  one `mode` value regardless of which family is active. Category, CEFR,
  and count fields are unchanged and shared by both families.
- **`static/js/vocab-quiz.js`** — extended, not restructured:
  - `buildPool()` gains the gap-eligibility filter for `gap-*` modes.
  - New `buildGapQuestion(word, gapMode)` mirrors production's function:
    resolves `gap-mixed` to a concrete sub-mode first, then builds the
    sub-mode-specific distractor pool, calls the existing `buildOptions()`
    helper unchanged, and returns `{ type: 'gap', prompt, text, options,
    correct, word }` (the `text` field holds the blanked sentence HTML).
  - `generateQuestions()` branches: `mode.indexOf('gap-') === 0` calls
    `buildGapQuestion` with the sub-mode (stripped of the `gap-` prefix,
    or resolved via `gap-mixed`'s per-question random pick) instead of
    the existing `buildQuestion`.
  - `handleAnswer()` gains one added branch: when `q.type === 'gap'`,
    append the target word's `example` (stripped of `<em>`/`</em>`) to
    the feedback line. Existing Quiz-mode feedback path is untouched.
  - `renderQuestion()`/`renderResults()` are unchanged — they already
    render whatever `prompt`/`text`/`options`/`correct` a question object
    carries, regardless of which builder produced it.
- **`static/css/vocab.css`** — small additions: family-toggle radio
  styling (reusing existing form patterns) and `.vocab-quiz-blank` (an
  underlined/emphasized inline span for the blank).

## Data flow

`GET /vocab/quiz/` → user picks Quiz or Gap family, a sub-mode, category,
CEFR, count → form submits (plain GET) → browser navigates to
`/vocab/quiz/play/?category=...&cefr=...&count=...&mode=gap-nuance` (e.g.)
→ `vocab_quiz_play` renders the same shell as Quiz mode → `vocab-quiz.js`
fetches `/api/words/` once → detects the `gap-` prefix → builds the
gap-eligible target pool → generates gap questions → renders/answers/
results exactly as Quiz mode's existing flow does, just with gap-shaped
question objects. "Try Again" and "Change Settings" behave identically to
Quiz mode (regenerate from same filters / navigate back to setup).

## Error handling

Same as Quiz mode: if the gap-eligible pool is empty for the selected
category/CEFR combination, the play page shows the existing "No words
available for this combination — try different settings" message with a
link back to `/vocab/quiz/`, rather than a new gap-specific error path.
`/api/words/` fetch failure uses the existing generic error message.

## Testing

Same split as Quiz mode. Python/pytest coverage: the setup page's
existing tests (renders, lists categories, lists CEFR levels) stay
unaffected since the family-toggle restructure doesn't remove or rename
the `mode` field; new tests assert the Gap family's 5 sub-mode options
and the toggle markup appear in the rendered form. No server-side
equivalent of gap question generation to unit test via pytest.

The gap question-generation/distractor-pool logic in
`vocab-quiz.js` has no Python-testable surface — verified via
`node --check` for syntax plus a line-by-line comparison against
production's `buildGapQuestion` (already pulled during design research)
rather than a "looks right" pass, per the precedent set in Quiz mode.
Manual browser testing covers: each of the 5 gap sub-modes generating a
sensible blanked sentence and options, correct scoring, the example-
sentence feedback appearing only on gap questions, Mixed Review picking
across all 4 concrete sub-modes, the zero-pool error case, and Try Again
/ Change Settings both working from a gap-mode quiz.

## Explicitly out of scope for this phase

Challenge mode, free-typed (non-multiple-choice) answer input, hand-
picking individual words as a quiz source, learned-state filtering,
section grouping, Vietnamese content translation, dialect-based word
substitution, dynamic "questions"/"sentences" unit-label switching, and
any score/progress persistence. Challenge mode gets its own design/plan
cycle once this phase is proven, reusing the same family-toggle shape
this spec introduces.
