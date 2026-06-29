# Quiz Category Search Bar

**Date:** 2026-06-29
**Status:** Approved

## Problem

There are 85 categories across 26 sections in the quiz setup. Finding a specific category means scanning through chips (hidden behind a "View All" toggle), which is slow.

## Solution

Add a local text search input to `TopicCefrFilter.jsx` that narrows the visible category chips by name in real time.

## Architecture

Single-file change: `src/components/TopicCefrFilter.jsx`

- Add `const [catSearch, setCatSearch] = useState("")` — local UI state only; not stored in `filters`
- Filter `visibleCats` before rendering: `visibleCats.filter(c => c.name.toLowerCase().includes(catSearch.toLowerCase()))`
- Reset `catSearch` to `""` via `useEffect` whenever `filters.section` changes
- When `catSearch` is non-empty: skip `ExpandableChips` and render all matching chips directly (no "View All" truncation)
- When `catSearch` is empty: keep existing `ExpandableChips` behaviour

## UI

- Search input placed directly above the category chips row
- Styled identically to `Filters.jsx`'s word search: `bg-surface2 border border-line rounded-xl pl-10 pr-4 py-2.5`, 🔍 icon
- Placeholder: `"Search categories…"`

## Scope

No changes to `filters.js`, `Test.jsx`, or any other file.
