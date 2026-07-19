# VocabLarry Professional Environment — Dashboard (design)

## Context

This is the fifth and (per the original Foundation roadmap) final major
sub-project of the VocabLarry Professional Environment rebuild. Unlike
every other sub-project, **there is no design/build work to do on the
Dashboard's actual functionality at all** — the entire `dashboard` Django
app (`dashboard/views.py`, `forms.py`, `admin.py`, models, and a full set
of Bootstrap-based CRUD templates for words/categories/colors/CEFR
levels/users/grammar topics/lesson blocks/quiz questions) was already
copied byte-for-byte from production during the Foundation phase (see
`docs/superpowers/specs/2026-07-17-vocablarry-professional-foundation-design.md`'s
"Reuse backend + data as-is" decision, which explicitly names `dashboard`
among the apps copied unchanged), and `'dashboard'` is already in
`INSTALLED_APPS`. It has simply never been wired into a URL — confirmed
via `get_resolver()` that no `dashboard` pattern is currently registered
in `config/urls.py`. This sub-project is **integration and verification**,
not feature design: hook the app up, confirm it actually works end-to-end
against this repo's real accounts/vocab/grammar models (proven correct in
production, but never exercised inside VLPE's own URL/settings/auth stack
until now), and fix anything that surfaces live.

**Confirmed self-contained, no cross-references to fix:** `dashboard/base.html`
is a fully independent HTML document — its own `<!doctype html>`, its own
Bootstrap 5 CDN styling, its own top nav — it does **not** `{% extends %}`
VLPE's own `templates/base.html` and has no dependency on VLPE's nav
partial, i18n system, or CSS variables. Every `{% url %}` tag inside the
app's templates only references other `dashboard_*` names (confirmed via
a full grep across `dashboard/templates/`) — no references to any
production-only or not-yet-existing route. `dashboard/base.html`'s own nav
also has 3 **hardcoded absolute links** (`/dashboard/words/`,
`/dashboard/grammar/`, etc. — not `{% url %}` tags), which pins the URL
prefix this app must be mounted at: it must be exactly `/dashboard/`, not
some other prefix, or those hardcoded links will point at the wrong place.

**Access control is already built in and does not need to be added:**
every view is decorated `@role_required('staff')` except `user_list`/
`user_detail`, which require `@role_required('admin')` (matching
`dashboard/base.html`'s own nav, which only shows its "Users" link
`{% if request.user.role == 'admin' %}`). `role_required` (in
`accounts/decorators.py`, already present, unmodified) redirects
unauthenticated users to login (via `@login_required`) and returns a
plain `403 Forbidden` for an authenticated user below the required role.
`CustomUser.role` (already present: `user`/`staff`/`admin` choices) is
what it checks — no new field, no new migration.

## Decisions

- **No new models, no new migrations, no new backend logic, no new
  templates.** The entire `dashboard` app is reused wholesale. This
  sub-project's only code changes are: one `include()` line in
  `config/urls.py`, and one staff-only link added to VLPE's own site nav.
- **URL prefix: exactly `/dashboard/`** — not negotiable per the
  hardcoded-absolute-link constraint above.
- **VLPE's site nav gets one new staff-only link**, gated the same way
  `dashboard/base.html`'s own "Users" link is gated (`user.role`
  comparison, matching this codebase's own template convention rather
  than inventing a new gating mechanism) — but at the broader `staff` OR
  `admin` level (`{% if user.role == 'staff' or user.role == 'admin' %}`),
  matching the majority of the app's own `@role_required('staff')` views,
  not the narrower `admin`-only Users section. A regular/guest user never
  sees this link at all — this mirrors how every other staff-gated
  surface in this codebase (e.g. the progress toggle's own auth gating)
  hides the control entirely rather than showing it disabled.
- **No changes to `dashboard/base.html`'s own internal nav or styling** —
  it stays exactly as copied, including its separate Bootstrap visual
  identity. Making it match VLPE's own design system is explicitly out of
  scope; production's own dashboard has never matched the SPA's styling
  either; a staff-only admin tool having a distinct, utilitarian look is
  an accepted, intentional pattern already established before this
  rebuild even started.
- **New test file, `tests/test_dashboard_pages.py`**, covering: access
  control across the role boundary (anonymous → redirect, `user` role →
  403, `staff` role → 200, and separately confirming `admin`-only views
  403 for a `staff`-but-not-`admin` user) applied broadly across
  sections, plus one full add → edit → delete round-trip for the two
  richest sections (Words, Grammar Topics — including a lesson block and
  a quiz question, since those involve the JSON-field forms that are the
  single highest-risk untested surface in this integration), with
  lighter existence/200-status smoke coverage for the simpler sections
  (Categories, Colors, CEFR Levels, Users).
- **Manual browser verification is required and should be thorough**,
  unlike a typical "spot check" — this is proven-in-production code being
  exercised inside this specific repo's stack for the first time, so the
  goal is to actually surface any integration-time surprise before
  calling this done, not just confirm the wiring resolves. One concrete,
  named risk to check deliberately: `GrammarLessonBlockForm.data` and
  `GrammarQuestionForm.options`/`answers` are model `JSONField`s exposed
  through Django's auto-generated `Textarea`-based JSON form field — a
  known-in-this-project failure mode (documented from production's own
  "Site Debug Mode" work: `forms.JSONField` can coerce an empty/blank
  submission to `None` rather than `{}`/`[]`, which crashed the write API
  there) that has never been exercised against `dashboard`'s specific
  form classes before. Confirm live whether it manifests here too; if it
  does, fix it in this app the same way it was fixed for the write API.

## Architecture

```
config/
  urls.py            (add 1 include line)
templates/
  partials/
    nav.html            (add 1 staff-only <li>)
tests/
  test_dashboard_pages.py   (new)
```

No changes anywhere under `dashboard/` itself unless live verification
surfaces a real bug (see the JSONField risk above) — if that happens, the
fix belongs in `dashboard/forms.py`, following the same `_jsonfield_safe`-
style pattern already proven correct in `api/write_views.py`.

URL wiring:

```python
path('dashboard/', include('dashboard.urls')),
```

## Components

- **`config/urls.py`** — add the include, placed logically alongside the
  other `include()`-based mounts (`accounts/`, `auth/`, `api/`).
- **`templates/partials/nav.html`** — one new `<li>`, staff/admin-gated,
  linking via `{% url 'dashboard_index' %}` (not a hardcoded href) —
  every existing sibling `<li>` in this file already uses `{% url %}`,
  and `dashboard_index` is the app's own name for `/dashboard/` (see
  `dashboard/urls.py`'s first pattern), so this is consistent with both
  this file's own convention and the target app's naming.
- **`tests/test_dashboard_pages.py`** — real `Client()` + real DB tests,
  no mocks, following this project's established testing convention
  (`regular_user`/`staff_user`/`admin_user` fixtures already exist in
  `conftest.py` and are reused directly, not redefined).

## Data flow

No new data flow — every dashboard view already talks directly to the
same `Word`/`Category`/`Color`/`CEFRLevel`/`GrammarTopic`/
`GrammarLessonBlock`/`GrammarQuestion`/`CustomUser` models every other
part of VLPE already uses. This sub-project's only "flow" is: an
authenticated staff/admin user clicks the new nav link → lands on
`/dashboard/` → uses the pre-built CRUD screens exactly as they already
work in production.

## Error handling

Already fully implemented in the reused code, nothing new to add:
`role_required` handles the auth/role boundary (login redirect / 403);
`category_delete` already guards against deleting a category with words
still assigned to it (shows an error message, refuses); `user_detail`
already guards an admin from self-locking-out (can't deactivate or demote
themselves) and from removing the last active admin account. This
sub-project's job is to confirm these guards actually fire correctly
inside VLPE's stack, not to design new ones.

## Testing

Python: access-control matrix (anonymous/user/staff/admin × a
representative view from each `@role_required` tier) plus full CRUD
round-trips for Words and Grammar (topic + block + question, exercising
the JSON-field forms), smoke tests for the remaining sections. Manual:
a real click-through of every section — Words, Categories, Colors, CEFR
Levels, Users, Grammar Topics/Blocks/Questions — add/edit/delete each at
least once against this repo's real seeded data (47 grammar topics,
~5000 words), specifically watching for the JSON-field risk named above
and for any hardcoded link (in `dashboard/base.html` or any list/form
template) that turns out to 404 once actually clicked rather than merely
grepped for.

## Explicitly out of scope for this phase

Restyling `dashboard/base.html` to match VLPE's own design system (a
deliberate non-goal, see Decisions). Any new dashboard functionality
beyond what production already has (no new CRUD sections, no new
reports/analytics). A learner-facing progress dashboard (a different,
unbuilt feature the user explicitly distinguished from this one during
brainstorming — would be a separate future sub-project with its own
design cycle if ever pursued). Fixing the JSONField risk preemptively
without confirming it's real first — the plan should verify live before
patching, not patch speculatively.
