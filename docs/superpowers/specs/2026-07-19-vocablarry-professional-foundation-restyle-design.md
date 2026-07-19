# VocabLarry Professional Environment — Foundation Restyle (design)

## Context

Every VLPE sub-project so far (Foundation through Dashboard, all merged)
focused on functional parity with production — routes, forms, quiz logic,
access control — using a deliberately minimal starter stylesheet
(`static/css/base.css`: system sans-serif stack, flat nav, plain bordered
buttons, no icons, no texture, generic color tokens). Production
(`VocabLarry/vocablarry.html`) has a much more developed "luxury restyle"
design system — Fraunces italic serif accents, a three-font type system,
mono-spaced letter-spaced eyebrow labels, a film-grain texture + violet
ambient glow, an inline SVG icon sprite including a parrot mascot, pill
nav with an active-state fill, and card-based stat/content components.
This gap was never a planning gap — visual restyle was simply never a
phase on the original roadmap, which only covered Foundation/Vocab/
Grammar/Dashboard functionality. This is the first of what will likely be
several restyle sub-projects (Foundation → Vocab pages → Grammar pages →
Quiz play/results, mirroring how the functional build itself was
decomposed), starting with the shared chrome (fonts, color tokens,
texture, nav) and the home page, since everything else inherits from it.

**Decided during brainstorming:** match production's design system
exactly (same fonts, palette, components, mascot) rather than a fresh
take — VLPE should become visually indistinguishable from production
where they overlap, just server-rendered instead of a SPA. All values
below were extracted directly from `vocablarry.html`'s actual CSS/markup,
not approximated from the screenshot.

## Decisions

- **Global tokens ported from production, not invented:**
  - Colors (dark theme, VLPE's default per its existing
    `prefers-color-scheme`/`[data-theme]` pattern): `--bg:#0b0d12`,
    `--surface:#12151d`, `--border:#232937`, `--text:#eceef4`,
    `--muted:#98a0b3`, `--gold:#d4af6a` (`--gold-rgb:212 175 106`),
    `--vio` (renamed from VLPE's existing `--violet` to match production's
    exact name/value): `124 58 237` — **this changes VLPE's current
    violet from `109 40 217` to production's actual value**, a real,
    intentional color shift as part of "match exactly," not a typo.
  - Colors (light theme, VLPE's existing `[data-theme="light"]`):
    `--bg:#f6f5f2`, `--surface:#ffffff`, `--border:#dcd7cc`,
    `--text:#16181d`, `--muted:#585d68`, `--gold:#b08a3e`
    (`--gold-rgb:176 138 62`).
  - `--card-bg`/`--card-border` keep VLPE's existing naming but take
    production's values (`--surface`/`--border` are the same values under
    a different name in production — VLPE already has `--card-bg` doing
    this job, just re-pointed to the ported values).
  - `--serif:'Fraunces',Georgia,serif;` and `--ease-luxe:cubic-bezier(.22,1,.36,1);`
    ported verbatim — both used by the hero/stat-card treatments below.
  - **Not ported in this phase:** the CEFR/tag/gram tier color tokens
    (`--a1`/`--a2`/`--b1`/`--b2`/`--c1`/`--c2`, `--t*`, `--gram-*`) —
    these belong to Vocab/Grammar-specific components that don't exist in
    this phase's scope. Add them when the sub-project that actually
    consumes them is built, matching this whole rebuild's established
    YAGNI discipline (no prior sub-project ever added CSS ahead of the
    component that needed it).
- **Fonts: the same 3-family system**, added via the same Google Fonts
  `<link>` production uses (`Sora:wght@400;600;700;800`,
  `Inter:wght@400;500;600;700`,
  `Plus+Jakarta+Sans:wght@400;500;600;700;800`,
  `JetBrains+Mono:wght@400;700`,
  `Fraunces:ital,opsz,wght@1,9..144,400..600`) — added to `base.html`'s
  `<head>`, not per-page, since every page needs at least the heading/body
  fonts. `body` gets `font-family:'Inter',sans-serif` (replacing the
  current system-font stack); `h1,h2,h3,.brand,.btn` get
  `'Plus Jakarta Sans','Sora',sans-serif`; a new `.eyebrow` utility class
  gets `'JetBrains Mono',monospace` with the exact letter-spacing/
  transform production uses.
- **Film grain + ambient glow, ported verbatim as global `body::before`/
  `body::after` pseudo-elements** — the SVG `feTurbulence` noise data-URI
  and the two-radial-gradient glow, both already self-contained CSS with
  no JS dependency, applied once in `base.css` so every page inherits
  them automatically (this is exactly how production applies them too —
  a single global rule, not per-page).
- **Icon sprite: a new inline `<svg style="display:none">` sprite in
  `base.html`**, containing only the symbols this phase's markup actually
  references (`i-mark` the parrot mascot, `i-moon`/`i-sun` theme toggle,
  `i-globe` language toggle, `i-check-circle`/`i-folder`/`i-bar-chart`
  for the stat cards, `i-grad-cap` for the hero eyebrow badge) — not
  production's full ~90-icon sprite, which covers category icons and
  other not-yet-restyled surfaces. More symbols get added by whichever
  future restyle phase first needs them, same YAGNI reasoning as the
  color tokens above.
- **Nav**: brand gains the mascot icon before the wordmark
  (`<svg class="ico ico-mark"><use href="#i-mark"/></svg>`, matching
  production's exact markup). Nav links become pill-shaped tabs
  (`.tab` class, ported verbatim: transparent/muted by default, violet-
  tinted hover, solid violet fill + white text + glow shadow when
  `.active` — "active" determined server-side per the current URL, e.g.
  `request.resolver_match.url_name`, since VLPE has real page navigation
  unlike production's client-side view-swapping single-page tabs).
  Theme/language toggles become icon-only buttons (`i-moon`/`i-sun`,
  `i-globe`) replacing today's plain-text "Theme"/"EN/VI" buttons — the
  theme toggle's icon still needs to swap moon↔sun on click, which
  `static/js/base.js` (unmodified logic, just swapping which element gets
  updated) already has a hook for via its existing theme-toggle handler.
- **Home hero**: full port of production's `.home-hero` treatment — grid-
  line background (`.home-grid-bg`, a repeating 40px linear-gradient
  grid, violet at 6% opacity), a centered radial glow (`.home-glow`), an
  eyebrow badge with icon (`.home-badge`, mono/uppercase/letter-spaced,
  e.g. "IELTS PREPARATION · BAND 5–9" equivalent copy for VLPE), a two-
  line `<h1>` where the second line is Fraunces italic violet
  (`.home-grad`), an italic serif subtitle (`.home-sub`), and pill CTA
  buttons (existing `.btn`/`.btn-primary` plus a new `.home-btn-outline`
  variant for the secondary action) — copy stays what VLPE already has
  ("Master every word, say it till it stays." / "Practice Grammar" etc.),
  only the visual treatment changes.
- **"Your Progress" stat board: 3 real stats, no streak card** (per your
  decision) — Words Learned, Categories Started, % Complete, each
  computed server-side in the `home` view exactly matching production's
  own definitions (verified against `vocablarry.html`'s `updateHome()`):
  - `words_learned` = count of `learn_map` entries whose value is exactly
    `'learned'` (the `'little'` state does NOT count, matching production
    precisely — a common point of confusion since both states show
    *some* progress, but only `'learned'` counts toward this stat).
  - `categories_started` = count of distinct `Category` rows that have
    at least one word with *any* `learn_map` entry (`'learned'` OR
    `'little'` both count as "started" — this is the one place the two
    states are NOT distinguished, again matching production exactly).
  - `pct_complete` = `round(words_learned / total_word_count * 100)`,
    `0` if there are no words (defensive, unreachable with real data but
    matches production's own `total ? ... : 0` guard).
  - **Rendered unconditionally, not auth-gated** — matches production's
    own behavior exactly: `learn_map` defaults to `{}` for a guest (same
    pattern every other VLPE view already uses), which naturally
    computes to `0`/`0`/`0%` rather than requiring a separate hidden/
    shown branch. This is simpler than an auth-gate and is what
    production actually does.
  - Stat cards (`.home-stats`/`.home-stat`/`.home-stat-ico`/
    `.home-stat-val`/`.home-stat-lbl`) ported verbatim: translucent
    backdrop-blur card, icon chip, large bold number, mono-spaced
    uppercase label, hover lift. A `.home-section-hd` eyebrow
    ("YOUR PROGRESS") with a trailing rule line precedes the grid,
    also ported verbatim.
- **No JS behavior changes** — `static/js/base.js`'s theme-toggle
  logic is reused as-is (only the icon swap target changes, from a text
  button's label to an `<svg><use>` element's `href`); no new client-side
  code is needed anywhere in this phase, since the stat numbers are
  computed server-side at render time, not live-updated.

## Architecture

```
templates/
  base.html            (add font <link>, icon sprite, mascot in brand)
  partials/
    nav.html            (pill tabs w/ active state, icon toggles)
  home.html              (hero + stat board markup)
config/
  views.py               (home() computes the 3 stats)
static/
  css/
    base.css              (ported tokens, fonts, grain/glow, nav pills,
                            home hero + stat card styles)
tests/
  test_home_page.py     (new — stat computation correctness)
```

## Components

- **`templates/base.html`** — adds the Google Fonts `<link>` (production's
  exact URL, all 5 families), the icon `<svg><symbol>` sprite (7 symbols,
  scoped per Decisions), and the mascot `<use>` reference inside
  `.brand`. `color-scheme` meta/attribute handling stays as VLPE's
  existing theme-toggle mechanism already does it — no change to the
  toggle's underlying logic, only its visual button.
- **`templates/partials/nav.html`** — each `<li><a>` gains `.tab` (plus
  `.active` when `request.resolver_match.url_name` is in that link's own
  section — VLPE's nav has no separate "Home" tab (the brand logo is the
  only home link, unchanged), so exactly 4 links need this treatment:
  **Vocabulary** active on `vocab_browse`/`vocab_category`/
  `vocab_word_detail`; **Quiz** active on `vocab_quiz_setup`/
  `vocab_quiz_play`; **Grammar** active on `grammar_browse`/
  `grammar_topic_detail`/`grammar_topic_quiz`; **Grammar Test** active on
  `grammar_test_setup`/`grammar_test_play`. This mirrors how production's
  own SPA tab stays highlighted across its whole section, adapted to
  VLPE's real per-page routing. Theme/lang toggle buttons swap their
  text content for the icon markup.
- **`config/views.py`'s `home(request)`** — extended to compute and pass
  `words_learned`, `categories_started`, `pct_complete` into the
  template context, reading `request.user.learn_map` (defaulting to `{}`
  for guests, matching the established pattern from every other VLPE
  view that reads this field).
- **`templates/home.html`** — restructured to the `.home-hero` +
  `.home-content` > `.home-stats` shape described in Decisions, keeping
  existing `data-i18n` keys/copy where they already exist, adding new
  ones only for the eyebrow badge and stat labels (which need Vietnamese
  translations added to `static/js/i18n.js` alongside, matching this
  codebase's existing i18n convention).
- **`static/css/base.css`** — the single file gaining all of the above:
  token block, font-family rules, grain/glow pseudo-elements, `.eyebrow`
  utility, `.tab`/`.tab.active` nav styles, `.home-*` hero and stat-card
  rules.

## Data flow

`GET /` → `home(request)` reads `request.user.learn_map` (or `{}` for a
guest) and `Word`/`Category` querysets already used elsewhere in this
codebase → computes the 3 stats → renders `home.html` with them baked
into the initial HTML (no client-side fetch, no JS computation — this is
simpler than production's own client-side `updateHome()`, since VLPE
already has the data server-side at render time and doesn't need a
separate API round-trip the way the SPA does).

## Error handling

No new error states. `pct_complete`'s zero-total-words guard is the only
defensive branch, and it's unreachable with real seeded data (this
repo always has ~5000 words) — included only because production's own
code has the same guard and it costs nothing to match.

## Testing

Python: a new `tests/test_home_page.py` asserting the 3 stats render
correctly for a fresh guest (`0`/`0`/`0%`), for an authenticated user
with a mix of `'learned'`/`'little'` states across words in multiple
categories (confirming `'little'` counts toward categories-started but
NOT toward words-learned — the one subtle asymmetry worth a dedicated
test), and confirming the pill-active nav state lands on the correct
link for at least the home/vocab/grammar pages. Manual: a real browser
comparison against the production screenshot already taken during
brainstorming — confirm the font rendering, texture, nav pill states,
hero layout, and stat cards visually match across both themes (light
"gallery" and dark), and confirm the theme/language toggle icons still
function (swap correctly on click) now that they're icon-only buttons
rather than labeled text buttons.

## Explicitly out of scope for this phase

Every other page's visual restyle (Vocab browse/category/word/quiz,
Grammar browse/topic/quiz/test, auth pages, Dashboard — Dashboard
explicitly stays on its own separate Bootstrap identity per the earlier
Dashboard sub-project's own decision) — each becomes its own future
restyle sub-project once this shared foundation exists. The day-streak
stat (needs new activity-tracking data, not just visual work — a
possible small separate feature later, not a restyle task). Production's
CEFR/tag/gram tier color tokens and the rest of its ~90-icon sprite
(added incrementally by whichever future phase first needs them).
Vietnamese translation of any *new* prose copy beyond what's needed for
this phase's own new `data-i18n` keys (eyebrow badge, stat labels).
