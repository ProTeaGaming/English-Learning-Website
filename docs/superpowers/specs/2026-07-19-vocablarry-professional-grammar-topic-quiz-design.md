# VocabLarry Professional Environment — Grammar Topic Quiz (design)

## Context

This is the second Grammar sub-project of the VocabLarry Professional
Environment rebuild, following directly on Grammar Browse + Topic
(`docs/superpowers/specs/2026-07-18-vocablarry-professional-grammar-browse-topic-design.md`,
merged to `main` 2026-07-19). That sub-project shipped a read-only topic
browse grid and lesson-content detail page, explicitly deferring "the
per-topic practice quiz" and "progress/mastery tracking and any UI
depending on it" — both are now in scope here.

The backend already fully supports this: `GrammarQuestion` (mcq/gap/
transform, with `options`/`answers`/`why` fields) is a byte-for-byte port
from production, the read-only `/api/grammar/` endpoint already serializes
each topic's full question bank nested under `quiz`, and
`CustomUser.grammar_map` (a `JSONField`, already migrated) plus the
existing `/auth/sync/` GET/POST endpoint (already merges `grammar_map`
without clobbering `learn_map` or vice versa) are already wired up and
unused by anything in this rebuild yet. **No backend work is needed at
all** — same shape of finding as Grammar Browse + Topic, just one layer
deeper. Verified the dev DB actually has the full production dataset, not
a stub: 47 topics × 300 questions each (14,100 rows total, evenly split
mcq/gap/transform).

Production's per-topic quiz (`vocablarry.html`, `startGrammarQuiz`/
`renderGrammarQuestion`/`checkGrammarMcq`/`checkGrammarTyped`/
`showGrammarResult`) is the direct reference implementation: a "Practice"
button on the topic page launches an in-place 10-question random draw (no
setup step, no options to configure), MCQ questions are click-to-answer,
gap/transform questions are typed with **strict** comparison (case,
spacing, and final punctuation all count — an explicit, deliberate past
product decision, not an oversight), each answer shows a `why`
explanation, and a completed run records `grammar_map[slug] = {best,
done}` (mastery at 80%) synced to the account. This spec ports that
behavior, adapted to VLPE's real-page-navigation architecture instead of
production's single-page-app view-swapping.

This sub-project does **not** cover the separate cross-topic "Grammar
Test" mode — that's a different, later sub-project (and is already speced
for a *different product* at
`docs/superpowers/specs/2026-07-11-grammar-test-mode-design.md`, which
targets `VocabLarry/vocab-master.html`, not this rebuild — don't confuse
the two).

## Decisions

- **No new backend, no new models, no new migrations.** `GrammarQuestion`
  already has every field needed; `/api/grammar/` already returns each
  topic's questions nested (`{id, order, qtype, prompt, options, answers,
  why}` per question); `CustomUser.grammar_map` and `/auth/sync/` already
  exist and already merge correctly (POSTing `{grammar_map: ...}` leaves
  `learn_map` untouched, and vice versa — confirmed in `accounts/views.py`).
- **Client-side quiz engine, not server-rendered questions.** The quiz page
  (`/grammar/topic/<slug>/quiz/`) is a near-empty container, same pattern
  as `vocab_quiz_play` — a new `static/js/grammar-quiz.js` fetches
  `/api/grammar/` on load, locates the topic by slug (flattening the
  stage-grouped response), and does everything else client-side: sampling,
  rendering, scoring, the results screen, and "Try Again" reshuffles.
  Rejected alternative: having the Django view do `topic.questions
  .order_by('?')[:10]` itself and embed the sample as JSON in the
  template. That would avoid one network round-trip, but it duplicates
  logic `/api/grammar/` already provides, and it breaks "Try Again"
  reshuffling without a full page reload (production redraws instantly
  in-place; a server-sampled page would need to either reuse the same 10
  forever or force a navigation to get a new set). Matches this project's
  established convention (Vocab Quiz/Gap/Challenge): interactive pages are
  plain JS modules against the existing JSON API, not server-rendered
  interactivity.
- **No setup step — a "Practice" button on the topic detail page launches
  the quiz directly**, always a fresh random 10-question draw from that
  topic's up-to-300-question bank (`GRAMMAR_QUIZ_DRAW = 10`, matching
  production exactly). Unlike Vocab Quiz, there's nothing worth
  configuring here (no mode/category/CEFR/count choices — a topic's
  question bank is fixed and every question type is mixed together, same
  as production).
- **Question rendering by `qtype`, faithfully ported from production:**
  - `mcq`: `options` (array of strings) + `answers: [correctIndex]`.
    Click an option → immediate correct/wrong styling on all options,
    feedback shows `why`.
  - `gap` / `transform`: typed text input, `answers` is an array of
    accepted strings (more than one when genuinely different correct forms
    exist, e.g. contraction/expansion pairs). Comparison is **strict**:
    only curly-vs-straight apostrophe normalization and outer
    trim — capitalization, internal spacing, and final punctuation all
    count as mistakes. This is a carried-over, deliberate product
    decision (see production's `grammarNorm` and its comment); do not add
    leniency.
  - Two data-driven edge cases in the real question set that must be
    handled correctly or specific real questions will misgrade:
    - A `gap` question whose prompt starts with `___` (blank opens the
      sentence) expects its stored-lowercase answer capitalized before
      comparison.
    - A small number of `gap` questions have an answer meaning "nothing
      goes here" (matches `/^\(?no article\)?$|^-$/i` after
      normalization) — for those, and only once any question in the
      current 10-question draw has one, an empty submission is accepted
      as a real answer choice rather than being rejected as "you must
      type something," and the input's placeholder hints this.
  - `why` (a short explanation) is always shown after answering,
    regardless of correctness.
- **Mastery persistence: on** (per your decision) — matches production. On
  reaching the results screen, `pct = round(score/total*100)` is computed,
  and if the page was rendered for an authenticated user
  (`request.user.is_authenticated`, checked server-side and exposed to the
  JS as a data attribute — same guard pattern `vocab-word.js`'s progress
  toggle already uses), the JS does the same GET-then-merge-then-POST
  round-trip against `/auth/sync/` that `vocab-word.js` already
  established for `learn_map`: GET the current `grammar_map`, set
  `grammar_map[slug] = {best: max(prev.best || 0, pct), done: (prev.done
  || false) || pct >= 80}`, POST the full map back. This is required
  because `/auth/sync/`'s POST fully replaces whichever top-level key is
  present — a naive `{grammar_map: {[slug]: ...}}` POST would silently
  wipe every other topic's progress. Guests get the full quiz experience
  (play, score, results) with nothing persisted and no status badge shown
  anywhere — mirrors the existing convention where anonymous users never
  see progress UI at all.
- **Topic detail page gains a "Practice" button** and, for authenticated
  users only, a status line reading the topic's `grammar_map` entry
  (rendered server-side by the view: `request.user.grammar_map.get(topic.slug)`)
  — "Not started yet" / "Best: N%" / "Mastered ✓" depending on state.
  Guests see the Practice button with no status line.
- **Browse grid gains a small per-card status badge**, authenticated users
  only, using the same three states, computed once per request from
  `request.user.grammar_map` (no per-card query — the map is already a
  single JSON field on the user). Guests see plain cards, unchanged from
  Grammar Browse + Topic.
- **Results screen actions, matching production exactly:** *Try Again*
  (draws a fresh random 10 and restarts in place, no navigation — this is
  why the client-side-sampling decision above matters), *Back to Lesson*
  (→ topic detail), *Back to Grammar* (→ browse). A *Leave* link is also
  present during play (→ topic detail), with no confirmation dialog —
  nothing is persisted until the results screen is reached, so leaving
  mid-quiz simply discards the in-progress attempt, same as production.
- **No i18n work.** VLPE's i18n is chrome-only (nav/home strings via a
  client-side dict) and was never extended to Grammar's lesson content;
  this sub-project doesn't touch it either. Question `prompt`/`options`/
  `why` render exactly as stored (English).
- **404 on an unknown topic slug** at the new quiz route, matching every
  other detail-style route in this codebase.

## Architecture

```
config/
  urls.py            (add 1 route under /grammar/<slug>/quiz/)
  views_grammar.py   (add grammar_topic_quiz; extend grammar_topic_detail
                       and grammar_browse to pass grammar_map status)
templates/
  grammar/
    topic_quiz.html     (new — near-empty container, mirrors quiz_play.html)
    topic_detail.html   (extend — Practice button + status line)
    browse.html          (extend — per-card status badge)
static/
  js/
    grammar-quiz.js     (new — question sampling, rendering, scoring,
                          results, mastery sync)
  css/
    grammar.css          (extend — quiz card/options/feedback/results
                           styles, status badge styles)
```

Route:

```python
path('grammar/topic/<slug:slug>/quiz/', grammar_topic_quiz, name='grammar_topic_quiz'),
```

## Components

- **`grammar_topic_quiz` view** — `get_object_or_404(GrammarTopic,
  slug=slug)` (confirms the topic exists, 404s otherwise — the JS re-fetches
  the topic's data itself via `/api/grammar/`, same double-check-via-two-paths
  shape as `vocab_quiz_play`, which also doesn't validate its query params
  server-side), renders `grammar/topic_quiz.html` with `topic` (for the
  page title/breadcrumb) and an `is_authenticated` flag for the template
  to stamp onto a data attribute.
- **`grammar_topic_detail` view (extended)** — additionally computes
  `grammar_status = request.user.grammar_map.get(topic.slug) if
  request.user.is_authenticated else None` and passes it to the template.
- **`grammar_browse` view (extended)** — additionally passes
  `request.user.grammar_map if request.user.is_authenticated else {}` so
  the template can look up each card's status by slug without a per-card
  query.
- **`templates/grammar/topic_quiz.html`** — topic title/breadcrumb (server-
  rendered, so it's correct even before JS loads) + an empty
  `<div id="grammarQuizRoot" data-topic-slug="{{ topic.slug }}"
  data-authenticated="{{ request.user.is_authenticated|yesno:'1,0' }}">`,
  then `<script src="{% static 'js/grammar-quiz.js' %}" defer></script>`.
- **`static/js/grammar-quiz.js`** — IIFE guarded on the root element
  existing (matches `vocab-quiz.js`'s own top-of-file guard). On init:
  `fetch('/api/grammar/')`, flatten `stages[].topics[]` to find the one
  matching `data-topic-slug`, error out to a plain "couldn't load" message
  (with a link back to the topic) if not found or the fetch fails. Core
  functions, deliberately named to mirror `vocab-quiz.js`'s existing
  `renderQuestion`/`handleAnswer`/`renderResults` shape for consistency
  within the codebase:
  - `drawQuestions(topic)` — `shuffle(topic.quiz).slice(0, 10)`.
  - `renderQuestion()` — branches on `q.qtype`: MCQ renders option
    buttons; gap/transform render a text input + Check button (Enter key
    also submits).
  - `checkMcq(selectedBtn, q)` / `checkTyped(inputValue, q)` — the
    strict-comparison + two-edge-case logic described above; both call a
    shared `showFeedback(isCorrect, q)`.
  - `showFeedback` — correct/wrong styling, `why` text, reveals the
    Next/See-Results button.
  - `renderResults()` — score/%, mastered message at ≥80%, the three
    action buttons, and (if `data-authenticated="1"`) triggers
    `syncMastery(pct)`.
  - `syncMastery(pct)` — GET `/auth/sync/` → merge → POST, matching
    `vocab-word.js`'s existing helper shape (a small reusable
    GET-merge-POST pattern now used in two places in this codebase).
- **`templates/grammar/topic_detail.html` (extended)** — a `<a class="btn"
  href="{% url 'grammar_topic_quiz' topic.slug %}">Practice</a>` near the
  top, plus (if `grammar_status`) a status line rendered from it.
- **`templates/grammar/browse.html` (extended)** — each card gains a
  conditional status badge, looked up from the map passed by the view
  (`{{ grammar_map|get_item:topic.slug }}` via a small template filter, or
  equivalently precomputed per-card in the view — implementation detail
  for the plan to pin down, functionally either works).
- **`static/css/grammar.css` (extended)** — quiz card, option buttons,
  typed-input row, feedback block, progress bar, results screen, and
  status badge styles — reusing the same CSS custom properties (`--border`,
  `--card-bg`, `--violet`, etc.) already established by every prior VLPE
  stylesheet, and structurally similar to `vocab.css`'s own quiz-play
  styles (option/feedback/results blocks) rather than inventing a new
  visual language.

## Data flow

`GET /grammar/topic/<slug>/` → topic detail (now with a Practice button
and status line) → click Practice → `GET /grammar/topic/<slug>/quiz/` →
near-empty page loads → `grammar-quiz.js` fetches `GET /api/grammar/` →
finds the topic, draws 10 questions → renders question 1 → user
answers each in turn (client-side scoring only, no network calls during
play) → results screen → if authenticated: `GET /auth/sync/` → merge →
`POST /auth/sync/` (updates `grammar_map`) → next visit to browse/topic
detail reflects the new status via the server-rendered badge.

## Error handling

- Unknown topic slug at `/grammar/topic/<slug>/quiz/` → standard Django
  404 (`get_object_or_404`), same as every other detail route.
- `/api/grammar/` fetch fails, or the slug from the URL isn't found in its
  response (should be unreachable in practice since the server-side view
  already validated the topic exists, but the two checks are independent
  code paths) → a plain error message in the quiz root with a link back to
  the topic page, matching `vocab-quiz.js`'s existing `renderError`
  pattern.
- `/auth/sync/` GET or POST failing during mastery sync → the results
  screen still displays and remains fully usable (score/actions all
  work); the sync silently doesn't take effect for that attempt. No error
  banner — matches `vocab-word.js`'s existing fire-and-forget tolerance
  for sync failures (it reverts its own optimistic UI state on failure,
  but doesn't surface an error to the user either).

## Testing

Python tests cover every server-rendered surface: `grammar_topic_quiz`
renders (200) and 404s on an unknown slug; the topic detail page's
Practice button links to the correct quiz URL; the status line/badge
appears with the right text for an authenticated user with a
`grammar_map` entry (both "in progress" and "mastered" states) and is
absent for a guest and for an authenticated user with no entry yet for
that topic; the browse page's per-card badges follow the same rule.

The quiz engine itself (`grammar-quiz.js`) is **not** Python-testable —
same situation as Vocab Quiz/Gap/Challenge, and this sub-project breaks
Grammar Browse + Topic's precedent of skipping browser verification
entirely, since this is the first Grammar page with real client-side JS.
The implementation plan must include `node --check` on the new JS file
plus a real Playwright click-through verifying: an MCQ question answers
correctly and incorrectly with the right styling, a typed gap/transform
question's strict comparison (including the sentence-start-capitalization
and blank-means-no-answer edge cases against real seeded questions that
exercise them), a full 10-question run reaching the results screen,
"Try Again" producing a new random set in place, and — for a logged-in
test session — the mastery sync actually landing (`grammar_map` reflects
the new state on a subsequent page load, both browse badge and topic
status line).

## Explicitly out of scope for this phase

The cross-topic Grammar Test mode (separate future sub-project, its own
setup screen + topic picker — and note again this is distinct from the
already-speced-for-a-different-product document at
`docs/superpowers/specs/2026-07-11-grammar-test-mode-design.md`), the
12-section grouping layer (still deferred from Grammar Browse + Topic),
Vietnamese content translation, dialect-based content substitution,
letting a user pick question count/type mix before starting (production
has no such setup step and this spec matches it), any richer analytics
beyond the single best/done pair per topic.
