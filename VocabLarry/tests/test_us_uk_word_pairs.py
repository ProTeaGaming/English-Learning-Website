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


# --- Migration 0008: revert the 18 new words added by 0007 ---
#
# The 18 new words (eggplant, elevator, etc.) turned out to be scope the
# user didn't want -- they only wanted existing US-form words to gain a
# UK-mode override, not brand-new vocabulary added to the dataset. 0008
# reverses 0007: remove_words() deletes the 18 rows; restore_words() (its
# reverse_code) recreates them, mirroring 0007's own add_words() logic.
migration_0008 = importlib.import_module(
    'vocab.migrations.0008_remove_us_uk_new_words'
)
NEW_WORDS_0008 = migration_0008.NEW_WORDS
NEW_WORD_PKS = [row[0] for row in NEW_WORDS_0008]


@pytest.fixture
def seeded_then_removed_words(db):
    cefr_codes = ['A1', 'A1+', 'A2', 'A2+', 'B1']
    cefr_by_code = {
        code: CEFRLevel.objects.create(code=code, name=code, order=i)
        for i, code in enumerate(cefr_codes)
    }
    cat_slugs = sorted({row[7] for row in NEW_WORDS_0008})
    categories = {slug: Category.objects.create(slug=slug, name=slug) for slug in cat_slugs}

    # Seed the 18 rows exactly as 0007 would have created them, so 0008's
    # remove_words() has real rows to delete rather than a no-op.
    for pk, word, pos, definition, example, synonyms, antonyms, cat_slug, cefr_code in NEW_WORDS_0008:
        Word.objects.create(
            pk=pk, word=word, pos=pos, definition=definition, example=example,
            synonyms=synonyms, antonyms=antonyms,
            category=categories[cat_slug], cefr_level=cefr_by_code[cefr_code],
        )

    migration_0008.remove_words(django_apps, None)


@pytest.mark.django_db
def test_eighteen_new_words_removed(seeded_then_removed_words):
    assert Word.objects.count() == 0  # only the 18 seeded rows existed in this test DB
    assert not Word.objects.filter(pk__in=NEW_WORD_PKS).exists()


@pytest.mark.django_db
def test_reverse_migration_restores_the_18_words(seeded_then_removed_words):
    migration_0008.restore_words(django_apps, None)
    assert Word.objects.count() == 18
    for pk, word, *_ in NEW_WORDS_0008:
        assert Word.objects.get(pk=pk).word == word
