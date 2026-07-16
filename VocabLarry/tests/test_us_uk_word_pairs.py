import importlib

import pytest
from django.apps import apps as django_apps

from vocab.models import CEFRLevel, Category, Word

# The FIXES dict and apply_fixes() below are the real migration logic from
# vocab/migrations/0006_fix_us_uk_word_pairs.py. pytest-django builds its
# test database from a fresh, empty schema (migrations create tables only;
# they do not seed the 5,000-word dataset that lives in the dev db.sqlite3),
# so RunPython(apply_fixes, ...) is a no-op if we just point at bare pks with
# no rows behind them. To genuinely exercise the migration rather than just
# re-asserting the FIXES dict against itself, this test seeds Word rows
# matching each entry's pre-migration ('old') state, then calls the real
# apply_fixes() function -- the same function `manage.py migrate` runs --
# and asserts the post-migration ('new') state.
migration_module = importlib.import_module(
    'vocab.migrations.0006_fix_us_uk_word_pairs'
)
FIXES = migration_module.FIXES


@pytest.fixture
def seeded_words(db):
    cat = Category.objects.create(slug='us-uk-fixture', name='US/UK Fixture')
    for pk, change in FIXES.items():
        old = change['old']
        Word.objects.create(
            pk=pk,
            word=old['word'],
            definition=old.get('definition', 'placeholder definition'),
            synonyms=old['synonyms'],
            example=old['example'],
            category=cat,
        )
    # pk 9276 ("candy") needs no DB change -- the US headword was already
    # correct pre-migration. Seed it as-is to prove the migration leaves it
    # untouched.
    Word.objects.create(
        pk=9276, word='candy', definition='placeholder definition',
        synonyms=[], example='The children shared a bag of <em>candy</em>.',
        category=cat,
    )
    migration_module.apply_fixes(django_apps, None)
    return cat


@pytest.mark.django_db
def test_twelve_words_have_us_headwords(seeded_words):
    expected = {
        6129: 'apartment', 9274: 'cookie', 9276: 'candy', 9336: 'vacation',
        9050: 'pants', 8994: 'garbage', 9269: 'line', 6377: 'movie',
        6135: 'yard', 8995: 'trash can', 9204: 'eraser', 9053: 'sneakers',
    }
    for pk, expected_word in expected.items():
        assert Word.objects.get(pk=pk).word == expected_word


@pytest.mark.django_db
def test_old_uk_terms_moved_to_synonyms(seeded_words):
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
def test_examples_use_us_spelling_and_terms(seeded_words):
    assert 'favorite' in Word.objects.get(pk=6377).example
    assert 'favourite' not in Word.objects.get(pk=6377).example
    assert '<em>trash can</em>' in Word.objects.get(pk=8995).example


# --- Task 2: 18 new words for US/UK pairs missing from the dataset entirely ---
#
# add_words() below is the real migration logic from
# vocab/migrations/0007_add_us_uk_new_words.py. As with 0006 above, the
# fresh/empty pytest-django test DB has no Category or CEFRLevel rows, and
# add_words() calls Category.objects.get(slug=...) / CEFRLevel.objects.get(
# code=...) directly (no .filter().update() no-op safety net like 0006's
# apply_fixes) -- so without seeding, it would raise DoesNotExist rather than
# silently doing nothing. It also relies on Word.objects.filter(category=...)
# to compute the next `order` value, and (via
# test_elevator_is_distinct_from_existing_lift_verb) on a pre-existing pk 5992
# ("lift", a verb) that isn't part of this migration -- that row lives only in
# the real dev db.sqlite3 dataset, not in migrations.
#
# test_eighteen_new_words_created asserts Word.objects.count() == 5018, which
# is only true against the real dataset (5,000 pre-existing words + 18 new
# ones). To exercise add_words() faithfully rather than weakening that
# assertion, this fixture seeds the required Category/CEFRLevel rows, the
# pre-existing pk 5992 "lift" verb, and 4,999 filler Word rows (5,000 total
# pre-existing words including "lift") before calling the real add_words().
migration_0007 = importlib.import_module(
    'vocab.migrations.0007_add_us_uk_new_words'
)
NEW_WORDS_0007 = migration_0007.NEW_WORDS

NEW_WORD_LIST = [
    'eggplant', 'zucchini', 'diaper', 'sweater', 'flashlight', 'gasoline',
    'sidewalk', 'faucet', 'parking lot', 'mailbox', 'cell phone', 'resume',
    'stroller', 'pacifier', 'band-aid', 'crib', 'elevator', 'math',
]
NEW_WORD_PKS = list(range(9921, 9939))  # 9921..9938 inclusive


@pytest.fixture
def seeded_new_words(db):
    cefr_codes = ['A1', 'A1+', 'A2', 'A2+', 'B1']
    cefr_by_code = {
        code: CEFRLevel.objects.create(code=code, name=code, order=i)
        for i, code in enumerate(cefr_codes)
    }

    cat_slugs = sorted({row[7] for row in NEW_WORDS_0007})
    categories = [Category.objects.create(slug=slug, name=slug) for slug in cat_slugs]
    filler_cat = categories[0]

    # Pre-existing "lift" verb (pk 5992), referenced by
    # test_elevator_is_distinct_from_existing_lift_verb. Not created by
    # migration 0007 -- it's part of the real dev dataset.
    Word.objects.create(
        pk=5992, word='lift', pos='verb', definition='placeholder definition',
        example='placeholder', category=filler_cat, cefr_level=cefr_by_code['A1'],
    )

    # Fill out the rest of the real dev db's 5,000 pre-existing words so
    # Word.objects.count() == 5018 after add_words() is meaningful.
    fillers = [
        Word(
            pk=pk, word=f'filler-word-{pk}', pos='noun',
            definition='placeholder definition', example='placeholder',
            category=filler_cat, cefr_level=cefr_by_code['A1'],
        )
        for pk in range(1, 5000) if pk != 5992
    ]
    Word.objects.bulk_create(fillers)

    migration_0007.add_words(django_apps, None)


@pytest.mark.django_db
def test_eighteen_new_words_created(seeded_new_words):
    assert Word.objects.count() == 5018
    for pk, word in zip(NEW_WORD_PKS, NEW_WORD_LIST):
        w = Word.objects.get(pk=pk)
        assert w.word == word, f"pk {pk} expected {word!r}, got {w.word!r}"


@pytest.mark.django_db
def test_new_words_have_categories_and_cefr(seeded_new_words):
    for word in NEW_WORD_LIST:
        w = Word.objects.get(word=word)
        assert w.category_id is not None, f"{word!r} has no category"
        assert w.cefr_level_id is not None, f"{word!r} has no CEFR level"
        assert w.definition, f"{word!r} has no definition"
        assert f"<em>{word}</em>" in w.example, f"{word!r} example doesn't italicize the headword"


@pytest.mark.django_db
def test_elevator_is_distinct_from_existing_lift_verb(seeded_new_words):
    elevator = Word.objects.get(word='elevator')
    lift_verb = Word.objects.get(pk=5992)
    assert lift_verb.word == 'lift'
    assert lift_verb.pos == 'verb'
    assert elevator.pos == 'noun'
