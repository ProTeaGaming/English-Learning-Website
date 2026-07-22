# VocabLarry Professional Environment — Vocabulary Category Section Grouping Design

## Context

VocabLarry Professional Environment (VLPE) is a from-scratch, server-templated Django rebuild of production VocabLarry (`VocabLarry/vocablarry.html`), reusing the same backend/models/data. VLPE's Vocabulary Category browse page (`/vocabulary/category/`, view `vocab_browse` in `config/views_vocab.py`, template `templates/vocab/browse.html`) has always shown a flat, ungrouped grid of all 250 `Category` rows — the "75-section category-grouping layer" deliberately deferred across multiple earlier VLPE phases (see project history). This spec builds that deferred layer.

Production's real behavior, confirmed directly against the live site and cross-checked against `vocablarry.html`'s source: categories are grouped into **75 real sections** across three CEFR-based tiers — 10 "Basic" sections, 27 "Intermediate" sections, 38 "Advanced" sections (totaling exactly 250 categories, verified) — rendered as collapsible accordions, each expanding to reveal that section's own category cards plus an aggregate progress percentage. This is a materially different scale than the analogous feature already built for Grammar (`GrammarSection`, only 12 sections total, no tiering, no section-level pagination needed) — this spec designs a parallel-but-larger system for Vocab.

**Verified source data (not assumed):** production's `SECTIONS` constant (`vocablarry.html:2666-2964`) is a flat, literal, hand-authored `{category-slug: "Section Name"}` map — 250 entries, confirmed to match VLPE's real 250 `Category.slug` values with an exact 1:1 set intersection (zero missing, zero extra) via direct comparison against the live database. `BASIC_SECTIONS`/`INTERMEDIATE_SECTIONS`/`SECTION_ORDER` (`vocablarry.html:2966-3050`, the last one is production's own literal name for the "advanced" tier's order list — confirmed via its own `SECTION_HEADLINES` mapping) give the exact real display order within each tier. Production's section headers (`renderBrowseSection()`, `vocablarry.html:14754-14839`) render only a numeral, section name, "N categories · M words" meta text, and a progress bar/percentage — confirmed no icon or hero image per section (unlike Grammar's topic-level icons/images), and confirmed the accordion reuses the exact same shared `.section-block` CSS family already used by Grammar (`vocablarry.html:831-867` — a single shared block, not two separate implementations).

## Goal

Add the section-accordion grouping layer to the Vocabulary Category browse page (all 75 sections, full tier structure), plus a small companion header upgrade to the category word-list drill-in page. Full production parity for the real 250-category/75-section system — explicitly excluding a separate, unrelated production feature (see Out of Scope).

## Data Model

New model, structurally parallel to the existing `GrammarSection` (`vocab/models.py`) but without `icon`/`image_ids` (confirmed unnecessary — production's vocab section headers use neither):

```python
class VocabSection(models.Model):
    TIERS = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    slug  = models.SlugField(max_length=100, unique=True)
    name  = models.CharField(max_length=100)
    tier  = models.CharField(max_length=12, choices=TIERS)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
```

`order` is a single **global** integer spanning all 75 sections (0-9 for the 10 Basic sections, 10-36 for the 27 Intermediate sections, 37-74 for the 38 Advanced sections) — matching production's own `ALL_SECTION_ORDER = [...BASIC_SECTIONS, ...INTERMEDIATE_SECTIONS, ...SECTION_ORDER]` concatenation exactly, so ordering categories by `section__order` alone naturally yields the correct tier-grouped sequence without needing a separate tier-ordering trick. `slug` is generated via Django's `slugify(name)` at migration time (production has no section slugs, only names — needed here for the drill-in page's section-context display and any future direct linking).

A new `Category.section` FK (nullable, `on_delete=models.SET_NULL`, mirroring `GrammarTopic.section` exactly):

```python
section = models.ForeignKey(VocabSection, null=True, blank=True, on_delete=models.SET_NULL, related_name='categories')
```

One data migration: creates all 75 `VocabSection` rows (literal seed data — the verified section names/tiers/order, not derived from any live field), then backfills all 250 `Category.section` assignments from the verified slug→section map (also literal seed data, ported verbatim from `SECTIONS`). Per this project's established `--no-migrations` pytest convention, any test needing this data must create its own `VocabSection`/`Category.section` fixture rows directly — the migration's effect is invisible to the test suite.

## Browse Page Behavior

`/vocabulary/category/` becomes a paginated list of section accordions:

- **Tier filter** (new): All / Basic / Intermediate / Advanced — a chip row alongside the existing CEFR/Progress filters, all combined via AND (server-side, GET query params, matching every other VLPE filter page's established convention — no client-side JS filtering).
- **Existing filters unchanged in meaning:** `q` (category name search), `cefr`, `progress` — now narrow categories *within* each section rather than a flat list; a section with zero remaining categories after filtering disappears entirely from the results (matching production's own `sectionsToShow` resolution).
- **Section accordion:** collapsed by default, expands client-side on header click to reveal that section's own category cards (reusing Grammar's existing tiny generic `.section-block` toggle script verbatim — it already operates purely on class selectors with zero Grammar-specific logic, so it's renamed from `grammar-browse.js` to a shared `section-accordion.js` and loaded on both pages, not duplicated). Each header shows: numeral, section name, "N categories · M words" (everyone), and a progress bar/percentage (authenticated users only, aggregated across the section's own categories — mirrors the existing per-category progress computation already in `vocab_browse`).
- **Pagination:** 10 sections per page (matching production's own `BROWSE_SECTIONS_PER_PAGE = 10`), reusing the existing `_pagination_window` helper — applied to the final filtered section list, same as production.
- **Shared CSS relocation:** `.section-block` and its sub-classes currently live only in `grammar.css` (built for Grammar Browse). Since Vocab now needs the identical component, they move to `base.css` as shared infrastructure — a relocation, not a duplication, with zero visual change to the existing Grammar Browse page.

## Category Word-List (Drill-In) Page

Small, companion header upgrade to `category_word_list.html`: replace the current plain `Vocabulary / {{ category.name }}` breadcrumb with a "← All Sections" link back to the browse page, the category's own icon (reusing the existing `category_icon` template filter, same rendering already used by `.cat-card` on the browse page), and meta text "N words · {{ category.section.name }}". No other change to that page — its own filters, pagination, and card grid stay exactly as they are.

## Out of Scope

- **The synthetic "CEFR Levels" tab** (production's 5th headline tab, alongside All/Basic/Intermediate/Advanced) — this is a genuinely separate feature: 12 synthetic pseudo-category cards (`CEFR_CATEGORIES`, `vocablarry.html:3064-3077`) grouped into 3 synthetic pseudo-sections ("Beginner"/"Independent"/"Expert", `CEFR_SECTIONS`), not real `Category`/section data at all. Deferred entirely, not partially built.
- Any change to the Vocabulary Word page, Vocab Quiz, or Grammar Browse's own existing section-accordion behavior (only its CSS file location changes, not its behavior or markup).
- Vietnamese translation, US/UK dialect substitution — already-standing deferred scope from earlier VLPE phases.

## Testing

Pytest + Django test client, mirroring `test_vocab_pages.py`'s established conventions. Per the `--no-migrations` constraint, every test creates its own `VocabSection`/`Category.section` fixture rows directly (no reliance on the real migration-seeded production data existing in the test database):

- Sections render as collapsed accordions with correct "N categories · M words" meta text.
- Tier filter narrows to only that tier's sections; combines correctly with existing `q`/`cefr`/`progress` filters (AND semantics).
- A section with zero categories remaining after filtering is entirely absent from the response.
- Section-level progress percentage: shown only for authenticated users, correctly aggregated across a section's own categories (not leaking another section's counts).
- Pagination: 10 sections per page, correct behavior on page 1, last page, and an out-of-range page number.
- Drill-in page: "← All Sections" link present, correct icon and "N words · Section Name" meta text render for a category with a real section assignment.
- Migration itself: all 75 `VocabSection` rows created with correct tier/order; all 250 `Category.section` assignments correctly backfilled (spot-check a representative sample across all three tiers, not just one).
