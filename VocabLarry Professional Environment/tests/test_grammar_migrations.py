import importlib


def _load_migration():
    return importlib.import_module('vocab.migrations.0009_grammarsection')


def test_topic_sections_map_has_all_47_entries():
    mod = _load_migration()
    assert len(mod.TOPIC_SECTIONS) == 47


def test_topic_sections_map_values_are_all_valid_section_names():
    mod = _load_migration()
    valid_names = {name for _, name, _, _ in mod.SECTIONS}
    assert set(mod.TOPIC_SECTIONS.values()) <= valid_names


def test_topic_sections_map_diverges_from_raw_tag_for_known_cases():
    # These are the topics whose grammar-content.json `tag` field does NOT
    # match their real production section — proving TOPIC_SECTIONS (not
    # `tag`) is genuinely doing the grouping work for these slugs.
    mod = _load_migration()
    assert mod.TOPIC_SECTIONS['phrasal-verbs'] == 'Verb Patterns & Modals'
    assert mod.TOPIC_SECTIONS['dependent-prepositions'] == 'Word Forms & Prepositions'
    assert mod.TOPIC_SECTIONS['comparison-structures'] == 'Adjectives & Adverbs'
    assert mod.TOPIC_SECTIONS['subject-verb-agreement'] == 'Nouns, Pronouns & Determiners'
    assert mod.TOPIC_SECTIONS['irregular-verbs'] == 'Tenses'


def test_sections_seed_data_has_12_entries_matching_order():
    mod = _load_migration()
    assert len(mod.SECTIONS) == 12
    assert [s[1] for s in mod.SECTIONS] == [
        'Tenses', 'Questions & Reported Speech', 'Nouns, Pronouns & Determiners',
        'Adjectives & Adverbs', 'Word Forms & Prepositions', 'Verb Patterns & Modals',
        'Voice', 'Conditionals & Unreal Forms', 'Clauses', 'Emphasis & Sentence Focus',
        'Cohesion & Academic Style', 'Idioms',
    ]
