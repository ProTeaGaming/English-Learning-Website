# Vocabulary US/UK Word-Swap Pairs — Design

**Date:** 2026-07-16
**Product:** Django only (`VocabLarry/vocablarry.html` + a new data migration)
**Status:** Approved by user (conversation, 2026-07-16)

## Purpose

Phase 1 (shipped, commit `2908e53`) handled *spelling* variants of the same
word (colour/favourite/sceptical). It deliberately excluded words where US
and UK use genuinely different words for the same thing (shoes/trainers,
eraser/rubber) — those don't exist in this academic/IELTS dataset as
distinct headwords, so there was nothing to swap yet.

Testing Phase 1 surfaced two real gaps:

1. **12 words already in the dataset have this exact problem today**, but
   nobody noticed until now: the canonical headword is the UK term with
   the US term buried in the synonym list (or vice versa), so the word
   displays identically regardless of which English mode is active. This
   is a pre-existing data mistake, not something introduced by the
   language switcher — English (US) mode should never have been showing
   "flat" or "rubbish" or "queue" as the default headword.
2. **Well-known US/UK pairs that aren't in the dataset at all** (eggplant/
   aubergine, elevator/lift, etc.) — genuinely new vocabulary, not a fix.

This is **Phase 3** (Phase 2 remains the future Grammar-content pass,
still not started). It reuses Phase 1's `WORD_GB` override dict and
accessor functions unchanged — no new JS mechanism, just more data plus
one Django data migration.

## Part A — Fix 12 existing words

For each row below: the DB headword changes from the current (wrong)
value to the correct US term, synonyms gain the old headword, and the
example sentence's `<em>` tag is rewritten to match (every existing word
in this dataset already follows the convention that its example
italicizes the headword itself). A `WORD_GB` entry restores the original
UK headword/example/synonyms for `en-gb` mode — mechanically, the UK
override is exactly the word's original pre-migration content.

| pk | Current (wrong) headword | → New US headword | UK override (`en-gb`) |
|---|---|---|---|
| 6129 | flat | apartment | flat |
| 9274 | biscuit | cookie | biscuit |
| 9276 | candy *(already correct — US default unchanged)* | candy | sweets |
| 9336 | holiday | vacation | holiday |
| 9050 | trousers | pants | trousers |
| 8994 | rubbish | garbage | rubbish |
| 9269 | queue | line | queue |
| 6377 | film | movie | film |
| 6135 | garden | yard | garden |
| 8995 | bin | trash can | bin |
| 9204 | rubber | eraser | rubber |
| 9053 | shoes | sneakers | trainers |

Two rows need more than a mechanical swap, found while drafting the exact
before/after content:

- **6377 "film"**: its example is `What's your favourite <em>film</em>?` —
  "favourite" is British spelling already sitting in what's supposed to be
  the US-default baseline, a pre-existing data slip unrelated to this
  feature. Since this row is already being touched, fix it to "favorite"
  in the US version at the same time (the UK override keeps "favourite",
  unchanged from original).
- **9053 "shoes" → "sneakers"**: unlike the other 11, this isn't a clean
  1:1 pre-existing pair — "shoes" is a generic term valid in both dialects,
  and its synonym "boots" is not accurate for "sneakers" specifically
  (sneakers ≠ boots). This row gets a tightened definition ("Casual
  athletic shoes worn for sport or everyday wear") and "boots" dropped
  from synonyms on both sides, plus an adjusted example context (party →
  gym, since sneakers-for-a-party reads oddly).

**Excluded from this pass** (per user decision, conversation 2026-07-16):
- pk 9075 "pharmacy" — synonyms already list both chemist (UK) and
  drugstore (US), but "pharmacy" itself is standard in both dialects, so
  it stays neutral, no swap.
- soccer/football, vest/waistcoat, and similar pairs found during the
  audit — these are false friends (different sports/garments in each
  dialect), not the same referent renamed. Swapping them would teach
  something factually wrong, so they're excluded from any list, not just
  deferred.

## Part B — Add 18 new words

None of these exist in the dataset in any form today. Each gets a full
new `Word` row — definition, POS, example (with the headword italicized
via `<em>`, matching every existing entry), synonyms/antonyms, a CEFR
level, and an existing category (no new categories needed — the current
85+ categories already cover clothing/home/food/travel/tech themes).
US term is the canonical headword; `WORD_GB` supplies the UK term.

New pairs (US → UK): eggplant→aubergine, zucchini→courgette, diaper→nappy,
sweater→jumper, flashlight→torch, gasoline→petrol, sidewalk→pavement,
faucet→tap, parking lot→car park, mailbox→postbox, cell phone→mobile
phone, resume→CV, stroller→pram, pacifier→dummy, band-aid→plaster,
crib→cot, elevator→lift, math→maths.

Category/CEFR assignment principle: match the word to whichever existing
category's theme it fits (e.g. sweater/diaper/crib → Home & Household or
Clothes & Appearance; gasoline/sidewalk/parking lot → a Travel category;
cell phone → a Technology category), at a CEFR level consistent with
similar everyday-object words already in that category (most such words
in this dataset sit around A1–A2). Exact category/CEFR per word is
finalized in the implementation plan, not this spec.

## Mechanism

No new JS architecture. Reuses Phase 1 exactly:

- **Data migration** (Django, `vocab` app): a single `RunPython` migration
  that (1) updates the 12 existing rows' `word`/`synonyms`/`example` (and
  the two extra content fixes above), and (2) creates the 18 new `Word`
  rows. Reversible where practical (the 12 fixes can restore original
  values in `reverse_code`; the 18 new rows can simply be deleted).
- **`WORD_GB`** (`vocablarry.html`): gains 30 more entries (12 fixes + 18
  new words), same `{word?, def?, example?, synonyms?, antonyms?}` shape
  already established.
- **No accessor changes.** `wordHeadword`/`wordDef`/`wordExample`/
  `wordSynonyms`/`wordAntonyms` already do exactly what's needed — every
  Task 3/4 call site from Phase 1 already routes through them, so the 18
  new words and 12 fixed words work in every render/search/quiz path
  automatically the moment their `WORD_GB` entries exist.

## Testing

- `pytest` suite: the migration needs its own test (row counts before/
  after, spot-check a few fixed rows' new values) — this is the one part
  of this phase that *does* touch the backend, unlike Phase 1.
- Playwright: confirm a sample of the 12 fixed words show the correct
  headword in both English (US) and English (UK) modes (and that search
  finds them under either spelling in the matching mode); confirm the 18
  new words appear in their assigned category's word list and behave
  identically to any other word (quiz, word detail modal, cross-reference
  links) in both language modes.
- Confirm total word count is now 5,018 (5,000 + 18 new), and that the 12
  fixed rows kept the same `pk` (only content changed, not identity —
  existing `learnMap` progress keyed by the *old* headword string would
  otherwise appear to "lose" progress for these 12 words, since
  `learnMap` is keyed by headword text, not `pk` — see Risk below).

## Known risk: `learnMap` is keyed by headword text, not `pk`

Phase 1's design deliberately kept `learnMap`/`selectedWords`/
`VOCAB_BY_WORD` on the *raw* headword field as a stable identity key,
specifically because within Phase 1 the raw field never changed underneath
a language switch. This phase's Part A changes the raw field's *value*
itself (fixing bad seed data), which is a different kind of change:
anyone who already marked "flat" as learned before this migration ships
will find their progress un-attached, since `learnMap["flat"]` no longer
matches the new headword `"apartment"`. This is unavoidable given the
existing keying scheme (only 12 words affected, one-time at migration
time) — flagged here as a known, accepted tradeoff rather than a surprise
found during review. Whether any real user has saved progress on these
12 words specifically hasn't been checked against the production
database; if that matters, check `learnMap`/`grammar_map` usage for these
12 words on the live site before shipping this migration there.

## Out of scope for this phase (YAGNI)

- Grammar content (still Phase 2, not started).
- Any further audit beyond the 12+18 words listed above — this is not an
  exhaustive sweep of all possible US/UK word pairs, just the ones found
  and approved in this conversation.
- New categories or CEFR levels — everything fits existing ones.
- Changing how `learnMap` keys words (e.g. switching to `pk`-based keys)
  — a real improvement but unrelated to this feature and a much larger,
  separate change touching every learn-state read/write site.
