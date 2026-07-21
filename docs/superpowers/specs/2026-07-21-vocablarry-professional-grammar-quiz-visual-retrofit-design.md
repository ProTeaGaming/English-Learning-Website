# VocabLarry Professional Environment — Grammar Quiz Visual Retrofit Design

## Context

VocabLarry Professional Environment (VLPE) is a parallel Django-templating rebuild of production VocabLarry (`VocabLarry/vocablarry.html` — a separate, real Django project in its own right, `vocablarry.html` specifically being read-only reference material for this rebuild; never edited). Five prior visual-retrofit sub-projects are complete and merged: Nav & Routing Skeleton, Vocab Browse/Category/Word, Vocab Quiz, Grammar Browse + Topic Detail. This is the sixth: **Grammar Quiz**, covering two surfaces:
- The cross-topic **Grammar Test** (`grammar/quiz_setup.html` → `grammar/quiz_play.html`, URLs `/grammar/quiz/` → `/grammar/quiz/play/`)
- The per-topic **Practice quiz** (`grammar/topic_quiz.html`, URL `/grammar/category/<slug>/quiz/`, launched directly from the topic detail page's "Practice — N questions" button, no setup step)

Both currently share one JS engine, `static/js/grammar-quiz.js` (`state.mode: "topic"|"test"`), and both render with the bland, unstyled `.grammar-quiz-*`/`.grammar-test-*` CSS classes kept untouched (deliberately, as out-of-scope) through every prior retrofit.

**Explicit instruction for this sub-project (consistent with the whole Grammar retrofit arc): match production exactly** — visual design and functional behavior — same standing as the Grammar Browse retrofit. Section/theme/other underlying data still doesn't need to be hardcoded where a real model already exists (none needed here — this sub-project adds no new persisted data).

**Two real, currently-live bugs found during this sub-project's research, fixed here as part of normal scope** (same pattern as the Vocab Quiz retrofit's own stale-link fix):
1. `.grammar-breadcrumb` — used by both `quiz_play.html` and `topic_quiz.html` — lost its CSS definition when the Grammar Browse retrofit's CSS rewrite removed it (Topic Detail switched to `.back-btn` instead, but these two files were never updated to match).
2. `static/js/grammar-quiz.js` hardcodes 4 occurrences of 2 distinct pre-Nav-Routing-Skeleton URLs that now 404: `/grammar/topic/<slug>/` (should be `/grammar/category/<slug>/`) and `/grammar/test/` (should be `/grammar/quiz/`) — in `backHref()` and `renderResults()`'s `secondaryAction`.

**Source of truth:** `VocabLarry/vocablarry.html` (confirmed current, matches the live site).

## Decisions

- **The multi-select topic-chip picker is built, not deferred.** Every prior VLPE retrofit has deferred an equivalent "pick specific items from a large set" picker (the vocab word-picker, 3 times) as out of scope. Given this sub-project's explicit exact-match mandate, this one is built: production's `gramtest.topics` is a `Set` of selected topic slugs (empty = "All topics", no filter); clicking a topic chip toggles membership (true multi-select, not radio-exclusive); clicking "All Topics" clears the set; changing the SECTION filter resets the topic selection (since the available topic list changes). Topic chips are themed with the same `.t-tX` class each topic already carries from the Grammar Browse retrofit (`topic.theme`), for visual consistency between the two surfaces.
- **Only the topic-chip picker and its live "N questions match" counter are genuinely client-side — everything else on the setup page is server-rendered, same as every other VLPE setup page.** The mode cards (4, fixed), count pills (5 + Custom, fixed), CEFR chips (12, from the same `GRAMMAR_CEFR_LEVELS` constant the Grammar Browse retrofit already added to `views_grammar.py`), and section chips (from the real `GrammarSection` queryset, also already used by Grammar Browse) are all static-per-request content with no dependency on live filter state — there's no reason to route them through a client-side fetch when Django already has this data at render time, and doing so would be an unnecessary architectural inconsistency with the rest of VLPE. Only the topic picker itself needs JS: production's live "N questions match" counter updates instantly as mode/count/section/topic/CEFR/search change, before the user ever submits — that genuinely can't be done via page reloads. The setup page fetches `/api/grammar/` once on load (the same endpoint `grammar-quiz.js` already calls for `initTestMode()`) purely to get each topic's own question pool (for the live count), holds topic-picker-relevant state (selected topics, search, and the section/CEFR/mode/count values needed to compute the live count) in JS, and only navigates (to `/grammar/quiz/play/?...`) when "Start Test" is clicked.
- **The per-topic Practice quiz keeps its current no-setup-screen architecture** — production's own `startGrammarQuiz(topic)` launches straight into the first question with no setup step either, called directly from the topic detail page. No new work needed here beyond restyling.
- **`.browse-bar` (production's own wrapper class for the topic-picker filter panel) is not ported as a new class — VLPE's existing `.filters`/`.filter-row`/`.chip`/`.search-row`/`.clear-btn` system is reused instead.** Functionally identical wrapper; no need to duplicate.
- **MCQ questions reuse `.q-options`/`.q-opt`(+`.correct`/`.wrong`) verbatim from the Vocab Quiz retrofit** — same visual family, no new CSS needed for this question type.
- **Gap/Transform (typed-answer) questions get new, small, self-contained CSS**: `.gram-gap-input`(+`.correct`/`.wrong`) plus its adjacent "Check" button (reusing the existing `.btn` class). This question type didn't exist in Vocab Quiz, so it's the one genuinely new question-rendering piece in this retrofit.
- **Results screens (both surfaces) reuse `.result-card`/`.result-score`/`.result-actions` verbatim from Vocab Quiz.** The per-topic quiz's mastery messaging ("You've mastered this topic!" / "Score 80%+ to master this topic.") and its `syncMastery` call are functionally unchanged — only the surrounding card markup is restyled.
- **The two live bugs (breadcrumb CSS, stale URLs) are fixed as explicit, in-scope work** — matching how the Vocab Quiz retrofit's Task 1 was a dedicated, isolated bug-fix before the visual work. `.grammar-breadcrumb` is replaced with `.back-btn` (not restored) in both templates, matching how Topic Detail already made this exact transition. The 4 stale URL occurrences are corrected to the real current route names.
- **Count row matches production's real values exactly**: `[10, 20, 30, 50, 100]` plus a "Custom" pill — note this differs from Vocab Quiz's `[10, 20, 30, "all"]` (no "All" option here; production caps Grammar Test runs at a hard `GRAMTEST_MAX = 100` regardless of pool size, and the Custom input is itself clamped to that same 100 cap). This cap and its absence of an "All" option are ported exactly, not reconciled with Vocab Quiz's different shape.
- **No new i18n keys** — English-only body copy, matching every prior retrofit's scoping (chrome/nav labels already wired).
- **No changes to the underlying quiz-generation/scoring/mastery-tracking logic** — `shuffle`, `grammarNorm`, `expectedAnswers`, `blankMeansNoAnswer`, `offersBlankGap`, `drawQuestions`, `checkMcq`, `checkTyped`, `syncMastery` in the existing `grammar-quiz.js` are correctness-critical and stay byte-identical except for the two bug fixes above and whatever class-name changes the new render functions require. This mirrors the Vocab Quiz retrofit's own "algorithm untouched, only rendering restyled" discipline.

## Architecture

Three templates change: `grammar/quiz_setup.html` (full rewrite — server-rendered mode cards/count pills/CEFR chips/section chips, plus empty containers for the JS-driven topic picker), `grammar/quiz_play.html` (chrome-only change — `.grammar-breadcrumb` → `.back-btn`), `grammar/topic_quiz.html` (chrome-only change — same breadcrumb swap). `config/views_grammar.py` gains minor context additions to `grammar_test_setup` (the fixed mode list, `GRAMMAR_CEFR_LEVELS` reused, `GrammarSection.objects.order_by('order')` reused) — no new models or migrations. `static/js/grammar-quiz.js` gets: the 2 URL-pattern fixes, a new setup-page-only block handling ONLY the topic picker + live counter (fetches `/api/grammar/` once, holds topic-picker-relevant JS state, mirrors how Vocab Quiz's `initSetupPage()` coexists with its play-page engine in one file — everything else on the setup page is plain server-rendered `<a href>`/form-driven interaction like the mode-card/count-pill/CEFR-chip selection already works elsewhere in VLPE, just written into hidden form fields the way Vocab Quiz's cards already do), and the play/results rendering functions restyled onto the shared `.q-card`/`.result-card` system plus the new gap-input markup for typed questions. New CSS in `grammar.css`: `.gram-gap-input`(+states) only — everything else needed (`.setup-card`, `.option-grid`/`.modeCard`, `.count-row`/`.custom-chip`, `.q-card` family, `.result-card` family, `.filters`/`.chip` family) already exists from Vocab Quiz and Grammar Browse.

## Components

### Cross-topic Grammar Test setup (`grammar/quiz_setup.html`)

- `.setup-card` with an `.option-grid` of 4 mode cards: Mixed / Multichoice / Fill the Gap / Rewrite the Sentence (exact production copy, ported verbatim) and a `.count-row` (10/20/30/50/100 + Custom, capped at 100) — both server-rendered and JS-driven for local selection exactly like Vocab Quiz's own mode cards/count pills (hidden form fields updated on click, no page reload needed just to select these).
- `.filters` panel: topic search input, section chips (server-rendered from the real `GrammarSection` queryset, reusing Grammar Browse's data), the new multi-select topic-chip picker (themed per-topic, "All Topics" clears selection — this part IS JS/API-driven, see Decisions), the full 12-value CEFR chip row (server-rendered from `GRAMMAR_CEFR_LEVELS`), "Clear filters", and the live "N questions match" counter (JS-computed from the topic picker's fetched data, reacting to mode/count/section/topic/CEFR/search changes).
- "Start Test" button, disabled/empty-state message when the current filter combination matches zero questions.

### Play screens (both surfaces)

- `.q-card`/`.progress-bar`/`.q-meta`/`.q-prompt`/`.q-text` (all reused verbatim). MCQ: `.q-options`/`.q-opt`. Gap/Transform: new `.gram-gap-input` + "Check" button, Enter-key submit (existing behavior, kept).
- `.back-btn` "Leave" link (replacing `.grammar-breadcrumb`).

### Results (both surfaces)

- `.result-card`/`.result-score`/`.result-actions` (reused verbatim). Per-topic: adds the mastery message line. Test mode: "Change Settings" secondary action (now correctly pointing at `/grammar/quiz/`, not the stale `/grammar/test/`).

## Data Flow

Unchanged endpoints and data: `grammar_category_quiz`, `grammar_quiz_setup`, `grammar_quiz_play`, `/api/grammar/`, `GrammarQuestion`, `request.user.grammar_map`. This is a rendering + setup-interaction retrofit — no new models, no migrations, no scoring/mastery logic changes.

## Error Handling

Unchanged trigger conditions (no questions match filters → existing "No questions match" messaging, restyled; a topic with zero quiz questions → existing "no quiz questions yet" error, restyled), corrected back/leave/change-settings links.

## Testing

Python tests: setup-page markup (mode cards, count pills, topic/section/CEFR chip presence and attributes, corrected URL assertions), play/results page markup (back-btn present, gap-input class present for typed question types via fixture data). Explicitly needs real-browser (Playwright) verification, consistent with this project's standing precedent that this JS engine's algorithmic correctness (scoring, mastery) is verified by code-tracing against production source, not Python tests: the live topic-picker counter actually updating as filters change, a full MCQ playthrough, a full gap-question playthrough (typed input, Enter-key submit, correct/wrong styling), mastery messaging after a per-topic quiz, both themes, and that the corrected URLs actually navigate (not 404).

## Explicitly Out of Scope

- Any change to quiz-generation, scoring, or mastery-tracking algorithms.
- Vocab/Grammar Word reference pages — separate, already-planned future sub-projects.
- i18n beyond what's already wired.
