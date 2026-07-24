# VocabLarry Professional Environment — Home Intent-Picker design

**Date:** 2026-07-24
**Status:** Approved, ready for planning

## Context

FIXES-NEEDED.md item 20: in production, the home page's "Start Learning" and
"Quick Test" buttons both open a modal (`modePickerOverlay`/
`openModePicker()`) asking whether the user wants Vocabulary or Grammar
before routing them anywhere. VLPE's home page instead has two hard-linked
buttons — "Start Learning" (→ Vocabulary Category) and "Practice Grammar"
(→ Grammar Category) — with no picker at all, so a user who wants Grammar
from "Start Learning," or a quiz from either button, gets routed into plain
Vocabulary browsing regardless of intent.

**Two scope decisions made with the user during brainstorming:**
- VLPE's button set changes to match production exactly: "Start Learning" +
  "Quick Test," both opening the picker (not "Start Learning" + "Practice
  Grammar" with Quick Test added as a third button). "Practice Grammar" as a
  direct shortcut is dropped.
- Production has a real quirk: inside the picker, clicking "Grammar" always
  routes to the grammar browse page regardless of whether the picker was
  opened via "Start Learning" or "Quick Test" — only the Vocabulary choice
  differentiates browse-vs-quiz by intent. This looks like an oversight in
  production, not an intentional design. VLPE will **not** inherit this quirk
  — "Quick Test" → Grammar routes to the grammar quiz, matching what a
  button literally labeled "Quick Test" implies, and matching how the
  Vocabulary side already behaves symmetrically.

**Key existing infrastructure this design reuses, not rebuilds:**
- `.auth-modal-overlay`/`.auth-modal`/`.auth-modal-close`/`.auth-modal-title`
  (`static/css/base.css:626-670`) — the exact modal shell already built for
  the sign-in modal (FIXES-NEEDED item 1). No new modal CSS needed.
- `.mode-picker-row`/`.mode-picker-row-disabled`/`.mode-picker-row.active`
  (`static/css/base.css:399-409`) — already built for the language dropdown
  (item 6, `nav.html`'s `.lang-menu`). Only `.mode-picker-list` (the flex
  column wrapper around the rows) needs adding — a 3-line rule, ported
  directly from production.
- `.home-sec-pill.soon` (`static/css/base.css:348-354`) — already used for
  the "Coming soon" pills on the home page's Explore Sections cards and the
  Reading/Writing/Listening/Speaking stub pages (item 18). Reused verbatim
  for the picker's 4 disabled rows.
- `window.t(key)` (`static/js/i18n.js:315-320`) — the existing translation
  lookup, used to swap the modal's title text per intent, matching
  production's own `UI_STRINGS`/`t()` mechanism.
- The open/close/backdrop-click/Escape pattern already established by
  `static/js/auth-modal.js`'s `openAuthModal`/`closeAuthModal` — the new
  `openModePicker`/`closeModePicker` follow the identical shape.

**Explicitly deferred / non-goals:**
- No changes to the Reading/Writing/Listening/Speaking stub pages themselves
  — their rows in the picker stay disabled/"Soon," matching their current
  real state (item 18 only added an "Under construction" card, no real
  content).
- No changes to `vocabulary_quiz_setup`/`grammar_quiz_setup`/
  `vocabulary_category_list`/`grammar_category_list` views — this is purely
  a home-page entry-point change, not a change to any destination page.

## Architecture

**New partial: `templates/partials/mode_picker_modal.html`.** Included
unconditionally from `base.html` (like `partials/auth_modal.html` — guests
need this too, unlike the auth-gated `partials/account_modals.html`).
Markup: `.auth-modal-overlay` wrapping an `.auth-modal` with a
`.auth-modal-close` button, an `.auth-modal-title` (text set dynamically per
intent by JS), and a `.mode-picker-list` of 6 `.mode-picker-row` buttons —
Vocabulary and Grammar real and clickable, Reading/Writing/Listening/
Speaking disabled with a `.home-sec-pill.soon` "Soon" tag, identical in
shape to production's own 6-row list.

**New file: `static/js/mode-picker.js`,** loaded sitewide from `base.html`
(same always-on convention as `auth-modal.js`). Exposes `openModePicker(intent)`
and `closeModePicker()`:
- `openModePicker(intent)` sets the title via `window.t("home.chooseLearn")`
  or `window.t("home.chooseTest")`, wires the Vocabulary and Grammar row
  click handlers to the correct destination per the routing table below, and
  adds the `.open` class — mirroring `auth-modal.js`'s `openAuthModal`
  exactly (including focus/backdrop/Escape handling).
- Routing table:

  | Intent | Vocabulary | Grammar |
  |---|---|---|
  | `learn` | `{% url 'vocabulary_category_list' %}` | `{% url 'grammar_category_list' %}` |
  | `test` | `{% url 'vocabulary_quiz_setup' %}` | `{% url 'grammar_quiz_setup' %}` |

  (These 4 URLs are rendered into `data-*` attributes on the modal's own
  Vocabulary/Grammar row elements — two rows, each carrying both its
  `learn` and `test` destination — so `mode-picker.js` never hardcodes a
  URL string; it just reads `row.dataset.learnHref`/`row.dataset.testHref`
  based on the intent passed to `openModePicker`.)

**`templates/home.html` changes:** the two hero buttons become
`<button type="button" data-intent="learn" data-i18n="home.startLearning">Start Learning</button>`
and `<button type="button" data-intent="test" data-i18n="home.quickTest">Quick Test</button>`,
each wired via a small inline script block (matching the existing
per-page-inline-script convention already used in `category_word_list.html`/
`word_list.html`) that calls `openModePicker(this.dataset.intent)` on click
— no inline `onclick`, matching this codebase's convention everywhere else.

**i18n:** two new key pairs (en/vi) added to `static/js/i18n.js`:
`home.startLearning`/`home.quickTest` (button labels) and
`home.chooseLearn`/`home.chooseTest` (modal titles, matching production's
"Choose what to learn" / equivalent test-intent phrasing). The old
`hero.start`/`hero.grammar` keys are retired — confirmed via grep to be
referenced nowhere else in the codebase.

## Testing

- New Django tests: modal partial markup present on the home page (guest and
  authenticated), both buttons carry the correct `data-intent`, and the
  routing `data-*` attributes on the Vocabulary/Grammar rows resolve to the
  4 correct URLs.
- Two existing tests (`tests/test_pages.py`, `tests/test_grammar_pages.py`)
  currently assert against the old `hero.start`/`hero.grammar` keys or
  button text and need updating to match the new markup — this is expected,
  not a regression, and should be done as part of the same task that changes
  `home.html`.
- Manual Playwright verification (required per this project's standing
  rule): open the picker via both buttons; click Vocabulary and Grammar
  under each intent and confirm all 4 destinations are correct (including
  the Grammar/test case landing on the quiz, not the browse page); confirm
  the 4 disabled rows don't navigate; confirm Escape and backdrop-click both
  close it; confirm the title text swaps correctly between English and
  Vietnamese.
