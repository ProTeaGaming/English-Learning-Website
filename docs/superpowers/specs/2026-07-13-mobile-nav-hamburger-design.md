# Mobile Hamburger Navigation — Design

**Date:** 2026-07-13
**Product:** VocabLarry (Django SPA, `VocabLarry/vocab-master.html`)
**Status:** Approved by user (chat, 2026-07-13)

## Goal

Below 640px (phone widths), the top nav (`Home / Vocabulary / Grammar / Reading /
Writing / Listening / Speaking`) currently wraps into 2-3 cramped rows and its
per-section submenus (Category/Word/Test) are unusable. Replace it with a
hamburger-triggered dropdown for top-level navigation, and move the
Category/Word/Test switcher into the page content itself as a button row.

Tablet (768px+) and desktop are unaffected — they already work correctly and keep
the current tab row + hover-dropdown exactly as-is. The theme toggle, language
menu, progress count, and profile/sign-in area in `.topbar-right` are also out of
scope — untouched by this change on any screen size.

## Breakpoint

`@media (max-width: 640px)` throughout. One breakpoint, no intermediate states.

## Hamburger button + panel

- New button (☰ icon, reuses the existing inline SVG sprite pattern) in
  `.topbar-left`, next to `.brand`. Visible only below 640px; `<nav class="tabs">`
  is hidden at that width via the same media query (CSS-only visibility swap, no
  markup duplication of the tab row itself).
- Clicking it opens a dropdown panel positioned with the same `positionDropdown()`
  helper already used for `#langMenu`/`#userMenu` (added in the dropdown-off-screen
  fix earlier this session) — guarantees on-screen placement regardless of where
  the hamburger ends up in the collapsed header.
- Panel lists the 7 top-level sections in existing nav order (Home, Vocabulary,
  Grammar, Reading, Writing, Listening, Speaking), each item mirroring the
  existing `.tab[data-section-btn]` labels/i18n keys.
- Clicking an item:
  - Closes the panel.
  - Navigates via the existing `goToPage(NAV_SECTIONS[section][0])` call (same
    function the desktop tab click handler already uses for sections without an
    open dropdown) — i.e. Vocabulary → `list`, Grammar → `grammar`, Reading/
    Writing/Listening/Speaking → their single existing page.
  - No nested submenu inside the panel — Vocabulary/Grammar go straight to their
    first page; the Category/Word/Test choice happens on the page itself (below).

## In-page section switcher

- Applies to the 6 pages backing Vocabulary (`list`, `examples`, `test`) and
  Grammar (`grammar`, `gramword`, `gramtest`).
- A row of 3 buttons (Category / Word / Test, using the existing `nav.category` /
  `nav.word` / `nav.test` i18n keys) is added to each of these 6 pages' markup,
  placed directly after the existing `.page-head` block (eyebrow/h1/description)
  and before the rest of the page's content (search bar, filters, list/grid).
- Hidden above 640px via the same media query — desktop/tablet keep using the
  header dropdown for this, so there's no visual duplication there.
- Visible on all three pages within a section (not just the one you land on from
  the hamburger), so switching between Category/Word/Test stays reachable without
  reopening the hamburger — matching how the desktop dropdown is reachable from
  any of the three pages today.
- Clicking a switcher button **does not duplicate navigation logic** — it
  programmatically clicks the corresponding (now phone-hidden) `.nav-dropdown-item`
  for that page. This means the existing per-item click handler — including the
  Test page's `applyBrowseFiltersToTest()` special case — runs exactly as it does
  today, with zero behavioral drift between desktop and phone.
- Active-page highlighting: the switcher buttons get `.active` toggled by the same
  code path that already updates `.nav-dropdown-item.active` inside `goToPage()`,
  so both stay in sync without separate state tracking.

## Explicitly out of scope

- `.topbar-right` (theme/language/progress/profile/sign-in) — confirmed working
  and unchanged.
- Reading/Writing/Listening/Speaking gain no switcher bar now (they're single
  "coming soon" pages with nothing to switch between) — the switcher-bar markup
  pattern is generic enough that adding it there later, once those sections have
  real sub-pages, is a small follow-up rather than a rework.
- No slide-out drawer / off-canvas menu — explicitly a dropdown per the approved
  design, consistent with the existing `#langMenu`/`#userMenu`/`.nav-dropdown`
  interaction pattern already in the app.

## Testing plan

- Playwright at 320/375/414px (phone) and 768/900/1024px (tablet/desktop):
  hamburger visible only below 640px, tab row visible only at/above it.
- Hamburger panel: opens on tap, all 7 items present and correctly labelled/
  translated (EN + VI), stays within the viewport (reuse the existing
  `positionDropdown` on-screen assertion pattern), closes on selection and on
  outside-tap.
- Switcher bar: present and correctly highlighted (`.active`) on each of the 6
  pages at phone widths, absent at tablet/desktop widths; clicking each button
  lands on the right page and preserves the Test page's existing filter-sync
  behavior (`applyBrowseFiltersToTest()` still fires).
- Regression check: existing desktop/tablet nav-dropdown hover behavior and the
  `#langMenu`/`#userMenu` positioning fix both still pass unchanged.
- `pytest` (backend suite — unaffected by this frontend-only change, run for
  regression safety) + `node --check`-equivalent script parse.
