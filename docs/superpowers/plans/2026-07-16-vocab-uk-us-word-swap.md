# Vocabulary US/UK Word-Swap Pairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 12 existing words whose canonical (US/`en`) headword is actually the UK term with no way to see the US term via language switching, and add 18 brand-new words for well-known US/UK pairs missing from the dataset entirely — both via a Django data migration, reusing Phase 1's `WORD_GB` override mechanism unchanged for `en-gb` display.

**Architecture:** Two Django data migrations (no schema changes) in the `vocab` app: one updates 12 existing `Word` rows' `word`/`synonyms`/`example` fields to the correct US baseline, the other creates 18 new `Word` rows. `VocabLarry/vocablarry.html` gets 30 new `WORD_GB` entries (reusing the existing `wordHeadword`/`wordDef`/`wordExample`/`wordSynonyms`/`wordAntonyms` accessors from Phase 1 — no JS changes beyond the data dict itself).

**Tech Stack:** Django data migrations (`RunPython`), the existing `vocab.models.Word`/`Category`/`CEFRLevel` models, the same single-file JS frontend as Phase 1.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-16-vocab-uk-us-word-swap-design.md` — read it if anything below is ambiguous.
- Only touch `VocabLarry/` (this project's rule: it's the only live product; `IELTS-Vocab/` is frozen legacy).
- No new categories, no new CEFR levels — every new word uses an existing `Category`/`CEFRLevel` row, looked up by slug/code (never hardcode a primary key — pks are environment-specific, slugs/codes are stable).
- Never commit-and-push to `elw` without the user explicitly asking in this session — commit locally after each task, hold the push until asked.
- Known accepted risk (see spec): `learnMap` is keyed by headword text, so any saved progress on the 12 fixed words (under their old headword string) will appear to reset. This is expected and not something to "fix" as part of this plan.
- Every code/data snippet below is exact, final content — verified against the live database as of commit `2908e53`. Paste it verbatim; do not regenerate or "improve" it.

---

### Task 1: Fix 12 existing words (migration + WORD_GB)

**Files:**
- Create: `VocabLarry/vocab/migrations/0006_fix_us_uk_word_pairs.py`
- Modify: `VocabLarry/vocablarry.html` (add to `WORD_GB`, ~line 8556)
- Test: `VocabLarry/tests/test_us_uk_word_pairs.py`

**Interfaces:**
- Consumes: nothing new — reuses `WORD_GB`/`ukOverride`/`wordHeadword`/`wordDef`/`wordExample`/`wordSynonyms`/`wordAntonyms` from Phase 1 (already in `vocablarry.html`).
- Produces: 12 `Word` rows with corrected `word`/`synonyms`/`example` (and 2 of them also `definition`); 12 new `WORD_GB` entries. Task 2 does not depend on anything from this task (they touch disjoint sets of words) but both edit the same `WORD_GB` dict, so do this task first to avoid a merge conflict in that dict.

- [ ] **Step 1: Write the migration**

Create `VocabLarry/vocab/migrations/0006_fix_us_uk_word_pairs.py`:

```python
from django.db import migrations

# Each entry: pk -> (old values to restore on reverse, new values to set forward)
FIXES = {
    6129: {
        'old': {'word': 'flat', 'synonyms': ['apartment', 'unit'],
                'example': 'She lives in a small <em>flat</em> in the city centre.'},
        'new': {'word': 'apartment', 'synonyms': ['flat', 'unit'],
                'example': 'She lives in a small <em>apartment</em> in the city centre.'},
    },
    9274: {
        'old': {'word': 'biscuit', 'synonyms': ['cookie'],
                'example': 'She offered him a <em>biscuit</em> with his tea.'},
        'new': {'word': 'cookie', 'synonyms': ['biscuit'],
                'example': 'She offered him a <em>cookie</em> with his tea.'},
    },
    9336: {
        'old': {'word': 'holiday', 'synonyms': ['vacation', 'break', 'time off', 'leave', 'trip'],
                'example': "We're going on <em>holiday</em> next month."},
        'new': {'word': 'vacation', 'synonyms': ['holiday', 'break', 'time off', 'leave', 'trip'],
                'example': "We're going on <em>vacation</em> next month."},
    },
    9050: {
        'old': {'word': 'trousers', 'synonyms': ['pants', 'jeans', 'slacks'],
                'example': 'He wears <em>trousers</em> to the office.'},
        'new': {'word': 'pants', 'synonyms': ['trousers', 'jeans', 'slacks'],
                'example': 'He wears <em>pants</em> to the office.'},
    },
    8994: {
        'old': {'word': 'rubbish', 'synonyms': ['trash', 'garbage', 'waste', 'litter'],
                'example': 'Please put your <em>rubbish</em> in the bin.'},
        'new': {'word': 'garbage', 'synonyms': ['rubbish', 'trash', 'waste', 'litter'],
                'example': 'Please put your <em>garbage</em> in the trash can.'},
    },
    9269: {
        'old': {'word': 'queue', 'synonyms': ['line', 'row', 'wait', 'snake'],
                'example': 'There was a long <em>queue</em> at the checkout.'},
        'new': {'word': 'line', 'synonyms': ['queue', 'row', 'wait', 'snake'],
                'example': 'There was a long <em>line</em> at the checkout.'},
    },
    6377: {
        'old': {'word': 'film', 'definition': 'A story told through moving pictures; a movie.',
                'synonyms': ['movie', 'motion picture', 'cinema', 'flick'],
                'example': "What's your favourite <em>film</em>?"},
        'new': {'word': 'movie', 'definition': 'A story told through moving pictures; a film.',
                'synonyms': ['film', 'motion picture', 'cinema', 'flick'],
                'example': "What's your favorite <em>movie</em>?"},
    },
    6135: {
        'old': {'word': 'garden', 'synonyms': ['yard', 'lawn', 'plot'],
                'example': 'She grows vegetables in the <em>garden</em>.'},
        'new': {'word': 'yard', 'synonyms': ['garden', 'lawn', 'plot'],
                'example': 'She grows vegetables in the <em>yard</em>.'},
    },
    8995: {
        'old': {'word': 'bin', 'definition': 'A container for waste or rubbish.',
                'synonyms': ['dustbin', 'trash can', 'waste basket', 'skip'],
                'example': 'Throw the empty can in the <em>bin</em>.'},
        'new': {'word': 'trash can', 'definition': 'A container for waste or garbage.',
                'synonyms': ['bin', 'dustbin', 'waste basket', 'skip'],
                'example': 'Throw the empty can in the <em>trash can</em>.'},
    },
    9204: {
        'old': {'word': 'rubber', 'synonyms': ['eraser', 'correction tool'],
                'example': 'Can I borrow your <em>rubber</em>?'},
        'new': {'word': 'eraser', 'synonyms': ['rubber', 'correction tool'],
                'example': 'Can I borrow your <em>eraser</em>?'},
    },
    9053: {
        'old': {'word': 'shoes', 'definition': 'Items worn on your feet.',
                'synonyms': ['boots', 'trainers', 'footwear'],
                'example': 'She bought new <em>shoes</em> for the party.'},
        'new': {'word': 'sneakers',
                'definition': 'Casual athletic shoes worn for sport or everyday wear.',
                'synonyms': ['trainers', 'shoes', 'footwear'],
                'example': 'She bought new <em>sneakers</em> for the gym.'},
    },
    # candy (pk 9276) needs no DB change — the US headword was already correct.
}


def apply_fixes(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    for pk, change in FIXES.items():
        Word.objects.filter(pk=pk).update(**change['new'])


def revert_fixes(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    for pk, change in FIXES.items():
        Word.objects.filter(pk=pk).update(**change['old'])


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0005_alter_grammartopic_stage'),
    ]

    operations = [
        migrations.RunPython(apply_fixes, revert_fixes),
    ]
```

- [ ] **Step 2: Run the migration**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python manage.py migrate vocab`
Expected: `Applying vocab.0006_fix_us_uk_word_pairs... OK`

- [ ] **Step 3: Write the test**

Create `VocabLarry/tests/test_us_uk_word_pairs.py`:

```python
import pytest
from vocab.models import Word


@pytest.mark.django_db
def test_twelve_words_have_us_headwords():
    expected = {
        6129: 'apartment', 9274: 'cookie', 9276: 'candy', 9336: 'vacation',
        9050: 'pants', 8994: 'garbage', 9269: 'line', 6377: 'movie',
        6135: 'yard', 8995: 'trash can', 9204: 'eraser', 9053: 'sneakers',
    }
    for pk, expected_word in expected.items():
        assert Word.objects.get(pk=pk).word == expected_word


@pytest.mark.django_db
def test_old_uk_terms_moved_to_synonyms():
    assert 'flat' in Word.objects.get(pk=6129).synonyms
    assert 'biscuit' in Word.objects.get(pk=9274).synonyms
    assert 'sweets' not in Word.objects.get(pk=9276).synonyms  # unchanged row, no DB-side UK synonym added
    assert 'holiday' in Word.objects.get(pk=9336).synonyms
    assert 'trousers' in Word.objects.get(pk=9050).synonyms
    assert 'rubbish' in Word.objects.get(pk=8994).synonyms
    assert 'queue' in Word.objects.get(pk=9269).synonyms
    assert 'film' in Word.objects.get(pk=6377).synonyms
    assert 'garden' in Word.objects.get(pk=6135).synonyms
    assert 'bin' in Word.objects.get(pk=8995).synonyms
    assert 'rubber' in Word.objects.get(pk=9204).synonyms
    assert 'trainers' in Word.objects.get(pk=9053).synonyms
    assert 'boots' not in Word.objects.get(pk=9053).synonyms  # dropped: not an accurate sneakers synonym


@pytest.mark.django_db
def test_examples_use_us_spelling_and_terms():
    assert 'favorite' in Word.objects.get(pk=6377).example
    assert 'favourite' not in Word.objects.get(pk=6377).example
    assert '<em>trash can</em>' in Word.objects.get(pk=8995).example
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests/test_us_uk_word_pairs.py -v`
Expected: `3 passed`

- [ ] **Step 5: Add the 12 `WORD_GB` entries**

In `VocabLarry/vocablarry.html`, find the `WORD_GB` object (added in Phase 1, currently ending with):

```js
  9874: { "antonyms": ["comfortable", "relaxed", "cosy"] }
};
```

Replace with (adding a comma after the existing last entry, then the 12 new entries):

```js
  9874: { "antonyms": ["comfortable", "relaxed", "cosy"] },
  6129: { "word": "flat", "example": "She lives in a small <em>flat</em> in the city centre.", "synonyms": ["apartment", "unit"] },
  9274: { "word": "biscuit", "example": "She offered him a <em>biscuit</em> with his tea.", "synonyms": ["cookie"] },
  9276: { "word": "sweets", "example": "The children shared a bag of <em>sweets</em>.", "synonyms": ["candy"] },
  9336: { "word": "holiday", "example": "We're going on <em>holiday</em> next month.", "synonyms": ["vacation", "break", "time off", "leave", "trip"] },
  9050: { "word": "trousers", "example": "He wears <em>trousers</em> to the office.", "synonyms": ["pants", "jeans", "slacks"] },
  8994: { "word": "rubbish", "example": "Please put your <em>rubbish</em> in the bin.", "synonyms": ["trash", "garbage", "waste", "litter"] },
  9269: { "word": "queue", "example": "There was a long <em>queue</em> at the checkout.", "synonyms": ["line", "row", "wait", "snake"] },
  6377: { "word": "film", "def": "A story told through moving pictures; a movie.", "example": "What's your favourite <em>film</em>?", "synonyms": ["movie", "motion picture", "cinema", "flick"] },
  6135: { "word": "garden", "example": "She grows vegetables in the <em>garden</em>.", "synonyms": ["yard", "lawn", "plot"] },
  8995: { "word": "bin", "def": "A container for waste or rubbish.", "example": "Throw the empty can in the <em>bin</em>.", "synonyms": ["dustbin", "trash can", "waste basket", "skip"] },
  9204: { "word": "rubber", "example": "Can I borrow your <em>rubber</em>?", "synonyms": ["eraser", "correction tool"] },
  9053: { "word": "trainers", "example": "She bought new <em>trainers</em> for the gym.", "synonyms": ["sneakers", "shoes", "footwear"] }
};
```

Note pk 6129, 9050, 9269, 6135, 9204 do NOT need a `"def"` key — their `definition` field wasn't touched by the migration (it was already dialect-neutral), so `wordDef()` correctly falls through to the raw (now-US) definition in both modes. Only 6377 and 8995 have a `def` override, matching the two rows whose `definition` field the migration actually changed.

- [ ] **Step 6: Syntax-check the script**

Run:
```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry"
python -c "
import re
html = open('vocablarry.html', encoding='utf-8').read()
scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
open('_script_check.js', 'w', encoding='utf-8').write('\n'.join(scripts))
"
node --check _script_check.js
rm _script_check.js
```
Expected: no output.

- [ ] **Step 7: Verify with Playwright (live server, real data)**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("typeof VOCAB_DATA !== 'undefined' && VOCAB_DATA.length > 0")

    # US (default) mode
    result_us = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 6129);
        return { word: w.w, syn: w.syn };
    }""")
    assert result_us["word"] == "apartment", result_us
    assert "flat" in result_us["syn"], result_us

    # UK mode via wordHeadword/wordExample (same accessors Task 3/4 of Phase 1 already wired in)
    page.evaluate("state.lang = 'en-gb'")
    result_uk = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 9053); // shoes/sneakers/trainers
        return { headword: wordHeadword(w), example: wordExample(w), synonyms: wordSynonyms(w) };
    }""")
    assert result_uk["headword"] == "trainers", result_uk
    assert "trainers" in result_uk["example"], result_uk
    assert "boots" not in result_uk["synonyms"], result_uk

    page.evaluate("state.lang = 'en'")
    result_us2 = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.pk === 9053);
        return { headword: wordHeadword(w), synonyms: wordSynonyms(w) };
    }""")
    assert result_us2["headword"] == "sneakers", result_us2
    assert "boots" not in result_us2["synonyms"], result_us2  # dropped on both sides, not just UK

    b.close()
print("Task 1 verified OK")
```

Expected: `Task 1 verified OK`. (Start the dev server first: `python manage.py runserver 8000` in the background; stop it after, per Task 3's Step 7 pattern below.)

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry/vocab/migrations/0006_fix_us_uk_word_pairs.py" "VocabLarry/tests/test_us_uk_word_pairs.py" "VocabLarry/vocablarry.html"
git commit -m "fix(vocab): correct 12 words whose US-default headword was actually the UK term"
```

---

### Task 2: Add 18 new words (migration + WORD_GB)

**Files:**
- Create: `VocabLarry/vocab/migrations/0007_add_us_uk_new_words.py`
- Modify: `VocabLarry/vocablarry.html` (add to `WORD_GB`, same location as Task 1's additions)
- Test: append to `VocabLarry/tests/test_us_uk_word_pairs.py`

**Interfaces:**
- Consumes: `Category` rows by slug (`food-drink-basic`, `home-household`, `a1plus-clothes-appearance`, `a1plus-home-objects`, `travel-experiences`, `technology-modern-life`, `work-career`, `body-health-basic`), `CEFRLevel` rows by code (`A1`, `A1+`, `A2`, `A2+`, `B1`) — all pre-existing, none created by this task.
- Produces: 18 new `Word` rows; 18 new `WORD_GB` entries.

- [ ] **Step 1: Write the migration**

Create `VocabLarry/vocab/migrations/0007_add_us_uk_new_words.py`:

```python
from django.db import migrations

# (pk, word, pos, definition, example, synonyms, antonyms, category_slug, cefr_code)
# Explicit pks continue the existing sequence (current max is 9920) so this
# plan can reference exact WORD_GB keys below without a runtime lookup step.
NEW_WORDS = [
    (9921, 'eggplant', 'noun', 'A purple vegetable with a smooth, shiny skin.',
     'She grilled some <em>eggplant</em> for dinner.', ['aubergine'], [],
     'food-drink-basic', 'A1+'),
    (9922, 'zucchini', 'noun', 'A long green vegetable similar to a cucumber.',
     'He sliced the <em>zucchini</em> for the stir-fry.', ['courgette'], [],
     'food-drink-basic', 'A1+'),
    (9923, 'diaper', 'noun', 'A piece of soft material worn by babies to absorb waste.',
     "She changed the baby's <em>diaper</em> before bed.", ['nappy'], [],
     'home-household', 'A1'),
    (9924, 'sweater', 'noun', 'A warm knitted garment worn on the upper body.',
     'He put on a <em>sweater</em> because it was cold.', ['jumper', 'pullover'], [],
     'a1plus-clothes-appearance', 'A1'),
    (9925, 'flashlight', 'noun', 'A small portable light powered by batteries.',
     'She used a <em>flashlight</em> to find her keys in the dark.', ['torch'], [],
     'a1plus-home-objects', 'A1+'),
    (9926, 'gasoline', 'noun', 'A fuel used to power most cars.',
     'The car ran out of <em>gasoline</em> on the highway.', ['petrol', 'fuel'], [],
     'travel-experiences', 'A2'),
    (9927, 'sidewalk', 'noun', 'A paved path for walking beside a road.',
     'Children were playing on the <em>sidewalk</em>.', ['pavement'], [],
     'travel-experiences', 'A1'),
    (9928, 'faucet', 'noun', 'A device that controls the flow of water from a pipe.',
     'She turned off the <em>faucet</em> after washing her hands.', ['tap'], [],
     'a1plus-home-objects', 'A1+'),
    (9929, 'parking lot', 'noun', 'An area where vehicles can be parked.',
     'We left the car in the <em>parking lot</em> near the mall.', ['car park'], [],
     'travel-experiences', 'A2'),
    (9930, 'mailbox', 'noun', 'A box where letters and packages are delivered.',
     'He checked the <em>mailbox</em> for new mail.', ['postbox'], [],
     'a1plus-home-objects', 'A1+'),
    (9931, 'cell phone', 'noun', 'A portable telephone used for calls and messaging.',
     'She left her <em>cell phone</em> at home by mistake.', ['mobile phone', 'cellphone'], [],
     'technology-modern-life', 'A1'),
    (9932, 'resume', 'noun', "A document summarizing a person's work experience and skills.",
     'He updated his <em>resume</em> before applying for the job.', ['CV', 'curriculum vitae'], [],
     'work-career', 'B1'),
    (9933, 'stroller', 'noun', 'A wheeled chair used to push a young child.',
     'She pushed the <em>stroller</em> through the park.', ['pram', 'buggy'], [],
     'home-household', 'A2'),
    (9934, 'pacifier', 'noun', 'A rubber or plastic nipple given to a baby to suck on.',
     'The baby calmed down once given a <em>pacifier</em>.', ['dummy', 'soother'], [],
     'home-household', 'A2+'),
    (9935, 'band-aid', 'noun', 'A small adhesive strip used to cover minor cuts.',
     'She put a <em>band-aid</em> on her scraped knee.', ['plaster'], [],
     'body-health-basic', 'A1'),
    (9936, 'crib', 'noun', 'A small bed with high sides for a baby.',
     'The baby slept peacefully in her <em>crib</em>.', ['cot'], [],
     'home-household', 'A2'),
    (9937, 'elevator', 'noun', 'A machine that carries people between floors of a building.',
     'They took the <em>elevator</em> to the tenth floor.', ['lift'], ['stairs'],
     'a1plus-home-objects', 'A1'),
    (9938, 'math', 'noun', 'The study of numbers, quantities, and shapes.',
     "She's always been good at <em>math</em>.", ['maths', 'mathematics'], [],
     'numbers-school-basic', 'A1'),
]


def add_words(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    Category = apps.get_model('vocab', 'Category')
    CEFRLevel = apps.get_model('vocab', 'CEFRLevel')

    for pk, word, pos, definition, example, synonyms, antonyms, cat_slug, cefr_code in NEW_WORDS:
        category = Category.objects.get(slug=cat_slug)
        cefr = CEFRLevel.objects.get(code=cefr_code)
        max_order = Word.objects.filter(category=category).order_by('-order').first()
        next_order = (max_order.order + 1) if max_order else 0
        Word.objects.create(
            pk=pk, word=word, pos=pos, definition=definition, example=example,
            synonyms=synonyms, antonyms=antonyms,
            category=category, cefr_level=cefr, order=next_order,
        )


def remove_words(apps, schema_editor):
    Word = apps.get_model('vocab', 'Word')
    Word.objects.filter(pk__in=[w[0] for w in NEW_WORDS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('vocab', '0006_fix_us_uk_word_pairs'),
    ]

    operations = [
        migrations.RunPython(add_words, remove_words),
    ]
```

- [ ] **Step 2: Run the migration**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python manage.py migrate vocab`
Expected: `Applying vocab.0007_add_us_uk_new_words... OK`

- [ ] **Step 3: Append tests**

Append to `VocabLarry/tests/test_us_uk_word_pairs.py`:

```python
NEW_WORD_LIST = [
    'eggplant', 'zucchini', 'diaper', 'sweater', 'flashlight', 'gasoline',
    'sidewalk', 'faucet', 'parking lot', 'mailbox', 'cell phone', 'resume',
    'stroller', 'pacifier', 'band-aid', 'crib', 'elevator', 'math',
]
NEW_WORD_PKS = list(range(9921, 9939))  # 9921..9938 inclusive


@pytest.mark.django_db
def test_eighteen_new_words_created():
    assert Word.objects.count() == 5018
    for pk, word in zip(NEW_WORD_PKS, NEW_WORD_LIST):
        w = Word.objects.get(pk=pk)
        assert w.word == word, f"pk {pk} expected {word!r}, got {w.word!r}"


@pytest.mark.django_db
def test_new_words_have_categories_and_cefr():
    for word in NEW_WORD_LIST:
        w = Word.objects.get(word=word)
        assert w.category_id is not None, f"{word!r} has no category"
        assert w.cefr_level_id is not None, f"{word!r} has no CEFR level"
        assert w.definition, f"{word!r} has no definition"
        assert f"<em>{word}</em>" in w.example, f"{word!r} example doesn't italicize the headword"


@pytest.mark.django_db
def test_elevator_is_distinct_from_existing_lift_verb():
    elevator = Word.objects.get(word='elevator')
    lift_verb = Word.objects.get(pk=5992)
    assert lift_verb.word == 'lift'
    assert lift_verb.pos == 'verb'
    assert elevator.pos == 'noun'
```

- [ ] **Step 4: Run the tests**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests/test_us_uk_word_pairs.py -v`
Expected: `6 passed`

- [ ] **Step 5: Add the 18 `WORD_GB` entries**

In `VocabLarry/vocablarry.html`, the `WORD_GB` object now ends with the 12 entries Task 1 added (ending `9053: { ... }`). Add these 18 entries after it, using the exact pks the migration assigned (9921-9938):

```js
  9921: { "word": "aubergine", "example": "She grilled some <em>aubergine</em> for dinner.", "synonyms": ["eggplant"] },
  9922: { "word": "courgette", "example": "He sliced the <em>courgette</em> for the stir-fry.", "synonyms": ["zucchini"] },
  9923: { "word": "nappy", "example": "She changed the baby's <em>nappy</em> before bed.", "synonyms": ["diaper"] },
  9924: { "word": "jumper", "example": "He put on a <em>jumper</em> because it was cold.", "synonyms": ["sweater", "pullover"] },
  9925: { "word": "torch", "example": "She used a <em>torch</em> to find her keys in the dark.", "synonyms": ["flashlight"] },
  9926: { "word": "petrol", "example": "The car ran out of <em>petrol</em> on the highway.", "synonyms": ["gasoline", "fuel"] },
  9927: { "word": "pavement", "example": "Children were playing on the <em>pavement</em>.", "synonyms": ["sidewalk"] },
  9928: { "word": "tap", "example": "She turned off the <em>tap</em> after washing her hands.", "synonyms": ["faucet"] },
  9929: { "word": "car park", "example": "We left the car in the <em>car park</em> near the mall.", "synonyms": ["parking lot"] },
  9930: { "word": "postbox", "example": "He checked the <em>postbox</em> for new mail.", "synonyms": ["mailbox"] },
  9931: { "word": "mobile phone", "example": "She left her <em>mobile phone</em> at home by mistake.", "synonyms": ["cell phone", "cellphone"] },
  9932: { "word": "CV", "example": "He updated his <em>CV</em> before applying for the job.", "synonyms": ["resume", "curriculum vitae"] },
  9933: { "word": "pram", "example": "She pushed the <em>pram</em> through the park.", "synonyms": ["stroller", "buggy"] },
  9934: { "word": "dummy", "example": "The baby calmed down once given a <em>dummy</em>.", "synonyms": ["pacifier", "soother"] },
  9935: { "word": "plaster", "example": "She put a <em>plaster</em> on her scraped knee.", "synonyms": ["band-aid"] },
  9936: { "word": "cot", "example": "The baby slept peacefully in her <em>cot</em>.", "synonyms": ["crib"] },
  9937: { "word": "lift", "example": "They took the <em>lift</em> to the tenth floor.", "synonyms": ["elevator"] },
  9938: { "word": "maths", "example": "She's always been good at <em>maths</em>.", "synonyms": ["math", "mathematics"] }
};
```

(The closing `};` moves to after the `9938` entry — remove it from wherever Task 1 left it and put it after `9938`'s entry.)

- [ ] **Step 6: Syntax-check the script**

Same command as Task 1 Step 6.

- [ ] **Step 7: Verify with Playwright (live server, real data)**

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("typeof VOCAB_DATA !== 'undefined' && VOCAB_DATA.length > 0")

    count = page.evaluate("VOCAB_DATA.length")
    assert count == 5018, count

    result_us = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.w === 'eggplant');
        return { def: w.def, ex: w.ex, cat: w.cat };
    }""")
    assert "purple vegetable" in result_us["def"], result_us
    assert "eggplant" in result_us["ex"], result_us

    page.evaluate("state.lang = 'en-gb'")
    result_uk = page.evaluate("""() => {
        const w = VOCAB_DATA.find(x => x.w === 'eggplant');
        return { headword: wordHeadword(w), example: wordExample(w) };
    }""")
    assert result_uk["headword"] == "aubergine", result_uk
    assert "aubergine" in result_uk["example"], result_uk

    # elevator (new noun) vs the pre-existing "lift" verb (pk 5992) must not collide
    elevator = page.evaluate("VOCAB_DATA.find(x => x.w === 'elevator')")
    assert elevator["pos"] == "noun", elevator
    lift_verb = page.evaluate("VOCAB_DATA.find(x => x.pk === 5992)")
    assert lift_verb["pos"] == "verb", lift_verb

    b.close()
print("Task 2 verified OK")
```

Expected: `Task 2 verified OK`.

- [ ] **Step 8: Commit**

```bash
git add "VocabLarry/vocab/migrations/0007_add_us_uk_new_words.py" "VocabLarry/tests/test_us_uk_word_pairs.py" "VocabLarry/vocablarry.html"
git commit -m "feat(vocab): add 18 new words for common US/UK pairs missing from the dataset"
```

---

### Task 3: Full end-to-end verification pass

**Files:** none (verification only)

**Interfaces:**
- Consumes: everything from Tasks 1-2.
- Produces: nothing — this is the acceptance checkpoint before the feature is done.

- [ ] **Step 1: Run the full Playwright acceptance script**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto("http://127.0.0.1:8000/")
    page.wait_for_function("typeof VOCAB_DATA !== 'undefined' && VOCAB_DATA.length > 0")

    # 1. Total word count is 5,018
    assert page.evaluate("VOCAB_DATA.length") == 5018

    # 2. Switch to English (UK) via the real UI
    page.click("#langToggle")
    page.click("#langMenu [data-lang='en-gb']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en-gb"

    # 3. A fixed existing word (rubber/eraser) shows the UK term in the modal
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9204))")
    assert page.locator("#modal-word").text_content() == "rubber"
    page.evaluate("closeWordModal()")

    # 4. A new word (eggplant/aubergine) shows the UK term in the modal
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9921))")
    assert page.locator("#modal-word").text_content() == "aubergine"
    page.evaluate("closeWordModal()")

    # 5. Search finds the UK-displayed spelling while in UK mode
    page.evaluate("goToPage('list')")
    page.wait_for_selector("#page-list.active", state="attached")

    # 6. Switch back to English (US): both fixed and new words revert
    page.click("#langToggle")
    page.click("#langMenu [data-lang='en']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "en"
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9204))")
    assert page.locator("#modal-word").text_content() == "eraser"
    page.evaluate("closeWordModal()")
    page.evaluate("openWordModal(VOCAB_DATA.find(x => x.pk === 9921))")
    assert page.locator("#modal-word").text_content() == "eggplant"
    page.evaluate("closeWordModal()")

    # 7. Vietnamese mode unaffected
    page.click("#langToggle")
    page.click("#langMenu [data-lang='vi']")
    assert page.evaluate("localStorage.getItem('ivm_lang')") == "vi"

    b.close()
print("Task 3 — full acceptance pass OK")
```

Expected: `Task 3 — full acceptance pass OK`.

- [ ] **Step 2: Run the full pytest suite**

Run: `cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry" && python -m pytest tests -q`
Expected: `91 passed` (85 from before this feature + 6 new tests from Tasks 1-2: 3 in `test_us_uk_word_pairs.py` from Task 1, 3 more appended in Task 2).

- [ ] **Step 3: Stop the dev server, report status**

Find and kill whatever process is listening on port 8000. Do not push (`git push elw main`) or regenerate `VocabLarry/vocablarry-deploy.zip` until the user explicitly asks in the conversation where this plan is executed.
