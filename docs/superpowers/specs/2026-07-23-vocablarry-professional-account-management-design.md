# VocabLarry Professional Environment — Account Management design

**Date:** 2026-07-23
**Status:** Approved, ready for planning

## Context

A fresh comparison pass of VLPE against production (`VocabLarry/vocablarry.html`)
found that VLPE's entire authenticated-user chrome is essentially unbuilt:
logged-in users see only a plain username and a "Sign Out" link in the nav.
Production has a full `.user-chip`/`.user-menu` dropdown (avatar, Edit Profile,
Reset Progress, Sign Out, Delete Account), a live `Learned: X / Y` stat with a
review-shortcut button, an Edit Profile modal (avatar/name/username +
connected-social-accounts management), and a Delete Account modal.

These findings were recorded as FIXES-NEEDED.md items 12-16 (see that file for
the exact production references this design was built against). Two related
findings from the same pass — a sitewide footer (item 17) and the
Reading/Writing/Listening/Speaking stub pages missing an "Under construction"
card (item 18) — are explicitly **out of scope** for this design; they are
separate, independent sub-projects.

**Key existing infrastructure this design reuses, not rebuilds:**
- `accounts/views.py:update_profile` and `:delete_account` — fully built,
  already handle edge cases (username-taken, image-too-large, Google-only
  accounts with no usable password) — just never exposed to any UI after the
  one-time call during signup.
- `accounts/urls.py` already mounts `update-profile/` and `delete-account/`
  under `/auth/` (`AUTH_BASE` in `auth-modal.js`).
- `allauth.headless`'s own `GET`/`DELETE /account/providers` endpoint —
  production's connected-accounts list talks to this directly; no new backend
  needed for it.
- `static/js/auth-modal.js`'s private helpers (`getCsrf`, `authFetch`,
  `socialLogin`, `previewAvatarFile`) — reusable as-is once exposed.
- `config/context_processors.py` already has one processor
  (`nav_active_section`) establishing the pattern for a second one.

**Explicitly deferred (not part of this design):**
- The US/UK vocabulary-dialect toggle in the Edit Profile modal. VLPE's `User`
  model has no `dialect` field, and per `tests/test_us_uk_word_pairs.py`, VLPE's
  word data was already normalized to single US-spelling headwords with UK
  terms folded into synonyms — there is no second spelling variant left to
  actually switch to. Building the toggle now would be UI with no real effect,
  which contradicts this project's own "don't build things that don't
  functionally work" rule (FIXES-NEEDED.md's ground rule). Revisit only if
  VLPE ever gains real per-word dialect variants.
- Production's native `confirm()` for Reset Progress. VLPE has never used a
  native browser dialog anywhere; Reset Progress instead gets a small custom
  `.auth-modal-overlay`-based confirm step, consistent with every other
  destructive-ish action in this codebase.

## Architecture

Two new frontend surfaces stay separate from the existing anonymous
sign-in modal, since they're a different concern (managing an
already-authenticated account rather than getting one):

- **`templates/partials/account_modals.html`** — new partial: Edit Profile
  overlay, Delete Account overlay, Reset Progress confirm overlay. Included
  from `base.html`, guarded by `{% if user.is_authenticated %}` (unlike
  `auth_modal.html`, which is unconditional since anonymous users need it).
- **`static/js/account-modals.js`** — new file: user-menu open/close, the
  three modals' open/close/submit logic. `auth-modal.js` exposes its private
  helpers via `window.vlpeAuth = { getCsrf, authFetch, socialLogin,
  previewAvatarFile, AUTH_BASE, ALLAUTH_BASE }` at the end of its IIFE so the
  new file can reuse them without duplicating any of that logic.

Backend additions, both reusing existing conventions rather than introducing
new ones:

- **`config/context_processors.py`**: new `user_progress_stats(request)`,
  returning `{}` for anonymous requests and `{'words_learned': N,
  'total_words': N, 'little_count': N}` for authenticated ones. The
  words-learned/total-words computation is extracted into a small shared
  helper (e.g. `vocab/services.py::learned_word_stats(user)`) used by both
  this processor and `config/views.py:home`, which currently duplicates that
  exact logic inline — removing the duplication as part of this work, not as
  an unrelated drive-by refactor.
- **`accounts/views.py`**: one new view, `reset_progress` — `POST`-only,
  auth-required, clears `request.user.learn_map` and `.grammar_map`, mirrors
  the existing `sync`/`delete_account` views' shape exactly (same
  `_require_auth` guard, same `JsonResponse({'ok': True})` success shape).
  Registered at `accounts/urls.py` as `reset-progress/`.

## User-facing behavior

**Nav (`templates/partials/nav.html`), authenticated users only:**
- `.user-chip`: avatar (uploaded `picture`, or a gradient-circle fallback
  showing the first letter of `name`, falling back to `email` if `name` is
  blank — matching production's exact `(name || email).charAt(0)` logic,
  not `username`) + name (or email if name is blank), click to open a
  `.user-menu` dropdown showing name/username/email and four buttons — Edit
  profile, Reset progress, Sign out (unchanged existing link), Delete account.
  Same click-to-open/outside-click-to-close interaction already established
  for `.nav-group`/`.lang-chip`.
- Live stats next to the lang/theme toggles: `Learned: {words_learned} /
  {total_words}`, server-rendered. A "N to review" link to
  `/vocabulary/word/?progress=little` renders only when `little_count > 0` —
  a server-side-conditional improvement over production's
  always-render-then-hide-via-JS approach, matching VLPE's established
  server-computed-stat convention.
- Anonymous users: unchanged (Sign In button only).

**Edit Profile modal:**
- Avatar upload with live preview (reusing `previewAvatarFile` verbatim), full
  name, username, pre-filled from the current user. Submits to the existing
  `POST /auth/update-profile/`, reusing its existing validation messages.
- Connected-accounts list: all 4 providers (Google/Facebook/Microsoft/Apple),
  live state fetched from `GET /account/providers`; each row shows
  Connect (`socialLogin(provider, 'connect')`, redirect flow, unchanged) or
  Disconnect (`DELETE /account/providers`) — ported close to verbatim from
  production's `renderProfileConnections`/`disconnectProvider` since that
  logic already talks to a stable, already-integrated API.
- On success: close modal, reload page (matches the existing signup-flow
  pattern) so the nav's avatar/name reflect the change immediately.

**Delete Account modal:**
- Password field, shown/required only if `has_usable_password()` — Google-only
  accounts aren't asked for a password they don't have.
- Submits to the existing `POST /auth/delete-account/`. On success, redirect
  to `/` (the view already flushes the session server-side).

**Reset Progress confirm overlay:**
- Small `.auth-modal-overlay`-based confirm ("Reset all learning progress?
  This can't be undone." + Cancel/Reset), not the full-size auth modal shape.
- Reset posts to the new `POST /auth/reset-progress/`, then reloads.

## Testing

- Backend: new tests for `POST /auth/reset-progress/` — requires auth,
  clears both `learn_map` and `grammar_map`, doesn't touch other users' data,
  rejects `GET`.
- Backend: new test(s) for the `user_progress_stats` context processor —
  empty for anonymous, correct counts for an authenticated user with a mix of
  learned/little/untouched words.
- Pages: new tests asserting the nav's new markup (`.user-chip` present only
  when authenticated, avatar-vs-initials-fallback rendering, live stats
  present only when authenticated, "N to review" link present only when
  `little_count > 0` and absent otherwise), and that the two new modals'
  markup/i18n strings render on every authenticated page (mirroring the
  existing `test_auth_modal_renders_on_home_page` pattern for the sign-in
  modal).
- Manual browser verification (this project's now-standard practice for
  anything touching real rendering/JS behavior): open/close the user menu;
  edit name/username; upload and preview an avatar; connect and disconnect a
  real provider; delete a real test account; mark a few words learned/little,
  confirm the live stats and review link, then reset progress and confirm
  both the stats and the underlying data actually clear.

## Out of scope (tracked separately)

- FIXES-NEEDED.md item 17 (sitewide footer) — own sub-project.
- FIXES-NEEDED.md item 18 (stub-page "Under construction" card) — small
  enough to patch directly, no spec needed.
