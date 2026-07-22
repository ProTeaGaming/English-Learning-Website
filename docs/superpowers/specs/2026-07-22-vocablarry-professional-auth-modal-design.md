# VocabLarry Professional Environment — Auth Modal Design

## Context

`VocabLarry Professional Environment/FIXES-NEEDED.md` items 1-5 (a standing checklist the user has directed this project to follow) describe VLPE's sign-in as functionally broken relative to production: it's currently a plain `<a href="{% url 'account_login' %}">` (full page reload to django-allauth's bare default template), while production has a JS-driven modal (`#authOverlay`) that never leaves the page, handling login/signup/MFA-authentication/password-reset entirely via `allauth.headless`'s JSON API plus VLPE's own already-built `accounts/` app endpoints.

This reopens a deliberate prior deferral: the Foundation phase (2026-07-17) chose classic template-rendered allauth views over headless specifically because headless wasn't needed at the time; auth parity with production was explicitly scoped as "a future sub-project, not an oversight to rush into" (confirmed with the user 2026-07-21). This spec is that sub-project, now explicitly requested via FIXES-NEEDED.md.

**Verified against production directly, not assumed (per the file's own ground rule):**
- Modal markup: `VocabLarry/vocablarry.html:1606-1690` (`#authOverlay`, one `<form id="authForm">` with conditionally-hidden field groups for each step, plus sibling `deleteOverlay`/`profileOverlay`/`modePickerOverlay` reusing the same `.auth-modal-overlay` CSS family — those three are separate features, out of scope here).
- Modal CSS: `.auth-modal-overlay`/`.auth-modal`/`.auth-social-row`/`.auth-social-btn`/`.auth-field`/`.auth-submit-btn`/`.auth-switch`/`.auth-modal-error`/`.auth-modal-info` (~`vocablarry.html:241-350`).
- Modal JS: a single `authState = {step, email, resetKey}` machine (~`vocablarry.html:13920-14400`) — `resetAuthForm`/`openAuthModal`/`closeAuthModal`, step transitions (email→login/signup→mfa/reset/forgot), `socialLogin(provider, process)` (hidden-form POST, not `fetch`, to `/_allauth/browser/v1/auth/provider/redirect`), the main form-submit handler branching per step against `${ALLAUTH_BASE} = '/_allauth/browser/v1'` endpoints, and `initAuth()` (session check on load).
- **Correction to FIXES-NEEDED.md item 3 (confirmed with the user, not silently overridden):** production's real social row has exactly 4 buttons — Google, Facebook, Microsoft, Apple. No GitHub button or GitHub OAuth config exists anywhere in production's actual source or settings. Item 3 was based on inaccurate information; this spec builds the real 4, not 5.
- Production's `config/settings.py`: `HEADLESS_FRONTEND_URLS = {'account_confirm_email': '/verify-email/{key}', 'account_reset_password_from_key': '/reset-password/{key}'}`; `INSTALLED_APPS` includes `allauth.headless`; `urls.py` mounts **all three** simultaneously: `path('_allauth/', include('allauth.headless.urls'))`, `path('accounts/', include('allauth.urls'))` (classic — kept for OAuth provider redirect/callback infrastructure, which needs classic-style URLs even under headless), and its own `path('auth/', include('accounts.urls'))`.
- VLPE's current `settings.py`: `INSTALLED_APPS` and `SOCIALACCOUNT_PROVIDERS` already byte-identical to production for Google/Facebook/Microsoft/Apple — only `allauth.headless` is missing from `INSTALLED_APPS`, and `HEADLESS_FRONTEND_URLS` doesn't exist at all. `urls.py` has no `/_allauth/` route.
- VLPE's `accounts/urls.py` already exposes `session/`, `sync/`, `update-profile/`, `delete-account/`, `check-email/` (`accounts/views.py`) — confirmed these exist and match the shape production's own modal calls as its non-allauth "app-side" endpoints. **No new backend logic needed** — this is a frontend (modal HTML/CSS/JS) plus settings/URL wiring task.
- VLPE has no `/verify-email/<key>/` or `/reset-password/<key>/` routes yet (`HEADLESS_FRONTEND_URLS`'s targets) — these need adding as new, small views.
- Confirmed via full-codebase search: zero existing `authOverlay`/`auth-modal`/`authModal` markup, CSS, or JS anywhere in VLPE — genuinely unstarted, not partially built.

## Goal

Replace VLPE's plain sign-in link with a real modal matching production's `#authOverlay` exactly — same states, same API call shape, same 4 social providers — wired to `allauth.headless` (newly enabled) and VLPE's already-built `accounts/` app endpoints (no changes needed there).

## Architecture

**Settings/URL wiring (mechanical, exact production values):**
- Add `'allauth.headless'` to `INSTALLED_APPS`.
- Add `HEADLESS_FRONTEND_URLS = {'account_confirm_email': '/verify-email/{key}', 'account_reset_password_from_key': '/reset-password/{key}'}` verbatim.
- Add `path('_allauth/', include('allauth.headless.urls'))` to `urls.py`. The existing `path('accounts/', include('allauth.urls'))` (classic) **stays mounted, unchanged** — matches production's own three-routes-simultaneously pattern; needed for OAuth provider redirects to complete correctly even though the UI itself no longer links to classic pages.
- Add two new views + routes: `/verify-email/<key>/` and `/reset-password/<key>/` — each renders the base page with a small inline script that opens the modal directly into the `reset`/verification-pending state and passes the `key` along (matching production's own deep-link handling), rather than a full classic allauth template render.

**The modal itself:**
- New `authOverlay` HTML block (a `base.html` partial, rendered on every page so the nav's sign-in trigger can open it from anywhere) — one `<form>`, conditionally-hidden field groups per step, ported structurally from production's exact markup.
- New `.auth-modal-overlay`/`.auth-modal`/`.auth-social-row`/`.auth-social-btn`/`.auth-field`/`.auth-submit-btn`/`.auth-switch`/`.auth-modal-error`/`.auth-modal-info` CSS in `base.css` (global chrome, not vocab/grammar-specific).
- New `static/js/auth-modal.js`: the `authState` state machine, `openAuthModal`/`closeAuthModal`, step-transition handlers, `socialLogin()` (hidden-form POST to `/_allauth/browser/v1/auth/provider/redirect`), and the main submit handler branching per step against `/_allauth/browser/v1/auth/*` (login/signup/2fa/password/reset/request) and VLPE's existing `/auth/check-email/`+`/auth/update-profile/` endpoints — ported function-for-function from production's logic, adapted only to VLPE's own URL names via `{% url %}` where the JS needs a server-provided path.
- Nav change: `templates/partials/nav.html`'s plain `<a href="{% url 'account_login' %}">Sign In</a>` / `<a href="{% url 'account_signup' %}">Sign Up</a>` become a single button that calls `openAuthModal()` — matching production's single `#signInBtn` trigger.

**State machine (exact production steps, verified):** `email` (initial screen, calls `check-email/` to decide login-vs-signup UI) → `login` or `signup` → conditionally `mfa` (authentication-time 6-digit code entry only, not enrollment/setup) or a "check your email" pending-verification screen → `forgot` (request a reset email) → `reset` (enter new password via the deep-linked key). Matches production's own `authState.step` values exactly.

**Social providers:** exactly 4 — Google, Facebook, Microsoft, Apple (already configured identically in both projects' `SOCIALACCOUNT_PROVIDERS`). No GitHub (corrects FIXES-NEEDED.md item 3, confirmed with the user).

## Out of Scope

- MFA enrollment/setup UI (a genuinely different feature from authentication-time MFA code entry — production's modal only does the latter).
- The Profile management overlay, Delete-account overlay, and "mode picker" overlay — separate production features reusing the same `.auth-modal-overlay` CSS family, not part of "the sign-in modal."
- GitHub OAuth (not real in production; FIXES-NEEDED.md item 3 corrected).
- Any change to VLPE's existing `accounts/` app views/endpoints — confirmed already correct and sufficient.

## Testing

Pytest + Django test client for the settings/URL/view layer:
- `allauth.headless` present in `INSTALLED_APPS`; `HEADLESS_FRONTEND_URLS` has the exact 2 keys/values.
- `/_allauth/` resolves to `allauth.headless.urls` (a smoke request against a known headless endpoint returns something other than 404).
- The new `/verify-email/<key>/` and `/reset-password/<key>/` routes render successfully with a given key in the URL.
- Nav no longer links directly to `account_login`/`account_signup`; the modal-open trigger element is present in the rendered page.
- The modal's HTML partial renders on every page (present in a base-template-inheriting page's response) with all expected field-group containers.

Given this JS-heavy feature (a real state machine driving real network calls, similar in kind to the vocab-quiz.js engine elsewhere in this project), most of the actual behavioral correctness (does login really work, does MFA challenge really appear, does social redirect really work) is **not** Python-test-coverable — this needs real manual/Playwright verification against real test accounts (including at least one MFA-enabled account and one real social-provider round-trip) before being considered done, matching this project's standing "manual verification is not optional for anything touching rendering/interaction" rule.
