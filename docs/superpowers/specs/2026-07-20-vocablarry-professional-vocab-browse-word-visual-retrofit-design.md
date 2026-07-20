# VocabLarry Professional Environment — Vocab Browse/Category/Word Visual Retrofit (design)

## Context

This is the first of four decomposed "visual retrofit" sub-projects, following
the user's directive to copy production's (`VocabLarry/vocablarry.html`)
designs and functions directly rather than re-derive VLPE's own visual
language — the source of an earlier, real `rgba(var(--violet))` bug. The four
sub-projects: **this one** (Vocab Browse + Category + Word), Vocab Quiz retrofit,
Grammar Browse + Topic Detail retrofit, Grammar Quiz retrofit.

Scoped to 3 existing VLPE pages: `vocab/browse.html` (category grid),
`vocab/category_word_list.html` (word list within one category),
`vocab/word_detail.html` (single word page). All three currently use minimal
"starter" CSS (~215 lines total in `vocab.css`) with no icon sprite, no
progress visualization, and no interactivity beyond a single learn-state
toggle button on the word detail page.

Production's equivalents were researched directly from `vocablarry.html`
(confirmed via line-by-line reading, not memory): the category grid's
`.cat-card` (~16 distinct CSS rules, icon + CEFR pill + word-count tag +
hover-lift + a live progress bar that turns green with a gold medal at 100%);
the word grid within a category's `.word-card` (hover-reveal panel showing
definition/synonyms/antonyms/progress toggle, CEFR-accent top border); and
word detail, which in production is a **modal** (`#word-modal`), not a
separate page.

This sub-project is not purely visual — several pieces require new server
logic or new client-side interactivity, confirmed and scoped explicitly
during brainstorming (see Decisions).

## Decisions

- **Word detail stays a real page, restyled to match the modal's content.**
  Production shows word detail as a JS modal; VLPE deliberately chose a real
  `/vocabulary/word/<id>/` URL in an earlier phase (better for
  deep-linking/sharing than a modal). This retrofit does not reverse that —
  it restyles the page's *content* to match what the modal shows: a card
  container with a CEFR-accent top border, a CEFR badge, and synonyms/
  antonyms rendered as clickable links to those words' own detail pages
  (adapting production's "click a synonym, modal re-opens for that word" into
  "click a synonym, navigate to that word's page").
- **Category progress bar + gold-medal-at-100% is in scope**, computed
  server-side from `request.user.learn_map` — same data source Home's
  existing stats already use (`words_learned`/`categories_started`),
  extended to per-category granularity. Guests (no `learn_map`) see the card
  with no progress bar — nothing to compute, matches word_detail's existing
  "progress row only for authenticated users" pattern.
- **Category accent color reuses VLPE's own existing `Category.color`
  model** (`bg_hex`/`text_hex`, already populated in the DB, already used for
  `--cat-bg`/`--cat-text` inline vars in the current card) instead of
  porting production's separate system of 15 fixed `--t*` theme classes
  cycled by category order. Same visual effect — a distinct, consistent
  accent per category — without introducing a second, redundant color
  mechanism. `--accent-c` becomes an inline custom property sourced from
  `category.color.bg_hex`, and every production rule that reads
  `var(--accent-c, ...)` (the card border/arrow/name/pbar-fill colors) is
  ported using that same custom-property name so the fallback chain behaves
  identically to production's.
- **Word list within a category becomes hover-reveal `.word-card`s**, not a
  plain link list — matches production's actual browsing experience (see
  word info without leaving the grid). Requires the `vocab_category` view to
  pass full word data (definition/synonyms/antonyms/each word's own
  `learn_state`) instead of just word+id, and a per-card progress toggle
  inside the reveal panel (reusing/extending the existing GET-then-merge-
  then-POST pattern `static/js/vocab-word.js` already implements against
  `/auth/sync/`, rather than duplicating that logic in a new file).
- **Numbered pagination** (ellipsis-windowed page buttons + jump-to-page
  input) replaces the current plain Previous/Next text links on the
  category word-list page, matching production's `buildPagination` shape.
- **Bulk "Mark All Completed" / "Reset All" actions** are in scope at the
  bottom of the category word-list page — real new write behavior (not just
  visual), using the same GET-then-merge-then-POST contract against
  `/auth/sync/` every other `learn_map` writer in this codebase already
  follows: GET the current full map, mutate every word ID in *this*
  category, POST the complete map back. Never POST a partial map (see the
  standing project rule on this endpoint's non-merging POST behavior).
  **"Mark All Completed" sets each of this category's word IDs to
  `"learned"`; "Reset All" deletes each of this category's word ID keys
  from the map entirely** — matching `vocab-word.js`'s existing convention
  exactly (`learn_map` is sparse; cycling a word back to "not learned"
  already deletes its key rather than storing an explicit `"none"` value).
  This matters beyond consistency: Home's `categories_started` stat counts
  `len(learn_map.keys())`, so writing an explicit `"none"` entry instead of
  deleting the key would incorrectly keep that category counted as
  "started" after a full reset.
- **Icon sprite: port production's emoji→icon-id lookup table, adapted to
  server-side resolution.** Production resolves category emoji to an SVG
  icon client-side in JS (`iconSvg(emoji, cls)` reading an `EMOJI_ICON_MAP`
  object, falling back to a generic book icon for unmapped emoji). VLPE
  renders categories server-side via Django templates already, so this
  retrofit ports the *lookup table* as a Python dict (a new template filter,
  e.g. `{{ category.icon|category_icon }}` returning the resolved icon id,
  falling back to `"book"`) rather than porting it as client JS — same
  behavior, mechanism adapted to VLPE's existing server-rendered
  architecture (the same kind of adaptation already made for the nav
  dropdown in the routing-skeleton phase). The map itself must be
  transcribed verbatim from production's actual `EMOJI_ICON_MAP` object
  (`vocablarry.html`, ~lines 1440–1468) — not re-invented. Only the SVG
  `<symbol>` definitions actually needed are added to the sprite: at
  implementation time, cross-reference VLPE's real DB (119 distinct
  `Category.icon` values, confirmed via a live query) against the ported
  map, and add exactly the icon symbols those values resolve to, plus the
  `#i-book` fallback — not all ~90 of production's icons blindly.
- **CEFR badge system ported as a 12-way CSS rule family**
  (`.cefr-badge.A1` … `.cefr-badge.C2+`), keyed by `CEFRLevel.code` — pure
  CSS port, no new backend (both `Category.cefr_level` and `Word.cefr_level`
  already exist and are already available in every relevant view's context).
- **Chip-based filter bar replaces the search box + CEFR `<select>`** on the
  category browse page: text search stays a plain input, CEFR becomes pill
  chips (click to toggle, single-select, matching production's
  `data-cat-cefr` chip behavior), and a **new** progress filter (All/
  Learned/In Progress/Not Started) is added as a second chip row — this
  exists in production's `.cat-filter-bar` and requires the same per-category
  progress computation the progress bar already needs, so it's not
  meaningfully extra work once that computation exists.
- **`@ensure_csrf_cookie` added to `vocab_category`** (the category
  word-list view) — this page gains real `fetch()`-based writes (per-card
  progress toggle, bulk actions) for the first time, so the cookie must be
  guaranteed present on first load, matching the established project rule
  (added at the same task that first renders the page, not deferred to
  whichever task adds the JS).
- **No i18n content translation** — same exclusion as every other phase.
  Any new static chrome labels (e.g. "Mark All Completed") get `data-i18n`
  attributes + `en`/`vi` entries in `static/js/i18n.js`, matching every
  existing chrome string's dual-entry pattern; word/definition/example
  content itself is never translated.

## Architecture

```
vocab/
  models.py              (unchanged — no new fields, no migrations)
  templatetags/
    vocab_extras.py       (new — category_icon filter, EMOJI_ICON_MAP dict
                           transcribed from production)
config/
  views_vocab.py          (extend vocab_browse: per-category progress +
                           progress-chip filter; extend vocab_category:
                           full word data per word, @ensure_csrf_cookie,
                           pagination context for numbered pages;
                           vocab_word_detail: resolve synonym/antonym
                           strings to real Word objects where they exist)
templates/
  vocab/
    browse.html            (rewrite — chip filter bar, redesigned .cat-card)
    category_word_list.html (rewrite — .word-card hover-reveal grid,
                             numbered pagination, bulk actions)
    word_detail.html        (rewrite — card container, CEFR badge,
                             clickable synonym/antonym links)
static/
  js/
    vocab-word.js           (extend — generalize the existing toggle logic
                             so category_word_list's per-card toggles and
                             the bulk mark-all/reset-all actions reuse it,
                             rather than duplicating GET-then-merge-then-POST
                             in a new file)
    i18n.js                 (add new chrome-label keys)
  css/
    vocab.css               (rewrite/extend — .cat-card, .word-card,
                             .cefr-badge family, .filters/.chip, pagination,
                             all ported from production with
                             rgba(var(--violet)) converted to
                             rgb(var(--violet) / X) per the established rule)
templates/base.html          (extend icon sprite — only the symbols the
                             category_icon filter's cross-referenced result
                             set actually needs, plus #i-book fallback)
```

## Components

- **`vocab_extras.py` template filter `category_icon`** — pure lookup,
  `EMOJI_ICON_MAP.get(icon, "book")`, no DB access, no side effects.
- **`vocab_browse` view** — extended to compute, per category in the current
  page/filter result set, `{little: N, learned: N, total: N}` from
  `request.user.learn_map` for authenticated users (an efficient one-query
  `Word.objects.filter(category__in=categories).values_list('id',
  'category_id')` word→category map, then a single pass over `learn_map`'s
  entries — not one query per category); `None`/absent for guests. Also
  accepts a new `progress` query param (`learned`/`in_progress`/
  `not_started`) alongside the existing `q`/`cefr` params, filtering
  categories by the same computed progress data.
- **`vocab_category` view** — extended to serialize each page's words with
  their full definition/synonyms/antonyms/`learn_state`, and gains
  `@ensure_csrf_cookie`.
- **`vocab_word_detail` view** — extended to look up each synonym/antonym
  string against `Word.objects.filter(word__iexact=...)` (scoped
  reasonably — see Error Handling) and pass resolved objects (or `None`)
  so the template can render a link vs. plain text per entry.
- **`templates/vocab/browse.html`** — chip filter bar (search input +
  CEFR chip row + progress chip row, all inside one `.filters` glass bar),
  `.cat-card` grid using the ported CSS/markup shape from production,
  `category_icon`-resolved SVG icon, computed progress bar/medal.
- **`templates/vocab/category_word_list.html`** — `.word-card` grid with
  hover-reveal panels (definition/synonyms/antonyms/per-word progress
  toggle), numbered pagination, bulk mark-all/reset-all buttons at the
  bottom.
- **`templates/vocab/word_detail.html`** — card container with CEFR-accent
  top border, CEFR badge, synonym/antonym entries individually rendered as
  either a link (`{% url 'vocabulary_word_detail' resolved.pk %}`) or plain
  text depending on whether resolution found a match.
- **`static/js/vocab-word.js` (extended)** — the existing single-word toggle
  logic becomes a reusable function taking a word ID and target state;
  `category_word_list.html`'s per-card toggles call it per-card, and a new
  bulk handler (same file) does one GET, mutates every word ID belonging to
  the current category in a single pass, one POST.

## Data flow

Category browse: `GET /vocabulary/category/?q=...&cefr=...&progress=...` →
view queries categories (existing filters) → computes per-category
progress from `learn_map` (one extra query + one in-memory pass, guests
skip this entirely) → renders. Category word list: `GET
/vocabulary/category/<slug>/?page=N` → view queries the page's words with
full fields → renders hover-reveal cards; a card's toggle click does the
existing GET `/auth/sync/` → mutate one key → POST full map round-trip; the
bulk buttons do the same round-trip mutating every word ID in the category
at once. Word detail: unchanged read path, plus a synonym/antonym
resolution query at render time.

## Error handling

- Synonym/antonym → `Word` resolution: case-insensitive exact match only
  (`word__iexact`); if a synonym string doesn't correspond to any real word
  in the dataset (common — synonym lists were authored as plain vocabulary
  words, not guaranteed to exist as their own `Word` row), render it as
  plain text, not a broken link. If a synonym matches *multiple* words
  (e.g. the same spelling appears in two categories), link to the first
  match by `id` — ambiguous cross-category synonym linking is a pre-existing
  content-data ambiguity, not something this retrofit needs to resolve.
- Bulk actions on a category with zero words: buttons render but produce a
  no-op POST (empty mutation set) — no special-casing needed, matches how
  the existing single-word toggle already behaves on an already-correct
  state.
- Progress-chip filter (`progress=learned` etc.) combined with `q`/`cefr`:
  all three narrow the same queryset conjunctively, matching how `q`+`cefr`
  already compose today.
- Guests hitting the bulk-action buttons or a per-card toggle: buttons are
  simply not rendered for unauthenticated users (matches the existing
  word_detail page's `{% if user.is_authenticated %}` gate on its own
  toggle) — no client-side auth check needed since the server never sends
  the controls to a guest session.

## Testing

Python tests (extend `tests/test_vocab_pages.py`): category browse renders
the new chip markup and computed progress bar values for a seeded
authenticated user with partial progress (some categories fully learned →
medal+green, some partial → split bar, some untouched → no bar for guests /
zero-state for authenticated); progress-chip filtering actually narrows
results; category word-list renders hover-reveal card markup with real
def/syn/ant content and the correct per-word `data-state`; numbered
pagination renders the right page buttons for a multi-page category;
`@ensure_csrf_cookie` sets the cookie on first load; bulk mark-all/reset-all
round-trip correctly (mirroring the existing
`test_progress_toggle_round_trip_preserves_other_words` pattern — GET
`/auth/sync/`, mutate, POST, assert only the target category's word IDs
changed, everything else in `learn_map` untouched); word detail renders a
real `<a>` for a synonym that resolves to a real word and plain text for one
that doesn't.

No Python-testable surface for the hover-reveal panel's actual show/hide
behavior (pure CSS `:hover`, no JS). **The filter chips are plain
`<a href="?cefr=X&progress=Y&q=...">` navigation links, not JS-driven
client-side toggling** — VLPE has no existing chip-filter precedent
anywhere in its own codebase to follow (every current VLPE filter is a
`<select>`/text-input form submit or a plain link), and production's own
chips are JS-driven only because production is a client-side SPA filtering
already-loaded JSON; VLPE re-renders server-side per filter change already,
so a plain link matches its existing architecture with no new JS filtering
pattern introduced. Each chip's `href` carries the full current filter
state (all three params) plus its own toggle, computed server-side in the
view/template.
The implementation plan must include a real Playwright
click-through: hover a word card and confirm the reveal panel appears with
correct content, click a category card and confirm progress bar/medal
renders correctly for a real multi-category authenticated session, click
through numbered pagination, click bulk mark-all and confirm all cards in
that category update, click a resolved synonym link and confirm real
navigation to that word's page — both themes, per this project's standing
verification bar.

## Explicitly out of scope for this phase

The Vocab Quiz pages' visual retrofit (separate sub-project). Any change to
the Grammar pages. Additional filtering within a single category's word list
beyond pagination (no CEFR/search chips scoped to one category's words —
matches VLPE's existing scope, not identified as a gap during brainstorming).
The pre-existing `rgba(var(--violet))` bug already present in `vocab.css`
(flagged in a prior phase, real but unrelated — this phase's own new CSS
must not introduce new instances of it, but fixing the existing ones is a
separate cleanup). Porting all ~90 of production's category icons
regardless of whether VLPE's actual data uses them (only the cross-
referenced subset, per Decisions). Any change to how `learn_map`/
`grammar_map` are stored or synced beyond reusing the existing
GET-then-merge-then-POST contract.
