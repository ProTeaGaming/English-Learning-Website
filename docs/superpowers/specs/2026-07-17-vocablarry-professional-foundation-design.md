# VocabLarry Professional Environment — Foundation (design)

## Context

Production `VocabLarry/` serves the entire site as one client-rendered SPA:
`config/urls.py` has a single `serve_vocab` view that `FileResponse`s the raw
`vocablarry.html` (~14k lines, all pages/JS/CSS inlined) for every route.
Django does zero templating today — all rendering happens in the browser via
JS reading a JSON API (`api/`).

This is a parallel, from-scratch rebuild in a new sibling folder,
`D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment\`,
intended to eventually replace production. Goal: recreate the same site
using standard Django templating
(template inheritance, split static CSS/JS) instead of one monolithic file.
The full rebuild is too large for one spec — it decomposes into sub-projects:

1. **Foundation** (this spec) — project scaffold, base template, static
   asset split, nav, home page, auth pages.
2. Vocab — category browse, word pages, quiz engine.
3. Grammar — lessons, topic browse, quiz engine.
4. Dashboard — staff CRUD.

i18n (en/vi) threads through all of them rather than being its own phase.

## Decisions

- **Reuse backend + data as-is.** Copy `VocabLarry/`'s Django apps
  (`accounts`, `api`, `config`, `dashboard`, `grammar`, `vocab`), migrations,
  `db.sqlite3`, and `grammar-content.json` into the new folder unchanged.
  Models, the API layer, and business logic are proven and out of scope for
  this rebuild — only the presentation layer changes.
- **Interactivity: Django templates + plain JS modules per page.** Each page
  gets its own template and its own small JS file (`<script src>`), calling
  the same existing `api/` JSON endpoints the SPA calls today. Same runtime
  behavior as production, just organized as separate files instead of one
  blob. (Rejected: htmx/Alpine — would require rewriting the API layer as
  fragment-returning views, a bigger behavioral change than this rebuild
  needs. Rejected: hybrid SPA-islands — unnecessary hedge once per-page JS
  modules are the default for every page anyway.)
- **Auth: switch to allauth's classic template-based views**
  (`allauth.account.urls`, `allauth.socialaccount.urls`) instead of
  `allauth.headless`. Allauth already implements full server-rendered
  login/signup/password-reset/email-verify/social-redirect flows; this
  rebuild supplies templates overriding its defaults rather than
  reimplementing auth logic. Same `CustomUser` model and
  `AccountAdapter`/`SocialAccountAdapter` as production — no change to
  signup rules or email verification behavior.
- **Auth UX: dedicated pages**, not modal overlays. `/accounts/login/`,
  `/accounts/signup/`, `/accounts/logout/`, `/accounts/password/reset/`,
  email-verify/confirm routes are real server-rendered routes (allauth's
  defaults), not JS-toggled overlays on top of a single-page shell.
- **Templates live in one project-level `templates/` directory**
  (`templates/home.html`, `templates/account/login.html`, ...), not
  per-app `templates/<app>/` directories — simpler to browse at this
  project's size.
- **i18n: keep the current client-side pattern.** `data-i18n` attributes +
  a JS string dictionary swapped on toggle (no page reload), ported into
  `static/js/i18n.js`. Only the strings Foundation's own pages need (nav,
  home hero, auth forms) are ported now; more get added as later
  sub-projects land. Server-side Django i18n (`{% trans %}`,
  locale-prefixed URLs) is a bigger behavioral change than this rebuild
  needs and is explicitly rejected.

## Architecture

```
VocabLarry Professional Environment/
  manage.py
  config/            (settings.py, urls.py — rewritten root routing)
  accounts/          (unchanged from VocabLarry/)
  api/               (unchanged)
  vocab/             (unchanged — models only used in this phase)
  grammar/           (unchanged — models only used in this phase)
  dashboard/         (unchanged — not wired into urls.py yet)
  db.sqlite3         (copied snapshot, isolated from production)
  grammar-content.json
  requirements.txt
  templates/
    base.html
    home.html
    partials/nav.html
    account/
      login.html
      signup.html
      logout.html
      password_reset.html
      password_reset_from_key.html
      email_confirm.html
      ... (allauth's default template set, restyled)
  static/
    css/base.css
    js/base.js
    js/i18n.js
```

`config/urls.py` changes from the single `serve_vocab` FileResponse view to:

```python
urlpatterns = [
    path('', home_view),
    path('accounts/', include('allauth.urls')),   # classic, template-based
    path('auth/', include('accounts.urls')),        # unchanged custom views
    path('api/', include('api.urls')),               # unchanged
] + static(...)
```

`allauth.headless` and its `_allauth/` JSON routes are dropped from this
project (production keeps them — this is a separate codebase).

## Components

- **`templates/base.html`** — HTML skeleton, `{% block title %}` /
  `{% block content %}`, includes `partials/nav.html`, links
  `static/css/base.css` + `static/js/base.js` (+ per-page extra
  CSS/JS via blocks).
- **`templates/home.html`** — ports the current hero + mode-picker cards
  (Vocabulary/Grammar entries). Since Vocab/Grammar pages don't exist yet
  in this project, those links point at placeholder routes (acceptable gap
  for this phase — later sub-projects fill them in).
- **`templates/partials/nav.html`** — top nav: logo, section links
  (Vocabulary/Grammar, both disabled/placeholder until sub-projects 2–3),
  language switcher, auth state (sign-in link vs. account menu).
- **`templates/account/*.html`** — allauth's default template set,
  restyled to match VocabLarry's current visual language (colors, fonts,
  card styling) but as full pages, not modals.
- **`static/css/base.css`** — global resets, fonts, CSS variables
  (violet palette, light/dark theme vars), nav styling, button styles —
  extracted from the shared chrome portion of the current monolith's
  `<style>` block, not the whole thing.
- **`static/js/base.js`** — nav interactions (mobile menu, language
  switcher toggle, theme toggle).
- **`static/js/i18n.js`** — `UI_STRINGS`-style dict for `en`/`vi`, applies
  `data-i18n` swaps on load and on toggle, scoped to Foundation's own
  strings only.

## Data flow

Standard Django request/response: each route's view fetches whatever
context it needs from the ORM (home page needs none yet — it's static
chrome) and renders a template. No JSON round-trip for page loads. Any
future interactive widget on these pages (there are none yet in Foundation)
would still call `api/` via `fetch`, same as production.

## Error handling

Relies on allauth's existing error handling for auth flows (invalid
credentials, expired reset tokens, unverified email) — unchanged from
production since the adapter and model layer are untouched, only the
template rendering it. Django's standard 404/500 templates apply elsewhere;
no custom error pages are in scope for this phase.

## Testing

Port the relevant slice of the existing pytest suite, adapted from
headless-API assertions to template-rendering assertions: status codes,
correct template used (`assertTemplateUsed`), form re-render with errors on
invalid submission, redirect-after-success. Covers signup, login, logout,
password reset request + confirm, email verification, and the social-login
redirect kickoff (not full OAuth completion, which needs real provider
credentials). Uses the same pytest + Django test client tooling as
production.

## Explicitly out of scope for this phase

Vocab pages (browse/word/quiz), grammar pages (lessons/quiz), dashboard
CRUD UI, and i18n string coverage beyond what Foundation's own pages need.
These are separate sub-projects, each getting their own design/plan cycle
once Foundation is working end to end.
