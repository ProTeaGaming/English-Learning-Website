# VocabLarry Professional Environment — Vocab Quiz (Quiz mode) (design)

## Context

This is sub-project 2b of the VocabLarry Professional Environment rebuild
(see `docs/superpowers/specs/2026-07-17-vocablarry-professional-foundation-design.md`
and `docs/superpowers/specs/2026-07-17-vocablarry-professional-vocab-browse-word-design.md`
for parent context and locked-in architecture decisions). Foundation
(scaffold, home, auth) and Vocab Browse + Word (category browse, paginated
word list, word detail with progress toggle) are both merged to `main`.

The production `VocabLarry/` SPA's vocabulary Test page has 3 top-level
modes — Quiz, Gap (fill-the-blank), Challenge (random mix of everything) —
with 5 submodes each for Quiz and Gap. That's too much for one spec, on
top of already being the largest remaining piece of the Vocab section.
This spec covers **Quiz mode only**: Definition Match, Word from
Definition, Synonym Match, Antonym Match, and Mixed Review (which
randomly picks one of the other four per question). Gap mode and
Challenge mode are separate future sub-projects, built on the same
architecture once this one is proven.

Quiz results are **not persisted anywhere** in production — no backend
write happens on quiz completion, no `learn_map`/`grammar_map` update, no
score history. It's a purely ephemeral, session-scoped scoring exercise
(confirmed by reading `vocablarry.html`'s `showTestResult()`, which only
renders a results screen and never calls a sync/save function). This
significantly narrows this sub-project's scope: no new backend writes are
needed anywhere in it.

## Decisions

- **No new backend at all.** Two Django views render static template
  shells; all question generation, scoring, and the play flow happen in
  client-side JS, fetching from the **existing** `/api/words/`,
  `/api/categories/`, `/api/cefr-levels/` JSON endpoints (already built
  for the SPA, already returning every field this needs — `definition`,
  `synonyms`, `antonyms`, `pos`, `category_id`, `cefr_code`). No new
  models, no new migrations, no new API surface.
- **Setup is a real server-rendered form; play is client-driven.**
  `GET /vocab/quiz/` renders a form (category, CEFR level, question
  count). Submitting it is a plain `GET` that navigates to
  `/vocab/quiz/play/?category=<slug>&cefr=<code>&count=<n>&mode=<id>`.
  The play page's view renders an near-empty template shell; its JS
  (`static/js/vocab-quiz.js`) reads the query string via
  `URLSearchParams(window.location.search)`, fetches word data, and
  drives the entire question → answer → next → results flow in the
  browser with no page reloads between questions — matching the current
  SPA's UX (in-place DOM updates, not page navigation per question).
  Consistent with Foundation's "Django templates + plain per-page JS
  modules calling existing `api/` endpoints" decision, just with more
  logic in this one module since the quiz interaction is inherently
  stateful in a way browse/word pages aren't.
- **Setup filters: category + CEFR level only**, both optional
  ("all categories" / "all levels" are valid selections). Question count
  is 10/20/30/All, matching production's `TEST_COUNTS`. No section
  grouping (already deferred in Vocab Browse + Word), no learned-state
  filter, no hand-picking individual words as a quiz source (production's
  `sourceMode: "words"` alternate flow) — all explicitly out of scope for
  this pass.
- **Question generation is ported faithfully from `vocablarry.html`**,
  not redesigned:
  - **Definition Match**: show the word, 4 definition options (1 correct
    + 3 distractor definitions from other words).
  - **Word from Definition**: show a definition, 4 word options.
  - **Synonym Match**: show the word, 4 word options where the correct
    answer is one of its synonyms. When this mode is selected, the target
    pool is filtered to only words with at least one synonym (words with
    none are excluded from the pool entirely before question count/random
    selection happens, not skipped one-by-one during generation) —
    matches production's `testPool()` filtering exactly.
  - **Antonym Match**: same shape and same pool-filtering rule, but
    filtered to words with at least one antonym instead.
  - **Mixed Review**: per question, randomly picks Definition/Word from
    Definition always available, plus Synonym/Antonym only when that
    specific word has synonyms/antonyms to draw from (matches
    `randomMixedMode()`'s exact logic).
  - **Distractor sampling matches production exactly**: wrong-answer
    options are sampled from the **full** word dataset fetched from
    `/api/words/`, not just the CEFR/category-filtered pool the quiz's
    real questions are drawn from. This is a faithful port of an existing
    behavioral detail (`buildQuestion`'s `others = VOCAB_DATA.filter(...)`
    uses the whole dataset), not a new design choice — the play page
    fetches all ~5,000 words once on load specifically to support this.
  - Target question count is `min(requested count, filtered pool size)`
    when the pool is smaller than requested (e.g. "30 questions" on a
    12-word category only produces 12).
- **No score/progress persistence** — matches production. The play page
  is pure client-side session state; refreshing the page loses progress
  (same as today).
- **Results screen includes a review list** (each question, the word,
  what you selected, the correct answer) — this is a render-only addition
  since the play flow already tracks every answer for scoring purposes;
  no new state design needed.
- **Nav: a new "Quiz" entry** alongside "Vocabulary" in
  `templates/partials/nav.html`, linking to `/vocab/quiz/`. Both live
  under the Vocabulary umbrella (Grammar's entry stays disabled).
- **No dialect substitution, no Vietnamese content translation** — same
  exclusions as Vocab Browse + Word; words render whatever their stored
  fields say.

## Architecture

```
config/
  urls.py            (add 2 routes under /vocab/quiz/)
  views_vocab.py     (add 2 view functions)
templates/
  vocab/
    quiz_setup.html   (category/CEFR/count/mode form)
    quiz_play.html    (near-empty shell — JS renders everything inside it)
  partials/
    nav.html           (add "Quiz" entry)
static/
  css/vocab.css        (append: setup form, play-screen question card,
                         progress bar, results/review styles)
  js/vocab-quiz.js      (question generation, play flow, scoring, results)
```

Routes:

```python
path('vocab/quiz/', vocab_quiz_setup, name='vocab_quiz_setup'),
path('vocab/quiz/play/', vocab_quiz_play, name='vocab_quiz_play'),
```

## Components

- **`vocab_quiz_setup` view** — queries `Category.objects.order_by('order')`
  and `CEFRLevel.objects.order_by('order')` for the form's category/CEFR
  select options, renders `quiz_setup.html`. The form also has a mode
  selector (Definition Match / Word from Definition / Synonym Match /
  Antonym Match / Mixed Review) and the count selector (10/20/30/All) —
  both are static option sets requiring no DB query, hardcoded directly
  in the template. No POST handling — the form submits via GET, so the
  browser's own query-string serialization does the work, and the play
  page is a plain bookmarkable/shareable URL.
- **`vocab_quiz_play` view** — renders `quiz_play.html` with no context
  beyond the base template chrome. All real behavior is client-side;
  the view's only job is serving the page shell and static asset links.
- **`static/js/vocab-quiz.js`** — on load: parses `category`, `cefr`,
  `count`, `mode` from the query string; fetches `/api/words/` (full
  dataset) and filters a target pool by `category_id`/`cefr_code` if
  those params are present; picks `min(count, pool.length)` words at
  random without replacement; generates one question per word using the
  selected mode's generator (or Mixed's per-question random pick);
  renders one question at a time (prompt, word/definition text, 4
  shuffled options); on answer click, disables options, highlights
  correct/incorrect, shows inline feedback (word + definition), and a
  "Next"/"See Results" button; tracks running score and the full answer
  list; on the last question, renders the results screen (score, message,
  Try Again / Change Settings / Review buttons) using the tracked answers
  for the review list.
- **`static/css/vocab.css`** — extended with setup-form styling (reusing
  `base.css`'s existing form/select patterns from Vocab Browse's category
  filter), a question-card layout, a progress bar, and results/review
  list styling — all scoped to `.vocab-quiz-*` classes, reusing the CSS
  custom properties already established in `base.css`.

## Data flow

`GET /vocab/quiz/` → user submits the form (plain GET) → browser
navigates to `/vocab/quiz/play/?category=...&cefr=...&count=...&mode=...`
→ `vocab_quiz_play` renders the shell → `vocab-quiz.js` fetches
`/api/words/` once → builds pool + generates questions → renders question
1 → user clicks an option → feedback shown → user clicks Next → question
2 → ... → last question's Next shows results. "Try Again" regenerates a
fresh question set from the same filters (new random distractors/order,
same pool). "Change Settings" navigates back to `/vocab/quiz/`.

## Error handling

If the filtered pool has zero eligible words for the selected mode (e.g.
Antonym Match on a category where no word has antonyms), the play page
shows a message ("No words available for this combination — try
different settings") instead of attempting to render a question, with a
link back to `/vocab/quiz/`. `/api/words/` fetch failure shows a generic
error message with a retry link (same "no toast system exists yet, plain
inline message" pattern established in Vocab Browse + Word's progress
toggle).

## Testing

Python/pytest coverage is limited to what has server-side behavior to
test: `vocab_quiz_setup` (200, correct template, category/CEFR choices
from the DB appear in the rendered form) and `vocab_quiz_play` (200,
correct template, renders regardless of query-string content since all
real logic is client-side). There is no server-side equivalent of the
question-generation/scoring logic to unit test via pytest — matching the
precedent set by Foundation's theme/language toggles (also pure client
JS with no Python test surface), this sub-project's actual quiz-engine
correctness is verified through thorough manual browser testing per task
rather than automated tests: each question mode generating sensible
options, scoring correctly, Mixed Review respecting the
synonym/antonym-availability rule, the zero-pool error case, and Try
Again / Change Settings both working.

## Explicitly out of scope for this phase

Gap mode, Challenge mode, hand-picking individual words as a quiz source,
learned-state filtering, section grouping, Vietnamese content
translation, dialect-based word substitution, and any score/progress
persistence (matches production — quiz results are ephemeral). These are
deferred, not rejected — Gap and Challenge get their own design/plan
cycles once this architecture is proven.
