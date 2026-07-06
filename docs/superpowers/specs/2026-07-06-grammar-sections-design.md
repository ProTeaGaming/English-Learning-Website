# Grammar Thematic Sections — Design

**Date:** 2026-07-06
**Product:** LexiLoop Django (`ielts-vocab-master/Python/Django/`) only. Flask/PHP/React untouched.
**Follows:** `2026-07-06-grammar-restyle-filter-design.md` (stage filter bar + vocab palette, shipped).

## Problem

The grammar home groups topics by CEFR stage (Basic / Intermediate / Advanced). The user wants it organized like the vocab Browse view instead: thematic sections, each holding related topic cards (all tense topics under a Tenses section, etc.). The stage filter stays, working like vocab's cross-section headline filter.

## Decisions (user-confirmed)

- Curated **11 sections** (no single-card sections), replacing the 3 stage groups as the page structure.
- The **stage filter bar stays**: Basic/Intermediate/Advanced filters cards inside every section; sections left empty disappear; All (default) shows everything. Canonical section numbering (01–11) is kept when filtered.
- Mapping is **client-side by slug** (like the vocab SECTIONS remap) — no backend/API/model change. Slug-level is required because the `Sentence` tag splits across three sections.

## Section taxonomy (canonical order, 36 slugs)

| # | Section | Slugs |
|---|---------|-------|
| 01 | Tenses | present-simple-continuous, past-simple-continuous, future-forms, perfect-tenses |
| 02 | Questions & Reported Speech | question-forms, reported-speech, question-tags-indirect |
| 03 | Nouns, Pronouns & Determiners | nouns-plurals, pronouns-possessives, articles, quantifiers |
| 04 | Adjectives & Adverbs | comparatives-superlatives, gradable-adjectives, adverbs-word-order |
| 05 | Word Forms & Prepositions | word-forms, prepositions-time-place |
| 06 | Verb Patterns & Modals | gerunds-infinitives, used-to, modal-verbs, advanced-modality |
| 07 | Voice | passive-voice, causatives |
| 08 | Conditionals & Unreal Forms | conditionals, mixed-conditionals, wish-if-only, subjunctive-unreal-past |
| 09 | Clauses | relative-clauses, participle-clauses |
| 10 | Emphasis & Sentence Focus | inversion-emphasis, cleft-sentences, fronting-ever-clauses, dummy-subjects |
| 11 | Cohesion & Academic Style | linking-words, ellipsis-substitution, nominalisation, hedging-academic-tone |

Counts: 4+3+4+3+2+4+2+4+2+4+4 = 36 ✓

**Fallback:** a topic whose slug is not in the map is grouped under its own `tag` as an extra section appended after 11, in encounter order — dashboard-created topics never vanish.

## SPA changes (`vocab-master.html`, GRAMMAR SECTION module only)

- New consts: `GRAMMAR_SECTION_ORDER` (the 11 names, in order) and `GRAMMAR_SECTIONS` (36 slug → section-name entries).
- `renderGrammarHome`:
  1. Flatten the fetched stages into one topic list, attaching `stageId` (the parent stage's id) to each topic.
  2. Apply `grammarStageFilter` (`all` or a stage id) to the flat list.
  3. Group by `GRAMMAR_SECTIONS[slug] || tag`; order groups by `GRAMMAR_SECTION_ORDER` index (unmapped appended); within a group sort by stage rank (`beginner` 0, `independent` 1, `expert` 2), preserving API order within a rank.
  4. Render each non-empty group with `renderGrammarSection(name, topics, num)` where `num` is the canonical 1-based index in the ordered full list (stable when filtered).
  5. If nothing renders (empty DB or an impossible filter), show `<p class="sub" style="text-align:center;">No grammar topics yet.</p>`.
- `renderGrammarSection(name, topics, num)` replaces `renderGrammarStage(stage, num)` — same `section-block` markup and collapse behaviour, with: name = section name, meta = `${topics.length} topic${topics.length !== 1 ? 's' : ''}`, progress = mastered-in-section count over section size, and **no** `gram-s-*` class on the block root (mixed stages → default accent progress fill). Topic cards are unchanged except `stageKey` now derives from the topic's attached `stageId`.
- CSS: remove the three now-unused rules `#grammarStages .section-block.gram-s-* .section-block-pfill{...}`. Everything else (chips, card fills, filter bar, palette) stays.
- Lesson/quiz views, progress storage, and the filter wiring are untouched.

## Error handling / edge cases

- Filter leaving zero sections → the "No grammar topics yet." message (also covers an empty DB).
- Unmapped slugs → tag-named fallback sections (see above).
- Re-render reuses the memoised `loadGrammar()`; no extra requests.

## Testing

- Backend untouched: `python -m pytest` stays 42 passed.
- SPA: `node --check` on the main script; served-page greps for `GRAMMAR_SECTIONS`/`renderGrammarSection`; a data-shape sanity script asserting the 36 seed slugs exactly cover the map (no missing, no extras).
- Browser pass: 11 sections in order with correct counts; filter narrows cards and hides empty sections (Basic leaves only sections 01–05; Advanced leaves 01 Tenses out since it has no expert topic — expect 04, 06, 08–11); mastered medal/bars unchanged; both themes.
