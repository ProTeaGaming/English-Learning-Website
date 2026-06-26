# IELTS Vocab Master — Django Rewrite Design

## Context

`ielts-vocab-master/Python/Flask/` is a Flask + SQLite backend backing
`vocab-master.html`: email/password auth, remember-me tokens, Firebase
OAuth, profile editing, avatar upload, password reset, and vocab-progress
sync. Vocabulary data is embedded as static JS files in
`React-Native/src/data/data-part1.js` through `data-part11.js`.

Goal: build a Django version at `ielts-vocab-master/Python/Django/` that
adds:
- Vocabulary data stored in a database, editable via an admin dashboard
  (words, categories, CEFR levels, colors)
- API-driven frontend — vocab-master.html fetches data from Django instead
  of reading embedded JS files; admin changes appear immediately on refresh
- Professional auth via django-allauth: more OAuth providers, mandatory
  email verification, 2FA (TOTP), role-based access control
- Staff dashboard for managing vocab data; admin dashboard for managing
  users

The Flask version stays in `Python/Flask/` unchanged. Both have their own
`vocab-master.html` that references their own backend.

## 1. Project layout

```
ielts-vocab-master/Python/
  Flask/                         ← existing, untouched
    auth/
    vocab-master.html
  Django/
    manage.py
    config/
      settings.py
      urls.py
    accounts/
      models.py                  ← CustomUser with role field
      adapters.py                ← allauth adapter (username gen, role init)
      urls.py
    vocab/
      models.py                  ← Word, Category, CEFRLevel, Color
      migrations/
      management/
        commands/
          import_vocab.py        ← seed DB from React-Native JS data files
    dashboard/
      views.py                   ← staff/admin-only CRUD UI
      urls.py
      templates/
        dashboard/
    api/
      views.py                   ← JSON endpoints for vocab-master.html
      urls.py
    templates/
      base.html
      allauth/                   ← override allauth default templates
    vocab-master.html            ← updated to fetch from Django API
    .env
    .env.example
    requirements.txt
```

## 2. Data models

### `accounts/models.py`

```python
class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER  = 'user'   # use vocab master, sync progress, manage own profile
        STAFF = 'staff'  # user + access /dashboard/ (words, categories, CEFR, colors)
        ADMIN = 'admin'  # staff + /dashboard/users/ (promote, demote, deactivate)

    email     = models.EmailField(unique=True)
    username  = models.CharField(max_length=20, unique=True)
    name      = models.CharField(max_length=60, blank=True)
    picture   = models.ImageField(upload_to='avatars/', blank=True)
    role      = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    learn_map = models.JSONField(default=dict)  # { word_id: learned_at_timestamp }

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']
```

`learn_map` maps word IDs (from the database) to timestamps so the
frontend can track which words have been learned. Word IDs come from
`GET /api/words/` and are used when syncing progress.

allauth's `SocialAccount` model handles OAuth linked accounts — no custom
`OAuthAccount` table needed. Django sessions handle remember-me — no
`RememberToken` table needed.

Django's `is_superuser` flag is reserved for emergency Django admin access
only and is not used in the application's permission logic.

### `vocab/models.py`

```python
class CEFRLevel(models.Model):
    code   = models.CharField(max_length=2, unique=True)  # A1, A2, B1, B2, C1, C2
    name   = models.CharField(max_length=50)               # Beginner, Elementary, etc.
    order  = models.PositiveSmallIntegerField()            # 1–6 for sorting

class Color(models.Model):
    name      = models.CharField(max_length=50)
    bg_hex    = models.CharField(max_length=7)   # background, e.g. #3B82F6
    text_hex  = models.CharField(max_length=7)   # text on bg, e.g. #FFFFFF

class Category(models.Model):
    name        = models.CharField(max_length=100)
    cefr_level  = models.ForeignKey(CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL)
    color       = models.ForeignKey(Color, null=True, blank=True, on_delete=models.SET_NULL)
    order       = models.PositiveSmallIntegerField(default=0)

class Word(models.Model):
    word        = models.CharField(max_length=200)
    definition  = models.TextField()
    example     = models.TextField(blank=True)
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='words')
    cefr_level  = models.ForeignKey(CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL)
    order       = models.PositiveSmallIntegerField(default=0)
```

## 3. Auth system

### django-allauth configuration

- Login by email (not username) — username kept for display only
- `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` — must verify email before
  first login; OAuth-sourced emails are considered pre-verified
- "Remember me" checkbox on login → 30-day session cookie; unchecked →
  browser-session only (`ACCOUNT_SESSION_REMEMBER = None`)
- Password reset via allauth's built-in flow (uses SMTP from `.env`)

### OAuth providers (via allauth social apps)

Google, Facebook, GitHub, Microsoft — each added as a `SocialApp` record
in the database. Credentials (client ID + secret) stored in `.env`, not
hardcoded. First OAuth login auto-creates an account with email
pre-verified.

### 2FA via `allauth.mfa`

- TOTP-based (Google Authenticator, Authy, etc.)
- Users opt in from their profile settings page
- Staff and admin accounts are required to have 2FA enabled — enforced by
  a middleware check on all `/dashboard/` routes

### RBAC

| Role | Access |
|---|---|
| `user` | Vocab master, progress sync, own profile |
| `staff` | Above + `/dashboard/` (words, categories, CEFR, colors) |
| `admin` | Above + `/dashboard/users/` (promote/demote, deactivate) |

Enforced with a decorator `@role_required('staff')` on dashboard views and
`@role_required('admin')` on user management views, each wrapping
Django's `@login_required`.

### `accounts/adapters.py`

Subclass of `DefaultAccountAdapter`:
- Auto-generates a username from the email prefix on OAuth signup
  (e.g. `john.doe@gmail.com` → `john_doe`, deduplicated if taken)
- Sets `role = USER` on every new signup regardless of auth source

## 4. API endpoints

### Auth — allauth headless mode

`allauth.headless` provides a JSON API for all auth operations — no custom
auth views needed. The frontend uses `fetch()` against these endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/login/` | POST | Email + password login |
| `/auth/signup/` | POST | Register + trigger verification email |
| `/auth/session/` | GET | Current user info |
| `/auth/session/` | DELETE | Logout |
| `/auth/password/request/` | POST | Forgot password |
| `/auth/password/reset/` | POST | Reset with token |
| `/auth/2fa/authenticate/` | POST | 2FA code entry |
| `/auth/social/{provider}/login/` | GET | OAuth redirect (google, facebook, github, microsoft) |

Response shapes follow allauth headless format — `vocab-master.html` auth
fetch handlers are updated to match (login, signup, session check, logout).

### Custom endpoints (`api/` app)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/words/` | GET | All words with IDs, grouped by category |
| `/api/categories/` | GET | All categories with color + CEFR level |
| `/api/cefr-levels/` | GET | All CEFR levels in sorted order |
| `/auth/sync/` | GET / POST | Read/write `learn_map` for current user |
| `/auth/update-profile/` | POST | Name, username, avatar upload |
| `/auth/delete-account/` | POST | Password-confirm then delete |
| `/auth/check-email/` | POST | Returns `{"exists": true/false}` |

`vocab-master.html` fetches `/api/words/` and `/api/categories/` on page
load instead of reading embedded JS data. The rest of the page logic
(showing/hiding profile, marking words learned, syncing) stays the same
in structure, with fetch call targets updated.

## 5. Dashboard UI

Server-rendered Django templates with Bootstrap 5 (CDN, no build step).

### Routes

| URL | Role | Purpose |
|---|---|---|
| `/dashboard/` | staff+ | Overview: word count, category count, user count |
| `/dashboard/words/` | staff+ | Paginated list, filterable by category + CEFR |
| `/dashboard/words/add/` | staff+ | Add new word |
| `/dashboard/words/<id>/edit/` | staff+ | Edit word |
| `/dashboard/words/<id>/delete/` | staff+ | Delete with confirm modal (POST) |
| `/dashboard/categories/` | staff+ | List with color swatches and word counts |
| `/dashboard/categories/add/` | staff+ | Add category |
| `/dashboard/categories/<id>/edit/` | staff+ | Edit name, CEFR, color |
| `/dashboard/colors/` | staff+ | List with hex preview, add/edit |
| `/dashboard/cefr-levels/` | staff+ | List + inline edit (6 levels, rarely changes) |
| `/dashboard/users/` | admin | List users, search by email/username |
| `/dashboard/users/<id>/` | admin | Change role, deactivate account |

Deleting a category that still has words is blocked at the view level with
a clear error message — the user must reassign or delete the words first.

### One-time data import

A management command seeds the database from the existing static JS files:

```
python manage.py import_vocab
```

Reads `React-Native/src/data/data-part1.js` through `data-part11.js`,
parses the vocabulary data, and creates `CEFRLevel`, `Color`, `Category`,
and `Word` records. Idempotent — safe to run multiple times (skips
records that already exist by name). Run once after initial `migrate`
before starting the server.

## 6. Config (`.env` / `.env.example`)

`python-dotenv` loads `.env` into `os.environ`:

```
DJANGO_SECRET_KEY=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraccount@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
FROM_EMAIL=youraccount@gmail.com
FROM_NAME=IELTS Vocab Master
APP_BASE_URL=http://localhost:8000
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
FACEBOOK_CLIENT_ID=...
FACEBOOK_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

## 7. Running the server

```
cd ielts-vocab-master/Python/Django
python manage.py migrate
python manage.py import_vocab
python manage.py runserver localhost:8000
```

Replaces `python auth/app.py` from the Flask version. Everything served
from the same process: `GET /` serves `vocab-master.html`, `/api/*` serves
vocab data, `/auth/*` serves allauth headless JSON, `/dashboard/*` serves
the management UI.

## 8. Out of scope

- Production deployment (WSGI/ASGI, HTTPS, real domain)
- Automated test suite
- Migrating existing Flask user accounts to Django (different DB, fresh start)
- React-Native API integration (different project; DRF can be added later)
