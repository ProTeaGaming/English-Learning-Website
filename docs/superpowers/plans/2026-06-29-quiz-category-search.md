# Quiz Category Search Bar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a text search input to the quiz's category chip row so users can quickly find categories among 85 options.

**Architecture:** Local `catSearch` state lives entirely inside `TopicCefrFilter.jsx`. It filters `visibleCats` before render. When non-empty it bypasses `ExpandableChips` (shows all matches directly). It resets whenever `filters.section` changes. No changes to filters.js, Test.jsx, or any other file.

**Tech Stack:** React 18 (useState, useEffect), Tailwind CSS

## Global Constraints

- Single file change: `ielts-vocab-master/React-Native/src/components/TopicCefrFilter.jsx`
- No new dependencies
- Search is case-insensitive substring match on category name
- `catSearch` is never stored in the `filters` prop — it is UI-only state
- Styling must match `Filters.jsx` search input verbatim

---

### Task 1: Add category search to TopicCefrFilter

**Files:**
- Modify: `ielts-vocab-master/React-Native/src/components/TopicCefrFilter.jsx`

**Interfaces:**
- Consumes: `CATEGORIES` (array of `{ id, name, icon, theme, section }`), `filters.section` (string)
- Produces: filtered category chips and a search input — no interface changes to parent

- [ ] **Step 1: Add `useEffect` to imports**

Change line 1 of the file from:
```jsx
import { CATEGORIES, SECTION_ORDER } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";
```
to:
```jsx
import { useEffect, useState } from "react";
import { CATEGORIES, SECTION_ORDER } from "../data/vocab-data";
import { CEFR_LEVELS, cefrColor } from "../utils/cefr";
import ExpandableChips from "./ExpandableChips";
```

- [ ] **Step 2: Add `catSearch` state and reset effect**

After the opening line of the component (`export default function TopicCefrFilter...`) and before `const visibleCats`, insert:
```jsx
  const [catSearch, setCatSearch] = useState("");

  useEffect(() => {
    setCatSearch("");
  }, [filters.section]);
```

- [ ] **Step 3: Derive `filteredCats` from `visibleCats`**

After the existing `const visibleCats = ...` line, add:
```jsx
  const q = catSearch.toLowerCase();
  const filteredCats = q
    ? visibleCats.filter((c) => c.name.toLowerCase().includes(q))
    : visibleCats;
```

- [ ] **Step 4: Add the search input above the category chips row**

Replace the category chips `<div>` (currently starting at line 40):
```jsx
      <div className="flex gap-2 flex-wrap items-center">
        <button
          className={"chip" + (filters.cat === "all" ? " active" : "")}
          onClick={() => update({ cat: "all" })}
        >
          All Categories
        </button>
        <ExpandableChips
          items={visibleCats}
          renderItem={(c) => (
            <button
              key={c.id}
              className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
              onClick={() => update({ cat: c.id })}
            >
              {c.icon} {c.name}
            </button>
          )}
        />
      </div>
```
with:
```jsx
      <div className="relative">
        <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[.85rem] opacity-50">🔍</span>
        <input
          type="search"
          value={catSearch}
          onChange={(e) => setCatSearch(e.target.value)}
          placeholder="Search categories…"
          className="w-full appearance-none bg-surface2 border border-line text-ink pl-10 pr-4 py-2.5 rounded-xl text-[.95rem] focus:outline-none focus:border-accent [&::-webkit-search-decoration]:appearance-none [&::-webkit-search-cancel-button]:appearance-none"
        />
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <button
          className={"chip" + (filters.cat === "all" ? " active" : "")}
          onClick={() => update({ cat: "all" })}
        >
          All Categories
        </button>
        {catSearch ? (
          filteredCats.length > 0 ? (
            filteredCats.map((c) => (
              <button
                key={c.id}
                className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
                onClick={() => update({ cat: c.id })}
              >
                {c.icon} {c.name}
              </button>
            ))
          ) : (
            <span className="text-[.82rem] text-muted">No categories match</span>
          )
        ) : (
          <ExpandableChips
            items={visibleCats}
            renderItem={(c) => (
              <button
                key={c.id}
                className={`chip t-${c.theme}` + (filters.cat === c.id ? " active" : "")}
                onClick={() => update({ cat: c.id })}
              >
                {c.icon} {c.name}
              </button>
            )}
          />
        )}
      </div>
```

- [ ] **Step 5: Verify manually**

Start the dev server:
```bash
cd ielts-vocab-master/React-Native
npm run dev
```

Check the following:
1. Navigate to the quiz/test setup page — a search input appears above the category chips
2. Type "emotion" — chips narrow to matching categories only, no "View All" toggle
3. Type a string with no match (e.g. "zzz") — "No categories match" message appears
4. Clear the input — chips return to normal with "View All" toggle
5. Click a section chip (e.g. "Academic Writing Toolkit") — search input clears automatically
6. Click "All Sections" — search input clears

- [ ] **Step 6: Commit**

```bash
git add ielts-vocab-master/React-Native/src/components/TopicCefrFilter.jsx
git commit -m "feat: add category search bar to quiz topic filter"
```
