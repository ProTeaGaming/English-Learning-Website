# IELTS Vocab Master — PHP → Django Auth Backend Migration

## Context

`ielts-vocab-master/site/auth/` is a PHP + SQLite backend (13 scripts)
backing `vocab-master.html`: email/password signup/login/logout,
"remember me", forgot/reset password (via raw-socket SMTP), profile
edit + avatar upload, delete account, vocab-progress sync
(`learn_map`), and Firebase-verified social login
(see `2026-06-23-oauth-login-design.md`). The site is served locally
via `php -S localhost:8000` run from `ielts-vocab-master/site/`.

Goal: replace the PHP backend with a Django backend — "more modern,
easier to manage, suitable for LLM and automation" per the user. This
is a like-for-like behavioral port, not a redesign: same SQLite data,
same validation rules, same cookie/session semantics. The one existing
real account (`pichusis2019@gmail.com`, id 1 — has a full `learn_map`
and an uploaded avatar) must keep working, including its current
password.

## 1. Project layout

New Django project at `ielts-vocab-master/site/` (replacing the
`auth/*.php` scripts; `manage.py` runs from the same directory `php
-S` used to, for parity):

```
ielts-vocab-master/site/
  manage.py
  config/
    settings.py
    urls.py                 # mounts accounts.urls + the 2 static-page views
  accounts/
    models.py                # User, RememberToken, OAuthAccount (managed=False)
    hashers.py                # BcryptPasswordHasher (php password_hash compat)
    urls.py
    views/
      login.py, signup.py, session.py, logout.py, check_email.py,
      forgot_password.py, reset_password.py, delete_account.py,
      update_profile.py, sync.py, firebase_login.py
    services/
      mailer.py               # smtplib STARTTLS send
      firebase.py             # ID-token verification + account resolution
      avatar.py                # Pillow-based upload validation/storage
      remember.py              # remember-me cookie create/consume/clear
      validators.py            # name/username/email regex checks
  vocab-master.html            # unchanged, served by a view
  auth/
    reset_password.html        # unchanged, served by a view
    uploads/avatars/            # unchanged location, unchanged contents
  data/
    users.sqlite                 # unchanged, reused as Django's DB file
  .env.example
  .env                           # gitignored
  requirements.txt
```

`auth/config.local.example.php` and `auth/config.local.php` are
replaced by `.env.example` / `.env`. `auth/FIREBASE_SETUP.md` is
updated in place to reference `.env` instead of `config.local.php`
(its Firebase-console steps are unchanged).

## 2. Data layer (`accounts/models.py`)

Django's `DATABASES['default']` points at the existing
`data/users.sqlite` file — no export/import step. Three models map
onto the existing tables with `managed = False` and explicit
`db_table`, so Django's `migrate` never touches their schema — it only
adds Django's own tables (`django_session`, `django_migrations`) into
the same file:

- `User` → `users` table (`id, email, password_hash, name, picture,
  learn_map, created_at, last_login, reset_token,
  reset_token_expires, username`)
- `RememberToken` → `remember_tokens`
- `OAuthAccount` → `oauth_accounts`

`learn_map` stays a `TextField` holding a JSON string (parsed/dumped
in views, same as the PHP code's `json_decode`/`json_encode` — not
worth a Django JSONField given `managed=False`).

No `django.contrib.auth` — no Django `User`/permissions app. Sessions
use `django.contrib.sessions` only, with `request.session['user_id']`
exactly mirroring PHP's `$_SESSION['user_id']`. `request.session.cycle_key()`
is the equivalent of `session_regenerate_id(true)` (rotates the
session id, keeps the data) and is called after every login/signup/
firebase-login, same as the PHP code.

## 3. Password hashing (`accounts/hashers.py`)

A custom hasher subclassing Django's `BasePasswordHasher`, wrapping
the `bcrypt` package, registered as the only entry in
`PASSWORD_HASHERS`. It treats `$2y$` and `$2b$` prefixes as
equivalent (a PHP/Python bcrypt library quirk — both are standard
bcrypt, the prefix difference is historical) so the existing
`$2y$12$...` hash for account id 1 verifies as-is. New signups hash
with the same scheme, so the format stays consistent going forward —
not a one-off compatibility shim for old data only.

## 4. Endpoints

Clean REST paths (no `.php`), all under `/auth/`:

| Old PHP | New Django | Method |
|---|---|---|
| `login.php` | `/auth/login` | POST |
| `signup.php` | `/auth/signup` | POST (multipart, for avatar) |
| `session.php` | `/auth/session` | GET |
| `logout.php` | `/auth/logout` | POST |
| `check_email.php` | `/auth/check-email` | POST |
| `forgot_password.php` | `/auth/forgot-password` | POST |
| `reset_password.php` | `/auth/reset-password` | POST |
| `delete_account.php` | `/auth/delete-account` | POST |
| `update_profile.php` | `/auth/update-profile` | POST (multipart) |
| `sync.php` | `/auth/sync` | GET, POST |
| `firebase_login.php` | `/auth/firebase-login` | POST |

Each view ports its PHP script's logic 1:1: same validation rules
(email format, 8-char min password, name = `\p{L}` + spaces 1-60
chars, username = alnum 3-20 chars), same status codes (400/401/409/
405), same JSON response shapes (`{"ok": true}`, `{"error": "..."}`,
`{"loggedIn": ..., ...}`, etc.).

`\p{L}` (any Unicode letter) needs the third-party `regex` package —
stdlib `re` doesn't support Unicode property escapes. Email format
validation uses Django's built-in `django.core.validators.validate_email`.

### Frontend changes (`vocab-master.html`)

`AUTH_BASE` changes from `"auth/"` to `"/auth/"`, and each of the 11
`fetch(AUTH_BASE + "...")` calls drops its `.php` suffix and switches
to the kebab-case name (e.g. `"login.php"` → `"login"`,
`"check_email.php"` → `"check-email"`, `"firebase_login.php"` →
`"firebase-login"`). No other frontend logic changes — request
methods, bodies (FormData vs JSON), and response handling are
unchanged since the contracts are unchanged.

Avatar image URLs are a different kind of path — they're *stored data*
(`users.picture`), not API routes — and are left exactly as-is
(`auth/uploads/avatars/<file>`), so the existing stored path for
account id 1 keeps resolving with no data migration. A Django URL
pattern serves that directory at the same relative path.

## 5. Services

- **`mailer.py`** — `smtplib.SMTP` + `.starttls()` + `.login()` +
  `email.mime.text.MIMEText`, replacing the hand-rolled SMTP socket
  client (manual EHLO/STARTTLS/AUTH LOGIN/DATA framing). Same Gmail
  App Password flow, same config keys, same behavior of always
  returning `{"ok": true}` from `forgot-password` regardless of
  whether an account/email existed (prevents account enumeration).
- **`firebase.py`** — `requests.post` to
  `https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=...`,
  same provider-detection (`google`/`facebook`/`apple`/`microsoft`
  substring match on `providerId`) and `resolve_oauth_user` logic
  (match `oauth_accounts` → match verified email → create new user +
  auto-generated username), ported from `oauth_common.php`.
- **`avatar.py`** — Pillow (`PIL.Image.open(...).verify()`) for
  MIME/format validation instead of `getimagesize`, same 2MB limit,
  same `bin2hex(random_bytes(16))`-style random filename
  (`secrets.token_hex(16)`), same storage path.
- **`remember.py`** — same cookie name (`remember_token`), same
  `selector:validator` format, same SHA-256 validator hash, same
  30-day TTL, same httponly+`SameSite=Lax` cookie attributes, ported
  to `request.COOKIES` / `HttpResponse.set_cookie`.

## 6. Config (`.env` / `.env.example`)

`python-dotenv` loads `.env` into `os.environ`, read by
`config/settings.py`:

```
DJANGO_SECRET_KEY=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraccount@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
FROM_EMAIL=youraccount@gmail.com
FROM_NAME=IELTS Vocab Master
APP_BASE_URL=http://localhost:8000
FIREBASE_API_KEY=YOUR_FIREBASE_WEB_API_KEY
```

`.env.example` (committed, placeholder values, same comments as the
old `config.local.example.php` about Gmail App Passwords and the
Firebase key being client-safe) replaces the PHP example file. `.env`
is gitignored. Root `.gitignore`'s
`ielts-vocab-master/site/auth/config.local.php` line is replaced with
a `.env` rule; the `ielts-vocab-master/site/data/*.sqlite` and
`ielts-vocab-master/site/auth/uploads/` rules stay as-is.

## 7. Static & media serving

`python manage.py runserver localhost:8000`, run from
`ielts-vocab-master/site/`, replaces `php -S localhost:8000` as the
single command serving everything:

- `GET /` → view returning `vocab-master.html`'s contents
  (`Content-Type: text/html`)
- `GET /reset-password` → view returning `auth/reset_password.html`'s
  contents (the link generated by `forgot-password`'s email points
  here instead of `auth/reset_password.html?token=...`)
- `GET /auth/uploads/avatars/<file>` → served from
  `auth/uploads/avatars/` (`django.views.static.serve`, fine for local
  dev; this app has no production deployment yet)
- All `/auth/*` API routes from §4

## 8. Verification

Manual exercise against the running dev server, no automated test
suite (matches the project's existing testing posture — there are no
PHP tests today either):

- `GET /auth/session` while logged out → `{"loggedIn": false}`
- Log in as the real account (`pichusis2019@gmail.com`) → verify the
  bcrypt hasher accepts the existing `$2y$12$...` hash, session
  cookie set, `GET /auth/session` now returns the full profile
  including `learn_map` size/avatar path unchanged
- `GET /auth/sync` returns the existing `learn_map` intact; a
  no-op `POST /auth/sync` round-trips it unchanged
- `POST /auth/logout` clears the session
- Full signup → profile-update (name/username/avatar) → delete-account
  cycle on a **throwaway** second account — never touching account id 1
- `check-email` returns true/false correctly for existing vs. new
  emails
- `forgot-password` → `reset-password` cycle on the throwaway account,
  if SMTP creds are filled into `.env`; if not, confirms the endpoint
  still responds `{"ok": true}` without crashing (matching the PHP
  behavior of silently no-running mail send failures)
- Firebase login is verified by code review only — no real Firebase
  ID token is available to test against in this environment

## 9. Cleanup (final step, after verification passes)

Delete the 13 PHP files in `auth/` and `config.local.example.php`;
update `FIREBASE_SETUP.md` to reference `.env` instead of
`config.local.php`. This happens **after** the Django version is
confirmed working — not before, since deleting the PHP files first
would take down login on a site with no replacement live yet.

## Out of scope

- Production deployment (WSGI/ASGI server choice, HTTPS, real
  domain/Firebase authorized-domain config) — local dev parity only,
  matching the current PHP setup's scope.
- Automated test suite — none exists for the PHP version either;
  could be a follow-up.
- Changing any validation rule, response shape, or business logic —
  this is a language/framework port, not a behavior change.
