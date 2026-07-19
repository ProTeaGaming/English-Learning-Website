# VocabLarry Professional Environment — Grammar Test Mode (design)

## Context

This is the fourth Grammar sub-project of the VocabLarry Professional
Environment rebuild, following Grammar Browse + Topic and Grammar Topic
Quiz (both merged to `main`). It adds a **cross-topic** practice test —
draw questions from many topics at once, filtered by level and question
type — distinct from the per-topic quiz, which only ever draws from one
topic's bank.

There is already an **approved design for this exact feature on a
different product**:
`docs/superpowers/specs/2026-07-11-grammar-test-mode-design.md` targets
`VocabLarry/vocablarry.html` (the production single-page app), not this
rebuild — do not confuse the two, but its user-approved decisions are a
strong reference here: four modes (Multichoice/Gap/Transform/Mixed, Mixed
default), a topic/level filter, a count selector, and — most importantly —
an explicit, already-settled decision that **this mode is practice-only
and never touches mastery tracking** (`grammar_map` stays exclusive to a
topic's own quiz). This spec adopts that mastery decision directly; it
diverges from the production spec on UI shape, described below, because
VLPE's own established conventions (from Vocab Quiz and Grammar Topic
Quiz) point to a simpler shape than production's richer picker.

Production's reference implementation (`grammarQuiz.mode: 'topic' |
'test'`, a `grammarQuizViewEl()` container-lookup swapping which page's
quiz view functions render into) is the direct precedent for this spec's
"extend the engine with a mode flag" decision, confirmed during
brainstorming as the preferred approach over building a parallel,
duplicated engine file.

## Decisions

- **No new models, no new migrations, no new backend endpoints.** Same
  finding as every other Grammar sub-project — `/api/grammar/` already
  returns every topic's full question bank nested; nothing new is needed
  to pool them across topics client-side.
- **Topic filtering: stage only, not individual topics.** Production's
  reference spec has a rich multi-select topic-chip picker (search +
  section + CEFR narrowing). VLPE has no multi-select-chip UI pattern
  anywhere yet — every existing filter in this rebuild (Vocab Browse,
  Grammar Browse, Vocab Quiz's category/CEFR fields) is a plain
  single-value `<select>` or text search. This sub-project uses a single
  `<select name="stage">` over `GrammarTopic.STAGES` (`beginner`/
  `independent`/`expert` — the same 3-value field Grammar Browse's own
  filter already uses), no topic multi-select. Deferred, not rejected —
  same "defer richer filtering" call Grammar Browse made for its own
  12-section grouping layer, and Vocab Browse made for its 75-section
  layer.
- **Mode selection and count fields are plain `<select>` dropdowns, not
  card UI.** Production's reference spec uses a 4-card `option-grid` for
  mode and a count row with a custom-number option. VLPE's own Vocab Quiz
  setup page (the direct same-repo precedent, not the cross-product one)
  already established plain `<select>` dropdowns for every field
  including its own mode-family concept, with count values `10/20/30/All`
  (no custom-number input). This spec reuses that exact shape rather than
  introducing a new visual pattern: `<select name="qtype">` (Mixed /
  Multichoice / Fill the Gap / Rewrite the Sentence, Mixed as the
  `selected` default) and `<select name="count">` (`10`/`20`/`30`/`all`,
  identical values to Vocab Quiz's own count field).
- **New flat nav entry "Grammar Test"**, alongside the existing "Grammar"
  entry — not a dropdown. Production's nav is `Category / Word / Test`
  under one Grammar dropdown; VLPE's nav has no dropdowns at all — its
  precedent for "a second, closely-related page" is Vocab Quiz getting
  its own flat top-level entry (`Vocabulary`, `Quiz` — two separate
  `<li>`s, not one nested under the other). This spec follows that
  precedent exactly rather than introducing dropdown nav.
- **Setup → play via a GET-submitted form and query-string params**,
  identical mechanism to `vocab_quiz_setup` → `vocab_quiz_play`:
  `/grammar/test/` renders the form; submitting it navigates to
  `/grammar/test/play/?stage=...&qtype=...&count=...`, read by the JS
  from `URLSearchParams` (the same convention `vocab-quiz.js` already
  uses), not from a data attribute.
- **Engine: extend `static/js/grammar-quiz.js` with a mode flag**, per
  your decision — not a parallel file. The existing rendering/grading
  functions (`renderQuestion`, `checkMcq`, `checkTyped`, `showFeedback`,
  `grammarNorm`, `expectedAnswers`, `blankMeansNoAnswer`, `offersBlankGap`)
  are reused completely unchanged. What generalizes:
  - `topicSlug` becomes `root.dataset.topicSlug || null` (test mode's
    container has no such attribute); a new `testMode` flag is
    `root.dataset.mode === "test"` (only the new test-play template sets
    this — the already-shipped topic-quiz template is untouched).
  - `drawQuestions()` stops taking a `topic` parameter and instead reads
    two new `state` fields, `state.pool` (the candidate question array)
    and `state.drawCount` (how many to slice after shuffling) —
    topic mode sets `state.pool = topic.quiz` and `state.drawCount =
    DRAW_COUNT` (still fixed at 10, unchanged); test mode sets `state.pool`
    to the filtered cross-topic array and `state.drawCount =
    Math.min(count, pool.length)` (or the full pool length when `count`
    is `"all"` — the same clamp-to-pool-size behavior `vocab-quiz.js`'s
    own `pickTargetWords` already established).
  - `state.mode` (`"topic"` or `"test"`) replaces bare `topicSlug`
    presence checks wherever behavior must branch: the Leave link's
    href (`/grammar/topic/<slug>/` vs `/grammar/test/`), whether
    `syncMastery` is ever called (topic mode only — test mode NEVER
    calls it, full stop, matching the mastery decision below), whether a
    "Mastered" message renders on results, and results' secondary action
    (`Back to Lesson` in topic mode vs `Change Settings` → `/grammar/test/`
    in test mode). `Back to Grammar` and `Try Again` behave identically
    in both modes.
  - `init()` branches to one of two now-separate functions
    (`initTopicMode()` — the prior `init()` body, unchanged logic, now
    named and also setting `state.mode`/`state.pool`/`state.drawCount`;
    `initTestMode()` — new, reads query params, fetches `/api/grammar/`,
    flattens+filters by stage then by qtype into `state.pool`).
- **Mastery: practice-only, exactly matching the already-approved
  production decision.** A test run never calls `syncMastery`, never
  reads or writes `grammar_map`, regardless of auth state. No status
  UI of any kind on the test setup or play pages. Topic detail/browse
  mastery status (from Grammar Topic Quiz) is completely unaffected —
  this sub-project touches none of that code.
- **No `@ensure_csrf_cookie` needed on `grammar_test_play`** — unlike
  Grammar Topic Quiz's play view (which anticipated Task 2's mastery-sync
  POST), test mode makes no `fetch()` writes, ever, so there is no future
  write to prepare for.
- **Results actions:** Try Again (fresh draw, same stage/qtype/count
  settings, restarts in place — no navigation, no re-fetch of
  `/api/grammar/`), Change Settings (→ `/grammar/test/`), Back to Grammar
  (→ `/grammar/`). No "Back to Lesson" (there is no single topic).
- **Empty-pool handling**: if a stage+qtype combination yields zero
  questions, render the same plain error message pattern
  `vocab-quiz.js`'s `renderError` already uses, with a link back to
  `/grammar/test/`. In practice this is expected to be unreachable — the
  dev DB has exactly 100 mcq / 100 gap / 100 transform questions per
  topic across all 47 topics (confirmed via `GrammarQuestion.objects
  .values_list('qtype', flat=True)` — evenly `4700` each), so every
  stage (which groups multiple topics) × qtype combination has ample
  supply — but the guard is cheap and matches this codebase's established
  defensive-UI convention.
- **No i18n content translation** — same exclusion as every other Grammar
  sub-project. The new nav entry and setup-page labels get `data-i18n`
  attributes matching sibling nav items' existing convention, with
  corresponding entries added to the client-side i18n dict (chrome only,
  not question content).

## Architecture

```
config/
  urls.py            (add 2 routes under /grammar/test/)
  views_grammar.py   (add grammar_test_setup, grammar_test_play)
templates/
  grammar/
    test_setup.html    (new — stage/qtype/count form, GET → play)
    test_play.html      (new — near-empty container, data-mode="test")
  partials/
    nav.html            (add "Grammar Test" flat entry)
static/
  js/
    grammar-quiz.js     (extend — mode flag, generalized pool/draw,
                          mode-aware Leave/results actions, new
                          initTestMode())
    i18n.js               (add nav.grammarTest + setup-page label keys)
  css/
    grammar.css          (extend — test setup form styles, reusing the
                           existing .grammar-filters-style patterns)
```

Routes:

```python
path('grammar/test/', grammar_test_setup, name='grammar_test_setup'),
path('grammar/test/play/', grammar_test_play, name='grammar_test_play'),
```

## Components

- **`grammar_test_setup` view** — no DB query beyond `GrammarTopic.STAGES`
  (a plain Python list of tuples, not a queryset — matching how
  `grammar_browse` already exposes it), renders `grammar/test_setup.html`.
- **`grammar_test_play` view** — no context needed at all beyond the base
  template chrome; the JS reads everything it needs from the URL query
  string. Effectively as thin as `vocab_quiz_play`.
- **`templates/grammar/test_setup.html`** — a GET form (`action="{% url
  'grammar_test_play' %}"`) with 3 `<select>` fields (stage/qtype/count)
  and a Start button, styled with the same field/label markup pattern
  `vocab/quiz_setup.html` already uses (`.grammar-test-field` mirroring
  `.vocab-quiz-field`).
- **`templates/grammar/test_play.html`** — `<div id="grammarQuizRoot"
  data-mode="test"></div>` plus the `grammar-quiz.js` script tag, same
  shape as `topic_quiz.html` minus the topic-specific attributes.
- **`static/js/grammar-quiz.js` (extended)** — see the Decisions section
  above for the exact generalization; no other file changes needed since
  every rendering/grading function is reused as-is.
- **`templates/partials/nav.html` (extended)** — one new `<li>` between
  the existing `Grammar` and the theme/lang toggles, `data-i18n=
  "nav.grammarTest"`, linking to `{% url 'grammar_test_setup' %}`.

## Data flow

`GET /grammar/test/` → setup form → submit → `GET /grammar/test/play/
?stage=...&qtype=...&count=...` → near-empty page loads →
`grammar-quiz.js`'s `init()` sees `data-mode="test"` → `initTestMode()`
reads the query params, fetches `GET /api/grammar/`, builds `state.pool`
by flattening every topic under the matching stage(s) and filtering by
`qtype` (skipped when `qtype=mixed`) → draws `min(count, pool.length)`
questions → renders questions exactly as topic mode does (same functions)
→ results screen → Try Again reshuffles `state.pool` in place; Change
Settings navigates back to `/grammar/test/`; Back to Grammar to
`/grammar/`. No account writes at any point in this flow, authenticated
or not.

## Error handling

- Zero-question pool for the selected stage+qtype → `renderError`,
  matching `vocab-quiz.js`'s existing pattern, link back to
  `/grammar/test/`. Expected to be unreachable given real seed data (see
  Decisions), but handled defensively.
- `/api/grammar/` fetch failure → same generic "couldn't load" error as
  topic mode already has.
- No new 404 surface — `grammar_test_setup`/`grammar_test_play` take no
  URL parameters to validate.

## Testing

Python tests cover the server-rendered setup page (renders, contains the
3 select fields with the right options, stage values match
`GrammarTopic.STAGES`) and the nav entry (`grammar_test_setup` URL
present, `data-i18n="nav.grammarTest"`). `grammar_test_play` gets a
minimal render test (200, contains the expected container markup) — same
shallow-server-test-plus-real-browser-check split every prior quiz
sub-project has used.

The engine extension has no Python-testable surface. The implementation
plan must include a Playwright click-through covering: all 4 `qtype`
values individually (confirming e.g. `qtype=mcq` never shows a typed
question, `qtype=transform` never shows an MCQ question) plus Mixed
(confirming a real blend appears over enough draws), a stage filter
actually narrowing the pool (spot-checked by confirming only topics
under that stage's real question content ever appears, using this
project's actual seeded 47-topic dataset), each count value including
`all`, the empty Leave/Change-Settings/Back-to-Grammar navigation, Try
Again reshuffling in place, and — critically, given this sub-project's
core distinguishing decision — a logged-in test run's `grammar_map`
confirmed **unchanged** before and after (via `GET /auth/sync/` or Django
shell), proving no mastery write occurs, mirroring how Grammar Topic
Quiz's manual check proved the opposite (that its own writes DO persist).

## Explicitly out of scope for this phase

Individual multi-select topic filtering (deferred, same call as Grammar
Browse's own section-grouping deferral), mode-selection card UI (plain
dropdowns instead, matching VLPE's own Vocab Quiz precedent), a custom
numeric question-count input (the existing 10/20/30/All set covers it,
matching Vocab Quiz), any mastery/progress recording of any kind, Grammar
Dashboard (a separate future sub-project), Vietnamese content translation
of question/topic content.
