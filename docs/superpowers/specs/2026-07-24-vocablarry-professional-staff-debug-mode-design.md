# VocabLarry Professional Environment — Staff Debug Mode design

**Date:** 2026-07-24
**Status:** Approved, ready for planning

## Context

FIXES-NEEDED.md item 19: production has a staff-only "Debug mode" toggle
(`debugToggle` in the user menu) that, once on, reveals inline add/edit/delete
controls for words, categories, grammar topics, grammar lesson blocks, and
grammar questions directly on the pages that already display them — no
separate admin UI, no page navigation. VLPE has none of this.

The item's own text only mentions the word detail view, but a direct
comparison against `vocablarry.html` found the real feature is much broader:
inline controls on category cards (`vocab_browse`), word cards
(`category_word_list`, `word_list`), the word detail page, grammar topic cards
(`grammar_browse`), and — most extensively — an inline lesson-block editor
plus a full question-manager panel on the grammar topic detail page. Per user
decision (2026-07-24), this design targets full production parity, all five
entity types, all listed pages.

**Key existing infrastructure this design reuses, not rebuilds — the entire
backend already exists and is already tested:**
- `api/write_views.py` — staff-gated (`staff_required`) REST endpoints for
  `word_create`/`word_detail` (PATCH/DELETE), `category_create`/`category_detail`,
  `grammar_topic_create`/`grammar_topic_detail`, `grammar_block_create`/`grammar_block_detail`,
  `grammar_question_create`/`grammar_question_detail`. Payload shapes already
  match what production's debug JS sends (confirmed against `_word_form_data`'s
  synonyms/antonyms array handling and `_jsonfield_safe`'s JSON-field coercion).
- `api/urls.py` already mounts every one of the above under `/api/...`, at the
  exact same paths production's own `debugFetch()` calls hit.
- `accounts/decorators.py:is_staff_user`/`effective_role_level` — the staff
  check, already used by `dashboard/views.py` and `/auth/session/`.
- `tests/test_debug_api.py` — already covers staff-only access and full
  CRUD round-trips for the write API. No new backend tests are needed for
  the API itself; only a test that the new toggle button/markup is
  staff-gated server-side.
- `dashboard` app (existing staff CRUD templates/forms) stays completely
  untouched — this is an additive, in-place UX layer, not a replacement.

**Explicitly deferred / non-goals:**
- No changes to the `dashboard` app.
- No i18n for any new debug-mode markup — production doesn't localize it
  either (staff-only tool, not user-facing).
- No native `confirm()` ban exception review needed beyond noting it: this
  feature reuses production's own `window.confirm()` for deletes (unlike
  every user-facing destructive action elsewhere in VLPE, which uses a custom
  overlay) — acceptable here specifically because this is an internal staff
  tool being ported byte-for-byte, not a user-facing flow.

## Architecture

**Toggle & gating.** A `debugToggle` button is added to the user-menu
dropdown in `templates/partials/nav.html`, rendered only when
`is_staff_user(request.user)` is true (a new boolean added to whatever
context already feeds that menu — extend the existing pattern from
`user_progress_stats` rather than adding a second context processor).
Because the button itself only exists in the DOM for staff, the on/off state
can be pure client-side: `static/js/debug-mode.js` stores `debugMode` in
`sessionStorage` (`'1'`/`'0'`) exactly as production does, toggles a
`body.debug-on` class, and shows/hides a fixed `#debugRibbon` "DEBUG" badge.
No new backend endpoint needed for the toggle itself.

**CSS.** Port production's `.dbg-ctl`, `.dbg-add-card`, `.dbg-overlay`,
`.dbg-modal`, `.dbg-field`, `.dbg-err`, `.dbg-form-err`, `.dbg-actions`,
`.dbg-question-mgr`, `#debugRibbon` rules into `base.css` (shared
infrastructure across vocab and grammar pages, same placement precedent as
the CEFR-badge/filter-chip CSS from earlier phases). Class names and
`body.debug-on`-gated visibility stay identical to production.

**JS.** One new file, `static/js/debug-mode.js`, included via `extra_body` on
every page that needs it (matching the existing `vocab-word.js`/
`grammar-quiz.js` per-page opt-in convention). Ports, essentially verbatim:
- `openDebugModal({title, fields, initial, onSave})` — generic field-driven
  overlay form generator (text/textarea/select/csv/json/number field types).
- `DEBUG_FORMS` — the field-spec table for word/category/topic/block/question,
  cross-checked field-by-field against `dashboard/forms.py`'s
  `WordForm`/`CategoryForm`/`GrammarTopicForm`/`GrammarLessonBlockForm`/`GrammarQuestionForm`
  so every field the modal collects is one the underlying form actually accepts.
- `debugFetch`/`debugConfirm` — CSRF-header fetch wrapper (own
  `getCsrfToken()`, matching this codebase's established per-file convention
  rather than a shared helper) + `window.confirm` for deletes.
- `debugSaveWord`/`debugDeleteWord`/`debugSaveCategory`/`debugDeleteCategory`/
  `debugSaveTopic`/`debugDeleteTopic`/`debugSaveBlock`/`debugDeleteBlock`/
  `debugSaveQuestion`/`debugDeleteQuestion` — same logic, pointed at VLPE's
  already-existing `/api/...` endpoints.

**Refresh strategy — simplified vs. production.** Production re-renders from
an in-memory SPA cache after each save/delete (`debugRefreshVocab`/
`debugRefreshGrammar`). VLPE is server-rendered per page, so every
`onSave`/delete handler instead calls `window.location.reload()` on success —
same visible outcome, far less code, consistent with this project's "outcome
not method" ground rule.

## Entity coverage

| Entity | Add | Edit/Delete | Template(s) |
|---|---|---|---|
| Word | `+ Add word` button on the search/filter bar | Per-card `.dbg-ctl` on hover-reveal cards + on the detail page | `vocab/category_word_list.html`, `vocab/word_list.html`, `vocab/word_detail.html` |
| Category | `.dbg-add-card` tile appended to the grid | Per-card `.dbg-ctl` | `vocab/browse.html` |
| Grammar topic | `.dbg-add-card` tile appended to the grid | Per-card `.dbg-ctl` | `grammar/browse.html` |
| Lesson block | `.dbg-add-card` under the lesson content | Per-block `.dbg-ctl`, including blocks rendered inside the scroll-scrub "stack" cards (`lesson_items` grouping in `grammar/topic_detail.html`) | `grammar/topic_detail.html` |
| Question | New `.dbg-question-mgr` panel (list + add) | Per-row edit/delete inside that panel | `grammar/topic_detail.html` |

The question-manager panel is the one genuinely new piece of UI: VLPE's
`topic_detail.html` currently has no non-debug question list at all (only a
"Practice — N questions" link), so this panel exists purely behind
`body.debug-on` with no non-debug equivalent to build on — confirmed
acceptable by the user rather than substituted with a link out to the
existing `dashboard_grammar_questions` page.

## Testing

- New Django test: the `debugToggle` button/markup renders in `nav.html` for
  a staff/admin user and is entirely absent from the response body for a
  regular user (not just CSS-hidden — check page source, matching this
  project's established "styled but reachable" concern from prior phases).
- No new backend tests needed for the API itself — `tests/test_debug_api.py`
  already covers staff-gating and full CRUD for all five entity types.
- Manual Playwright verification (required per this project's standing rule
  for anything touching rendering/interaction, not optional): toggle on/off,
  add/edit/delete for each of the 5 entity types against real seeded data,
  confirm ribbon appears/disappears, confirm a non-staff account never sees
  any `.dbg-ctl` markup in the rendered page source.

## Non-goals recap

No changes to the `dashboard` app; no i18n; no mobile-specific redesign of
the overlay (production's CSS is already responsive, ported as-is).
