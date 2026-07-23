from django import template

register = template.Library()

# Transcribed verbatim from VocabLarry/vocablarry.html's EMOJI_ICON_MAP
# (production's client-side lookup, ported here for server-side
# resolution since VLPE renders categories via Django templates).
# Keys are stored without U+FE0F variation selectors, matching
# production's own convention — category_icon() strips them before
# lookup, same as production's iconSvg() does.
EMOJI_ICON_MAP = {
    '⚽': 'i-activity', '🏃': 'i-activity', '⚠': 'i-alert', '⚠️': 'i-alert', '🍎': 'i-apple',
    '💰': 'i-banknote', '📊': 'i-bar-chart', '🕊': 'i-bird', '📚': 'i-book', '📖': 'i-book-open',
    '🤖': 'i-bot', '🧠': 'i-brain', '🧮': 'i-brain', '💼': 'i-briefcase', '🧳': 'i-briefcase',
    '🏙️': 'i-building', '🏫': 'i-building', '🚌': 'i-bus', '📅': 'i-calendar', '🛒': 'i-cart',
    '✅': 'i-check-circle', '📋': 'i-clipboard', '⏰': 'i-clock', '🌤️': 'i-cloud', '🌦': 'i-cloud',
    '🤔': 'i-compass', '🧭': 'i-compass', '🏥': 'i-cross', '🩺': 'i-cross', '🎩': 'i-crown',
    '🎲': 'i-dice', '💪': 'i-dumbbell', '📝': 'i-file-text', '🔥': 'i-flame', '🧪': 'i-flask',
    '🧘': 'i-flower', '◈': 'i-gem', '💎': 'i-gem', '🔮': 'i-gem', '🌍': 'i-globe', '🌐': 'i-globe',
    '🎓': 'i-grad-cap', '✊': 'i-hand', '✋': 'i-hand', '🏗': 'i-hard-hat', '🏗️': 'i-hard-hat',
    '🔢': 'i-hash', '🏠': 'i-home', '⏳': 'i-hourglass', '🔑': 'i-key', '🗝️': 'i-key',
    '🏛': 'i-landmark', '🏛️': 'i-landmark', '🌿': 'i-leaf', '💡': 'i-lightbulb', '➿': 'i-link',
    '🔗': 'i-link', '📨': 'i-mail', '📌': 'i-map-pin', '🎭': 'i-masks', '📢': 'i-megaphone',
    '🗣': 'i-megaphone', '💬': 'i-message', '💭': 'i-message', '🗨️': 'i-message', '🎙️': 'i-mic',
    '🔬': 'i-microscope', '🔭': 'i-microscope', '💻': 'i-monitor', '🌄': 'i-mountain',
    '📰': 'i-newspaper', '🎨': 'i-palette', '✍️': 'i-pen', '✒️': 'i-pen', '🖊️': 'i-pen',
    '🖋': 'i-pen', '🖋️': 'i-pen', '✈': 'i-plane', '✈️': 'i-plane', '🧩': 'i-puzzle',
    '🚀': 'i-rocket', '🔄': 'i-rotate', '📏': 'i-ruler', '📐': 'i-ruler', '⚖': 'i-scale',
    '⚖️': 'i-scale', '📜': 'i-scroll', '🔍': 'i-search', '⚙️': 'i-settings', '👕': 'i-shirt',
    '↔️': 'i-shuffle', '🔀': 'i-shuffle', '📱': 'i-smartphone', '😊': 'i-smile', '😏': 'i-smile',
    '✨': 'i-sparkles', '🌌': 'i-sparkles', '🌡': 'i-sparkles', '🌱': 'i-sprout', '⭐': 'i-star',
    '🌟': 'i-star', '☀️': 'i-sun', '🌅': 'i-sun', '🎯': 'i-target', '📉': 'i-trend-down',
    '📈': 'i-trend-up', '🏆': 'i-trophy', '🔤': 'i-type', '🧍': 'i-user', '🪞': 'i-user',
    '👨‍👩‍👧‍👦': 'i-users', '🤝': 'i-users', '🍜': 'i-utensils', '🍽️': 'i-utensils',
    '🔧': 'i-wrench', '🛠️': 'i-wrench', '🧰': 'i-wrench', '⚡': 'i-zap', '🌪': 'i-zap',
    '🌊': 'i-waves', '🦋': 'i-butterfly', '💙': 'i-heart', '🌹': 'i-rose',
}

# Some EMOJI_ICON_MAP keys only exist in their U+FE0F (variation selector)
# suffixed form (e.g. '⚙️') with no bare-form counterpart. category_icon()
# strips U+FE0F from its input before lookup, so without this normalization
# step those suffixed-only keys would be unreachable. Build the lookup once
# at import time with every key's own U+FE0F stripped too, so either form
# of the same emoji resolves to the same icon regardless of which form the
# map happened to store.
_ICON_LOOKUP = {key.replace('️', ''): value for key, value in EMOJI_ICON_MAP.items()}


@register.filter
def category_icon(emoji):
    key = (emoji or '').replace('️', '')
    return _ICON_LOOKUP.get(key, 'i-book')


@register.filter
def cefr_accent_var(cefr_level):
    """CSS var() expression for a word's own CEFR-level accent color
    (e.g. A1+ -> var(--a1p)), falling back to the shared violet accent
    when a word has no CEFR level. Shared by word_detail.html,
    category_word_list.html, and word_list.html so a word's example-
    sentence emphasis (and anything else keyed off --accent-c) always
    matches its own level, mirroring production's per-word CEFR
    color-coding rather than a single flat accent color everywhere."""
    if not cefr_level:
        return 'rgb(var(--violet))'
    return 'var(--{})'.format(cefr_level.code.lower().replace('+', 'p'))
