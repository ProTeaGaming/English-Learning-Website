# VocabLarry Professional Environment — Nav & Routing Skeleton (design)

## Context

Functional parity (Foundation → Vocab → Grammar → Dashboard) and a first
visual-restyle pass (shared chrome + Home) are both done. The user then
pushed back on two fronts at once: (1) VLPE's independently-designed
per-page visuals still aren't as good as production's, and going forward
VLPE should **copy production's designs/functions directly** rather than
re-derive them (the source of the earlier `rgba(var(--violet))` bug); and
(2) VLPE's information architecture should match production's real
structure — a dropdown-style Vocabulary/Grammar nav with Category/Word/
Quiz sub-pages at real URLs (`/vocabulary/category`, `/vocabulary/word`,
`/vocabulary/quiz`, same shape for Grammar), plus the four still-missing
Reading/Listening/Speaking/Writing placeholder sections production already
has.

This is too large for one spec, so it was decomposed (user-approved) into
four sub-projects, built in this order:

1. **This spec — nav & routing skeleton.** URL rename, dropdown nav,
   two brand-new intro pages, six new stub pages (Reading/Listening/
   Speaking/Writing placeholders + the two new "Word" pages, which get
   routes registered now but stubbed content this phase).
2. Vocabulary Word page (sitewide word browse) — real content.
3. Grammar Word page (reference: irregular verbs/comparisons/linkers) —
   real content.
4. Visual retrofit of the *existing* Vocab/Grammar/Quiz pages' CSS to
   copy production's exactly (separate from this phase — this phase's
   two brand-new intro pages and four stub pages use VLPE's *current*
   restyled chrome, not a preview of phase 4's retrofit).

**VLPE is not deployed anywhere and has no external inbound links**, so
this phase renames URLs outright — no backwards-compatibility redirects
from the old `/vocab/...`/`/grammar/topic/...`/`/grammar/test/...` paths.

## Decisions

- **Full URL rename**, not additive routes. Every existing `{% url %}`
  reference, every `reverse()`/`redirect()` call, and every test's
  `reverse('vocab_browse')`-style reference must be updated to the new
  names below — this touches `config/urls.py`, `config/views_vocab.py`,
  `config/views_grammar.py`, `api/write_views.py`, `dashboard/views.py`,
  and `tests/test_pages.py` / `test_vocab_pages.py` / `test_grammar_pages.py`
  / `test_dashboard_pages.py` / `test_debug_api.py` (all confirmed via
  grep to reference the old names).
- **New URL name convention: every Vocabulary page's name starts with
  `vocabulary_`, every Grammar page's name starts with `grammar_`.** This
  isn't just cosmetic — it's what makes the nav active-state check (see
  below) maintainable as a prefix match instead of an ever-growing
  hand-enumerated OR list (today's `nav.html` already does the latter for
  4 names; this phase adds 7 more).
- **Nav active-section as a context processor, not per-view context.**
  Rather than adding an `active_section` variable to 15+ existing and new
  views, a small context processor derives it once from
  `request.resolver_match.url_name`: strips the trailing page-specific
  part and matches against a static `{"vocabulary": "vocabulary", "grammar":
  "grammar", "reading": "reading", ...}`-style prefix table. `nav.html`
  then does one `{% if nav_active_section == "vocabulary" %}` per
  top-level tab instead of a growing OR chain.
- **Intro pages are a genuine VLPE-only addition — production has no
  equivalent.** Production's own "Vocabulary"/"Grammar" tab click jumps
  straight to Category; this spec deliberately diverges (per your
  request) so the tab click lands on a topic-specific intro page first.
  Content: a hero (headline + subtitle text specific to that skill) + 3
  clickable cards linking to Category/Word/Quiz — no stats (declined
  during brainstorming), reusing Home's existing `.home-hero`/card
  visual language, not new CSS patterns. Hero copy itself isn't
  prescribed here — the implementer writes skill-specific headline/
  subtitle text following Home's existing tone (see `home.title1`/
  `home.title2`/`hero.subtitle` in `i18n.js` as the reference voice),
  reviewed for fit at task-review time same as any other new
  user-facing copy in this project.
- **Home's own hero CTAs ("Start Learning" / "Practice Grammar") keep
  bypassing the intro pages** and link directly to the Category page
  (`vocabulary_category_list` / `grammar_category_list`) — only their
  `{% url %}` target names change, not their destination semantics. This
  matches production's existing behavior for those two specific buttons
  and avoids adding an extra click to the already-established "jump
  straight into browsing" home flow.
- **Dropdown nav replicates production's exact interaction**, not a new
  invention: clicking an inactive top-level tab (Vocabulary/Grammar)
  navigates to that section's intro page and closes any open dropdown;
  clicking the tab while it's already active toggles the dropdown open/
  closed (showing Category/Word/Quiz); clicking outside any nav-group
  closes open dropdowns. Ported from production's `goToPage`/
  `.tab[data-section-btn]` click-handler logic, adapted from production's
  single-page section-swap model to VLPE's real per-page navigation (a
  dropdown item is a plain `<a href>`, not a JS page-swap call).
- **Mobile nav: full parity with production**, per your explicit choice.
  Two pieces, both ported: (1) the hamburger (`#mobileNavChip` /
  `#mobileNavToggle` / `#mobileNavMenu`) replacing the desktop nav-links
  row below the breakpoint, listing all 7 top-level sections flat (no
  nesting — tapping Vocabulary/Grammar goes to the intro page, same
  deviation as desktop); (2) each Category/Word/Quiz page (for both
  Vocabulary and Grammar) renders production's `.mobile-page-switcher`
  chip row (Category/Word/Quiz) at the top of its content on small
  screens, for lateral navigation between siblings without returning to
  the hamburger menu. Confirmed against production's actual markup: the
  chip row appears on Category, Word, and the entire Quiz flow (setup +
  play are one continuous container in production). **Scope for this
  spec: the chip row appears only on the 3 dropdown-linked landing pages
  per section** — `vocabulary_category_list`, `vocabulary_word_list`,
  `vocabulary_quiz_setup` **and** `vocabulary_quiz_play` (both setup and
  play carry it, since VLPE splits what production treats as one
  container), and the grammar equivalents
  (`grammar_category_list`/`grammar_word`/`grammar_quiz_setup`/
  `grammar_quiz_play`). It does **not** appear on deeper drill-in pages
  that have no production-page equivalent at all
  (`vocabulary_category_detail`, `vocabulary_word_detail`,
  `grammar_category_detail`, `grammar_category_quiz`) — those are VLPE-
  only real pages one level below the 3 dropdown destinations, not
  additional siblings to switch between. The two new intro pages also do
  **not** get this chip row (nothing to switch away from — matches
  production, which has no intro page to add one to either).
- **Reading/Listening/Speaking/Writing: four new flat top-level nav
  tabs** (no dropdown, no intro-page pattern — they're single pages),
  each rendering production's exact minimal shape: an eyebrow line
  (`Section NN / <Name>`), an `<h1>`, and a single `<p>Coming soon.</p>`.
  Section numbering follows production's own ordering (Vocabulary 01,
  Grammar 02, Reading 03, Writing 04, Listening 05, Speaking 06 — matches
  production's literal `Section 03 / Reading` etc. markup found in
  `vocablarry.html`).
- **`/vocabulary/word/` and `/grammar/word/` are real registered routes
  with stub content this phase**, not deferred/unregistered — same
  forward-reference-avoidance pattern this project always uses (see
  project memory's "stub route" rule): register now at the exact path
  the later sub-project will fill in, so the dropdown's Word link is
  never a dead/`NoReverseMatch` link. Stub content matches the
  Reading/Listening/Speaking/Writing pattern (eyebrow + h1 + "Coming
  soon.") rather than inventing a different placeholder style.
- **No i18n content translation of anything new beyond chrome labels.**
  New `data-i18n` keys needed: `nav.category`, `nav.word`,
  `nav.reading`, `nav.writing`, `nav.listening`, `nav.speaking`, plus
  intro-page hero copy keys for both Vocabulary and Grammar (English +
  Vietnamese, matching every existing chrome string's dual-entry
  pattern in `static/js/i18n.js`). `nav.quiz` and `nav.grammarTest`
  already exist — `nav.grammarTest`'s string becomes unused chrome-label
  cruft once the flat "Grammar Test" tab is folded into the dropdown;
  remove it rather than leave a dead key.
- **No new models, no new migrations, no new backend endpoints of any
  kind.** This phase is pure routing/template/nav — every renamed page's
  underlying view logic (queries, context) is untouched, just moved to
  its new URL and (where applicable) new template location.

## Architecture

```
config/
  urls.py                 (full rewrite of the vocab/grammar url() block)
  context_processors.py   (new — nav_active_section)
  settings.py              (register the new context processor)
  views_vocab.py           (add vocabulary_home, vocabulary_word_list stub;
                            rename existing view functions' url names only
                            — function bodies unchanged)
  views_grammar.py         (add grammar_home, grammar_word stub; rename
                            existing view functions' url names only)
templates/
  vocab/
    home.html               (new — intro page)
    word_list.html          (new — stub, gets mobile chip row)
    browse.html               (now served at /vocabulary/category/,
                              gains mobile chip row)
    category_word_list.html   (unchanged content, unchanged nested path,
                               no chip row — see mobile-nav decision above)
    word_detail.html          (unchanged content, unchanged nested path,
                               no chip row)
    quiz_setup.html            (gains mobile chip row)
    quiz_play.html             (gains mobile chip row)
  grammar/
    home.html                (new — intro page)
    word.html                 (new — stub, gets mobile chip row)
    browse.html                (now served at /grammar/category/,
                                gains mobile chip row)
    topic_detail.html          (unchanged content, unchanged nested path,
                                no chip row)
    topic_quiz.html             (unchanged content, unchanged nested path,
                                 no chip row — per-topic quiz is a drill-in,
                                 not a dropdown-linked landing page)
    test_setup.html → quiz_setup.html   (renamed file, gains chip row)
    test_play.html  → quiz_play.html    (renamed file, gains chip row)
  reading.html, writing.html, listening.html, speaking.html   (new — stubs)
  partials/
    nav.html                  (rewrite — dropdown groups, mobile chip menu)
static/
  js/
    nav.js                     (new — dropdown open/close + mobile chip
                                toggle logic, ported from production)
    i18n.js                     (add new keys, remove nav.grammarTest)
  css/
    base.css                    (extend — nav-group/dropdown/mobile-chip
                                 styles ported from production, plus
                                 shared `.page-stub` eyebrow/h1/p pattern
                                 for the 6 stub pages)
```

Routes (`config/urls.py`):

```python
path('vocabulary/', vocabulary_home, name='vocabulary_home'),
path('vocabulary/category/', vocabulary_category_list, name='vocabulary_category_list'),
path('vocabulary/category/<slug:slug>/', vocabulary_category_detail, name='vocabulary_category_detail'),
path('vocabulary/word/', vocabulary_word_list, name='vocabulary_word_list'),
path('vocabulary/word/<int:pk>/', vocabulary_word_detail, name='vocabulary_word_detail'),
path('vocabulary/quiz/', vocabulary_quiz_setup, name='vocabulary_quiz_setup'),
path('vocabulary/quiz/play/', vocabulary_quiz_play, name='vocabulary_quiz_play'),

path('grammar/', grammar_home, name='grammar_home'),
path('grammar/category/', grammar_category_list, name='grammar_category_list'),
path('grammar/category/<slug:slug>/', grammar_category_detail, name='grammar_category_detail'),
path('grammar/category/<slug:slug>/quiz/', grammar_category_quiz, name='grammar_category_quiz'),
path('grammar/word/', grammar_word, name='grammar_word'),
path('grammar/quiz/', grammar_quiz_setup, name='grammar_quiz_setup'),
path('grammar/quiz/play/', grammar_quiz_play, name='grammar_quiz_play'),

path('reading/', reading, name='reading'),
path('writing/', writing, name='writing'),
path('listening/', listening, name='listening'),
path('speaking/', speaking, name='speaking'),
```

Old-name → new-name map (for the implementer doing the mechanical rename):

| Old | New |
|---|---|
| `vocab_browse` | `vocabulary_category_list` |
| `vocab_category` | `vocabulary_category_detail` |
| `vocab_word_detail` | `vocabulary_word_detail` |
| `vocab_quiz_setup` | `vocabulary_quiz_setup` |
| `vocab_quiz_play` | `vocabulary_quiz_play` |
| `grammar_browse` | `grammar_category_list` |
| `grammar_topic_detail` | `grammar_category_detail` |
| `grammar_topic_quiz` | `grammar_category_quiz` |
| `grammar_test_setup` | `grammar_quiz_setup` |
| `grammar_test_play` | `grammar_quiz_play` |

## Components

- **`context_processors.nav_active_section`** — reads
  `request.resolver_match.url_name` (guarding `None`, e.g. during 404
  handling before resolution completes), matches it against a static
  prefix table (`vocabulary_*` → `"vocabulary"`, `grammar_*` →
  `"grammar"`, `reading`/`writing`/`listening`/`speaking`/`home` →
  themselves), returns `{"nav_active_section": <value or None>}`.
- **`templates/partials/nav.html`** — two `nav-group`s (Vocabulary,
  Grammar) each with a top-level `<a>` (href = that section's intro
  page) plus a `.nav-dropdown` of 3 items (Category/Word/Quiz, plain
  `<a href>`s to the real URLs — not JS page-swaps, since VLPE has real
  routing); 5 more flat top-level `<a>`s (Home already exists via brand
  link; Reading/Writing/Listening/Speaking new); the mobile hamburger
  block (`#mobileNavChip`) with its own flat 7-item menu; auth/theme/lang
  controls unchanged from today.
- **`static/js/nav.js`** — click handler on `.tab[data-section-btn]`-
  equivalent nav-group headers (toggle dropdown open when already
  `.active`, else follow the link normally — i.e. don't
  `preventDefault()` on the initial navigating click, only intercept the
  toggle-when-already-active case), a document-level click-outside
  handler to close open dropdowns, and the mobile chip open/close toggle
  — all adapted from production's `goToPage`/`data-section-btn`/
  `mobileNavToggle` handlers, minus anything that does client-side page
  swapping (not applicable here).
- **`templates/vocab/home.html`, `templates/grammar/home.html`** — hero
  section (reusing `.home-hero`-family classes) + a 3-card row (reusing
  Home's existing `.home-sec`/card CSS class, not new markup) linking to
  that skill's Category/Word/Quiz pages.
- **6 stub templates** (`reading.html`, `writing.html`, `listening.html`,
  `speaking.html`, `vocab/word_list.html`, `grammar/word.html`) — all
  share one new `.page-stub` CSS pattern: eyebrow + `<h1>` + "Coming
  soon." paragraph, matching production's literal markup shape.

## Data flow

Pure routing/template work — no new queries, no new writes, no new
client-server data exchange anywhere in this phase. The only "dynamic"
behavior added is nav dropdown open/close and mobile-menu toggle, both
pure client-side DOM state with no persistence (matches production,
which also doesn't persist dropdown-open state).

## Error handling

- No new URL parameters beyond what already exists on the unchanged
  nested detail pages (`vocabulary_category_detail`,
  `vocabulary_word_detail`, `grammar_category_detail`,
  `grammar_category_quiz`) — their existing `get_object_or_404` behavior
  is untouched.
- `nav_active_section`'s context processor must not raise if
  `request.resolver_match` is `None` (e.g. a 404) — return `None` in
  that case, and `nav.html`'s `{% if %}` chain simply matches nothing
  (no tab highlighted), matching how an unmatched URL renders today.

## Testing

Python tests (extend/rename within `test_pages.py`, `test_vocab_pages.py`,
`test_grammar_pages.py`, `test_dashboard_pages.py`, `test_debug_api.py`
wherever they `reverse()` an old name):

- Every renamed URL resolves and 200s at its new path; every old path
  (`/vocab/`, `/grammar/topic/...`, `/grammar/test/...`) is confirmed
  **gone** (404), proving the rename is real and not additive.
- The 6 new stub pages (`vocabulary_word_list`, `grammar_word`,
  `reading`, `writing`, `listening`, `speaking`) 200 and contain their
  expected eyebrow/h1 text.
- The 2 new intro pages (`vocabulary_home`, `grammar_home`) 200 and
  contain their 3 expected Category/Word/Quiz links (by resolved URL,
  not just link text) plus hero copy.
- `nav_active_section` context processor: a small direct unit test per
  representative URL name confirming the right section string (or
  `None` for an unmatched/404 case).
- Nav markup: for one representative page per section, confirm the
  correct top-level tab carries the active class/state and the correct
  dropdown (where applicable) is the one marked open-eligible — via
  rendered HTML class assertions, not JS execution.
- Home's hero CTAs still resolve to `vocabulary_category_list` /
  `grammar_category_list` (regression guard for the "CTAs bypass the
  intro page" decision).

No Python-testable surface for the dropdown/mobile-chip *interaction*
itself (open/close on click, click-outside-to-close) — the implementation
plan must include a real Playwright click-through per this project's
standing rule for anything touching client-side rendering/interaction:
desktop dropdown open on second click of an active tab, close on
outside click, each dropdown item actually navigating to its real URL;
mobile viewport hamburger open/close and each of its 7 items navigating
correctly; the `.mobile-page-switcher` chip row appearing (and
functioning) only on the 8 pages named in the mobile-nav decision above
(both Vocabulary and Grammar Category-list/Word/Quiz-setup/Quiz-play) at
a mobile viewport width, and confirmed absent on the two intro pages and
on the drill-in pages (category detail, word detail, topic detail,
per-topic quiz); both themes (light/dark) for all new markup, matching
this project's standing verification bar.

## Explicitly out of scope for this phase

Real content for the Vocabulary Word (sitewide browse) and Grammar Word
(reference) pages — sub-projects 2 and 3. Any visual retrofit of the
already-existing Category/Word-detail/Quiz pages' CSS to copy production
more closely — sub-project 4 (this phase's two new intro pages and six
stub pages use VLPE's current restyled chrome, not a preview of that
retrofit). Skill-specific stats on the intro pages (declined during
brainstorming — hero + cards only). Backwards-compatible redirects from
old URLs (VLPE has no external inbound links to preserve). Any change to
existing nested detail-page URLs' query/behavior beyond their path prefix
moving. Vietnamese translation of anything beyond new chrome labels.
