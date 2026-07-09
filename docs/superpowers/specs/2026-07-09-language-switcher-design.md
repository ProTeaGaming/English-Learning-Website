# UI Language Switcher (Vietnamese) — Design

**Date:** 2026-07-09
**Product:** Django only (`VocabLarry/Python/Django/vocab-master.html`)
**Status:** Approved by user (conversation, 2026-07-09)

## Purpose

Add a Duolingo-style "learn English from your own language" UI switcher.
A new globe button next to the theme toggle opens a language dropdown.
For now only English (default) and Vietnamese are functional; ten more
common languages are listed but inert ("coming soon"), so the dropdown
reads as a genuinely broad, real product surface rather than a stub.

Switching to Vietnamese translates the app's own interface — navigation,
page titles/descriptions, buttons, filter chips, empty-states, quiz
feedback sentence structure, category/section/grammar-topic names — into
Vietnamese. It never translates the English content being learned: words,
definitions, example sentences, quiz answer values, synonyms, antonyms,
or grammar example tables. Word definitions and grammar lesson
explanatory prose are explicitly deferred to a separate Phase 2 (see
below) — they stay English until that follow-up ships.

## Language list

12 languages in the dropdown, each shown in its own native script:

| Code | Native name | Status |
|---|---|---|
| en | English | active (default) |
| vi | Tiếng Việt | active |
| zh | 中文 | soon |
| ja | 日本語 | soon |
| ko | 한국어 | soon |
| ar | العربية | soon |
| fr | Français | soon |
| nl | Nederlands | soon |
| de | Deutsch | soon |
| es | Español | soon |
| pt | Português | soon |
| ru | Русский | soon |

## UI

- New button in `.topbar-right`, immediately after `#themeToggle`, same
  `.theme-toggle` circular styling, icon `#i-globe` (existing sprite
  symbol, no new asset needed).
- Clicking opens a dropdown panel (same open/close/outside-click/Escape
  pattern as the existing account menu `#userMenu`) listing all 12
  languages in the table order above.
- Active language row shows a checkmark; inert rows show the existing
  `.home-sec-pill.soon` "Soon" pill, dimmed, `cursor:default`, no click
  handler — the same treatment already established for the mode-picker's
  disabled Reading/Writing/Listening/Speaking rows.
- Selecting English or Vietnamese closes the dropdown and re-renders the
  page in place — no reload, no navigation.

## State & persistence

- New `state.lang`, default `'en'`, persisted to `localStorage` under
  `ivm_lang` — same mechanism as `ivm_theme` for dark/light mode.
- Local-only for now; not synced to the account (matches the theme
  toggle's current behavior). No backend/API changes.

## Translation architecture

Two mechanisms, depending on where the English text currently lives:

**1. Static HTML chrome → `data-i18n` + `UI_STRINGS` + `applyI18n()`**

Most of the app's chrome (nav labels, page `<h1>`/description text,
button labels, filter chip labels, placeholders, empty-states, quiz
feedback wrapper sentences, home hero/Explore-Sections copy) is literal
static HTML today — there is no render function to hook into. Each
translatable element gets `data-i18n="key"` (English text stays as the
element's default content, doubling as the `en` fallback). A new
dictionary `UI_STRINGS = { en: {...}, vi: {...} }` holds every key's text
in both languages. A new `applyI18n()` walks every `[data-i18n]` element
and sets its text from `UI_STRINGS[state.lang]`, falling back to English
if a key is missing for the current language. Runs once on load and again
on every language change.

For quiz feedback ("Correct!", "Not quite.", "The answer is \"...\""),
only the wrapper sentence is a `data-i18n`-style translatable template —
the actual English answer value substituted into it is untouched, since
answer content stays English.

**2. Data-driven names → per-slug lookup maps + accessor helpers**

Category names, vocab section names, and grammar topic/section names come
from JS data structures (`CATEGORIES`, section-name constants, grammar
topics), not static HTML. Each gets its own Vietnamese lookup map keyed
by slug/name, plus a small accessor helper (e.g. `catName(cat)`) that
returns the Vietnamese name when `state.lang === 'vi'` and a translation
exists, else the English name unchanged. Every render site that currently
reads `.name` / `.title` directly for one of these gets routed through
its helper instead.

The brand name "VocabLarry" is never translated anywhere — it's a
product name, not UI copy.

## Phase boundary

**Phase 1 (this feature):**
- Language switcher itself (button, dropdown, state, persistence)
- All static UI chrome across every page: nav, page heads, buttons,
  filter chips, placeholders, empty-states, quiz feedback wrapper text,
  home hero, Explore Sections cards
- All vocab category names + vocab section names
- All grammar topic titles + grammar thematic section names

**Phase 2 (separate, later — not part of this build):**
- All ~5,000 word definitions (`word.def`)
- Grammar lesson explanatory prose (intro/rule blocks) and quiz "why"
  explanations

**Never translated, any language, any phase:**
- The words themselves, synonyms, antonyms, example sentences, quiz
  question/prompt text, quiz answer values, grammar example tables

## Out of scope for Phase 1 (YAGNI)

- Auth/profile modal form field labels and validation messages (Sign in,
  Edit profile, Delete account, password reset flows) — large, separate
  form-heavy surface; a later pass.
- Debug-mode admin UI (staff-only, not learner-facing).
- Any backend/API change, any new dependency, account-level language
  sync, machine-translation-on-the-fly.
- Partial/placeholder translations for the other 10 inert languages —
  they stay fully inert, no content in any language besides their native
  name label.

## Execution note

Given the size of this surface, implementation proceeds one self-contained
piece at a time — infrastructure and the switcher itself first (shipped
and verified working end-to-end before starting the next piece), then
each page's chrome translated in turn. This mirrors how the Grammar
Section feature was built in this project (one spec, many sequential
implementation tasks).
