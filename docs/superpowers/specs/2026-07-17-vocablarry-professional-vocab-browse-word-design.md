# VocabLarry Professional Environment — Vocab Browse + Word (design)

## Context

This is sub-project 2a of the VocabLarry Professional Environment rebuild
(see `docs/superpowers/specs/2026-07-17-vocablarry-professional-foundation-design.md`
for the parent project's context and locked-in architecture decisions).
Foundation (sub-project 1, merged to `main`) built the project scaffold, a
branded home page, and a full server-rendered auth flow. Its home page nav
and hero currently mark "Vocabulary" and "Grammar" as disabled/coming-soon.

The production `VocabLarry/` SPA's vocabulary section is large: category
browse (250 categories, client-side grouped into 75 curated "sections" via
a JS-only lookup table — not backend data), a word list/detail view (5,000
words), and a genuinely large quiz engine (3 top-level modes — Quiz/Gap/
Challenge — with 5 submodes each for Quiz and Gap). That's too much for one
spec. This spec covers only **Browse + Word**: category browse and word
list/detail pages, including per-word progress tracking. The quiz engine
is a separate future sub-project (2b), built on top of this one.

## Decisions

- **No new Django app.** This pass only *renders* data the existing `vocab`
  app's models (`Category`, `Word`, `CEFRLevel`) already own — no new
  models or migrations. Routes are added directly in `config/urls.py`
  (mirroring Foundation's `home` view — a `views.py` per concern, not a
  full app scaffold, until there's enough vocab-specific logic to justify
  one).
- **Server-rendered pages query the ORM directly**, not the JSON `api/`
  endpoints. Those endpoints exist for the SPA and the future JS-driven
  quiz engine; a server-rendered page hitting its own JSON API over HTTP
  would be an unnecessary round-trip and isn't idiomatic Django. The one
  exception is the progress-toggle write (see below), which does reuse an
  existing endpoint because it's a real client-side interaction, not a
  page render.
- **Word detail is a dedicated page** (`/vocab/word/<id>/`), not a modal —
  consistent with Foundation's precedent (dedicated pages over overlays).
  Real URL, bookmarkable, works without JS for the read path.
- **Progress toggle is included in this pass** (not deferred to the quiz
  sub-project). The backend already supports it unchanged: `CustomUser.
  learn_map` (`accounts/models.py`) is a `JSONField` mapping
  `{"<word_id>": "little"|"learned"}` (key absent = not learned), read/
  written via the existing `/auth/sync/` endpoint
  (`accounts/views.py:sync`, `GET` returns `{'learn_map': ..., 'grammar_map':
  ...}`, `POST` accepts `{'learn_map': {...}}` and updates only that key).
  The word detail page's progress toggle is a small JS module
  (`static/js/vocab-word.js`) that `fetch()`s this same endpoint the SPA
  already uses — no new backend endpoint, matching Foundation's "reuse
  existing `api/`/`auth/` endpoints" pattern. Only shown/interactive for
  signed-in users; signed-out users see the word's content with no toggle.
- **Category grouping: flat grid, not the 75-section layer.** The current
  SPA's section grouping is presentation-only (a JS lookup table, not a
  `Category` field) — replicating it is pure UI work with no backend
  dependency, so it's deferred as a low-risk follow-up rather than blocking
  this pass. Browse shows all 250 categories in one grid, filterable by
  CEFR level (real backend data — `Category.cefr_level`) and a name search
  box.
- **Word/category content stays English-only.** The current SPA's
  Vietnamese translations for word definitions and category names are
  large lookup tables (`WORD_DEF_VI`, `CATEGORY_NAME_VI`) embedded in the
  monolith JS, keyed by id/slug — porting them is substantial, separable
  work. Foundation's UI-chrome `data-i18n` toggle (nav, buttons, filter
  labels, "no results" messages, etc.) still works on these new pages;
  only word/category *content* (definitions, names, examples) is
  English-only for now.
- **No US/UK dialect-based word substitution.** The current SPA's dialect
  preference affects which headword variant (US vs UK spelling) appears
  for certain word pairs. This pass renders whatever the `Word` record's
  canonical fields say, with no per-user substitution logic — same "defer
  content-shaping complexity" reasoning as the i18n decision above.
- **Pagination:** Django's built-in `Paginator`, 25 words per page (matches
  current SPA UX), `?page=N` query param.
- **Search/filter on browse:** server-side `icontains` filtering via query
  params (`?q=...` for name search, `?cefr=...` for CEFR level), not
  client-side JS — consistent with "server-rendered pages, plain JS only
  for real interactions" from Foundation.

## Architecture

```
config/
  urls.py         (add 3 routes under /vocab/)
  views.py        (add 3 view functions, or a views/vocab.py if it grows)
templates/
  vocab/
    browse.html            (category grid + CEFR chips + search)
    category_word_list.html (paginated word list for one category)
    word_detail.html        (word detail + progress toggle)
static/
  css/vocab.css   (category cards, CEFR chip styling, word list rows,
                    progress-toggle buttons)
  js/vocab-word.js (progress toggle: fetch() to /auth/sync/)
```

Routes:

```python
path('vocab/', vocab_browse, name='vocab_browse'),
path('vocab/category/<slug:slug>/', vocab_category, name='vocab_category'),
path('vocab/word/<int:pk>/', vocab_word_detail, name='vocab_word_detail'),
```

Home page's `templates/home.html` "Vocabulary" hero CTA and
`templates/partials/nav.html`'s "Vocabulary" nav entry (currently
`.disabled` spans marked "Coming soon") become real links to
`{% url 'vocab_browse' %}`.

## Components

- **`vocab_browse` view** — queries `Category.objects.select_related(
  'cefr_level', 'color').order_by('order')`, applies `?q=` (name
  `icontains`) and `?cefr=` (level code) filters if present, renders
  `browse.html`.
- **`vocab_category` view** — looks up `Category` by slug (404 if not
  found), queries its `words.order_by('order')`, paginates 25/page,
  renders `category_word_list.html`. Rows are plain links to
  `vocab_word_detail` — no progress indicator on this page; the toggle
  and any progress display live only on the word detail page, to keep
  this view's scope to "list and link," not duplicate state rendering.
- **`vocab_word_detail` view** — looks up `Word` by pk (404 if not found,
  `select_related('category', 'cefr_level')`), renders `word_detail.html`
  with definition/synonyms/antonyms/example/gap and the word's current
  `learn_map` state if signed in.
- **`static/js/vocab-word.js`** — on the word detail page only, wires up
  the 3-state toggle button (cycle `null → "little" → "learned" → null`,
  matching the current SPA's exact cycle logic in `vocablarry.html`'s
  `learn-state-btn` click handler) to `fetch('/auth/sync/', {method:
  'POST', body: JSON.stringify({learn_map: {...}})})`. This is the first
  `fetch`-based write in the new project — Foundation's auth pages are
  traditional form POSTs using Django's `{% csrf_token %}` hidden input,
  not JS `fetch`. This module needs its own CSRF handling: read the
  `csrftoken` cookie (Django sets it on any page rendering a form or
  decorated with `ensure_csrf_cookie` — the word detail page needs the
  latter if it has no other form on it) and send it as the `X-CSRFToken`
  request header. Updates the button's visual state optimistically,
  reverts on a failed request.
- **`static/css/vocab.css`** — new stylesheet, linked only from the 3 vocab
  templates (not `base.html`, to keep Foundation's base bundle from growing
  for pages that don't need it), reusing `base.css`'s CSS custom properties
  (`--violet`, `--bg`, `--text`, etc.) for visual consistency.

## Data flow

Standard Django request/response for browse and category-word-list (no
client-side data fetching). Word detail is the same for the initial render;
the progress toggle is the one piece of client-side interactivity, calling
the existing `/auth/sync/` JSON endpoint exactly as the current SPA does —
no new API surface.

## Error handling

`Http404` (Django's standard `get_object_or_404`) for unknown category slug
or word id — no custom 404 template in this pass (Django's default, matching
Foundation's "no custom error pages in scope" stance). The progress-toggle
fetch handles a non-200 response by reverting the optimistic UI update and
leaving the button in its prior state (no toast/alert system exists yet —
silent revert is acceptable for this pass; matches the "small, focused
interaction" scope).

## Testing

Django test-client assertions per page, `pytest` + the existing
`regular_user`/`staff_user` fixtures from `conftest.py`:
- `vocab_browse`: 200, correct template, CEFR filter narrows results, search
  query narrows results, category cards link to the right category URLs.
- `vocab_category`: 200 for a valid slug, 404 for an unknown slug, pagination
  produces the right word count per page and correct total page count,
  words ordered by `order`.
- `vocab_word_detail`: 200 for a valid id, 404 for an unknown id, progress
  toggle markup present only when `request.user.is_authenticated`, absent
  for anonymous requests.
- Progress sync: reuses the *existing* `/auth/sync/` test coverage in
  `tests/test_auth_api.py` (already tests `learn_map` GET/POST) — no new
  backend test needed since no backend code changes; the new JS module is
  the only new client-side logic, verified via the same manual
  browser-check pattern Foundation used per task (no JS unit-test tooling
  exists in this project).

## Explicitly out of scope for this phase

The quiz engine (3 modes × up to 5 submodes each — separate future
sub-project 2b), the 75-section category grouping layer, Vietnamese
translation of word/category content, US/UK dialect-based word
substitution, and any dashboard/CRUD editing of vocab content (that's the
Dashboard sub-project). These are deferred, not rejected — each gets its
own design/plan cycle when its turn comes.
