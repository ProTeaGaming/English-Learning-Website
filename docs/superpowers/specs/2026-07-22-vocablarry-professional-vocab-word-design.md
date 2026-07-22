# VocabLarry Professional Environment — Vocabulary Word Page Design

## Context

VocabLarry Professional Environment (VLPE) is a from-scratch, server-templated Django rebuild of production VocabLarry (`VocabLarry/vocablarry.html`), reusing the same backend/models/data. The Nav & Routing Skeleton phase (2026-07-20) registered a stub route at `/vocabulary/word/` (`config/urls.py`, view `vocabulary_word_list` in `config/views_vocab.py:162-163`, template `templates/vocab/word_list.html`) showing only "Coming soon." This is the last unstarted page from the original 4-way visual-retrofit split (the other three — Nav & Routing Skeleton, Vocab Browse/Category/Word visual retrofit, Vocab Quiz visual retrofit, Grammar Browse+Topic Detail retrofit, Grammar Quiz retrofit — are all done; see project memory).

This is distinct from `/vocabulary/word/<pk>/` (`vocabulary_word_detail`, already fully built), which renders a single word's own detail page. This spec is for the **list/browse** page: a sitewide, filterable, paginated index across all ~5,000 words in all 250 categories — production's own "Word" nav tab (internally `renderExamples()`/`state.examples` in `vocablarry.html`, lines ~2046-2093 and ~15132-15215), distinct from the per-category word grid.

Production's version filters entirely client-side over an in-memory dataset and opens a modal (`openWordModal`) per word. VLPE has already established a different, deliberate pattern for both of these:
- Every other VLPE browse-style page (category browse `vocab_browse`, category word-list `vocab_category`) re-renders server-side per filter via plain `<a href>`/GET params — no client-side filtering JS.
- The Vocab Browse + Word phase deliberately chose real per-word URLs over a modal, specifically for deep-linking. `word_detail.html` already exists and is fully built.

This page follows both established patterns rather than production's own mechanism.

## Goal

Build `/vocabulary/word/` as a real, filterable, paginated sitewide word index, matching VLPE's established visual system and server-rendering conventions — the CSS, chip, badge, card, and pagination infrastructure this needs already exists from prior phases; this is primarily a new view + template wiring existing pieces together, plus one new small stage→CEFR grouping.

## Filters

All filters are GET query params on `/vocabulary/word/`, combinable, page-resetting on change:

- **`q`** — case-insensitive substring search across `word`, `definition`, and the JSON list fields `synonyms`/`antonyms` (matches production's "Search words, definitions, synonyms…" placeholder intent). Implemented as a Python-level filter over the queryset's JSON list fields (icontains doesn't apply cleanly to JSONField list contents across SQLite/Postgres) — see Data Flow below for the exact approach.
- **`category`** — plain `<select>` dropdown, all 250 `Category` rows by name. Not chips (250 options is unusable as a flat chip row — the same call already made for Vocab Quiz's setup page).
- **`stage`** — coarse tabs: All / Basic / Intermediate / Advanced. New module-level mapping in `config/views_vocab.py`, mirroring the existing `GRAMMAR_STAGES` convention in `api/views.py:61`:
  ```python
  WORD_STAGES = [
      ('basic', 'Basic', ['A1', 'A1+', 'A2', 'A2+']),
      ('intermediate', 'Intermediate', ['B1', 'B1+', 'B2', 'B2+']),
      ('advanced', 'Advanced', ['C1', 'C1+', 'C2', 'C2+']),
  ]
  ```
  Selecting a stage filters `cefr_level__code__in` that stage's list. This is a coarser view of the same underlying field as the CEFR chip row below — the two filters compose (stage narrows first, CEFR chip can further narrow within it), matching production's own two-level relationship.
- **`cefr`** — fine-grained chip row, all 12 `CEFRLevel` codes (`CEFRLevel.objects.order_by('order')` already returns exactly `A1, A1+, A2, A2+, B1, B1+, B2, B2+, C1, C1+, C2, C2+` — confirmed against the live dataset). Reuses the existing `.chip.active[data-browse-cefr="X"]` CSS already in `base.css`.
- **`progress`** — All / Learned / Little Bit / Not Learned — chip row, **rendered only when `request.user.is_authenticated`**, absent entirely for guests (matching `vocab_browse`'s existing progress-chip guest behavior).
- **Clear filters** — a plain link back to `/vocabulary/word/` with no query params.

## Cards & Pagination

Each result renders as a `.word-card` — the identical hover-reveal component already built for `category_word_list.html` (`templates/vocab/category_word_list.html`): at rest shows word / part-of-speech / CEFR badge; on hover reveals full definition, synonyms/antonyms, and example sentence. Two differences from the category-page version, since this page spans all 250 categories instead of one:
- Each card additionally shows a small category tag (name, linking to that category's own word-list page) so users can tell which category a word belongs to.
- No bulk actions (`Mark All Completed`/`Reset All`) — scoping a mass-write action to an arbitrary, filter-dependent result set (rather than one bounded category) was judged confusing/risky and is intentionally out of scope for this page. Per-word progress toggle (see below) remains available.

Synonyms/antonyms in the hover-reveal render as plain text on this page (not cross-reference links) — unlike `word_detail.html`, which resolves them via `_resolve_word_refs` (one query per synonym/antonym; acceptable there since it's a single word, but not repeated per-card across a 25-row page — see the N+1 note in Testing below). Matching the existing `category_word_list.html` convention exactly: only the word headword itself is a clickable `<a>` to `vocabulary_word_detail` — the rest of the card is not a navigation target (the card also hosts the interactive progress-toggle button, so making the whole card a link would conflict with it). Full cross-reference links remain available on the word's own detail page.

Pagination: 25/page, reusing the existing `_pagination_window` helper (`config/views_vocab.py`) and `.pagination`/`.page-btn` CSS already built for the category word-list page — same numbered, ellipsis-windowed shape.

## Progress Toggle (authenticated users)

Each card's hover-reveal includes the same `.card-toggle` button markup already used in `category_word_list.html` (`data-word-id`, `data-state`, bound by the existing global `window.vocabToggleWord` handler in `static/js/vocab-word.js`) — no new JS. This already implements the required GET-then-merge-then-POST pattern against `/auth/sync/`'s `learn_map` field.

## Data Flow

```python
# config/views_vocab.py

WORD_STAGES = [ ... ]  # see Filters above

def vocabulary_word_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    stage = request.GET.get('stage', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()

    words = Word.objects.select_related('category', 'cefr_level').order_by('word')

    if category_slug:
        words = words.filter(category__slug=category_slug)

    stage_codes = next((codes for sid, _, codes in WORD_STAGES if sid == stage), None)
    if stage_codes:
        words = words.filter(cefr_level__code__in=stage_codes)
    if cefr_filter:
        words = words.filter(cefr_level__code=cefr_filter)

    if query:
        q_lower = query.lower()
        words = [
            w for w in words
            if q_lower in w.word.lower()
            or q_lower in w.definition.lower()
            or any(q_lower in s.lower() for s in w.synonyms)
            or any(q_lower in a.lower() for a in w.antonyms)
        ]
        # falls back to a Python list here since JSON-list substring matching
        # isn't portable across the ORM; combined with the filters above
        # (already applied at the DB level) this only iterates the
        # already-narrowed queryset, not the full 5,000-row table.
    ...
```

The `query` branch necessarily evaluates the queryset into a Python list (JSONField list-substring matching has no portable ORM expression), but only after every DB-level filter (`category`, `stage`, `cefr`) has already narrowed it — it never scans the full unfiltered 5,000-row table. `progress` filtering (needs `request.user.learn_map`, a per-user dict) is applied last, also in Python, exactly like `vocab_browse`'s existing `progress_filter` handling.

Pagination (`Paginator`, 25/page) applies to the final filtered list. Category dropdown options and CEFR chip values come from `Category.objects.order_by('name')` / `CEFRLevel.objects.order_by('order')` respectively — both already fetched elsewhere in this file.

## Out of Scope

- Category section-grouping (the ~75/12-section layer deferred twice already in this project) — the category filter is a plain dropdown, not grouped chips.
- Bulk mark-all/reset-all actions on this page (see Cards section above).
- Any change to `word_detail.html`, `_resolve_word_refs`, or `vocab-word.js` — all reused as-is.
- Vietnamese translation / US-UK dialect substitution (already-standing deferred scope from the original Vocab Browse + Word phase).

## Testing

Pytest + Django test client, mirroring the existing `test_vocab_pages.py` conventions:
- Each filter individually (`q`, `category`, `stage`, `cefr`, `progress`) and in combination.
- Stage→CEFR mapping correctness (e.g. `stage=basic` returns only A1/A1+/A2/A2+ words, never a B1 word).
- Pagination boundaries (page 1, last page, out-of-range page number).
- Guest vs. authenticated behavior: progress chips and the inline `.card-toggle` are absent for guests, present for authenticated users; `progress` filter has no effect for guests.
- "Clear filters" produces the unfiltered, page-1 result set.
- Category dropdown lists all 250 categories by name.
- **N+1 guard, called out ahead of time given this project's history of exactly this bug class on card-grid pages (Vocab Browse + Word phase hit two N+1s in one task):** confirm the view issues a small, fixed number of queries regardless of result-set size — no per-word `.count()` or per-word extra query in a loop over the page. `select_related('category', 'cefr_level')` must be present on the base queryset.
