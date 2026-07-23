from vocab.templatetags.vocab_extras import category_icon


def test_category_icon_known_emoji_resolves():
    assert category_icon('📚') == 'i-book'
    assert category_icon('🎓') == 'i-grad-cap'


def test_category_icon_unmapped_emoji_falls_back_to_book():
    assert category_icon('🦄') == 'i-book'


def test_category_icon_empty_string_falls_back_to_book():
    assert category_icon('') == 'i-book'


def test_category_icon_resolves_variation_selector_only_keys():
    # '⚙️' (gear) only exists in EMOJI_ICON_MAP in its VS16-suffixed form.
    # Before the lookup-normalization fix, stripping the *input's* VS16
    # made this key unreachable even though it was requested exactly as
    # stored — this test locks in that it now resolves correctly both
    # with and without the input carrying VS16.
    assert category_icon('⚙️') == 'i-settings'
    assert category_icon('⚙') == 'i-settings'


def test_category_icon_resolves_waves_butterfly_heart_rose():
    # These 4 map entries (and their corresponding <symbol> sprite icons)
    # were missing from VLPE despite the map's "transcribed verbatim"
    # claim — FIXES-NEEDED.md item 21. Locks in both pieces together.
    assert category_icon('🌊') == 'i-waves'
    assert category_icon('🦋') == 'i-butterfly'
    assert category_icon('💙') == 'i-heart'
    assert category_icon('🌹') == 'i-rose'
