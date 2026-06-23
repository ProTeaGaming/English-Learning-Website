# IELTS Vocab Master — OAuth Login (Google, Facebook, GitHub, Microsoft)

## Context

`ielts-vocab-master/site/` is a plain PHP + SQLite backend (no Composer,
no vendor dependencies) backing `vocab-master.html`. It already has a
working email/password auth system: signup, login, logout, "remember me",
forgot/reset password, profile edit, delete account
(`auth/*.php`, `users` table in `site/data/users.sqlite`).

The sign-in modal already has 4 social buttons (Google, Facebook, GitHub,
Microsoft) but they are placeholders — clicking any of them shows
"Signing in with X is coming soon." This spec wires up real OAuth for all
four.

## 1. Backend: shared OAuth plumbing

New `auth/oauth.php` — no external libraries, plain `curl`/`stream`
calls, matching the existing dependency-free codebase:

- A config map per provider (`google`, `facebook`, `github`, `microsoft`):
  authorize URL, token URL, userinfo URL(s), scope, and client
  id/secret pulled from `auth/config.local.php`.
- `oauth_build_authorize_url($provider, $state)` — builds the redirect
  URL with `client_id`, `redirect_uri`, `scope`, `state`,
  `response_type=code`.
- `oauth_exchange_code($provider, $code)` — POSTs the code to the
  provider's token endpoint, returns the access token.
- `oauth_fetch_profile($provider, $accessToken)` — fetches the user's
  profile and normalizes it to
  `{provider, provider_id, email, email_verified, name, picture}`.
  - Google: `userinfo` endpoint gives email + `email_verified` directly.
  - Facebook: Graph API `/me?fields=id,name,email,picture` — Facebook
    only returns an email if it's confirmed, so presence = verified.
  - GitHub: `/user` for name/picture, plus a second call to
    `/user/emails` to find the `primary && verified` email (GitHub's
    `/user.email` is often null/private).
  - Microsoft: Microsoft Graph `/me`, using `mail ?? userPrincipalName`
    as the email; treated as verified (ownership already proven via
    Microsoft login).

`auth/config.local.example.php` gains an `oauth` block (client
id/secret per provider) alongside the existing mail config.
`auth/OAUTH_SETUP.md` documents, step by step, how to register an app
in Google Cloud Console, Facebook Developers, GitHub OAuth Apps, and
Microsoft Entra, and exactly which redirect URI to register
(`{app_base_url}/auth/oauth_callback.php?provider=<name>`).

## 2. Backend: start + callback

- `auth/oauth_start.php?provider=<name>` — generates a random `state`,
  stores it in `$_SESSION['oauth_state']` (tagged with the provider and
  a short expiry), redirects (302) to the provider's authorize URL.
- `auth/oauth_callback.php?provider=<name>&code=...&state=...`:
  1. Validate `state` matches the session value for that provider and
     hasn't expired; reject otherwise.
  2. Exchange `code` for an access token, fetch the normalized profile.
  3. **Account resolution**, in order:
     - Match `(provider, provider_id)` in `oauth_accounts` → log in as
       that user.
     - Else, if `email_verified` and it matches an existing
       `users.email` → insert the `oauth_accounts` link, log in as that
       user.
     - Else → this is a new person. For `google` specifically, do NOT
       create the user yet (see §3). For `facebook`/`github`/
       `microsoft`, auto-create immediately (see below) and log in.
  4. Auto-create (facebook/github/microsoft new-user path): insert a
     `users` row with the provider's email/name/picture, a random
     unusable `password_hash` (so password login stays impossible until
     they explicitly set one), and an auto-generated unique `username`
     (sanitized from name/email, falls back to a random suffix on
     collision). Insert the `oauth_accounts` link. Set
     `$_SESSION['user_id']`.
  5. Redirect back to `../vocab-master.html`. On any failure (denied
     consent, state mismatch, provider error, exchange failure),
     redirect back with `?auth_error=<message>` instead of a raw PHP
     error.

## 3. Google-only profile-completion step

Per product decision: Google is "simple tap to sign in" for returning
users, but a **brand-new** Google sign-up gets a short profile step
before the account exists, because Google has no "username" concept and
the site needs one.

- On the new-person branch for `google`, the callback stores the
  normalized profile in `$_SESSION['oauth_pending']` (provider, email,
  name, picture) and redirects to `../vocab-master.html?oauth_pending=1`.
  No `users` row exists yet.
- Frontend: on page load, if the URL has `oauth_pending=1`, strip it and
  call `GET auth/oauth_pending.php`, which returns the stashed profile
  (404/empty JSON if nothing pending). The auth modal opens directly
  into a new "Complete your profile" step:
  - Avatar preview + full name input, both pre-filled from the pending
    profile (editable) — reuses the existing `authSignupExtra` markup
    (name/username/picture fields), with the email + password fields
    hidden (email is already fixed via Google).
  - Username input, blank, same validation as manual signup
    (`^[A-Za-z0-9]{3,20}$`, uniqueness-checked).
- Submitting calls `POST auth/oauth_complete.php` with `{name,
  username}`. The server re-reads `$_SESSION['oauth_pending']` (errors
  if absent — e.g. session expired), creates the `users` row + the
  `oauth_accounts` link using the pending data + chosen
  name/username, clears `oauth_pending`, sets `$_SESSION['user_id']`.
- Frontend then does the same `closeAuthModal(); await initAuth();`
  used by the existing login/signup success paths.
- Facebook/GitHub/Microsoft never produce `oauth_pending` — they always
  auto-create immediately per §2.

## 4. Database changes (`auth/db.php`)

New table:

```sql
CREATE TABLE IF NOT EXISTS oauth_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  provider TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_provider_user
  ON oauth_accounts(provider, provider_user_id);
```

`users.password_hash` stays `NOT NULL` (avoids an SQLite table rebuild)
— OAuth-created accounts get `password_hash(random_bytes(32))`, an
unusable hash, so password-login simply fails until the user sets a
real password via some future "set password" flow (out of scope here).

## 5. Frontend changes (`vocab-master.html`)

- Replace the placeholder social-button handler:
  `window.location.href = AUTH_BASE + "oauth_start.php?provider=" +
  btn.dataset.provider.toLowerCase()`.
- Add `id="authEmailGroup"` to the email field's wrapping `<label>` so
  it can be hidden for the new profile-completion step (currently the
  only field not wrapped in a hideable container).
- New `authState.step === "oauth-profile"` handling: hide
  email+password groups, show `authSignupExtra` (minus email/password),
  pre-fill name/avatar preview from the fetched pending profile, submit
  posts to `oauth_complete.php`.
- On page load (alongside the existing `initAuth()` call): check for
  `?oauth_pending=1`, fetch `oauth_pending.php`, and if it returns a
  profile, open the modal directly into the `oauth-profile` step.
  Also check for `?auth_error=`, show it via `showAuthError()` in an
  opened modal, and strip both params from the URL via
  `history.replaceState`.

## 6. Verification

- Each provider: full round trip in the local PHP dev server
  (`php -S localhost:8000`) using a real registered OAuth app pointed at
  `http://localhost:8000/auth/oauth_callback.php?provider=<name>`.
- New Google user → lands on "Complete your profile" with name/avatar
  pre-filled, blank username; submitting creates the account and logs
  in.
- New Facebook/GitHub/Microsoft user → logs in immediately, no extra
  screen; account row has provider-sourced name/picture and an
  auto-generated username.
- Returning user, any provider → logs in immediately (no profile step),
  whether matched via `oauth_accounts` or freshly linked by verified
  email to an existing password-based account.
- Tampered/expired `state` on callback → redirects with `auth_error`,
  no session created.
- Denied consent on provider screen → redirects with `auth_error`, no
  crash.

## Out of scope

- "Set a password" flow for OAuth-only accounts.
- Unlinking a provider from an existing account (only linking is
  covered).
- Production deployment / real domain registration — all 4 provider
  apps are registered against `localhost:8000` for now per current
  hosting; redirect URIs will need updating when a real domain exists.
