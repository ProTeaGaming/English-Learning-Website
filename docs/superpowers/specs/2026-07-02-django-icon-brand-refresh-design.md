# Django Vocab Master — Icon & Brand Refresh

**Date:** 2026-07-02
**Scope:** `ielts-vocab-master/Python/Django/vocab-master.html` only. Shared data files untouched.

## Problem

The app's "logo" surfaces are raw emoji (📚 brand, 📚✏️📖📝🎧🎤 section cards, 🌱📈🎓📊 level buttons, 🌙/☀ theme toggle, 🔄 reset, category icons, etc.) plus a violet→green gradient wordmark. Full-color emoji ignore the violet theme palette and read as AI-generated filler. The 🔥 streak is the one emoji that works and stays.

## Design

### Icon system
- One inline SVG sprite (`<svg style="display:none"><symbol id="i-…" viewBox="0 0 24 24">…</symbol>…</svg>`) at the top of `<body>`.
- All icons: 24×24 grid, 1.75px stroke, round caps/joins, `stroke="currentColor"`, no fill.
- Used as `<svg class="ico"><use href="#i-book"/></svg>`; `.ico` CSS class sets size `1em`/em-relative and `vertical-align`.
- Icons inherit theme colors (light/dark, violet accent) automatically via `currentColor`.

### Brand
- Custom mark: open-book glyph with a center-spine upward tick, solid `var(--accent)`.
- Wordmark: `IELTS` in normal text color, `Vocab Master` solid violet accent, weight 800. **No gradient.** Same in topbar and footer.

### Emoji → icon mapping
| Surface | Now | New sprite id |
|---|---|---|
| Brand/footer | 📚 | `i-mark` (custom book-tick) |
| Sections | 📚 ✏️ 📖 📝 🎧 🎤 | `i-book` `i-pen` `i-book-open` `i-file-text` `i-headphones` `i-mic` |
| Levels | 🌱 📈 🎓 📊 | `i-sprout` `i-trend-up` `i-grad-cap` `i-bar-chart` |
| Home stats | 📂 📊 | `i-folder` `i-bar-chart` |
| Home badge | 🎓 | `i-grad-cap` |
| Theme toggle | 🌙/☀ | `i-moon`/`i-sun` (JS swaps `<use>` href) |
| Reset | 🔄 | `i-rotate` |
| Search `::before` | 🔍 | magnifier via CSS `mask-image` data-URI tinted by theme |
| Password toggle | 👁/🙈 | `i-eye`/`i-eye-off` |
| Chat avatar | 🤖 | `i-bot` in tinted circle |
| Under construction | 🚧 | `i-hard-hat` |
| CEFR | 🌱⭐🦋🦅🏆🎯🔮 | sprout, star, butterfly, bird, trophy, target, gem |
| Data categories | 🧠🔥🔍📉💪🎭🌐⭐ | brain, flame, search, trend-down, dumbbell, masks, globe, star |
| Streak (card + home stat) | 🔥 | **unchanged** |

### Shared data compatibility
`data/data-part1.js` category `icon` fields stay emoji (Flask/PHP/React depend on them). Django page adds `EMOJI_ICON_MAP = { "🧠": "i-brain", … }` and a helper that resolves an emoji to sprite markup at render time, falling back to `i-book` for unknown emoji. Every JS sink that injects `cat.icon` as text switches to the helper.

### Out of scope
- Conversational emoji inside chat message strings and share text (copy, not iconography).
- ✓/✗ typographic marks.
- Flask/PHP/React ports (later, separately).

## Verification
Run the Django server, load the app, toggle light/dark, click through Home, Category, Word, Test, auth modal. Confirm all icons render, tint correctly in both themes, and JS-swapped icons (theme, password, category header) still switch.
