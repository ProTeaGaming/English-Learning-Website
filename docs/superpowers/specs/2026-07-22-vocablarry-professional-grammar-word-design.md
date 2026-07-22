# VocabLarry Professional Environment — Grammar Word Page Design

## Context

VocabLarry Professional Environment (VLPE) is a from-scratch, server-templated Django rebuild of production VocabLarry (`VocabLarry/vocablarry.html`), reusing the same backend/models/data. The Nav & Routing Skeleton phase (2026-07-20) registered a stub route at `/grammar/word/` (`config/urls.py:32`, view `grammar_word` in `config/views_grammar.py:164-165`, template `templates/grammar/word.html`) showing only "Coming soon." This is the last unstarted page from the original VLPE roadmap (the Vocabulary Word page, its sibling, was completed 2026-07-22; see project memory).

Production's Grammar Word page (`#page-gramword` in `vocablarry.html`, ~lines 2274-2343 and ~12840-13290) is a 5-tab searchable/filterable/paginated reference table: Irregular Verbs, Irregular Plurals, Comparisons, Linking Words, Idioms. Two of these tabs (Verbs, Comparisons) source their rows from the SAME `GrammarTopic` lesson-table content VLPE already has in its database (topics `irregular-verbs` and `comparison-structures`, each with one `GrammarLessonBlock` of `type='table'`, shape `{head: [...], rows: [[...], ...]}`) — confirmed live: 64 rows for verbs, 6 rows for comparisons. The other three tabs (Plurals, Linkers, Idioms) are standalone hardcoded JS arrays in production with zero backing content in VLPE anywhere.

## Goal

Ship the two tabs that already have real backing data — **Irregular Verbs** and **Comparisons** — as a real, filterable, paginated reference page. Plurals/Linkers/Idioms are explicitly deferred to future phases once their content is sourced (matching this project's established "decompose a large page into content-ready sub-phases" pattern, e.g. Vocab Quiz's Quiz/Gap/Challenge split).

## Data Source

**No new models, no migration.** The view reads the existing lesson-table content directly at request time:

```python
GrammarLessonBlock.objects.get(topic__slug='irregular-verbs', type='table').data
# -> {'head': ['Base (V1)', 'Past simple (V2)', 'Past participle (V3)'], 'rows': [['be','was/were','been'], ...]}

GrammarLessonBlock.objects.get(topic__slug='comparison-structures', type='table').data
# -> {'head': ['Base', 'Comparative', 'Superlative'], 'rows': [['good / well','better','best'], ...]}
```

This is the same content the Grammar Topic Detail page already renders inline on each topic's own page — reading it a second way for the reference table means there is only one copy of the data, so the two views can never drift apart. Comparisons is scoped to the irregular comparisons already in this table only — production's separate hardcoded regular -er/-est list is out of scope for this phase (a real, deliberate content-completeness trade-off, not an oversight).

## Filters

All server-side via GET query params on `/grammar/word/`, no client-side JS filtering (matching every other VLPE list page's established convention):

- **`set`** — `verbs` (default) or `comparisons`. A plain 2-item tab-link row, same convention as Vocab Word's Stage tabs.
- **`q`** — case-insensitive substring match across every cell in a row (e.g. searching "went" matches the Verbs row `['go', 'went', 'gone']` via its 2nd cell).
- **`pattern`** — Verbs tab only: `AAA`/`ABA`/`ABB`/`ABC`, a chip row. Not shown/applicable on the Comparisons tab.
- **`page`** — pagination, reusing the existing `_pagination_window`-style helper (see Architecture below).

## Pattern Classification (Verbs only)

Each verb row `[v1, v2, v3]` is classified at render time by a new pure-function helper, using the standard ESL pedagogical categorization (not something scraped from production — a well-known, documented classification, computed fresh each render rather than stored):

- **AAA** — all three forms identical (e.g. `cut, cut, cut`)
- **ABB** — V2 and V3 identical, V1 different (e.g. `buy, bought, bought`)
- **ABA** — V1 and V3 identical, V2 different (e.g. `come, came, come`)
- **ABC** — all three different (e.g. `go, went, gone`)

Classification compares the raw stored strings exactly (no attempt to split multi-word variants like `was/were` into sub-alternatives) — a deliberate simplification appropriate for a reference/browsing feature, not scored content.

## Table Rendering

Reuses the existing `.gram-table`/`.gram-table-wrap`/`.gram-table-title` CSS verbatim (already built for Grammar Topic Detail's `type='table'` lesson blocks, `static/css/grammar.css:142-155`) — the exact same table look, now driven by a `head`/`rows` list read directly from the same underlying data instead of a Django template loop over a topic's own lesson blocks. Verbs table gets one additional column (Pattern, rendered as a small colored badge — the only genuinely new CSS this phase needs). Filter bar reuses `.filters`/`.search-row`/`.filter-row`/`.chip`/`.clear-btn` verbatim from `base.css`. Pagination reuses the existing pagination CSS (`.pagination`/`.page-btn`/`.page-ellipsis`) already built for Vocab/Grammar Browse's own paginated views.

Verbs: 64 rows, paginated 25/page. Comparisons: 6 rows — fits on one page; the existing `{% if page_obj.paginator.num_pages > 1 %}` guard means no pagination controls render at all for this tab, which is correct behavior, not a special case to build.

## Out of Scope

- Irregular Plurals, Linking Words, Idioms tabs — no backing content exists in VLPE yet for any of them; each is its own future phase once real content is sourced (the already-existing `docs/superpowers/specs/2026-07-09-grammar-irregular-plurals-design.md` targets a *different* product, `VocabLarry/Python/Django/vocab-master.html`, not this VLPE rebuild — useful only as prior art on the Plurals taxonomy, not a ready-to-port VLPE plan).
- Production's regular -er/-est comparison list (`GRAMWORD_ER_EST`) — Comparisons tab stays scoped to the irregular lesson-table content only.
- Any progress/mastery tracking, per-row detail pages, or bulk actions — this is pure reference content with no practice/scoring concept in production either (no modal, no learn-state).
- Any change to `templates/grammar/topic_detail.html` or the `GrammarLessonBlock`/`GrammarTopic` models — read-only consumption of already-existing data.

## Testing

Pytest + Django test client, mirroring `test_grammar_pages.py`'s established conventions.

**Important — this project's `pytest.ini` sets `addopts = --no-migrations`, so the real production `irregular-verbs`/`comparison-structures` lesson-table content (seeded via a management command, not a data migration, but equally absent from a fresh test database either way) will NOT exist in any test's database.** Every test must create its own `GrammarTopic(slug='irregular-verbs', ...)` + `GrammarLessonBlock(type='table', data={...})` fixture rows directly, exactly like the existing `topic_with_blocks` fixture in `test_grammar_pages.py` already does for other block types. Fixture data should be small and synthetic but deliberately include at least one real-feeling row per Pattern classification (AAA/ABA/ABB/ABC) so the filter tests are meaningful, plus a `comparison-structures` topic+table block for the Comparisons tab. (The `cut`/`buy`/`come`/`go` examples verified against the real dataset above are useful as inspiration for the fixture's synthetic rows, not as something the tests can read from a live-seeded database.)

- Default `set=verbs` renders the Verbs table with all rows from the fixture's `irregular-verbs` block, across pagination if the fixture has enough rows to exercise it.
- `set=comparisons` renders the Comparisons table from the fixture's `comparison-structures` block.
- Search (`q`) matches across every column, not just the first.
- Pattern filter (`pattern=AAA`/`ABA`/`ABB`/`ABC`) returns only rows of that classification, using the fixture's own known rows.
- Pattern filter has no effect / is not shown on the Comparisons tab.
- Clear-filters link resets to the default (verbs, no search/pattern, page 1).
- The classification helper itself is unit-testable directly (pure function, no DB needed) for its 4 branches plus an edge case or two — this part of the test suite CAN safely use the real `cut`/`buy`/`come`/`go` examples as literal inputs, since it doesn't touch the database at all.
