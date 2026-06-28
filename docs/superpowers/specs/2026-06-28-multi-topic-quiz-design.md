# Multi-Topic Quiz Selection

**Date:** 2026-06-28
**Status:** Approved

## Summary

Allow users to select multiple topic categories simultaneously when setting up a quiz. Questions are drawn randomly from the combined word pool of all selected categories.

## Current Behaviour

`state.test.filters.cat` is a single string (`"all"` or one category ID). `buildCategoryChips` renders chips as a radio-group — clicking one deactivates all others. `matchesFilters` does a direct string equality check: `word.cat !== f.cat`.

## Target Behaviour

Category chips become toggles. Multiple chips can be active at once. The quiz pool is the union of all selected categories' words. "All Categories" chip resets to the full pool.

## State Change

| Field | Before | After |
|---|---|---|
| `f.cat` | `string` ("all" \| catId) | **removed** |
| `f.cats` | — | `Set<string>` (empty = all) |

`state.test.filters` initialisation:
```js
// before
{ headline:"all", section:"all", cat:"all", cefr:"all", learned:"all" }
// after
{ headline:"all", section:"all", cats: new Set(), cefr:"all", learned:"all" }
```

## matchesFilters

```js
// remove:
if (f.cat !== "all" && word.cat !== f.cat) return false;

// add:
if (f.cats && f.cats.size > 0 && !f.cats.has(word.cat)) return false;
```

`matchesFilters` is shared by Browse, Examples, and Test pages. Only the Test page uses `f.cats`; Browse/Examples continue to use `f.cat` (their filter objects are separate). No change needed to those paths.

## buildCategoryChips

- "All Categories" chip: active when `f.cats.size === 0`; clicking sets `f.cats = new Set()` and calls `onChange()`
- Option chips: active when `f.cats.has(c.id)`; clicking **toggles** the id in/out of `f.cats` and calls `onChange()`
- Visual: active chips keep the existing `.active` class — no new styling needed

## initTopicFilters / Clear Button

Clear button resets `f.cats = new Set()` alongside `f.section = "all"`, `f.cefr = "all"`, `f.learned = "all"`, `f.headline = "all"`.

## applyBrowseFiltersToTest

When navigating from a category view into the quiz:
```js
// before
state.test.filters.cat = catState.cat;
// after
state.test.filters.cats = catState.cat ? new Set([catState.cat]) : new Set();
```

## Scope

Files touched: `vocab-master.html` only.

Functions changed:
- `buildCategoryChips` — toggle logic
- `matchesFilters` — `f.cats` set check (test filter path only)
- `initTopicFilters` — clear resets `f.cats`
- `applyBrowseFiltersToTest` — sets `f.cats` as a Set
- `state.test` initialisation — `cats: new Set()` replaces `cat: "all"`

Functions unchanged: `testPool`, `buildTestQuestion`, `renderTopicFilters`, `buildSectionChips`, all question builders, quiz engine.

## Out of Scope

- Per-topic question count balancing
- Saving selected topics across sessions
- Multi-select for section or CEFR filters
