# Home Hero Mode-Picker Popup — Design

**Date:** 2026-07-08
**Product:** Django only (`VocabLarry/Python/Django/vocab-master.html`)
**Status:** Approved by user (conversation, 2026-07-08)

## Purpose

The homepage hero has two buttons, "Start Learning →" and "Quick Test",
which today jump straight to the vocab word list / vocab quiz setup page.
The site actually has six sections (Vocabulary, Grammar, Reading, Writing,
Listening, Speaking); jumping straight to vocab skips past that choice.
Both buttons should instead open a mode-picker popup so the user chooses
which section they want, then land on the right page for that section and
that button's intent (learn vs. test).

## Decisions (settled with user)

- **Popup lists all six sections**, matching the homepage's existing
  "Explore Sections" cards (same icon, same name). Reading, Writing,
  Listening, Speaking are visibly disabled with a "Soon" label — same
  live/soon status those cards already show — and are not clickable.
- **Grammar has no cross-topic quick quiz.** Picking Grammar from either
  button (Start Learning or Quick Test) navigates to the Grammar home page,
  where the user picks a topic and starts that topic's own quiz. No new
  quiz-selection logic is built.
- **Vocabulary keeps today's two destinations:** Start Learning → word list
  page (`goToPage('list')`); Quick Test → vocab quiz setup page
  (`goToPage('test')`).
- **One reusable popup**, not two — it is parameterized by which button
  opened it (`'learn'` or `'test'`), since only Vocabulary's destination
  depends on that; Grammar's destination is the same either way, and the
  four disabled rows have no destination at all.
- **Pure frontend, single file.** No backend/API changes — this is a
  navigation layer in front of pages that already exist and already work
  without login.

## Popup UI

- Visual style matches the site's existing modal pattern (`.auth-modal`):
  centered card over a blurred/dimmed overlay, dark/light themed via the
  same `[data-theme="light"]` override convention already used by every
  other modal in the file.
- Title: "Choose what to learn" for Start Learning, "Choose what to test"
  for Quick Test — one shared modal markup for both intents; only the
  title text and the two dynamic Vocabulary/Grammar click handlers change
  per intent, everything else (rows, order, icons, disabled state) is
  identical.
- Six rows in the fixed order: Vocabulary, Grammar, Reading, Writing,
  Listening, Speaking — same order, icons, and names as the homepage
  "Explore Sections" cards (`#i-book`, `#i-pen`, `#i-book-open`,
  `#i-file-text`, `#i-headphones`, `#i-mic`).
- Vocabulary and Grammar rows: icon + name, clickable, hover state.
- Reading/Writing/Listening/Speaking rows: icon + name + "Soon" pill
  (reuse the existing `.home-sec-pill.soon` look), reduced opacity,
  `cursor:default`, no click handler.
- Dismiss via backdrop click, Escape key, or an explicit close (×) button
  — same three dismiss paths the site's other modals already support.
- Clicking a live row closes the popup and immediately calls the
  destination's existing `goToPage(...)` — no new page-transition logic.

## Trigger wiring

- The home hero's two buttons (`vocab-master.html:1702-1703`) no longer
  call `goToPage(...)` directly. Both call one function,
  `openModePicker(intent)`, with `intent` being `'learn'` for Start
  Learning and `'test'` for Quick Test.
- `openModePicker(intent)` opens the shared popup and wires its Vocabulary
  row to `goToPage(intent === 'test' ? 'test' : 'list')` and its Grammar
  row to `goToPage('grammar')`, regardless of intent.

## Out of scope (YAGNI)

- No cross-topic/random grammar quiz.
- No changes to the homepage's "Explore Sections" cards — they keep
  navigating directly, unchanged.
- No "remember my last choice" persistence — the popup asks every time.
- No login gating — matches today's behavior where Vocabulary and Grammar
  need no login to browse.
- No backend/API changes.
