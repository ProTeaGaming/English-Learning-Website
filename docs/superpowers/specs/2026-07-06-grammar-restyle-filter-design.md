# Grammar Restyle & Stage Filter — Design

**Date:** 2026-07-06
**Product:** LexiLoop Django (`ielts-vocab-master/Python/Django/`) only. Flask/PHP/React untouched.
**Follows:** `2026-07-05-grammar-section-design.md` (the grammar section as shipped).

## Problem

User feedback on the shipped Grammar section:
1. Stage colours (CEFR chips, progress fills, mastered green) are too bright, and repeat identically on every card in a stage.
2. The grammar home has no stage filter; the vocabulary Browse view has an All / Basic / Intermediate / Advanced pill bar, and the grammar stage names (Beginner / Independent / Expert) don't match those terms.

## Decisions (user-confirmed)

- Mute **everything stage-related** on the grammar page: CEFR chips, per-card progress fills and mastered bar/medal tint, stage-group progress bars, filter active states.
- Add a filter bar like the vocab one. Selecting a stage shows **only that stage's group** (header + progress bar kept); **All** (default) shows all three groups exactly as today. Selection resets on reload.
- Rename stage **display labels only** to **Basic / Intermediate / Advanced** ("Advanced" with -d, matching the vocab filter). Stage ids stay `beginner` / `independent` / `expert` — no DB value, seed-JSON, or URL changes.

## 1. Rename (backend labels)

- `api/views.py` `GRAMMAR_STAGES`: names become `('beginner','Basic','A1–A2')`, `('independent','Intermediate','B1–B2')`, `('expert','Advanced','C1–C2')`. The API `name` field is what the SPA renders, so the SPA needs no copy change for group titles.
- `vocab/models.py` `GrammarTopic.STAGES` labels: `Basic` / `Intermediate` / `Advanced` (dashboard dropdown, list column, and stage filter labels inherit via `get_stage_display`). Generate the resulting no-op `AlterField` migration.
- Tests asserting the old display names (e.g. `test_grammar_api.py` `beginner['name'] == 'Beginner'`) update to the new labels.

## 2. Filter bar (SPA — `vocab-master.html`)

- Markup: a `headline-bar` inserted inside `#grammarHome`, between the `page-head` and `#grammarStages`, reusing the existing `.headline-bar` / `.headline-btn` classes and sprite icons, but with a grammar-own data attribute so the vocab filter's active-state CSS doesn't apply:
  - `All` (no icon) · `Basic` (`#i-sprout`) · `Intermediate` (`#i-trend-up`) · `Advanced` (`#i-grad-cap`), `data-grammar-stage` = `all|beginner|independent|expert`.
- State: module-level `let grammarStageFilter = 'all';` in the GRAMMAR SECTION module. Not persisted.
- Behaviour: clicking a pill sets the state, toggles `.active`, and re-renders the stage list (`renderGrammarHome` filters the fetched stages array to the selected id before appending groups; `all` appends all three). Stage groups keep their header/progress-bar layout unchanged.
- Active-state CSS (new rules): `all` uses `var(--accent)` like the vocab bar; `beginner`/`independent`/`expert` use the muted stage colours below with white text.

## 3. Muted stage colour system (grammar page only)

> **Rev 2 (2026-07-06, user feedback after ship):** the invented muted palette didn't match the app; the user wants the vocab tier palette. `--gram-*` now alias the vocab vars — `--gram-basic:var(--a2)` (cyan), `--gram-inter:var(--b2)` (blue), `--gram-adv:var(--c1)` (amber) — defined once in `:root` (aliases resolve per theme automatically), and `--gram-done:#10b981` matches vocab's hard-coded mastered green. The mastered medal reverts to the vocab default (gold `#eab308` + glow; the grammar-only medal override and the light-theme `.gram-chip` filter override are removed so vocab treatment applies). Active filter pills use vocab's text colours (`#064e3b` on Basic, `#fff` on Intermediate, `#1c1917` on Advanced). The table below documents Rev 1 (superseded):

| Var | Light ("gallery") | Dark ("velvet") | Used for |
|---|---|---|---|
| `--gram-basic` | `#5b8a6e` (muted sage) | `#8fbf9f` | Basic chips/fills/active pill |
| `--gram-inter` | `#5872a8` (slate blue) | `#95aed6` | Intermediate |
| `--gram-adv` | `#a1743e` (warm bronze) | `#cfa36b` | Advanced |
| `--gram-done` | `#3f7a5f` (calm green) | `#7aab8f` | Mastered bar + medal tint |

Applied via CSS classes, not inline hex:

- **Chips:** `cefrRangePillHtml` stops using `CEFR_COLORS`; it emits `<span class="cat-cefr-pill gram-chip gram-s-{basic|inter|adv}">` chosen by CEFR-label prefix (A1→basic, B1→inter, C1→adv). New rules style each class: low-alpha background (`color-mix(in srgb, var(--gram-*) 14%, transparent)`), 1px border at ~35%, text in the full var. Vocab's `cefrPillHtml`/`CEFR_COLORS` untouched.
- **Card progress fill:** stage colour at rest (`.gram-s-*` modifier on the fill), `var(--gram-done)` when mastered (replaces inline `#10b981`).
- **Medal:** scoped override `#grammarStages .cat-medal { color: var(--gram-done); }`.
- **Stage-group progress bar:** scoped override for `.section-block-pfill` inside `#grammarStages`, coloured per stage via a `gram-s-*` class on the group root.
- **Lesson header chip:** same `cefrRangePillHtml`, so it inherits the muted style automatically.

Rejected alternatives: desaturating global `CEFR_COLORS` (restyles the whole vocab app as a side effect); colourless grey chips (loses stage distinction).

## Error handling / edge cases

- Filter with a stage that has 0 topics: group renders with `0/0` as today (unchanged logic).
- `cefrRangePillHtml` with an unrecognised label prefix falls back to the neutral chip (no `gram-s-*` class → base `gram-chip` styling, muted grey).
- Re-render on filter click reuses the memoised `loadGrammar()` — no extra network requests.

## Testing

- Backend: updated label assertions in `test_grammar_api.py`; full suite stays green. Dashboard tests unaffected (they filter by stage *value*).
- SPA: no JS runner (per project); verification is `node --check`, served-page greps, and a browser pass (filter behaviour, both themes, chip/bar/medal colours).

## Verification checklist

1. Grammar home: filter bar renders; All default; each stage pill shows only its group; group headers read Basic / Intermediate / Advanced.
2. Chips, card fills, stage bars, medal all use the muted palette in both themes; nothing on the vocab pages changed.
3. `/api/grammar/` names are Basic/Intermediate/Advanced; dashboard shows the same labels; `python -m pytest` all pass.
