# Vocab Browse/Category/Word Visual Retrofit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle VLPE's category browse, category word-list, and word-detail
pages to match production's actual design (`vocablarry.html`) — icon sprite,
CEFR badges, progress bars/medals, hover-reveal word cards, numbered
pagination, bulk actions — while keeping VLPE's own architecture (real pages,
not modals; server-rendered filters, not client-side JS).

**Architecture:** Django server-rendered templates + extended views (no new
models/migrations). CSS ported verbatim from production with the established
`rgba(var(--violet))` → `rgb(var(--violet) / X)` conversion. Filter chips are
plain `<a href>` links (VLPE re-renders server-side per filter change, unlike
production's client-side SPA filtering). Icon resolution moves from
production's client-side JS lookup to a server-side Django template filter.

**Tech Stack:** Django 5, pytest + Django test `Client`, Playwright for
browser-interaction checks.

## Global Constraints

- Word detail stays a real page at its existing URL — never a modal.
- Category progress bar / gold medal computed server-side from
  `request.user.learn_map`; absent entirely for guests (nothing rendered,
  not a zero-state bar).
- Category accent color comes from VLPE's own `Category.color.bg_hex`, not
  production's 15 fixed `--t*` theme classes.
- Filter chips (`data-browse-cefr`, `data-browse-status`) are plain
  server-rendered `<a href="?...">` links — no new client-side JS filtering.
- "Mark All Completed" sets each of a category's word IDs to `"learned"`;
  "Reset All" **deletes** each of that category's word ID keys from
  `learn_map` entirely (never writes an explicit `"none"` — `learn_map` is
  sparse and Home's `categories_started` stat counts `len(learn_map.keys())`).
- Every `learn_map` write is GET-then-merge-then-POST against `/auth/sync/`,
  never a partial POST.
- No new i18n content translation — only new chrome labels get `data-i18n` +
  `en`/`vi` entries in `static/js/i18n.js`.
- No new models, no new migrations, no new backend/API endpoints beyond
  extending the 3 existing views in `config/views_vocab.py`.
- Full spec: `docs/superpowers/specs/2026-07-20-vocablarry-professional-vocab-browse-word-visual-retrofit-design.md`.

---

### Task 1: Icon sprite + `category_icon` template filter

**Files:**
- Create: `vocab/templatetags/__init__.py`
- Create: `vocab/templatetags/vocab_extras.py`
- Modify: `templates/base.html`
- Create: `tests/test_vocab_extras.py`

**Interfaces:**
- Produces: a Django template filter `category_icon` (usage:
  `{{ category.icon|category_icon }}` → returns an icon id string like
  `"i-book"`), and 80 new `<symbol id="i-...">` elements in `templates/base.html`'s
  sprite. Consumed by Task 3 (`vocab/browse.html`'s card icon).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_vocab_extras.py`:

```python
from vocab.templatetags.vocab_extras import category_icon


def test_category_icon_known_emoji_resolves():
    assert category_icon('📚') == 'i-book'
    assert category_icon('🎓') == 'i-grad-cap'


def test_category_icon_unmapped_emoji_falls_back_to_book():
    assert category_icon('🦄') == 'i-book'


def test_category_icon_empty_string_falls_back_to_book():
    assert category_icon('') == 'i-book'


def test_category_icon_strips_variation_selector():
    # Production's own lookup strips U+FE0F before matching; the map
    # itself already contains both variants for several emoji, but the
    # filter must handle a stray U+FE0F on an otherwise-unmapped base
    # emoji the map doesn't have a bare variant for.
    assert category_icon('✈️') == 'i-plane'  # ✈️ -> i-plane
    assert category_icon('✈') == 'i-plane'         # ✈ (no VS16) -> i-plane
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_extras.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vocab.templatetags'`

- [ ] **Step 3: Create `vocab/templatetags/__init__.py`**

Empty file (marks the directory as a Python package).

- [ ] **Step 4: Create `vocab/templatetags/vocab_extras.py`**

```python
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
}


@register.filter
def category_icon(emoji):
    key = (emoji or '').replace('️', '')
    return EMOJI_ICON_MAP.get(key, 'i-book')
```

- [ ] **Step 5: Add 73 icon symbols to `templates/base.html`**

`EMOJI_ICON_MAP` above resolves to 80 distinct icon ids across VLPE's real
119 `Category.icon` values (confirmed via a live query — all 119 resolve,
none fall back to `i-book` today, though the fallback stays defensive for
future data). Of those 80, **7 already exist** in `templates/base.html`
from earlier phases — confirmed by reading the current sprite directly:
`i-book`, `i-target`, `i-check-circle`, `i-bar-chart`, `i-grad-cap`
(Foundation Restyle), `i-sun`, `i-globe` (also Foundation Restyle — used by
the theme/language toggles). Do not re-add these 7. The remaining **73**
need to be added; the block below is exactly that set, alphabetically
sorted, cross-checked to contain no id already present in the file.

In the inline `<svg style="display:none">` sprite, change:
```html
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
</svg>
```
to:
```html
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
  <symbol id="i-activity" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></symbol>
  <symbol id="i-alert" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></symbol>
  <symbol id="i-apple" viewBox="0 0 24 24"><path d="M12 20.94c1.5 0 2.75 1.06 4 1.06 3 0 6-8 6-12.22A4.91 4.91 0 0 0 17 4.5c-1.8 0-3 .5-5 .5s-3.2-.5-5-.5A4.9 4.9 0 0 0 2 9.78C2 14 5 22 8 22c1.25 0 2.5-1.06 4-1.06Z"/><path d="M10 2c1 .5 2 2 2 5"/></symbol>
  <symbol id="i-banknote" viewBox="0 0 24 24"><rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></symbol>
  <symbol id="i-bird" viewBox="0 0 24 24"><path d="M16 7h.01"/><path d="M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"/><path d="m20 7 2 .5-2 .5"/><path d="M10 18v3"/><path d="M14 17.75V21"/><path d="M7 18a6 6 0 0 0 3.84-10.61"/></symbol>
  <symbol id="i-book-open" viewBox="0 0 24 24"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></symbol>
  <symbol id="i-bot" viewBox="0 0 24 24"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></symbol>
  <symbol id="i-brain" viewBox="0 0 24 24"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></symbol>
  <symbol id="i-briefcase" viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></symbol>
  <symbol id="i-building" viewBox="0 0 24 24"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/></symbol>
  <symbol id="i-bus" viewBox="0 0 24 24"><path d="M8 6v6"/><path d="M15 6v6"/><path d="M2 12h19.6"/><path d="M18 18h3s.5-1.7.8-2.8c.1-.4.2-.8.2-1.2 0-.4-.1-.8-.2-1.2l-1.4-5C20.1 6.8 19.1 6 18 6H4a2 2 0 0 0-2 2v10h3"/><circle cx="7" cy="18" r="2"/><path d="M9 18h5"/><circle cx="16" cy="18" r="2"/></symbol>
  <symbol id="i-calendar" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></symbol>
  <symbol id="i-cart" viewBox="0 0 24 24"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></symbol>
  <symbol id="i-clipboard" viewBox="0 0 24 24"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></symbol>
  <symbol id="i-cloud" viewBox="0 0 24 24"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></symbol>
  <symbol id="i-compass" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></symbol>
  <symbol id="i-cross" viewBox="0 0 24 24"><path d="M11 2a2 2 0 0 0-2 2v5H4a2 2 0 0 0-2 2v2c0 1.1.9 2 2 2h5v5c0 1.1.9 2 2 2h2a2 2 0 0 0 2-2v-5h5a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2h-5V4a2 2 0 0 0-2-2h-2z"/></symbol>
  <symbol id="i-crown" viewBox="0 0 24 24"><path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7z"/><path d="M5 20h14"/></symbol>
  <symbol id="i-dice" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><path d="M16 8h.01"/><path d="M8 8h.01"/><path d="M8 16h.01"/><path d="M16 16h.01"/><path d="M12 12h.01"/></symbol>
  <symbol id="i-dumbbell" viewBox="0 0 24 24"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></symbol>
  <symbol id="i-file-text" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></symbol>
  <symbol id="i-flame" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></symbol>
  <symbol id="i-flask" viewBox="0 0 24 24"><path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/></symbol>
  <symbol id="i-flower" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 16.5A4.5 4.5 0 1 1 7.5 12 4.5 4.5 0 1 1 12 7.5a4.5 4.5 0 1 1 4.5 4.5 4.5 4.5 0 1 1-4.5 4.5"/><path d="M12 7.5V9"/><path d="M7.5 12H9"/><path d="M16.5 12H15"/><path d="M12 16.5V15"/></symbol>
  <symbol id="i-gem" viewBox="0 0 24 24"><path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/></symbol>
  <symbol id="i-hand" viewBox="0 0 24 24"><path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/><path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/></symbol>
  <symbol id="i-hard-hat" viewBox="0 0 24 24"><path d="M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1z"/><path d="M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5"/><path d="M4 15v-3a6 6 0 0 1 6-6"/><path d="M14 6a6 6 0 0 1 6 6v3"/></symbol>
  <symbol id="i-hash" viewBox="0 0 24 24"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></symbol>
  <symbol id="i-home" viewBox="0 0 24 24"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></symbol>
  <symbol id="i-hourglass" viewBox="0 0 24 24"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></symbol>
  <symbol id="i-key" viewBox="0 0 24 24"><circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/></symbol>
  <symbol id="i-landmark" viewBox="0 0 24 24"><line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="11"/><line x1="14" y1="18" x2="14" y2="11"/><line x1="18" y1="18" x2="18" y2="11"/><polygon points="12 2 20 7 4 7"/></symbol>
  <symbol id="i-leaf" viewBox="0 0 24 24"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></symbol>
  <symbol id="i-lightbulb" viewBox="0 0 24 24"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></symbol>
  <symbol id="i-link" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></symbol>
  <symbol id="i-mail" viewBox="0 0 24 24"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></symbol>
  <symbol id="i-map-pin" viewBox="0 0 24 24"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></symbol>
  <symbol id="i-masks" viewBox="0 0 24 24"><path d="M10 11h.01"/><path d="M14 6h.01"/><path d="M18 6h.01"/><path d="M6.5 13.1h.01"/><path d="M22 5c0 9-4 12-6 12s-6-3-6-12c0-2 2-3 6-3s6 1 6 3"/><path d="M17.4 9.9c-.8.8-2 .8-2.8 0"/><path d="M10.1 7.1C9 7.2 7.7 7.7 6 8.6c-3.5 2-4.7 3.9-3.7 5.6 4.5 7.8 9.5 8.4 11.2 7.4.9-.5 1.9-2.1 1.9-4.7"/><path d="M9.1 16.5c.3-1.1 1.4-1.7 2.4-1.4"/></symbol>
  <symbol id="i-megaphone" viewBox="0 0 24 24"><path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></symbol>
  <symbol id="i-message" viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></symbol>
  <symbol id="i-mic" viewBox="0 0 24 24"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></symbol>
  <symbol id="i-microscope" viewBox="0 0 24 24"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></symbol>
  <symbol id="i-monitor" viewBox="0 0 24 24"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></symbol>
  <symbol id="i-mountain" viewBox="0 0 24 24"><path d="m8 3 4 8 5-5 5 15H2L8 3z"/></symbol>
  <symbol id="i-newspaper" viewBox="0 0 24 24"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/></symbol>
  <symbol id="i-palette" viewBox="0 0 24 24"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></symbol>
  <symbol id="i-pen" viewBox="0 0 24 24"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></symbol>
  <symbol id="i-plane" viewBox="0 0 24 24"><path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/></symbol>
  <symbol id="i-puzzle" viewBox="0 0 24 24"><path d="M19.4 14c.4 0 .6-.3.6-.6V9.4c0-.3-.3-.6-.6-.6h-2.9c-.3 0-.5-.2-.5-.5 0-.1 0-.2.1-.3.3-.4.5-.9.5-1.4A2.6 2.6 0 0 0 14 4a2.6 2.6 0 0 0-2.6 2.6c0 .5.2 1 .5 1.4.1.1.1.2.1.3 0 .3-.2.5-.5.5H8.6c-.3 0-.6.3-.6.6v2.9c0 .3-.2.5-.5.5-.1 0-.2 0-.3-.1-.4-.3-.9-.5-1.4-.5A2.6 2.6 0 0 0 3.2 15a2.6 2.6 0 0 0 2.6 2.6c.5 0 1-.2 1.4-.5.1-.1.2-.1.3-.1.3 0 .5.2.5.5v2.9c0 .3.3.6.6.6h9.8c.3 0 .6-.3.6-.6v-2.9c0-.3.2-.5.5-.5.1 0 .2 0 .3.1.4.3.9.5 1.4.5a2.6 2.6 0 0 0 2.6-2.6 2.6 2.6 0 0 0-2.6-2.6c-.5 0-1 .2-1.4.5-.1.1-.2.1-.3.1-.3 0-.5-.2-.5-.5z"/></symbol>
  <symbol id="i-rocket" viewBox="0 0 24 24"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></symbol>
  <symbol id="i-rotate" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></symbol>
  <symbol id="i-ruler" viewBox="0 0 24 24"><path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/></symbol>
  <symbol id="i-scale" viewBox="0 0 24 24"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/></symbol>
  <symbol id="i-scroll" viewBox="0 0 24 24"><path d="M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/></symbol>
  <symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></symbol>
  <symbol id="i-settings" viewBox="0 0 24 24"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></symbol>
  <symbol id="i-shirt" viewBox="0 0 24 24"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></symbol>
  <symbol id="i-shuffle" viewBox="0 0 24 24"><path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"/><path d="m18 2 4 4-4 4"/><path d="M2 6h1.9c1.5 0 2.9.9 3.6 2.2"/><path d="M22 18h-5.9c-1.3 0-2.6-.7-3.3-1.8l-.5-.8"/><path d="m18 14 4 4-4 4"/></symbol>
  <symbol id="i-smartphone" viewBox="0 0 24 24"><rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/></symbol>
  <symbol id="i-smile" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></symbol>
  <symbol id="i-sparkles" viewBox="0 0 24 24"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/></symbol>
  <symbol id="i-sprout" viewBox="0 0 24 24"><path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-3.7.3-4.6 1.4-4.9 2z"/></symbol>
  <symbol id="i-star" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></symbol>
  <symbol id="i-trend-down" viewBox="0 0 24 24"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></symbol>
  <symbol id="i-trend-up" viewBox="0 0 24 24"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></symbol>
  <symbol id="i-trophy" viewBox="0 0 24 24"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></symbol>
  <symbol id="i-type" viewBox="0 0 24 24"><polyline points="4 7 4 4 20 4 20 7"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="4" x2="12" y2="20"/></symbol>
  <symbol id="i-user" viewBox="0 0 24 24"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></symbol>
  <symbol id="i-users" viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></symbol>
  <symbol id="i-utensils" viewBox="0 0 24 24"><path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/><path d="M7 2v20"/><path d="M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7"/></symbol>
  <symbol id="i-wrench" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></symbol>
  <symbol id="i-zap" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></symbol>
</svg>
```

Before finalizing this step, grep `templates/base.html` for `<symbol id="i-`
and confirm no id appears twice in the final file — Django/browsers
tolerate duplicate SVG `<symbol>` ids by silently using whichever is first
in the DOM, which would make the second definition dead code, so this must
be verified directly rather than assumed. Confirm the final count is 84
symbols (the 11 that existed before this step + these 73 new ones).

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_extras.py -v`
Expected: PASS (4 passed)

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass — this task adds no template usage yet, purely additive.

- [ ] **Step 8: Commit**

```bash
git add vocab/templatetags tests/test_vocab_extras.py templates/base.html
git commit -m "feat(vlpe): port category icon map + sprite symbols from production"
```

---

### Task 2: CEFR badge CSS + shared filter-bar/chip CSS system

**Files:**
- Modify: `static/css/base.css`

**Interfaces:**
- Produces: CSS custom properties `--a1`/`--a1p`/`--a2`/`--a2p`/`--b1`/
  `--b1p`/`--b2`/`--b2p`/`--c1`/`--c1p`/`--c2`/`--c2p` (dark + light theme
  variants), a `.cefr-badge` + 12 `.cefr-badge.<LEVEL>` CSS rule family, and
  a shared `.filters`/`.search-row`/`.filter-row`/`.filter-label`/`.chip`/
  `.clear-btn` filter-bar CSS system (generic — not vocab-specific, put in
  `base.css` rather than `vocab.css` since a future Grammar retrofit will
  need the identical pattern). Consumed by Task 3 (category browse's filter
  bar + category cards) and Task 6 (word detail's CEFR badge).

This task has no Python-testable surface (pure CSS). Verify by confirming
the file parses and the existing suite stays green (nothing references
these classes yet).

- [ ] **Step 1: Add the 12 CEFR color custom properties to `static/css/base.css`**

Change:
```css
:root{
  color-scheme: dark;
  --violet: 124 58 237;
  --bg: #0b0d12;
  --text: #eceef4;
  --muted: #98a0b3;
  --border: #232937;
  --card-bg: #12151d;
  --gold: #d4af6a;
  --gold-rgb: 212 175 106;
  --serif: 'Fraunces', Georgia, serif;
  --ease-luxe: cubic-bezier(.22,1,.36,1);
}
```
to:
```css
:root{
  color-scheme: dark;
  --violet: 124 58 237;
  --bg: #0b0d12;
  --text: #eceef4;
  --muted: #98a0b3;
  --border: #232937;
  --card-bg: #12151d;
  --gold: #d4af6a;
  --gold-rgb: 212 175 106;
  --serif: 'Fraunces', Georgia, serif;
  --ease-luxe: cubic-bezier(.22,1,.36,1);
  --a1: #10b981; --a1p: #eab308; --a2: #06b6d4; --a2p: #f97316;
  --b1: #6366f1; --b1p: #ec4899; --b2: #3b82f6; --b2p: #1e40af;
  --c1: #f59e0b; --c1p: #f43f5e; --c2: #ef4444; --c2p: #a855f7;
}
```

Change:
```css
:root[data-theme="light"]{
  color-scheme: light;
  --bg: #f6f5f2;
  --text: #16181d;
  --muted: #585d68;
  --border: #dcd7cc;
  --card-bg: #ffffff;
  --gold: #b08a3e;
  --gold-rgb: 176 138 62;
}
```
to:
```css
:root[data-theme="light"]{
  color-scheme: light;
  --bg: #f6f5f2;
  --text: #16181d;
  --muted: #585d68;
  --border: #dcd7cc;
  --card-bg: #ffffff;
  --gold: #b08a3e;
  --gold-rgb: 176 138 62;
  --a1: #059669; --a1p: #ca8a04; --a2: #06b6d4; --a2p: #ea580c;
  --b1: #4f46e5; --b1p: #db2777; --b2: #2563eb; --b2p: #1e3a8a;
  --c1: #d97706; --c1p: #e11d48; --c2: #dc2626; --c2p: #9333ea;
}
```

(The `@media (prefers-color-scheme: dark){ :root:not([data-theme]){...} }`
block does not need these — it's the same values as the base `:root`
already, which already inherit correctly since custom properties cascade;
production's own dark-vs-light-media-query split for these 12 vars mirrors
exactly this same pattern, only the explicit dark/light `[data-theme]`
blocks differ.)

- [ ] **Step 2: Append the `.cefr-badge` family to `static/css/base.css`**

Append to the end of the file:

```css

/* CEFR level badges — ported from production's .cefr-badge family */
.cefr-badge{
  font-size: .68rem; font-weight: 800; padding: 3px 9px; border-radius: 6px;
  color: #fff; letter-spacing: .06em; flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
}
.cefr-badge.A1{ background: var(--a1); }
.cefr-badge.A1\+{ background: var(--a1p); }
.cefr-badge.A2{ background: var(--a2); }
.cefr-badge.A2\+{ background: var(--a2p); }
.cefr-badge.B1{ background: var(--b1); }
.cefr-badge.B1\+{ background: var(--b1p); }
.cefr-badge.B2{ background: var(--b2); }
.cefr-badge.B2\+{ background: var(--b2p); }
.cefr-badge.C1{ background: var(--c1); }
.cefr-badge.C1\+{ background: var(--c1p); }
.cefr-badge.C2{ background: var(--c2); }
.cefr-badge.C2\+{ background: var(--c2p); }
```

- [ ] **Step 3: Append the shared filter-bar/chip CSS system to `static/css/base.css`**

Ported from production's `.filters`/`.chip` family (lines ~362-424 of
`vocablarry.html`). **Important theme-convention flip:** production's
unthemed/base rule is its LIGHT appearance with `[data-theme="dark"]` as
the override, but VLPE's convention is the opposite — dark is the
unthemed/base appearance and `[data-theme="light"]` is the override (see
`base.css`'s existing `:root` vs `:root[data-theme="light"]` split). The
CSS below has already been flipped accordingly — do not port production's
`[data-theme="dark"] .filters{...}` override literally, it would apply
backwards.

Append to the end of the file:

```css

/* Shared filter bar + chip system — ported from production's .filters/
   .chip family, adapted for VLPE's dark-default theme convention (see
   note above) and rgba(var(--violet)) converted to rgb(var(--violet) / X). */
.filters{
  display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px;
  background: rgba(20,20,26,.82); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgb(var(--violet) / .22); border-radius: 20px; padding: 20px 22px;
}
[data-theme="light"] .filters{
  background: rgba(255,255,255,.72);
  border-color: rgb(var(--violet) / .18);
}
.search-row{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.search-row input[type="search"]{
  flex: 1; min-width: 200px; background: rgb(var(--violet) / .06); border: 1px solid rgb(var(--violet) / .2);
  color: var(--text); padding: 10px 16px; border-radius: 12px; font-size: .93rem;
  font-family: 'Plus Jakarta Sans','Inter',sans-serif;
}
.search-row input[type="search"]:focus{ outline: none; border-color: rgb(var(--violet) / .6); box-shadow: 0 0 0 3px rgb(var(--violet) / .12); }
.filter-row{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.filter-label{ font-size: .72rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; margin-right: 4px; font-family: 'JetBrains Mono', monospace; }
.chip{
  font-size: .82rem; font-weight: 600; padding: 6px 14px; border-radius: 999px;
  background: rgb(var(--violet) / .06); border: 1px solid rgb(var(--violet) / .18); color: var(--muted);
  cursor: pointer; display: inline-flex; align-items: center; gap: 6px; text-decoration: none;
  transition: color .15s ease, border-color .15s ease, background .15s ease, transform .2s cubic-bezier(.25,.46,.45,.94), box-shadow .2s ease;
}
.chip:hover{ color: var(--text); border-color: rgb(var(--violet) / .5); background: rgb(var(--violet) / .1); transform: translateY(-1px); box-shadow: 0 4px 12px rgb(var(--violet) / .15); }
.chip.active{ color: #fff; border-color: transparent; background: rgb(var(--violet)); box-shadow: 0 4px 14px rgb(var(--violet) / .35); }
.chip.active[data-browse-cefr="A1"]{ background: var(--a1); }
.chip.active[data-browse-cefr="A1+"]{ background: var(--a1p); }
.chip.active[data-browse-cefr="A2"]{ background: var(--a2); }
.chip.active[data-browse-cefr="A2+"]{ background: var(--a2p); }
.chip.active[data-browse-cefr="B1"]{ background: var(--b1); }
.chip.active[data-browse-cefr="B1+"]{ background: var(--b1p); }
.chip.active[data-browse-cefr="B2"]{ background: var(--b2); }
.chip.active[data-browse-cefr="B2+"]{ background: var(--b2p); }
.chip.active[data-browse-cefr="C1"]{ background: var(--c1); }
.chip.active[data-browse-cefr="C1+"]{ background: var(--c1p); }
.chip.active[data-browse-cefr="C2"]{ background: var(--c2); }
.chip.active[data-browse-cefr="C2+"]{ background: var(--c2p); }
.chip.active[data-browse-status="completed"]{ background: #22c55e; }
.chip.active[data-browse-status="inProgress"]{ background: var(--c1); }
.chip.active[data-browse-status="notStarted"]{ background: var(--muted); }
.clear-btn{
  font-size: .78rem; color: var(--muted); background: rgb(var(--violet) / .05); border: 1px solid rgb(var(--violet) / .18);
  border-radius: 999px; padding: 6px 14px; cursor: pointer; font-weight: 600; text-decoration: none;
  font-family: 'JetBrains Mono', monospace; letter-spacing: .04em;
  transition: color .15s, border-color .15s, background .15s, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.clear-btn:hover{ color: var(--text); border-color: rgb(var(--violet) / .5); background: rgb(var(--violet) / .1); transform: translateY(-1px); }
```

(`.chip.active[data-browse-status="completed"]` uses a literal `#22c55e`
rather than a `--tfg`-style custom property, since VLPE never ported
production's separate `--tfg`/15-theme-class system — see Task 3's own
Decision on reusing `Category.color` instead. Green is hardcoded to match
the same "completed" green production, `.cat-medal`, and `.word-card.learned`
all already use elsewhere in this retrofit.)

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass unchanged.

- [ ] **Step 5: Commit**

```bash
git add static/css/base.css
git commit -m "feat(vlpe): port CEFR badge + shared filter-bar/chip CSS from production"
```

---

### Task 3: Category browse page retrofit

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `templates/vocab/browse.html`
- Modify: `templates/base.html`
- Modify: `static/css/vocab.css`
- Modify: `static/js/i18n.js`
- Modify: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: `category_icon` filter (Task 1), `.cefr-badge` CSS +
  `.filters`/`.search-row`/`.filter-row`/`.filter-label`/`.chip`/
  `.clear-btn` filter-bar CSS (Task 2).
- Produces: nothing new consumed by later tasks in this plan (Tasks 4-6
  touch different pages) — this task is self-contained end to end.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocabulary_category_list_shows_progress_bar_for_authenticated_user(cefr_a1, regular_user):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=category, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned', str(w2.pk): 'little'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-pfill' in html
    assert 'cat-medal' not in html  # not 100% complete


@pytest.mark.django_db
def test_vocabulary_category_list_shows_medal_at_100_percent(cefr_a1, regular_user):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-medal' in html


@pytest.mark.django_db
def test_vocabulary_category_list_no_progress_bar_for_guest(cefr_a1):
    from vocab.models import Color
    color = Color.objects.create(name='blue', bg_hex='#3b82f6', text_hex='#ffffff')
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1,
        color=color, icon='📚',
    )
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'cat-pfill' not in html
    assert 'cat-medal' not in html


@pytest.mark.django_db
def test_vocabulary_category_list_renders_resolved_icon(cefr_a1):
    category = Category.objects.create(
        slug='animals', name='Animals', order=1, cefr_level=cefr_a1, icon='📚',
    )
    c = Client()
    r = c.get('/vocabulary/category/')
    assert '#i-book' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_list_progress_filter_narrows_results(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/?progress=learned')
    body = r.content.decode()
    assert 'Animals' in body
    assert 'Food' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_progress_filter_not_started(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(w1.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/?progress=not_started')
    body = r.content.decode()
    assert 'Food' in body
    assert 'Animals' not in body


@pytest.mark.django_db
def test_vocabulary_category_list_chip_filter_bar_present():
    c = Client()
    r = c.get('/vocabulary/category/')
    html = r.content.decode()
    assert 'data-browse-cefr="A1"' in html
    assert 'data-browse-status="completed"' in html
    assert 'data-browse-status="inProgress"' in html
    assert 'data-browse-status="notStarted"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_pages.py -k "vocabulary_category_list_shows_progress or vocabulary_category_list_no_progress or vocabulary_category_list_renders_resolved_icon or vocabulary_category_list_progress_filter or vocabulary_category_list_chip_filter_bar" -v`
Expected: FAIL — current `browse.html` has no progress bars, no icon
sprite, no `progress` query param support, no chip filter bar.

- [ ] **Step 3: Extend `config/views_vocab.py`'s `vocab_browse`**

Change:
```python
def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    categories = Category.objects.select_related('cefr_level', 'color').order_by('order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
    })
```
to:
```python
def vocab_browse(request):
    query = request.GET.get('q', '').strip()
    cefr_filter = request.GET.get('cefr', '').strip()
    progress_filter = request.GET.get('progress', '').strip()
    categories = Category.objects.select_related('cefr_level', 'color').order_by('order')
    if query:
        categories = categories.filter(name__icontains=query)
    if cefr_filter:
        categories = categories.filter(cefr_level__code=cefr_filter)
    categories = list(categories)

    if request.user.is_authenticated:
        learn_map = request.user.learn_map
        word_category = dict(Word.objects.values_list('id', 'category_id'))
        progress_by_category = {}
        for word_id_str, state in learn_map.items():
            try:
                word_id = int(word_id_str)
            except (TypeError, ValueError):
                continue
            category_id = word_category.get(word_id)
            if category_id is None:
                continue
            bucket = progress_by_category.setdefault(category_id, {'learned': 0, 'little': 0})
            if state == 'learned':
                bucket['learned'] += 1
            elif state == 'little':
                bucket['little'] += 1

        word_counts = {}
        for category in categories:
            word_counts[category.id] = category.words.count()

        for category in categories:
            total = word_counts[category.id]
            bucket = progress_by_category.get(category.id, {'learned': 0, 'little': 0})
            learned = bucket['learned']
            little = bucket['little']
            category.progress = {
                'learned': learned,
                'little': little,
                'total': total,
                'learned_pct': round(learned / total * 100) if total else 0,
                'little_pct': round(little / total * 100) if total else 0,
                'complete': total > 0 and learned == total,
            }

        if progress_filter == 'learned':
            categories = [c for c in categories if c.progress['complete']]
        elif progress_filter == 'in_progress':
            categories = [
                c for c in categories
                if not c.progress['complete'] and (c.progress['learned'] or c.progress['little'])
            ]
        elif progress_filter == 'not_started':
            categories = [
                c for c in categories
                if not c.progress['learned'] and not c.progress['little']
            ]
    else:
        for category in categories:
            category.progress = None

    cefr_levels = CEFRLevel.objects.order_by('order')
    return render(request, 'vocab/browse.html', {
        'categories': categories,
        'cefr_levels': cefr_levels,
        'query': query,
        'cefr_filter': cefr_filter,
        'progress_filter': progress_filter,
    })
```

- [ ] **Step 4: Add i18n keys to `static/js/i18n.js`**

In the `en` block, after the `"nav.speaking"` line, add:
```javascript
      "vocab.searchCategories": "Search categories…",
      "common.cefrLevel": "CEFR Level",
      "common.progress": "Progress",
      "common.all": "All",
      "common.completed": "Completed",
      "common.inProgress": "In Progress",
      "common.notStarted": "Not Started",
      "common.clearFilters": "Clear filters",
```
In the `vi` block, after the `"nav.speaking"` line, add:
```javascript
      "vocab.searchCategories": "Tìm kiếm danh mục…",
      "common.cefrLevel": "Trình độ CEFR",
      "common.progress": "Tiến độ",
      "common.all": "Tất cả",
      "common.completed": "Hoàn thành",
      "common.inProgress": "Đang học",
      "common.notStarted": "Chưa bắt đầu",
      "common.clearFilters": "Xóa bộ lọc",
```

- [ ] **Step 5: Rewrite `templates/vocab/browse.html`**

```html
{% extends "base.html" %}
{% load static vocab_extras %}
{% block title %}Vocabulary — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-browse">
  <h1>Vocabulary</h1>
  <div class="filters">
    <form method="get" class="search-row">
      <input type="search" name="q" value="{{ query }}" placeholder="Search categories…" data-i18n-placeholder="vocab.searchCategories">
      {% if cefr_filter %}<input type="hidden" name="cefr" value="{{ cefr_filter }}">{% endif %}
      {% if progress_filter %}<input type="hidden" name="progress" value="{{ progress_filter }}">{% endif %}
      <button type="submit" class="btn">Filter</button>
    </form>
    <div class="filter-row">
      <span class="filter-label" data-i18n="common.cefrLevel">CEFR Level</span>
      <a class="chip{% if not cefr_filter %} active{% endif %}" href="?q={{ query }}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}" data-i18n="common.all">All</a>
      {% for level in cefr_levels %}
      <a class="chip{% if cefr_filter == level.code %} active{% endif %}" data-browse-cefr="{{ level.code }}" href="?q={{ query }}&cefr={{ level.code }}{% if progress_filter %}&progress={{ progress_filter }}{% endif %}">{{ level.code }}</a>
      {% endfor %}
    </div>
    {% if user.is_authenticated %}
    <div class="filter-row">
      <span class="filter-label" data-i18n="common.progress">Progress</span>
      <a class="chip{% if not progress_filter %} active{% endif %}" href="?q={{ query }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}" data-i18n="common.all">All</a>
      <a class="chip{% if progress_filter == 'learned' %} active{% endif %}" data-browse-status="completed" href="?q={{ query }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=learned" data-i18n="common.completed">Completed</a>
      <a class="chip{% if progress_filter == 'in_progress' %} active{% endif %}" data-browse-status="inProgress" href="?q={{ query }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=in_progress" data-i18n="common.inProgress">In Progress</a>
      <a class="chip{% if progress_filter == 'not_started' %} active{% endif %}" data-browse-status="notStarted" href="?q={{ query }}{% if cefr_filter %}&cefr={{ cefr_filter }}{% endif %}&progress=not_started" data-i18n="common.notStarted">Not Started</a>
    </div>
    {% endif %}
    <div class="filter-row" style="justify-content:flex-end;">
      <a class="clear-btn" href="{% url 'vocabulary_category_list' %}" data-i18n="common.clearFilters">Clear filters</a>
    </div>
  </div>
  {% if categories %}
  <div class="cat-grid">
    {% for category in categories %}
    <a class="cat-card" href="{% url 'vocabulary_category_detail' category.slug %}"
       style="--accent-c:{{ category.color.bg_hex|default:'#7c3aed' }};">
      <div class="cat-card-top">
        <span class="cat-tag"><svg class="ico" aria-hidden="true"><use href="#{{ category.icon|category_icon }}"/></svg> {{ category.words.count }} words</span>
        {% if category.cefr_level %}<span class="cefr-badge {{ category.cefr_level.code }}">{{ category.cefr_level.code }}</span>{% endif %}
        <svg class="ico cat-arrow" aria-hidden="true"><use href="#i-arrow-up-right"/></svg>
      </div>
      <div class="cat-name">{{ category.name }}</div>
      {% if category.progress %}
      <div class="cat-pbar-row">
        <div class="cat-pbar">
          <div class="cat-pfill-little" style="width:{{ category.progress.little_pct }}%"></div>
          <div class="cat-pfill" style="width:{{ category.progress.learned_pct }}%;{% if category.progress.complete %}background:#10b981;{% endif %}position:absolute;top:0;left:0;"></div>
        </div>
        {% if category.progress.complete %}
        <svg class="ico cat-medal" aria-hidden="true"><use href="#i-medal"/></svg>
        {% else %}
        <span class="cat-plabel">{{ category.progress.learned }}/{{ category.progress.total }}</span>
        {% endif %}
      </div>
      {% endif %}
    </a>
    {% endfor %}
  </div>
  {% else %}
  <p class="vocab-empty">No categories match your search.</p>
  {% endif %}
</section>
{% endblock %}
```

(Note: `#i-arrow-up-right` and `#i-medal` are new icons this template
references but no earlier task added — see Step 6.)

- [ ] **Step 6: Add the 2 missing icons this template needs**

In `templates/base.html`, change:
```html
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
```
to:
```html
  <symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></symbol>
  <symbol id="i-arrow-up-right" viewBox="0 0 24 24"><line x1="7" y1="17" x2="17" y2="7"/><polyline points="7 7 17 7 17 17"/></symbol>
  <symbol id="i-medal" viewBox="0 0 24 24"><path d="M7.21 15 2.66 7.14a2 2 0 0 1 .13-2.2L4.4 2.8A2 2 0 0 1 6 2h12a2 2 0 0 1 1.6.8l1.6 2.14a2 2 0 0 1 .14 2.2L16.79 15"/><path d="M11 12 5.12 2.2"/><path d="m13 12 5.88-9.8"/><path d="M8 7h8"/><circle cx="12" cy="17" r="5"/><path d="M12 18v-2h-.5"/></symbol>
```

(This is a second edit to the same file Task 1 already modified — Task 1
added the 80 `EMOJI_ICON_MAP`-referenced icons; this step adds 2 more this
template's own chrome needs, unrelated to category emoji resolution.)

- [ ] **Step 7: Remove the now-dead old browse CSS, then append the new category-browse CSS to `static/css/vocab.css`**

Step 5's rewrite of `browse.html` stopped using `.vocab-filters`,
`.category-grid`, `.category-card`, `.category-icon`, `.category-name`,
and `.category-cefr` (replaced by `.filters`/`.search-row`, `.cat-grid`,
`.cat-card`, the icon sprite, `.cat-name`, and `.cefr-badge`
respectively) — remove these 6 now-orphaned rule blocks rather than
leaving dead CSS behind. `.vocab-browse h1` and `.vocab-empty` are still
used by the new template and must stay.

At the top of `static/css/vocab.css`, change:
```css
.vocab-browse h1{ margin-top: 32px; }

.vocab-filters{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 16px 0 28px;
}
.vocab-filters input[type="text"],
.vocab-filters select{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 0.95rem;
}
.vocab-filters input[type="text"]{ flex: 1; min-width: 180px; }

.category-grid{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px;
  padding-bottom: 48px;
}
.category-card{
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--cat-bg, var(--card-bg));
  color: var(--cat-text, var(--text));
  text-decoration: none;
}
.category-icon{ font-size: 1.6rem; }
.category-name{ font-weight: 700; }
.category-cefr{
  align-self: flex-start;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(var(--violet), 0.12);
  color: rgb(var(--violet));
}
.vocab-empty{ color: var(--muted); padding: 24px 0; }
```
to:
```css
.vocab-browse h1{ margin-top: 32px; }

.vocab-empty{ color: var(--muted); padding: 24px 0; }
```

Then append to the end of the file:

```css

/* Category browse — .cat-card family, ported from production */
.cat-grid{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(270px,1fr)); padding-bottom: 48px; }
.cat-card{
  position: relative; border: 1px solid var(--border); border-radius: 20px; padding: 18px;
  background: var(--card-bg); text-decoration: none; color: var(--text);
  cursor: pointer; display: flex; flex-direction: column; gap: 14px;
  transition: transform .4s var(--ease-luxe), box-shadow .4s var(--ease-luxe), border-color .4s var(--ease-luxe);
}
.cat-card:hover{
  transform: translateY(-4px); border-color: rgb(var(--violet) / .5);
  box-shadow: 0 24px 60px rgba(0,0,0,.18), 0 6px 18px rgb(var(--violet) / .08);
}
.cat-card-top{ display: flex; align-items: center; gap: 8px; }
.cat-tag{
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'JetBrains Mono', monospace; font-size: .58rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .12em; padding: 4px 10px; border-radius: 999px;
  color: var(--accent-c, rgb(var(--violet)));
  background: rgb(var(--violet) / .1); border: 1px solid rgb(var(--violet) / .38);
}
.cat-tag .ico{ font-size: .85rem; }
.cat-arrow{ margin-left: auto; font-size: 1rem; color: var(--muted); opacity: .5; flex-shrink: 0; transition: color .3s var(--ease-luxe), opacity .3s var(--ease-luxe), transform .45s var(--ease-luxe); }
.cat-card:hover .cat-arrow{ color: var(--accent-c, rgb(var(--violet))); opacity: 1; transform: translate(2px,-2px); }
.cat-medal{ font-size: 1.15rem; width: 1.15rem; height: 1.15rem; color: #eab308; flex-shrink: 0; filter: drop-shadow(0 0 6px rgba(234,179,8,.35)); }
[data-theme="light"] .cat-medal{ color: #ca8a04; filter: none; }
.cat-name{ font-family: 'Plus Jakarta Sans','Sora',sans-serif; font-weight: 800; font-size: 1.02rem; line-height: 1.3; color: var(--accent-c, var(--text)); letter-spacing: -.01em; }
.cat-pbar-row{ display: flex; align-items: center; gap: 10px; }
.cat-pbar{ flex: 1; height: 2.5px; border-radius: 99px; background: var(--border); overflow: hidden; position: relative; }
.cat-pfill{ height: 100%; border-radius: 99px; background: var(--accent-c, rgb(var(--violet))); transition: width .4s ease; }
.cat-pfill-little{ height: 100%; border-radius: 99px 0 0 99px; background: var(--c1); transition: width .4s ease; opacity: .7; }
.cat-plabel{ font-size: .66rem; color: var(--muted); white-space: nowrap; font-family: 'JetBrains Mono', monospace; }
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_pages.py -v`
Expected: PASS (all vocab page tests, including the new ones).

- [ ] **Step 9: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 10: Manual browser verification (required — real interaction, no Python-testable surface)**

Start the dev server and drive a real Playwright/Chromium session:
- Confirm real category icons render (not raw emoji) for several real
  categories from the seeded `db.sqlite3`.
- As a real authenticated test account with real progress in `learn_map`:
  confirm the progress bar renders with the right learned/little split for
  a partially-progressed category, and the gold medal + green bar for a
  100%-complete one.
- Click each CEFR chip and confirm the category grid narrows correctly and
  the chip's `active` class + color moves to the clicked one.
- Click each progress chip (Completed/In Progress/Not Started) and confirm
  correct narrowing.
- Confirm chips are entirely absent for a guest session (no progress row
  in the filter bar).
- Both themes.

- [ ] **Step 11: Commit**

```bash
git add config/views_vocab.py templates/vocab/browse.html templates/base.html \
  static/css/vocab.css static/js/i18n.js tests/test_vocab_pages.py
git commit -m "feat(vlpe): retrofit category browse page to match production"
```

---

### Task 4: `vocab-word.js` generalization (reusable toggle + bulk handler)

**Files:**
- Modify: `static/js/vocab-word.js`

**Interfaces:**
- Consumes: nothing new.
- Produces: two functions attached to `window` (`window.vocabToggleWord`
  and `window.vocabBulkSetCategory`) — consumed by Task 5's
  `category_word_list.html` inline script and per-card toggle buttons.
  `word_detail.html`'s existing single toggle button continues to work
  unchanged (it now calls the same generalized function internally).

- [ ] **Step 1: Rewrite `static/js/vocab-word.js`**

Replace the entire file:

```javascript
(function(){
  var CYCLE = [null, "little", "learned"];
  var LABELS = { null: "Not Learned", little: "Little Bit", learned: "Learned" };

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function readState(btn){
    var raw = btn.dataset.state;
    return raw === "none" ? null : raw;
  }

  function paint(btn, stateValue){
    btn.dataset.state = stateValue === null ? "none" : stateValue;
    btn.textContent = LABELS[stateValue === null ? "null" : stateValue];
  }

  // Cycles one word's state (none -> little -> learned -> none) and
  // syncs it to the server via GET-then-merge-then-POST against
  // /auth/sync/, never sending a partial map. Used by both the single
  // word_detail.html toggle and each per-card toggle on
  // category_word_list.html.
  function vocabToggleWord(btn){
    var wordId = btn.dataset.wordId;
    var prevState = readState(btn);
    var nextState = CYCLE[(CYCLE.indexOf(prevState) + 1) % CYCLE.length];
    paint(btn, nextState);

    return fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){
        if (!res.ok) throw new Error("sync GET failed");
        return res.json();
      })
      .then(function(data){
        var learnMap = data.learn_map || {};
        if (nextState === null) delete learnMap[wordId];
        else learnMap[wordId] = nextState;
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ learn_map: learnMap }),
        });
      })
      .then(function(res){
        if (!res.ok) throw new Error("sync POST failed");
      })
      .catch(function(){
        paint(btn, prevState);
      });
  }

  // Sets or clears every word ID in wordIds at once: mode "learned" sets
  // each to "learned"; mode "reset" deletes each key entirely (matching
  // vocabToggleWord's own none-state convention — learn_map stays sparse,
  // never gets an explicit "none" value).
  function vocabBulkSetCategory(wordIds, mode){
    return fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){
        if (!res.ok) throw new Error("sync GET failed");
        return res.json();
      })
      .then(function(data){
        var learnMap = data.learn_map || {};
        wordIds.forEach(function(wordId){
          if (mode === "reset") delete learnMap[wordId];
          else learnMap[wordId] = "learned";
        });
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ learn_map: learnMap }),
        });
      });
  }

  window.vocabToggleWord = vocabToggleWord;
  window.vocabBulkSetCategory = vocabBulkSetCategory;

  var btn = document.querySelector(".learn-state-btn");
  if (btn){
    btn.addEventListener("click", function(){ vocabToggleWord(btn); });
  }
})();
```

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass — `word_detail.html`'s existing behavior is unchanged
(same DOM query, same event, same fetch calls), only refactored internally.

- [ ] **Step 3: Manual browser verification (required — behavior-preserving refactor of existing interactive code)**

Real Playwright session against a live dev server, authenticated test
account: confirm the word detail page's single toggle button still cycles
none → little → learned → none correctly and persists across a page
reload (same check this button already had before this refactor — the
point is confirming zero regression, not new behavior).

- [ ] **Step 4: Commit**

```bash
git add static/js/vocab-word.js
git commit -m "refactor(vlpe): generalize vocab-word.js toggle logic for reuse"
```

---

### Task 5: Category word-list page retrofit

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `templates/vocab/category_word_list.html`
- Modify: `static/css/vocab.css`
- Modify: `static/js/i18n.js`
- Modify: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: `.cefr-badge` CSS (Task 2), `vocabToggleWord`/
  `vocabBulkSetCategory` from `vocab-word.js` (Task 4).
- Produces: nothing consumed by later tasks in this plan.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocabulary_category_detail_renders_hover_reveal_cards(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(
        word='Cat', pos='noun', definition='A small pet.', example='I have a cat.',
        synonyms=['feline'], antonyms=['dog'], category=category, order=1, cefr_level=cefr_a1,
    )
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'word-card' in html
    assert 'A small pet.' in html
    assert 'feline' in html
    assert 'I have a cat.' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_shows_per_word_state(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    regular_user.learn_map = {str(word.pk): 'learned'}
    regular_user.save(update_fields=['learn_map'])
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    assert 'data-state="learned"' in r.content.decode()


@pytest.mark.django_db
def test_vocabulary_category_detail_numbered_pagination(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    for i in range(60):
        Word.objects.create(word=f'Word{i:02d}', definition='x', category=category, order=i)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'page-btn' in html
    assert '<a class="page-btn active"' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_sets_csrf_cookie(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    assert 'csrftoken' in r.cookies


@pytest.mark.django_db
def test_vocabulary_category_detail_bulk_actions_present_for_authenticated(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    c.force_login(regular_user)
    r = c.get('/vocabulary/category/animals/')
    html = r.content.decode()
    assert 'cat-bulk-btn' in html
    assert 'catCompleteAllBtn' in html
    assert 'catResetAllBtn' in html


@pytest.mark.django_db
def test_vocabulary_category_detail_bulk_actions_absent_for_guest(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    Word.objects.create(word='Cat', definition='x', category=category, order=1)
    c = Client()
    r = c.get('/vocabulary/category/animals/')
    assert 'cat-bulk-btn' not in r.content.decode()


@pytest.mark.django_db
def test_bulk_mark_all_completed_round_trip_preserves_other_categories(cefr_a1, regular_user):
    cat1 = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    cat2 = Category.objects.create(slug='food', name='Food', order=2, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=cat1, order=1)
    w2 = Word.objects.create(word='Dog', definition='x', category=cat1, order=2)
    other_word = Word.objects.create(word='Bread', definition='x', category=cat2, order=1)
    regular_user.learn_map = {str(other_word.pk): 'little'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what vocabBulkSetCategory("learned") does: GET, set every
    # word ID in this category to "learned", POST the full map back.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    for w in (w1, w2):
        learn_map[str(w.pk)] = 'learned'
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {
        str(w1.pk): 'learned', str(w2.pk): 'learned', str(other_word.pk): 'little',
    }


@pytest.mark.django_db
def test_bulk_reset_all_deletes_keys_not_sets_none(cefr_a1, regular_user):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    w1 = Word.objects.create(word='Cat', definition='x', category=category, order=1)
    other_word = Word.objects.create(word='Bread', definition='x', category=category, order=2)
    regular_user.learn_map = {str(w1.pk): 'learned', str(other_word.pk): 'little'}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)

    # Exactly what vocabBulkSetCategory("reset") does: delete every word
    # ID in this category from the map entirely.
    get_res = c.get('/auth/sync/')
    learn_map = get_res.json()['learn_map']
    del learn_map[str(w1.pk)]
    post_res = c.post(
        '/auth/sync/', json.dumps({'learn_map': learn_map}),
        content_type='application/json',
    )

    assert post_res.status_code == 200
    regular_user.refresh_from_db()
    assert str(w1.pk) not in regular_user.learn_map
    assert regular_user.learn_map == {str(other_word.pk): 'little'}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_pages.py -k "hover_reveal or shows_per_word_state or numbered_pagination or category_detail_sets_csrf or bulk_actions or bulk_mark_all or bulk_reset_all" -v`
Expected: FAIL — current `category_word_list.html` is a plain `<ul>` with
no reveal cards, no CSRF cookie, no bulk actions, no numbered pagination.

- [ ] **Step 3: Extend `config/views_vocab.py`'s `vocab_category`**

Change:
```python
def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
    })
```
to:
```python
def _pagination_window(current, total, delta=2):
    """Page numbers to display, with None marking an ellipsis gap.
    Mirrors production's own windowed-pagination shape."""
    pages = []
    for p in range(1, total + 1):
        if p == 1 or p == total or (current - delta <= p <= current + delta):
            pages.append(p)
        elif pages and pages[-1] is not None:
            pages.append(None)
    return pages


@ensure_csrf_cookie
def vocab_category(request, slug):
    category = get_object_or_404(
        Category.objects.select_related('cefr_level', 'color'), slug=slug
    )
    words = category.words.order_by('order')
    paginator = Paginator(words, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    learn_map = request.user.learn_map if request.user.is_authenticated else {}
    for word in page_obj:
        word.learn_state = learn_map.get(str(word.pk))

    all_word_ids = list(words.values_list('id', flat=True))

    return render(request, 'vocab/category_word_list.html', {
        'category': category,
        'page_obj': page_obj,
        'pagination_window': _pagination_window(page_obj.number, paginator.num_pages),
        'all_word_ids': all_word_ids,
    })
```

Also change the import line at the top of the file:
```python
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
```
(this import already exists — `ensure_csrf_cookie` is already imported for
`vocab_word_detail`; no new import line needed, just apply the existing
decorator to `vocab_category` too.)

- [ ] **Step 4: Add i18n keys to `static/js/i18n.js`**

In the `en` block, after the `"common.clearFilters"` line added in Task 3,
add:
```javascript
      "vocab.markAllCompleted": "✓ Mark All Completed",
      "vocab.resetAll": "↺ Reset All",
      "common.allSections": "← All Sections",
```
In the `vi` block, after `"common.clearFilters"`, add:
```javascript
      "vocab.markAllCompleted": "✓ Đánh dấu tất cả đã học",
      "vocab.resetAll": "↺ Đặt lại tất cả",
      "common.allSections": "← Tất cả danh mục",
```

- [ ] **Step 5: Rewrite `templates/vocab/category_word_list.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ category.name }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-category">
  <p class="vocab-breadcrumb"><a href="{% url 'vocabulary_category_list' %}">Vocabulary</a> / {{ category.name }}</p>
  <h1>{{ category.name }}</h1>
  <div class="card-grid">
    {% for word in page_obj %}
    <div class="word-card{% if word.learn_state == 'learned' %} learned{% elif word.learn_state == 'little' %} little{% endif %}">
      <div class="face">
        <div>
          <div class="word"><a href="{% url 'vocabulary_word_detail' word.pk %}">{{ word.word }}</a></div>
          {% if word.pos %}<div class="pos">{{ word.pos }}</div>{% endif %}
        </div>
        {% if word.cefr_level %}<span class="cefr-badge {{ word.cefr_level.code }}">{{ word.cefr_level.code }}</span>{% endif %}
      </div>
      <div class="reveal">
        <div class="rdef">{{ word.definition }}</div>
        {% if word.synonyms %}<div class="rrow"><b>Synonyms:</b> {{ word.synonyms|join:", " }}</div>{% endif %}
        {% if word.antonyms %}<div class="rrow"><b>Antonyms:</b> {{ word.antonyms|join:", " }}</div>{% endif %}
        {% if word.example %}<div class="rex">"{{ word.example }}"</div>{% endif %}
        {% if user.is_authenticated %}
        <div class="learn-state-row">
          <span class="learn-state-label">Progress:</span>
          <button type="button" class="learn-state-btn card-toggle" data-word-id="{{ word.pk }}"
                  data-state="{{ word.learn_state|default:'none' }}">
            {% if word.learn_state == 'learned' %}Learned{% elif word.learn_state == 'little' %}Little Bit{% else %}Not Learned{% endif %}
          </button>
        </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% if page_obj.paginator.num_pages > 1 %}
  <nav class="pagination">
    <a class="page-btn{% if not page_obj.has_previous %} disabled{% endif %}"
       href="{% if page_obj.has_previous %}?page={{ page_obj.previous_page_number }}{% else %}#{% endif %}">«</a>
    {% for p in pagination_window %}
      {% if p is None %}<span class="page-ellipsis">…</span>
      {% else %}<a class="page-btn{% if p == page_obj.number %} active{% endif %}" href="?page={{ p }}">{{ p }}</a>
      {% endif %}
    {% endfor %}
    <a class="page-btn{% if not page_obj.has_next %} disabled{% endif %}"
       href="{% if page_obj.has_next %}?page={{ page_obj.next_page_number }}{% else %}#{% endif %}">»</a>
  </nav>
  {% endif %}
  {% if user.is_authenticated %}
  <div class="cat-bulk-actions">
    <button type="button" class="cat-bulk-btn" id="catCompleteAllBtn" data-i18n="vocab.markAllCompleted">✓ Mark All Completed</button>
    <button type="button" class="cat-bulk-btn cat-bulk-btn-secondary" id="catResetAllBtn" data-i18n="vocab.resetAll">↺ Reset All</button>
    <a class="cat-bulk-btn cat-bulk-btn-secondary" href="{% url 'vocabulary_category_list' %}" data-i18n="common.allSections">← All Sections</a>
  </div>
  {% endif %}
</section>
{% endblock %}
{% block extra_body %}
{% if user.is_authenticated %}
<script src="{% static 'js/vocab-word.js' %}" defer></script>
<script>
(function(){
  document.addEventListener("DOMContentLoaded", function(){
    document.querySelectorAll(".card-toggle").forEach(function(btn){
      btn.addEventListener("click", function(){ window.vocabToggleWord(btn); });
    });
    var allWordIds = {{ all_word_ids }};
    var completeBtn = document.getElementById("catCompleteAllBtn");
    var resetBtn = document.getElementById("catResetAllBtn");
    if (completeBtn){
      completeBtn.addEventListener("click", function(){
        window.vocabBulkSetCategory(allWordIds.map(String), "learned").then(function(){
          window.location.reload();
        });
      });
    }
    if (resetBtn){
      resetBtn.addEventListener("click", function(){
        window.vocabBulkSetCategory(allWordIds.map(String), "reset").then(function(){
          window.location.reload();
        });
      });
    }
  });
})();
</script>
{% endif %}
{% endblock %}
```

(`{{ all_word_ids }}` renders as a Django list's `str()` inside a `<script>`
tag, e.g. `[1, 2, 3]` — valid JS array literal syntax for integers, no
`|safe`/JSON filter needed since these are plain ints with no special
characters. Verify this renders as valid JS during Step 6's browser check.)

- [ ] **Step 6: Remove the now-dead old word-list CSS, then append the new category word-list CSS to `static/css/vocab.css`**

Step 5's rewrite of `category_word_list.html` stopped using `.word-list`
(replaced by `.card-grid`/`.word-card`) and `.vocab-pagination`
(replaced by `.pagination`/`.page-btn`, added in this same step below) —
remove these now-orphaned rules. `.vocab-breadcrumb` (and its `a` rule)
are still used by the new template and must stay.

In `static/css/vocab.css`, change:
```css
.vocab-breadcrumb{ color: var(--muted); font-size: 0.9rem; margin: 24px 0 4px; }
.vocab-breadcrumb a{ color: var(--muted); }

.word-list{
  list-style: none;
  padding: 0;
  margin: 20px 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}
.word-list li a{
  display: block;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
}
.vocab-pagination{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 0 48px;
  color: var(--muted);
}
.vocab-pagination a{ font-weight: 700; }
```
to:
```css
.vocab-breadcrumb{ color: var(--muted); font-size: 0.9rem; margin: 24px 0 4px; }
.vocab-breadcrumb a{ color: var(--muted); }
```

Then append to the end of the file:

```css

/* Word grid within a category — .word-card family, ported from production */
.card-grid{ display: grid; grid-template-columns: repeat(auto-fill, minmax(230px,1fr)); gap: 16px; margin: 20px 0; }
.word-card{
  position: relative; border: 1px solid rgb(var(--violet) / .15); border-radius: 18px;
  background: var(--card-bg); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  padding: 16px; min-height: 120px; overflow: hidden;
  border-top: 3px solid rgb(var(--violet));
  transition: transform .24s cubic-bezier(.25,.46,.45,.94), box-shadow .24s cubic-bezier(.25,.46,.45,.94);
}
.word-card:hover{
  transform: translateY(-5px);
  box-shadow: 0 20px 48px rgba(0,0,0,.45), 0 0 0 1px rgb(var(--violet) / .5), 0 4px 16px rgb(var(--violet) / .15);
}
.word-card .face{ display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.word-card .word a{ font-size: 1.1rem; font-weight: 700; font-family: 'Plus Jakarta Sans','Sora',sans-serif; letter-spacing: -.01em; line-height: 1.25; color: var(--text); text-decoration: none; }
.word-card .word a:hover{ color: rgb(var(--violet)); }
.word-card .pos{ font-size: .75rem; color: var(--muted); margin-top: 2px; font-style: italic; }
.word-card .reveal{
  position: absolute; inset: 0;
  background: linear-gradient(160deg, var(--card-bg) 0%, var(--card-bg) 100%);
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
  padding: 14px 16px; opacity: 0; transform: translateY(8px);
  transition: opacity .2s cubic-bezier(.4,0,.2,1), transform .2s cubic-bezier(.4,0,.2,1);
  overflow-y: auto; display: flex; flex-direction: column; gap: 6px; font-size: .82rem;
  pointer-events: none;
}
.word-card:hover .reveal{ opacity: 1; transform: translateY(0); pointer-events: auto; }
.reveal .rdef{ font-weight: 600; line-height: 1.4; color: var(--text); }
.reveal .rrow{ color: var(--muted); line-height: 1.4; }
.reveal .rrow b{ color: var(--text); font-weight: 600; }
.reveal .rex{ color: var(--muted); font-style: italic; line-height: 1.4; margin-top: auto; padding-top: 6px; border-top: 1px solid var(--border); }
.reveal .learn-state-row{ margin: 6px 0 0; }
.word-card.learned{ box-shadow: 0 0 0 2px #22c55e inset; }
.word-card.learned::before{
  content: "✓"; position: absolute; top: 10px; right: 10px; width: 20px; height: 20px;
  background: #22c55e; color: #fff; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: .7rem; font-weight: 800; z-index: 2;
}
.word-card.little{ box-shadow: 0 0 0 2px #f59e0b inset; }
.word-card.little::before{
  content: "~"; position: absolute; top: 10px; right: 10px; width: 20px; height: 20px;
  background: #f59e0b; color: #1c1917; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: .85rem; font-weight: 900; z-index: 2;
}

/* Numbered pagination — ported from production's .pagination/.page-btn */
.pagination{ display: flex; gap: 6px; align-items: center; justify-content: center; margin: 24px 0; flex-wrap: wrap; }
.page-btn{
  min-width: 36px; height: 36px; padding: 0 10px; border-radius: 9px; border: 1px solid rgb(var(--violet) / .18);
  background: rgb(var(--violet) / .06); color: var(--muted); font-family: 'JetBrains Mono', monospace;
  font-size: .82rem; font-weight: 600; text-decoration: none; display: inline-flex; align-items: center; justify-content: center;
  transition: background .15s, color .15s, border-color .15s, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.page-btn:hover:not(.disabled){ border-color: rgb(var(--violet) / .5); color: rgb(var(--violet)); transform: translateY(-1px); }
.page-btn.active{ background: rgb(var(--violet)); border-color: rgb(var(--violet)); color: #fff; box-shadow: 0 4px 12px rgb(var(--violet) / .35); }
.page-btn.disabled{ opacity: .4; pointer-events: none; }
.page-ellipsis{ color: var(--muted); font-size: .9rem; padding: 0 4px; font-family: 'JetBrains Mono', monospace; }

/* Category bulk actions — ported from production's .cat-bulk-actions */
.cat-bulk-actions{ display: flex; gap: 10px; justify-content: center; margin: 24px 0 8px; flex-wrap: wrap; }
.cat-bulk-btn{
  font-size: .82rem; font-weight: 700; font-family: 'Plus Jakarta Sans','Sora',sans-serif; padding: 9px 20px;
  border-radius: 12px; border: none; background: #22c55e; color: #fff; text-decoration: none;
  cursor: pointer; box-shadow: 0 4px 14px rgba(34,197,94,.35);
  transition: transform .2s cubic-bezier(.25,.46,.45,.94), box-shadow .2s ease;
}
.cat-bulk-btn:hover{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(34,197,94,.45); }
.cat-bulk-btn-secondary{ background: rgb(var(--violet) / .1); border: 1px solid rgb(var(--violet) / .2); color: var(--text); box-shadow: none; }
.cat-bulk-btn-secondary:hover{ background: rgb(var(--violet) / .16); box-shadow: none; }
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_pages.py -v`
Expected: PASS (all).

- [ ] **Step 8: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 9: Manual browser verification (required — real interaction, no Python-testable surface)**

Real Playwright session against a live dev server with real seeded data
and a real authenticated test account with mixed progress:
- Hover a word card and confirm the reveal panel actually shows
  (computed `opacity`/`transform`, not just class presence) with correct
  definition/synonyms/antonyms/example content.
- Click a card's own progress toggle and confirm it round-trips (reload
  the page, confirm the state persisted) without affecting other words.
- Click through numbered pagination on a category with 50+ words; confirm
  page-2+ content differs from page 1 and the active page button matches.
- Click "Mark All Completed" on a real multi-word category; confirm every
  word card now shows the learned state after reload, and a DIFFERENT
  category's own progress (seeded beforehand) is unaffected.
- Click "Reset All"; confirm every word in that category reverts to
  not-learned after reload.
- Both themes.

- [ ] **Step 10: Commit**

```bash
git add config/views_vocab.py templates/vocab/category_word_list.html \
  static/css/vocab.css static/js/i18n.js tests/test_vocab_pages.py
git commit -m "feat(vlpe): retrofit category word-list page with hover-reveal cards"
```

---

### Task 6: Word detail page retrofit

**Files:**
- Modify: `config/views_vocab.py`
- Modify: `templates/vocab/word_detail.html`
- Modify: `static/css/vocab.css`
- Modify: `tests/test_vocab_pages.py`

**Interfaces:**
- Consumes: `.cefr-badge` CSS (Task 2).
- Produces: nothing consumed by later tasks — this is this plan's final task.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_vocab_pages.py`:

```python
@pytest.mark.django_db
def test_vocabulary_word_detail_shows_cefr_badge(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(word='Cat', definition='x', category=category, order=1, cefr_level=cefr_a1)
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    html = r.content.decode()
    assert f'cefr-badge {cefr_a1.code}' in html


@pytest.mark.django_db
def test_vocabulary_word_detail_synonym_links_to_real_word(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    feline = Word.objects.create(word='Feline', definition='cat-like', category=category, order=1)
    word = Word.objects.create(
        word='Cat', definition='x', synonyms=['Feline'], antonyms=[],
        category=category, order=2,
    )
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    html = r.content.decode()
    assert f'href="/vocabulary/word/{feline.pk}/"' in html
    assert 'Feline' in html


@pytest.mark.django_db
def test_vocabulary_word_detail_synonym_without_match_renders_plain_text(cefr_a1):
    category = Category.objects.create(slug='animals', name='Animals', order=1, cefr_level=cefr_a1)
    word = Word.objects.create(
        word='Cat', definition='x', synonyms=['NotARealWordEntry'], antonyms=[],
        category=category, order=1,
    )
    c = Client()
    r = c.get(f'/vocabulary/word/{word.pk}/')
    html = r.content.decode()
    assert 'NotARealWordEntry' in html
    assert f'>NotARealWordEntry<' not in html.replace('<a ', '').replace(f'href="', '')  # crude but: no stray <a> around it
    # More precise: no anchor tag wraps this specific text
    import re
    assert not re.search(r'<a[^>]*>NotARealWordEntry</a>', html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_vocab_pages.py -k "vocabulary_word_detail_shows_cefr_badge or vocabulary_word_detail_synonym" -v`
Expected: FAIL — current `word_detail.html` shows no CEFR badge and
synonyms/antonyms are always plain comma-joined text.

- [ ] **Step 3: Extend `config/views_vocab.py`'s `vocab_word_detail`**

Change:
```python
@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    return render(request, 'vocab/word_detail.html', {
        'word': word,
        'learn_state': learn_state,
    })
```
to:
```python
def _resolve_word_refs(strings):
    resolved = []
    for text in strings:
        match = Word.objects.filter(word__iexact=text).first()
        resolved.append({'text': text, 'word': match})
    return resolved


@ensure_csrf_cookie
def vocab_word_detail(request, pk):
    word = get_object_or_404(
        Word.objects.select_related('category', 'cefr_level'), pk=pk
    )
    learn_state = None
    if request.user.is_authenticated:
        learn_state = request.user.learn_map.get(str(word.pk))
    return render(request, 'vocab/word_detail.html', {
        'word': word,
        'learn_state': learn_state,
        'synonym_refs': _resolve_word_refs(word.synonyms),
        'antonym_refs': _resolve_word_refs(word.antonyms),
    })
```

- [ ] **Step 4: Rewrite `templates/vocab/word_detail.html`**

```html
{% extends "base.html" %}
{% load static %}
{% block title %}{{ word.word }} — VocabLarry{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/vocab.css' %}">{% endblock %}
{% block content %}
<section class="vocab-word-detail">
  <p class="vocab-breadcrumb">
    <a href="{% url 'vocabulary_category_list' %}">Vocabulary</a> /
    <a href="{% url 'vocabulary_category_detail' word.category.slug %}">{{ word.category.name }}</a> /
    {{ word.word }}
  </p>
  <div class="word-detail-card" style="--accent-c:{% if word.cefr_level %}var(--{{ word.cefr_level.code|lower|cut:"+" }}{% if '+' in word.cefr_level.code %}p{% endif %}){% else %}rgb(var(--violet)){% endif %};">
    <div class="word-detail-header">
      <div>
        <h1>{{ word.word }}</h1>
        {% if word.pos %}<div class="vocab-pos">{{ word.pos }}</div>{% endif %}
      </div>
      {% if word.cefr_level %}<span class="cefr-badge {{ word.cefr_level.code }}">{{ word.cefr_level.code }}</span>{% endif %}
    </div>
    <p class="vocab-definition">{{ word.definition }}</p>
    {% if synonym_refs %}
    <p class="vocab-synonyms"><strong>Synonyms:</strong>
      {% for ref in synonym_refs %}{% if ref.word %}<a class="word-xref" href="{% url 'vocabulary_word_detail' ref.word.pk %}">{{ ref.text }}</a>{% else %}{{ ref.text }}{% endif %}{% if not forloop.last %}, {% endif %}{% endfor %}
    </p>
    {% endif %}
    {% if antonym_refs %}
    <p class="vocab-antonyms"><strong>Antonyms:</strong>
      {% for ref in antonym_refs %}{% if ref.word %}<a class="word-xref" href="{% url 'vocabulary_word_detail' ref.word.pk %}">{{ ref.text }}</a>{% else %}{{ ref.text }}{% endif %}{% if not forloop.last %}, {% endif %}{% endfor %}
    </p>
    {% endif %}
    {% if word.example %}<p class="vocab-example">"{{ word.example }}"</p>{% endif %}
    {% if user.is_authenticated %}
    <div class="learn-state-row">
      <span class="learn-state-label">Progress:</span>
      <button type="button" class="learn-state-btn" data-word-id="{{ word.pk }}"
              data-state="{{ learn_state|default:'none' }}">
        {% if learn_state == 'learned' %}Learned{% elif learn_state == 'little' %}Little Bit{% else %}Not Learned{% endif %}
      </button>
    </div>
    {% endif %}
  </div>
</section>
{% endblock %}
{% block extra_body %}
{% if user.is_authenticated %}
<script src="{% static 'js/vocab-word.js' %}" defer></script>
{% endif %}
{% endblock %}
```

**Note on the CEFR accent color inline style:** the `{{ word.cefr_level.code|lower|cut:"+" }}`
expression handles converting e.g. `"B2+"` to CSS var name `--b2p` and
`"B2"` to `--b2` — this is fragile string manipulation inside a template
attribute and the implementer should verify it renders correctly for all
12 codes during Step 6's browser check (test explicitly with an A1, an
A1+, a C2+ word). If it proves too fragile in practice, an acceptable
fallback (still matching the spec's intent) is computing the CSS var name
in the view instead (`word.cefr_var_name = code.lower().replace('+', 'p')`)
and passing it as plain context rather than doing the string
transformation in the template — prefer this cleaner approach if the
template-filter chain causes any rendering issues.

- [ ] **Step 5: Append word-detail CSS to `static/css/vocab.css`**

Append to the end of the file:

```css

/* Word detail — card container matching production's modal content */
.word-detail-card{
  position: relative; max-width: 480px; margin: 24px 0 48px;
  background: var(--card-bg); border-radius: 24px; overflow: hidden;
  border-top: 4px solid var(--accent-c, rgb(var(--violet)));
  border-left: 1px solid rgb(var(--violet) / .25); border-right: 1px solid rgb(var(--violet) / .25);
  border-bottom: 1px solid rgb(var(--violet) / .25);
  box-shadow: 0 32px 80px rgba(0,0,0,.25);
  padding: 24px 24px 28px;
}
.word-detail-header{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.word-detail-header h1{ font-size: 1.8rem; font-weight: 800; font-family: 'Plus Jakarta Sans','Sora',sans-serif; color: var(--accent-c, rgb(var(--violet))); line-height: 1.1; margin: 0; }
.word-xref{ color: rgb(var(--violet)); font-weight: 700; text-decoration: underline; text-decoration-style: dotted; text-underline-offset: 2px; }
.word-xref:hover{ text-decoration-style: solid; }
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_vocab_pages.py -v`
Expected: PASS (all).

- [ ] **Step 7: Run the full suite**

Run: `python -m pytest tests -v`
Expected: all pass.

- [ ] **Step 8: Manual browser verification (required — CSS custom-property computation, no Python-testable surface for visual correctness)**

Real Playwright session against a live dev server:
- Load word detail pages for words at several different CEFR levels
  (including at least one `+` level, e.g. B2+) and confirm via
  `getComputedStyle` that the card's top border color actually resolves to
  the right CEFR color, not falling through to the violet default due to a
  template-string bug (the exact risk flagged in Step 4's note).
- Confirm a synonym/antonym that resolves to a real word renders as a
  real clickable link, and clicking it navigates to that word's own page.
- Confirm a synonym/antonym with no match renders as plain text.
- Both themes.

- [ ] **Step 9: Commit**

```bash
git add config/views_vocab.py templates/vocab/word_detail.html \
  static/css/vocab.css tests/test_vocab_pages.py
git commit -m "feat(vlpe): retrofit word detail page to match production's modal content"
```
