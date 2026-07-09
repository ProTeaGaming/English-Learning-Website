# Grammar Word Page — "Irregular Plurals" Set — Design

**Date:** 2026-07-09
**Product:** Django only (`VocabLarry/Python/Django/vocab-master.html`)
**Status:** Approved by user (conversation, 2026-07-09)

## Purpose

The Grammar → Word reference page (`#page-gramword`) currently has four
sets, switched via `#gramwordSetBar` buttons: Irregular Verbs, Comparisons,
Linking Words, Idioms. There is no reference table for irregular plural
nouns (child→children, mouse→mice, etc.), even though the existing
"Nouns, Plurals & Countability" grammar topic (`nouns-plurals`) already
teaches the rule and gestures at examples in a 4-row overview table. This
adds a fifth set, **Irregular Plurals**, giving the same searchable,
filterable, paginated reference table the other four word types get.

## Data shape

New standalone array `GRAMWORD_PLURALS`, entries shaped
`[singular, plural, example, type]` — same shape as `GRAMWORD_LINKERS` /
`GRAMWORD_IDIOMS` (word/meaning-or-pair/example/type-tag).

**Not sourced from a lesson table.** Unlike Irregular Verbs / Comparisons /
Linking Words (which pull their row data from a specific topic's `table`
lesson block via `GRAMWORD_SOURCES`), the `nouns-plurals` topic's table is
a short 4-row rule summary (Regular / -y ending / Irregular / Uncountable),
not a per-word dataset — the same situation Idioms was in, which is why
Idioms is also a standalone array rather than sourced from one topic.

**Categories** (`type` field → filter chips + colored pill, same UX as
Idioms' Level chips / Linking Words' Family chips):

| type key      | label            | example                                   |
|----------------|------------------|--------------------------------------------|
| `vowel`        | Vowel change     | mouse→mice, foot→feet, man→men, tooth→teeth |
| `en`           | -en              | child→children, ox→oxen                     |
| `fve`          | f/fe → ves       | leaf→leaves, knife→knives, wife→wives       |
| `unchanged`    | Unchanged        | sheep, fish, deer, species, aircraft        |
| `foreign`      | Foreign (Latin/Greek) | cactus→cacti, criterion→criteria, datum→data |
| `other`        | Other            | person→people                               |

Target ~55–60 entries total, similar scale to the existing Comparisons
(46 irregular + er/est) and Linking Words (113) sets.

## UI wiring (mirrors the existing four sets)

1. New button in `#gramwordSetBar`: `Irregular Plurals`, icon `#i-users`,
   placed right after `Irregular Verbs` (both are "irregular forms of a
   word class" — grouped together ahead of Comparisons/Linking/Idioms).
   Full button order becomes: **Irregular Verbs, Irregular Plurals,
   Comparisons, Linking Words, Idioms.**
2. New filter row `#gramwordPtypeRow` (chips: All / Vowel change / -en /
   f→ves / Unchanged / Foreign / Other), shown only when
   `gramwordState.set === 'plurals'` — same pattern as
   `#gramwordItypeRow`/`#gramwordLtypeRow`.
3. `gramwordState.ptype = 'all'` added to `gramwordState`, reset alongside
   `pattern`/`ctype`/`ltype`/`itype` on set-switch (`#gramwordSetBar`
   click handler) and on the lesson-page deep-link handler.
4. New branch in `renderGramword()` for `gramwordState.set === 'plurals'`:
   table columns **Singular | Plural | Example | Type**; filtered by
   `ptype` (exact match) and `search` (substring match across singular/
   plural/example, same as the Idioms branch); paginated via the existing
   `GRAMWORD_PER_PAGE` / `buildPagination` machinery.
5. New chip click handler `[data-gramword-ptype]` → sets
   `gramwordState.ptype`, resets to page 1, re-renders — same pattern as
   the existing `[data-gramword-itype]` handler.

## Lesson deep-link

Add `'nouns-plurals': 'plurals'` to `GRAMWORD_TOPIC_SETS`. This is the
existing topic-slug → set-key map that `openGrammarTopic()` already uses
to decide whether a lesson gets a "View all N forms in Word" button after
its table (see `irregular-verbs`, `comparison-structures`, `conjunctions`).
No changes to the `nouns-plurals` lesson content itself — the button
attaches after its existing 4-row overview table automatically. Also
extend the two ternaries in `openGrammarTopic()` that compute the button's
word-count and label text (`wordTotal`, `gramwordLabel`) with a `plurals`
case, matching how `linkers`/`idioms` are handled there today.

## Out of scope (YAGNI)

- No changes to the grammar quiz questions or `grammar-content.json` quiz
  data.
- No changes to the Vocabulary section (word list, examples page) — this
  is purely a new set on the Grammar Word reference page.
- No changes to the `nouns-plurals` lesson's existing 4-row overview
  table — the new dataset is reachable only via the Word page set button
  and the new deep-link, not inlined into the lesson.
- No changes to any other product (Flask/PHP/React) — the Grammar module
  is Django-only, per existing project convention.
