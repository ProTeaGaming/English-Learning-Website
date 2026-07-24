# VocabLarry Professional Environment — Word Quick-View Modal design

**Date:** 2026-07-24
**Status:** Approved, ready for planning

## Context

FIXES-NEEDED.md item 22: production opens word details in a lightweight
modal (`#word-modal`/`openWordModal()`) over the current browse grid —
stays in place, closes on backdrop click, preserves scroll/filter state.
VLPE built `word_detail.html` as a real full page instead, a deliberate
earlier VLPE decision made specifically to support deep-linking
(shareable/bookmarkable word URLs). The file itself explicitly flags this
as "a decision, not an assumed fix" — do not silently pick a side.

**User decision (2026-07-24, this brainstorm):** build a hybrid. Clicking a
word from a browse/list page opens it as an in-place modal, matching
production's UX (no navigation away from the list). Visiting the word's URL
directly (deep link, bookmark, share) still renders the real full page.

**Real finding from reading production's actual `openWordModal()`/
`closeWordModal()` code:** production's own modal has **no URL or history
integration at all** — it's a pure client-side overlay, no deep-linking even
in production. The hybrid behavior this spec describes (modal + real,
shareable URL while browsing) is a genuine VLPE-specific enhancement beyond
what production itself does, not a port of anything production has.

**Key existing infrastructure this design reuses, not rebuilds:**
- `.auth-modal-overlay` (`static/css/base.css:626-630`) — the same modal
  backdrop shell already used by the sign-in modal and the home
  intent-picker modal. Reused verbatim for the word modal's backdrop.
- `.word-detail-card` (`static/css/vocab.css:321-...`) — already commented
  "card container matching production's modal content" from an earlier
  visual-retrofit phase. This is already visually modal-shaped; no new CSS
  needed for the card itself, only the backdrop wrapper.
- `config/views_vocab.py:vocab_word_detail` and its `_resolve_word_refs()`
  helper — already compute everything the modal needs (word, category,
  CEFR, resolved synonym/antonym word links, learn_state). Reused as-is,
  branching only on response shape (full page vs. partial fragment), not
  duplicated into a second endpoint.
- `static/js/vocab-word.js`'s `window.vocabToggleWord` — reused for the
  learn-state toggle button wherever it renders (page or modal), with one
  necessary addition: `vocab-word.js`'s own page-load-time
  `document.querySelector(".learn-state-btn")` binding cannot see a button
  injected later via AJAX, so `word-modal.js` must explicitly re-bind that
  button's click handler after every content injection.

**Explicitly deferred / non-goals:**
- No changes to `category_word_list.html`/`word_list.html` beyond adding
  click interception on word-title links — their own filter/pagination/
  bulk-action behavior is untouched.
- No visual redesign of `word_detail.html`'s content — only extracting its
  existing `.word-detail-card` markup into a shared partial so the full
  page and the modal render from one source.
- No change to `category_word_list.html`/`word_list.html`'s own hover-reveal
  card synonyms/antonyms, which render as plain text there (not links) —
  cross-linking only ever existed inside the word detail content itself
  (`synonym_refs`/`antonym_refs`), confirmed unchanged by this design.

## Architecture

**New partial: `templates/partials/word_modal.html`.** Included
unconditionally from `base.html` (like `mode_picker_modal.html`). Markup:
`.auth-modal-overlay` (`id="wordModalOverlay"`) wrapping an
`.auth-modal-close` button and an empty content container
(`id="wordModalContent"`) that JS fills with fetched HTML.

**Shared template: `templates/vocab/partials/word_detail_card.html`,**
extracted from `word_detail.html`'s existing `.word-detail-card` block
(word/pos/CEFR badge, definition, synonyms, antonyms, example, learn-state
row) with zero visual changes. `word_detail.html` becomes a thin wrapper:
`{% extends "base.html" %}` + breadcrumb + `{% include
"vocab/partials/word_detail_card.html" %}`.

**View change: `config/views_vocab.py:vocab_word_detail`.** Same context
computation as today (`word`, `learn_state`, `synonym_refs`, `antonym_refs`
— unchanged). New response branch: if
`request.headers.get('X-Requested-With') == 'XMLHttpRequest'`, render only
`vocab/partials/word_detail_card.html` (no `base.html`, no breadcrumb) with
that context; otherwise render `word_detail.html` as today. No new URL, no
new view function — same `vocabulary_word_detail` URL serves both shapes.

**New file: `static/js/word-modal.js`.** A delegated click listener on
`document` intercepts clicks on: (a) word-title links in
`category_word_list.html`/`word_list.html` (identified by a new
`data-word-modal-trigger` attribute added to those `<a>` tags — the anchor's
own `href` stays a real, working URL for no-JS/middle-click/right-click
"open in new tab" cases), and (b) `.word-xref` links wherever word content
renders. On a matching click: `e.preventDefault()`, `fetch(href, {headers:
{'X-Requested-With': 'XMLHttpRequest'}})`, inject the returned HTML into
`#wordModalContent`, re-bind that content's own `.learn-state-btn` and any
`.word-xref` links it contains (the delegated listener already covers
`.word-xref` clicks generically; only the toggle button needs explicit
re-binding per `vocab-word.js`'s existing per-page pattern), show the
overlay, and `history.pushState(null, '', href)`.

**History/close behavior.** Opening never triggers a page reload — only
`pushState`. Closing (× button, backdrop click) calls `history.back()`
rather than manually hiding the overlay and clearing the URL. A single
`window.addEventListener('popstate', ...)` handler is the only place that
actually hides the overlay — so × -click, backdrop-click, and the browser's
real back button all funnel through the same close path and stay
consistent with each other. A direct visit to a word's URL (no referring
list, or a hard refresh while the modal was open) hits the view with no
`X-Requested-With` header, so it always renders the real full page — the
modal is never involved in that path at all.

## Testing

- New Django tests on `vocab_word_detail`: with `X-Requested-With:
  XMLHttpRequest`, the response contains the word-detail-card content but
  no `<nav>`/site-wide chrome; without it, the response is the full page
  (existing behavior, already covered by existing tests — confirm they
  still pass unchanged).
- New tests confirming `category_word_list.html`/`word_list.html` word-title
  links carry `data-word-modal-trigger` and a real, working `href`.
- Manual Playwright verification (required, per this project's standing
  rule for anything touching rendering/interaction): click a word from a
  list → modal opens, URL updates, no reload, list scroll/filter state
  untouched underneath; click a synonym/antonym inside the modal → content
  swaps to the new word, URL updates again, modal stays open; press the
  real back button → modal closes, URL reverts to the list, list state
  intact; refresh the page while the modal is open → lands on the real full
  word page (not the list, not a broken modal); visit a word URL directly
  with no referring list → real full page, no modal ever appears; confirm
  the learn-state toggle button works correctly both on the full page and
  inside the modal (mark as learned inside the modal, close it, confirm the
  list's own progress indicator updated too).
