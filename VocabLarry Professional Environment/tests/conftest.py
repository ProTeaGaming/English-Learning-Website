import pytest
import importlib


@pytest.fixture(autouse=True)
def seed_grammar_sections(db):
    """
    Auto-seed GrammarSection objects from migration data.

    With pytest's --no-migrations flag, RunPython operations in migrations
    don't execute during test DB setup. This fixture seeds the sections
    before each test that touches GrammarSection, using the migration's
    SECTIONS data as the source of truth.
    """
    from vocab.models import GrammarSection

    # If sections already exist (shouldn't happen in test isolation), skip
    if GrammarSection.objects.exists():
        return

    # Import the migration module to get the authoritative SECTIONS data
    migration = importlib.import_module('vocab.migrations.0009_grammarsection')

    # Seed sections using the migration's data
    for order, (slug, name, icon, image_ids) in enumerate(migration.SECTIONS):
        GrammarSection.objects.create(
            slug=slug, name=name, icon=icon, order=order, image_ids=image_ids,
        )
