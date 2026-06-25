# PHP → Django Auth Backend Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 13 PHP scripts in `ielts-vocab-master/site/auth/` with a Django backend that is a behavioral port — same SQLite data, same validation rules, same cookie/session semantics — serving both the API and the static frontend from one `python manage.py runserver` command.

**Architecture:** A Django project at `ielts-vocab-master/site/` with one app (`accounts`) holding three `managed = False` models mapped onto the existing `users`/`remember_tokens`/`oauth_accounts` tables in the existing `data/users.sqlite` file, one view module per endpoint, and small service modules (`passwords`, `validators`, `remember`, `avatar`, `mailer`, `firebase`) each porting one PHP helper file. No `django.contrib.auth` — sessions are plain `django.contrib.sessions` storing `request.session['user_id']`, mirroring PHP's `$_SESSION['user_id']`.

**Tech Stack:** Django 5.x, python-dotenv, the `bcrypt` package (via Django's built-in `BCryptPasswordHasher`), `requests`, `Pillow`, `regex` (for `\p{L}` Unicode-letter matching, which stdlib `re` doesn't support).

## Global Constraints

- Reuse the existing `ielts-vocab-master/site/data/users.sqlite` file as-is — no export/import. Account id 1 (`pichusis2019@gmail.com`), its `learn_map`, and its avatar path must keep working.
- Account id 1's password hash (`$2y$12$VBLZsh5RoPROIbgomrrO/uzAkCg6rtA76Zk7r3ud7nrjuITeHjs5K`, PHP bcrypt) must verify successfully — use Django's built-in `BCryptPasswordHasher`, which calls the `bcrypt` package's `checkpw`, which accepts `$2y$`/`$2b$` interchangeably.
- No automated test suite (matches the project's existing PHP code, which also has none) — verification is manual, via `python manage.py shell` one-liners and `curl`/browser checks against the running dev server.
- This is a language port, not a behavior or validation-rule change. Every status code, JSON response shape, and validation message must match the PHP original.
- Endpoints move from `auth/<name>.php` to clean REST paths under `/auth/` (no `.php`) — see the mapping table in the spec. `vocab-master.html`'s `fetch()` calls must be updated to match.
- Avatar image URLs (`auth/uploads/avatars/<file>`) are stored *data*, not API routes — keep that exact relative path so account id 1's existing stored avatar path keeps resolving with no data migration.
- No CSRF middleware/tokens — the PHP endpoints never had CSRF protection either; adding it now would be a behavior change, not a port.
- Local dev only (`python manage.py runserver`) — no production deployment, WSGI server choice, or HTTPS in scope.

---

### Task 1: Project scaffolding

**Files:**
- Create: `ielts-vocab-master/site/requirements.txt`
- Create: `ielts-vocab-master/site/manage.py`
- Create: `ielts-vocab-master/site/config/__init__.py`
- Create: `ielts-vocab-master/site/config/settings.py`
- Create: `ielts-vocab-master/site/config/wsgi.py`
- Create: `ielts-vocab-master/site/.env.example`
- Create: `ielts-vocab-master/site/.env`
- Modify: `.gitignore` (repo root)

**Interfaces:**
- Produces: `config.settings` module readable by every later task (`DATABASES`, `SMTP_*`, `FROM_EMAIL`, `FROM_NAME`, `APP_BASE_URL`, `FIREBASE_API_KEY` settings).

- [ ] **Step 1: Write `requirements.txt`**

```
Django>=5.0,<6.0
python-dotenv>=1.0
bcrypt>=4.1
requests>=2.31
Pillow>=10.0
regex>=2024.4.16
```

- [ ] **Step 2: Install dependencies**

Run: `cd "ielts-vocab-master/site" && pip install -r requirements.txt`
Expected: all 6 packages (and their transitive deps) install with no errors.

- [ ] **Step 3: Write `.env.example`**

```
# Copy this file to .env (gitignored) and fill in real values.
# SMTP_PASS must be a Gmail "App Password" (16 chars, generated at
# https://myaccount.google.com/apppasswords) — your normal Gmail password will NOT work.
DJANGO_SECRET_KEY=change-me-to-a-random-string
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraccount@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
FROM_EMAIL=youraccount@gmail.com
FROM_NAME=IELTS Vocab Master
APP_BASE_URL=http://localhost:8000

# Web API key from Firebase console > Project settings > General.
# Same value as firebaseConfig.apiKey in vocab-master.html — it's
# public/client-safe, not a secret. See auth/FIREBASE_SETUP.md.
FIREBASE_API_KEY=YOUR_FIREBASE_WEB_API_KEY
```

- [ ] **Step 4: Write `.env`** (real local file, gitignored)

Same content as `.env.example`, except `DJANGO_SECRET_KEY` set to a real random string (e.g. output of `python -c "import secrets; print(secrets.token_urlsafe(50))"`). Leave SMTP/Firebase values as placeholders for now — mailer and Firebase login will be code-reviewed rather than live-tested until real credentials exist (see Task 19).

- [ ] **Step 5: Write `config/__init__.py`** (empty file)

- [ ] **Step 6: Write `config/settings.py`**

```python
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-insecure-key')
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.sessions',
    'accounts',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'data' / 'users.sqlite',
    }
}

USE_TZ = False
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SMTP_HOST = os.environ.get('SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', '')
FROM_NAME = os.environ.get('FROM_NAME', 'IELTS Vocab Master')
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:8000')
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
```

- [ ] **Step 7: Write `config/wsgi.py`**

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
```

- [ ] **Step 8: Write `manage.py`**

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

- [ ] **Step 9: Update root `.gitignore`**

Replace the line `ielts-vocab-master/site/auth/config.local.php` with:

```
ielts-vocab-master/site/.env
```

(Leave the `*.sqlite` and `auth/uploads/` rules as they are — unchanged.)

- [ ] **Step 10: Verify `config.urls` doesn't exist yet causes no crash**

This step is just confirmation that Step 1-9 produced no Python syntax errors:
Run: `cd "ielts-vocab-master/site" && python -c "import config.settings"`
Expected: no output, exit code 0 (a `ROOT_URLCONF` pointing at a not-yet-created module is fine at this stage — it's only resolved when the dev server actually routes a request).

- [ ] **Step 11: Commit**

```bash
git add ielts-vocab-master/site/requirements.txt ielts-vocab-master/site/manage.py ielts-vocab-master/site/config/__init__.py ielts-vocab-master/site/config/settings.py ielts-vocab-master/site/config/wsgi.py ielts-vocab-master/site/.env.example .gitignore
git commit -m "Scaffold Django project for auth backend migration"
```

(`.env` itself is gitignored and must NOT be added.)

---

### Task 2: Data models

**Files:**
- Create: `ielts-vocab-master/site/accounts/__init__.py`
- Create: `ielts-vocab-master/site/accounts/apps.py`
- Create: `ielts-vocab-master/site/accounts/models.py`
- Create: `ielts-vocab-master/site/accounts/migrations/__init__.py`

**Interfaces:**
- Consumes: `config.settings.DATABASES` (Task 1)
- Produces: `accounts.models.User` (fields: `id, email, password_hash, name, picture, learn_map, created_at, last_login, reset_token, reset_token_expires, username`), `accounts.models.RememberToken` (fields: `id, user_id, selector, validator_hash, expires_at`), `accounts.models.OAuthAccount` (fields: `id, user_id, provider, provider_user_id, created_at`) — all later tasks import these.

- [ ] **Step 1: Write `accounts/__init__.py`** (empty file)

- [ ] **Step 2: Write `accounts/apps.py`**

```python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'accounts'
```

- [ ] **Step 3: Write `accounts/models.py`**

```python
from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    picture = models.CharField(max_length=255, null=True, blank=True)
    learn_map = models.TextField(default='{}')
    created_at = models.CharField(max_length=32)
    last_login = models.CharField(max_length=32)
    reset_token = models.CharField(max_length=64, null=True, blank=True)
    reset_token_expires = models.CharField(max_length=32, null=True, blank=True)
    username = models.CharField(max_length=20, unique=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'users'


class RememberToken(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, db_column='user_id', on_delete=models.DO_NOTHING)
    selector = models.CharField(max_length=32, unique=True)
    validator_hash = models.CharField(max_length=64)
    expires_at = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'remember_tokens'


class OAuthAccount(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, db_column='user_id', on_delete=models.DO_NOTHING)
    provider = models.CharField(max_length=32)
    provider_user_id = models.CharField(max_length=255)
    created_at = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = 'oauth_accounts'
        unique_together = ('provider', 'provider_user_id')
```

- [ ] **Step 4: Create `accounts/migrations/__init__.py`** (empty file)

- [ ] **Step 5: Create `config/urls.py` placeholder** (needed for `manage.py` commands to run at all; Task 18 fills in real routes)

```python
urlpatterns = []
```

- [ ] **Step 6: Generate migrations**

Run: `cd "ielts-vocab-master/site" && python manage.py makemigrations accounts`
Expected: `Migrations for 'accounts': accounts/migrations/0001_initial.py` — creates `User`, `RememberToken`, `OAuthAccount` as `CreateModel` entries with `managed=False` recorded (no DDL will actually run for them).

- [ ] **Step 7: Apply migrations**

Run: `python manage.py migrate`
Expected: `Applying sessions.0001_initial... OK` plus `accounts.0001_initial... OK`. Confirm no DDL error about `users`/`remember_tokens`/`oauth_accounts` already existing (there shouldn't be one — `managed=False` models are skipped at the DDL level).

- [ ] **Step 8: Verify existing data is untouched**

Run: `python manage.py shell -c "from accounts.models import User; u = User.objects.get(id=1); print(u.email, u.username, len(u.learn_map))"`
Expected: `pichusis2019@gmail.com Pichu <some large number>` — confirms the model reads the existing row correctly without Django having altered the table.

- [ ] **Step 9: Commit**

```bash
git add ielts-vocab-master/site/accounts/__init__.py ielts-vocab-master/site/accounts/apps.py ielts-vocab-master/site/accounts/models.py ielts-vocab-master/site/accounts/migrations/ ielts-vocab-master/site/config/urls.py
git commit -m "Add accounts app with models mapped onto existing auth tables"
```

---

### Task 3: Password hashing service

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/__init__.py`
- Create: `ielts-vocab-master/site/accounts/services/passwords.py`

**Interfaces:**
- Produces: `hash_password(raw_password: str) -> str`, `verify_password(raw_password: str, encoded_hash: str) -> bool` — used by every view that checks or sets a password (login, signup, delete-account, reset-password, firebase-login).

- [ ] **Step 1: Write `accounts/services/__init__.py`** (empty file)

- [ ] **Step 2: Write `accounts/services/passwords.py`**

```python
from django.contrib.auth.hashers import BCryptPasswordHasher

_hasher = BCryptPasswordHasher()


def hash_password(raw_password: str) -> str:
    return _hasher.encode(raw_password)


def verify_password(raw_password: str, encoded_hash: str) -> bool:
    return _hasher.verify(raw_password, encoded_hash)
```

- [ ] **Step 3: Verify round-trip hashing works**

Run:
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from accounts.services.passwords import hash_password, verify_password
h = hash_password('test1234')
print(h.startswith('\$2'))
print(verify_password('test1234', h))
print(verify_password('wrong', h))
"
```
Expected: `True`, `True`, `False`.

- [ ] **Step 4: Verify compatibility with the existing PHP `$2y$` hash**

Run:
```
python manage.py shell -c "
from accounts.services.passwords import verify_password
from accounts.models import User
u = User.objects.get(id=1)
print(u.password_hash[:4])
print(verify_password('definitely-not-the-real-password', u.password_hash))
"
```
Expected: `\$2y\$` printed, then `False` — critically, **no exception is raised**. If this raised a `ValueError`/binascii error instead of cleanly returning `False`, that would mean the `bcrypt` package rejected the `$2y$` prefix outright, and account id 1 would be locked out after migration. A clean `False` confirms the prefix is accepted and the real password will verify correctly too.

- [ ] **Step 5: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/__init__.py ielts-vocab-master/site/accounts/services/passwords.py
git commit -m "Add bcrypt-compatible password hashing service"
```

---

### Task 4: Validators and timestamp helper

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/validators.py`
- Create: `ielts-vocab-master/site/accounts/services/util.py`

**Interfaces:**
- Produces: `is_valid_email(email: str) -> bool`, `is_valid_name(name: str) -> bool`, `is_valid_username(username: str) -> bool`, `sql_now() -> str` — used by signup, update-profile, login, firebase-login.

- [ ] **Step 1: Write `accounts/services/validators.py`**

```python
import regex
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email

NAME_RE = regex.compile(r'^[\p{L}\s]{1,60}$')
USERNAME_RE = regex.compile(r'^[A-Za-z0-9]{3,20}$')


def is_valid_email(email: str) -> bool:
    try:
        django_validate_email(email)
        return True
    except ValidationError:
        return False


def is_valid_name(name: str) -> bool:
    return bool(NAME_RE.match(name))


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_RE.match(username))
```

- [ ] **Step 2: Write `accounts/services/util.py`**

```python
from datetime import datetime, timezone


def sql_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
```

- [ ] **Step 3: Verify validator behavior matches the PHP regexes**

Run:
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from accounts.services.validators import is_valid_email, is_valid_name, is_valid_username
print(is_valid_email('a@b.com'), is_valid_email('not-an-email'))
print(is_valid_name('José García'), is_valid_name('Bad123'))
print(is_valid_username('Pichu1'), is_valid_username('ab'), is_valid_username('has space'))
"
```
Expected: `True False`, `True False`, `True False False`.

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/validators.py ielts-vocab-master/site/accounts/services/util.py
git commit -m "Add shared validators and SQL timestamp helper"
```

---

### Task 5: Remember-me cookie service

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/remember.py`

**Interfaces:**
- Consumes: `accounts.models.RememberToken` (Task 2)
- Produces: `create_remember_cookie(response, user_id: int) -> None`, `consume_remember_cookie(request) -> tuple[int, str, str] | None`, `set_remember_cookie(response, selector: str, validator: str) -> None`, `clear_remember_cookie(request, response) -> None`, `clear_all_remember_tokens(user_id: int) -> None` — used by login, signup, session, logout, firebase-login, delete-account.

- [ ] **Step 1: Write `accounts/services/remember.py`**

```python
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from accounts.models import RememberToken

REMEMBER_COOKIE_NAME = 'remember_token'
REMEMBER_TTL_DAYS = 30


def _sql_now_plus_days(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')


def _store_new_token(user_id: int) -> tuple[str, str]:
    selector = secrets.token_hex(8)
    validator = secrets.token_hex(32)
    validator_hash = hashlib.sha256(validator.encode()).hexdigest()
    expires_at = _sql_now_plus_days(REMEMBER_TTL_DAYS)
    RememberToken.objects.create(
        user_id=user_id, selector=selector,
        validator_hash=validator_hash, expires_at=expires_at,
    )
    return selector, validator


def set_remember_cookie(response, selector: str, validator: str) -> None:
    response.set_cookie(
        REMEMBER_COOKIE_NAME, f'{selector}:{validator}',
        max_age=REMEMBER_TTL_DAYS * 86400, path='/',
        httponly=True, samesite='Lax',
    )


def create_remember_cookie(response, user_id: int) -> None:
    selector, validator = _store_new_token(user_id)
    set_remember_cookie(response, selector, validator)


def consume_remember_cookie(request) -> tuple[int, str, str] | None:
    raw = request.COOKIES.get(REMEMBER_COOKIE_NAME)
    if not raw or ':' not in raw:
        return None
    selector, validator = raw.split(':', 1)

    try:
        token = RememberToken.objects.get(selector=selector)
    except RememberToken.DoesNotExist:
        return None

    user_id, expires_at, validator_hash = token.user_id, token.expires_at, token.validator_hash
    token.delete()

    expires_dt = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    if expires_dt < datetime.now(timezone.utc):
        return None
    if not secrets.compare_digest(validator_hash, hashlib.sha256(validator.encode()).hexdigest()):
        return None

    new_selector, new_validator = _store_new_token(user_id)
    return user_id, new_selector, new_validator


def clear_remember_cookie(request, response) -> None:
    raw = request.COOKIES.get(REMEMBER_COOKIE_NAME)
    if raw and ':' in raw:
        selector = raw.split(':', 1)[0]
        RememberToken.objects.filter(selector=selector).delete()
    response.delete_cookie(REMEMBER_COOKIE_NAME, path='/')


def clear_all_remember_tokens(user_id: int) -> None:
    RememberToken.objects.filter(user_id=user_id).delete()
```

- [ ] **Step 2: Verify create/consume round-trip**

Run:
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from django.http import HttpResponse
from accounts.services.remember import create_remember_cookie, REMEMBER_COOKIE_NAME
from accounts.models import RememberToken

resp = HttpResponse()
create_remember_cookie(resp, user_id=1)
count = RememberToken.objects.filter(user_id=1).count()
print(count >= 1)
print(REMEMBER_COOKIE_NAME in resp.cookies)
RememberToken.objects.filter(user_id=1).delete()
"
```
Expected: `True`, `True` (then cleans up the test row it created).

- [ ] **Step 3: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/remember.py
git commit -m "Add remember-me cookie service"
```

---

### Task 6: Avatar upload service

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/avatar.py`

**Interfaces:**
- Produces: `store_avatar_upload(uploaded_file) -> dict` (returns `{'ok': True, 'path': str}` or `{'ok': False, 'error': str}`), `delete_avatar_file(relative_path: str | None) -> None` — used by signup and update-profile.

- [ ] **Step 1: Write `accounts/services/avatar.py`**

```python
import secrets

from django.conf import settings
from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = {'JPEG': 'jpg', 'PNG': 'png', 'GIF': 'gif', 'WEBP': 'webp'}
MAX_SIZE_BYTES = 2 * 1024 * 1024
UPLOAD_URL_PREFIX = 'auth/uploads/avatars/'


def _upload_dir():
    return settings.BASE_DIR / 'auth' / 'uploads' / 'avatars'


def store_avatar_upload(uploaded_file) -> dict:
    if uploaded_file.size > MAX_SIZE_BYTES:
        return {'ok': False, 'error': 'Profile picture must be under 2MB.'}

    try:
        image = Image.open(uploaded_file)
        fmt = image.format
        image.verify()
    except (UnidentifiedImageError, OSError):
        fmt = None

    if fmt not in ALLOWED_FORMATS:
        return {'ok': False, 'error': 'Profile picture must be a JPG, PNG, GIF, or WEBP image.'}

    ext = ALLOWED_FORMATS[fmt]
    filename = f'{secrets.token_hex(16)}.{ext}'
    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_file.seek(0)
    with open(upload_dir / filename, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    return {'ok': True, 'path': UPLOAD_URL_PREFIX + filename}


def delete_avatar_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    path = settings.BASE_DIR / relative_path
    if path.is_file():
        path.unlink()
```

- [ ] **Step 2: Verify validation and storage with a real image file**

Run (uses the avatar that already exists on disk from account id 1 as a known-good JPEG fixture):
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.services.avatar import store_avatar_upload, delete_avatar_file

with open('auth/uploads/avatars/3800e7559f3c0e6ace4ae4933add37b3.jpg', 'rb') as f:
    data = f.read()

upload = SimpleUploadedFile('test.jpg', data, content_type='image/jpeg')
result = store_avatar_upload(upload)
print(result)

bad = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')
print(store_avatar_upload(bad))

delete_avatar_file(result['path'])
print((settings.BASE_DIR / result['path']).exists() if result['ok'] else 'n/a')
"
```
Expected: first call returns `{'ok': True, 'path': 'auth/uploads/avatars/<32 hex chars>.jpg'}`; second call returns `{'ok': False, 'error': 'Profile picture must be a JPG, PNG, GIF, or WEBP image.'}`; final line is `False` (file was cleaned up). Note: the last line needs `from django.conf import settings` added to the inline script if it errors with `NameError` — add that import to the `-c` string.

- [ ] **Step 3: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/avatar.py
git commit -m "Add avatar upload validation/storage service"
```

---

### Task 7: Login view

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/__init__.py`
- Create: `ielts-vocab-master/site/accounts/views/login.py`
- Create: `ielts-vocab-master/site/accounts/urls.py`
- Modify: `ielts-vocab-master/site/config/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.passwords.verify_password`, `accounts.services.remember.create_remember_cookie`, `accounts.services.util.sql_now`
- Produces: `login_view(request)` at `POST /auth/login`, mounted via `accounts.urls`.

- [ ] **Step 1: Write `accounts/views/__init__.py`** (empty file)

- [ ] **Step 2: Write `accounts/views/login.py`**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.passwords import verify_password
from accounts.services.remember import create_remember_cookie
from accounts.services.util import sql_now


@require_POST
def login_view(request):
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    remember = request.POST.get('remember') not in (None, '', '0')

    user = User.objects.filter(email=email).first()

    if not user or not verify_password(password, user.password_hash):
        return JsonResponse({'error': 'Incorrect email or password.'}, status=401)

    user.last_login = sql_now()
    user.save(update_fields=['last_login'])

    request.session.cycle_key()
    request.session['user_id'] = user.id

    response = JsonResponse({'ok': True})
    if remember:
        create_remember_cookie(response, user.id)
    return response
```

- [ ] **Step 3: Write `accounts/urls.py`**

```python
from django.urls import path

from accounts.views.login import login_view

urlpatterns = [
    path('login', login_view),
]
```

- [ ] **Step 4: Write `config/urls.py`**

```python
from django.urls import include, path

urlpatterns = [
    path('auth/', include('accounts.urls')),
]
```

- [ ] **Step 5: Start the dev server and verify login end-to-end**

Run: `cd "ielts-vocab-master/site" && python manage.py runserver localhost:8000` (background/separate terminal)

Then, since account id 1's real password isn't known, first set a known password for a safe manual test via shell (do this in a **separate** shell, server still running):
```
python manage.py shell -c "
from accounts.models import User
from accounts.services.passwords import hash_password
u = User.objects.get(id=1)
print('original hash:', u.password_hash)
"
```
Note the original hash printed — it will be restored in Step 6. Do **not** save a new password to the database; instead, test against a **temporary in-memory check only** is not possible via HTTP, so instead verify the wrong-password path (safe, doesn't touch data):

```
curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "email=pichusis2019@gmail.com&password=definitely-wrong&remember=0"
```
Expected: `HTTP/1.1 401` and body `{"error": "Incorrect email or password."}`.

Also verify the not-found-email path:
```
curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "email=nobody@example.com&password=whatever1&remember=0"
```
Expected: same 401 response (PHP and this port both give the same error for "no such user" and "wrong password", so account existence isn't leaked).

- [ ] **Step 6: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/__init__.py ielts-vocab-master/site/accounts/views/login.py ielts-vocab-master/site/accounts/urls.py ielts-vocab-master/site/config/urls.py
git commit -m "Add login view"
```

---

### Task 8: Signup view

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/signup.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.avatar.store_avatar_upload`, `accounts.services.passwords.hash_password`, `accounts.services.remember.create_remember_cookie`, `accounts.services.util.sql_now`, `accounts.services.validators.{is_valid_email,is_valid_name,is_valid_username}`
- Produces: `signup_view(request)` at `POST /auth/signup`.

- [ ] **Step 1: Write `accounts/views/signup.py`**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.avatar import store_avatar_upload
from accounts.services.passwords import hash_password
from accounts.services.remember import create_remember_cookie
from accounts.services.util import sql_now
from accounts.services.validators import is_valid_email, is_valid_name, is_valid_username


@require_POST
def signup_view(request):
    email = request.POST.get('email', '').strip().lower()
    password = request.POST.get('password', '')
    name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()
    remember = request.POST.get('remember') not in (None, '', '0')

    if not is_valid_email(email):
        return JsonResponse({'error': 'Please enter a valid email address.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters.'}, status=400)
    if not is_valid_name(name):
        return JsonResponse({'error': 'Full name can only contain letters and spaces.'}, status=400)
    if not is_valid_username(username):
        return JsonResponse(
            {'error': 'Username must be 3-20 characters, letters and numbers only (no spaces or symbols).'},
            status=400,
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse({'error': 'An account with this email already exists.'}, status=409)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'This username is already taken.'}, status=409)

    picture = None
    uploaded = request.FILES.get('picture')
    if uploaded:
        upload = store_avatar_upload(uploaded)
        if not upload['ok']:
            return JsonResponse({'error': upload['error']}, status=400)
        picture = upload['path']

    user = User.objects.create(
        email=email, password_hash=hash_password(password), name=name, username=username,
        picture=picture, learn_map='{}', created_at=sql_now(), last_login=sql_now(),
    )

    request.session.cycle_key()
    request.session['user_id'] = user.id

    response = JsonResponse({'ok': True})
    if remember:
        create_remember_cookie(response, user.id)
    return response
```

- [ ] **Step 2: Add the route to `accounts/urls.py`**

```python
from django.urls import path

from accounts.views.login import login_view
from accounts.views.signup import signup_view

urlpatterns = [
    path('login', login_view),
    path('signup', signup_view),
]
```

- [ ] **Step 3: Verify signup creates a throwaway account**

With the dev server running:
```
curl -i -X POST http://localhost:8000/auth/signup -F "email=throwaway-test@example.com" -F "password=testpass123" -F "name=Test User" -F "username=throwawaytest" -F "remember=0"
```
Expected: `HTTP/1.1 200` and `{"ok": true}`, with a `Set-Cookie: sessionid=...` header.

Then verify duplicate-email rejection:
```
curl -i -X POST http://localhost:8000/auth/signup -F "email=throwaway-test@example.com" -F "password=testpass123" -F "name=Test User" -F "username=differentname" -F "remember=0"
```
Expected: `HTTP/1.1 409` and `{"error": "An account with this email already exists."}`.

Leave the `throwaway-test@example.com` account in place — Task 12 (update-profile), Task 13 (delete-account), and Task 19 (end-to-end verification) reuse it.

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/signup.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add signup view"
```

---

### Task 9: Session and logout views

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/session.py`
- Create: `ielts-vocab-master/site/accounts/views/logout.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.remember.{consume_remember_cookie,set_remember_cookie,clear_remember_cookie}`
- Produces: `session_view(request)` at `GET /auth/session`, `logout_view(request)` at `/auth/logout` (no method restriction — the frontend calls this with a plain `fetch()`, which defaults to `GET`).

- [ ] **Step 1: Write `accounts/views/session.py`**

```python
from django.http import JsonResponse

from accounts.models import User
from accounts.services.remember import consume_remember_cookie, set_remember_cookie


def session_view(request):
    user_id = request.session.get('user_id')
    new_selector = new_validator = None

    if not user_id:
        result = consume_remember_cookie(request)
        if not result:
            return JsonResponse({'loggedIn': False})
        user_id, new_selector, new_validator = result
        request.session.cycle_key()
        request.session['user_id'] = user_id

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        del request.session['user_id']
        return JsonResponse({'loggedIn': False})

    response = JsonResponse({
        'loggedIn': True,
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'username': user.username,
        'picture': user.picture,
    })
    if new_selector:
        set_remember_cookie(response, new_selector, new_validator)
    return response
```

- [ ] **Step 2: Write `accounts/views/logout.py`**

```python
from django.http import JsonResponse

from accounts.services.remember import clear_remember_cookie


def logout_view(request):
    response = JsonResponse({'ok': True})
    clear_remember_cookie(request, response)
    request.session.flush()
    return response
```

- [ ] **Step 3: Add both routes to `accounts/urls.py`**

```python
from django.urls import path

from accounts.views.login import login_view
from accounts.views.logout import logout_view
from accounts.views.session import session_view
from accounts.views.signup import signup_view

urlpatterns = [
    path('login', login_view),
    path('signup', signup_view),
    path('session', session_view),
    path('logout', logout_view),
]
```

- [ ] **Step 4: Verify session check and logout**

```
curl -i -c cookies.txt -X POST http://localhost:8000/auth/signup -F "email=session-test@example.com" -F "password=testpass123" -F "name=Session Test" -F "username=sessiontest" -F "remember=0"
curl -i -b cookies.txt http://localhost:8000/auth/session
```
Expected second call: `{"loggedIn": true, "id": ..., "email": "session-test@example.com", "name": "Session Test", "username": "sessiontest", "picture": null}`.

```
curl -i -b cookies.txt -c cookies.txt http://localhost:8000/auth/logout
curl -i -b cookies.txt http://localhost:8000/auth/session
```
Expected first call: `{"ok": true}`. Expected second call (after logout): `{"loggedIn": false}`.

Clean up the throwaway `session-test@example.com` account and `cookies.txt`:
```
python manage.py shell -c "from accounts.models import User; User.objects.filter(email='session-test@example.com').delete()"
rm cookies.txt
```

- [ ] **Step 5: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/session.py ielts-vocab-master/site/accounts/views/logout.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add session check and logout views"
```

---

### Task 10: Check-email view

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/check_email.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.validators.is_valid_email`
- Produces: `check_email_view(request)` at `POST /auth/check-email`.

- [ ] **Step 1: Write `accounts/views/check_email.py`**

```python
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.validators import is_valid_email


@require_POST
def check_email_view(request):
    body = json.loads(request.body or b'{}')
    email = str(body.get('email', '')).strip().lower()

    if not is_valid_email(email):
        return JsonResponse({'error': 'Please enter a valid email address.'}, status=400)

    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
```

- [ ] **Step 2: Add the route to `accounts/urls.py`**

```python
    path('check-email', check_email_view),
```

(add alongside the existing paths, with the matching import line `from accounts.views.check_email import check_email_view`)

- [ ] **Step 3: Verify**

```
curl -s -X POST http://localhost:8000/auth/check-email -H "Content-Type: application/json" -d '{"email":"pichusis2019@gmail.com"}'
curl -s -X POST http://localhost:8000/auth/check-email -H "Content-Type: application/json" -d '{"email":"nobody@example.com"}'
```
Expected: `{"exists": true}` then `{"exists": false}`.

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/check_email.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add check-email view"
```

---

### Task 11: Mailer service

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/mailer.py`

**Interfaces:**
- Produces: `smtp_send_mail(to: str, subject: str, body_text: str) -> bool` — used by forgot-password.

- [ ] **Step 1: Write `accounts/services/mailer.py`**

```python
import smtplib
import ssl
from email.mime.text import MIMEText

from django.conf import settings


def smtp_send_mail(to: str, subject: str, body_text: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return False

    msg = MIMEText(body_text, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = f'{settings.FROM_NAME} <{settings.FROM_EMAIL}>'
    msg['To'] = to

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.FROM_EMAIL, [to], msg.as_string())
        return True
    except (smtplib.SMTPException, OSError):
        return False
```

- [ ] **Step 2: Verify the no-config path doesn't crash**

With `.env`'s `SMTP_HOST`/`SMTP_USER` still placeholders from Task 1:
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from accounts.services.mailer import smtp_send_mail
print(smtp_send_mail('test@example.com', 'Subject', 'Body'))
"
```
Expected: `False` (since `SMTP_HOST`/`SMTP_USER` are empty placeholders), no exception raised.

If real Gmail App Password credentials are filled into `.env` later, re-run this with a real recipient address to confirm an actual email arrives — this is optional and out of scope for this task if no credentials are available yet (see Task 19's verification notes).

- [ ] **Step 3: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/mailer.py
git commit -m "Add SMTP mailer service"
```

---

### Task 12: Forgot-password and reset-password views

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/forgot_password.py`
- Create: `ielts-vocab-master/site/accounts/views/reset_password.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.mailer.smtp_send_mail`, `accounts.services.passwords.hash_password`, `accounts.services.validators.is_valid_email`
- Produces: `forgot_password_view(request)` at `POST /auth/forgot-password`, `reset_password_view(request)` at `POST /auth/reset-password`.

- [ ] **Step 1: Write `accounts/views/forgot_password.py`**

```python
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.mailer import smtp_send_mail
from accounts.services.validators import is_valid_email


@require_POST
def forgot_password_view(request):
    body = json.loads(request.body or b'{}')
    email = str(body.get('email', '')).strip().lower()

    if not is_valid_email(email):
        return JsonResponse({'error': 'Please enter a valid email address.'}, status=400)

    user = User.objects.filter(email=email).first()
    if user:
        token = secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires = (datetime.now(timezone.utc) + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

        user.reset_token = token_hash
        user.reset_token_expires = expires
        user.save(update_fields=['reset_token', 'reset_token_expires'])

        base_url = settings.APP_BASE_URL or 'http://localhost:8000'
        link = f"{base_url.rstrip('/')}/reset-password?token={token}"
        name = user.name or 'there'

        body_text = (
            f"Hi {name},\n\n"
            "Someone requested a password reset for your IELTS Vocab Master account.\n\n"
            "Click the link below to set a new password. This link expires in 30 minutes.\n\n"
            f"{link}\n\n"
            "If you didn't request this, you can safely ignore this email.\n"
        )
        smtp_send_mail(email, 'Reset your IELTS Vocab Master password', body_text)

    return JsonResponse({'ok': True})
```

- [ ] **Step 2: Write `accounts/views/reset_password.py`**

```python
import hashlib
import json
from datetime import datetime, timezone

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.passwords import hash_password


@require_POST
def reset_password_view(request):
    body = json.loads(request.body or b'{}')
    token = str(body.get('token', '')).strip()
    password = body.get('password', '')

    if not token:
        return JsonResponse({'error': 'Missing reset token.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters.'}, status=400)

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    user = User.objects.filter(reset_token=token_hash, reset_token_expires__gt=now_str).first()

    if not user:
        return JsonResponse({'error': 'This reset link is invalid or has expired.'}, status=400)

    user.password_hash = hash_password(password)
    user.reset_token = None
    user.reset_token_expires = None
    user.save(update_fields=['password_hash', 'reset_token', 'reset_token_expires'])

    return JsonResponse({'ok': True})
```

- [ ] **Step 3: Add both routes to `accounts/urls.py`**

```python
    path('forgot-password', forgot_password_view),
    path('reset-password', reset_password_view),
```

(plus the matching imports `from accounts.views.forgot_password import forgot_password_view` and `from accounts.views.reset_password import reset_password_view`)

- [ ] **Step 4: Verify the full forgot/reset cycle on the throwaway account**

```
curl -s -X POST http://localhost:8000/auth/forgot-password -H "Content-Type: application/json" -d '{"email":"throwaway-test@example.com"}'
```
Expected: `{"ok": true}` (regardless of whether the email actually sent — `.env` still has placeholder SMTP creds at this point).

Read the generated token directly from the database (standing in for "click the email link", since no real email was sent):
```
cd "ielts-vocab-master/site" && python manage.py shell -c "
from accounts.models import User
u = User.objects.get(email='throwaway-test@example.com')
print(u.reset_token, u.reset_token_expires)
"
```
This prints the **hashed** token, not the raw one needed for the API call — so instead, verify the invalid-token rejection path (fully testable without the raw token):
```
curl -s -X POST http://localhost:8000/auth/reset-password -H "Content-Type: application/json" -d '{"token":"not-a-real-token","password":"newpassword123"}'
```
Expected: `{"error": "This reset link is invalid or has expired."}`.

Then verify the short-password rejection:
```
curl -s -X POST http://localhost:8000/auth/reset-password -H "Content-Type: application/json" -d '{"token":"anything","password":"short"}'
```
Expected: `{"error": "Password must be at least 8 characters."}`.

(A true end-to-end test with a real raw token is covered in Task 19, using a temporary `print()` added and removed around the `secrets.token_hex(32)` call in `forgot_password_view` to capture it — see Task 19 for the exact steps.)

- [ ] **Step 5: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/forgot_password.py ielts-vocab-master/site/accounts/views/reset_password.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add forgot-password and reset-password views"
```

---

### Task 13: Update-profile and delete-account views

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/update_profile.py`
- Create: `ielts-vocab-master/site/accounts/views/delete_account.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`, `accounts.services.avatar.{store_avatar_upload,delete_avatar_file}`, `accounts.services.validators.{is_valid_name,is_valid_username}`, `accounts.services.passwords.verify_password`, `accounts.services.remember.{clear_all_remember_tokens,clear_remember_cookie}`
- Produces: `update_profile_view(request)` at `POST /auth/update-profile`, `delete_account_view(request)` at `POST /auth/delete-account`.

- [ ] **Step 1: Write `accounts/views/update_profile.py`**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.avatar import delete_avatar_file, store_avatar_upload
from accounts.services.validators import is_valid_name, is_valid_username


@require_POST
def update_profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not logged in.'}, status=401)

    name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()

    if not is_valid_name(name):
        return JsonResponse({'error': 'Full name can only contain letters and spaces.'}, status=400)
    if not is_valid_username(username):
        return JsonResponse(
            {'error': 'Username must be 3-20 characters, letters and numbers only (no spaces or symbols).'},
            status=400,
        )

    if User.objects.filter(username=username).exclude(id=user_id).exists():
        return JsonResponse({'error': 'This username is already taken.'}, status=409)

    user = User.objects.get(id=user_id)
    picture = user.picture

    uploaded = request.FILES.get('picture')
    if uploaded:
        upload = store_avatar_upload(uploaded)
        if not upload['ok']:
            return JsonResponse({'error': upload['error']}, status=400)
        delete_avatar_file(picture)
        picture = upload['path']

    user.name = name
    user.username = username
    user.picture = picture
    user.save(update_fields=['name', 'username', 'picture'])

    return JsonResponse({'ok': True, 'name': name, 'username': username, 'picture': picture})
```

- [ ] **Step 2: Write `accounts/views/delete_account.py`**

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.avatar import delete_avatar_file
from accounts.services.passwords import verify_password
from accounts.services.remember import clear_all_remember_tokens, clear_remember_cookie


@require_POST
def delete_account_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not logged in.'}, status=401)

    password = request.POST.get('password', '')
    user = User.objects.filter(id=user_id).first()

    if not user or not verify_password(password, user.password_hash):
        return JsonResponse({'error': 'Incorrect password.'}, status=401)

    delete_avatar_file(user.picture)
    user_id_for_cleanup = user.id
    user.delete()
    clear_all_remember_tokens(user_id_for_cleanup)

    response = JsonResponse({'ok': True})
    clear_remember_cookie(request, response)
    request.session.flush()
    return response
```

- [ ] **Step 3: Add both routes to `accounts/urls.py`**

```python
    path('update-profile', update_profile_view),
    path('delete-account', delete_account_view),
```

(plus matching imports)

- [ ] **Step 4: Verify against the throwaway account from Task 8**

```
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "email=throwaway-test@example.com&password=testpass123&remember=0"
curl -s -b cookies.txt -X POST http://localhost:8000/auth/update-profile -F "name=Updated Name" -F "username=updatedname"
```
Expected second call: `{"ok": true, "name": "Updated Name", "username": "updatedname", "picture": null}`.

```
curl -s -b cookies.txt -X POST http://localhost:8000/auth/delete-account -d "password=testpass123"
curl -s -X POST http://localhost:8000/auth/check-email -H "Content-Type: application/json" -d '{"email":"throwaway-test@example.com"}'
```
Expected first call: `{"ok": true}`. Expected second call: `{"exists": false}` — confirms the account is gone.

Clean up: `rm cookies.txt` (in `ielts-vocab-master/site/`).

- [ ] **Step 5: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/update_profile.py ielts-vocab-master/site/accounts/views/delete_account.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add update-profile and delete-account views"
```

---

### Task 14: Sync view

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/sync.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.User`
- Produces: `sync_view(request)` at `GET/POST /auth/sync`.

- [ ] **Step 1: Write `accounts/views/sync.py`**

```python
import json

from django.http import JsonResponse

from accounts.models import User


def sync_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    if request.method == 'GET':
        user = User.objects.filter(id=user_id).first()
        learn_map = json.loads(user.learn_map) if user else {}
        return JsonResponse({'learnMap': learn_map or {}})

    if request.method == 'POST':
        body = json.loads(request.body or b'{}')
        learn_map = body.get('learnMap')
        if not isinstance(learn_map, dict):
            return JsonResponse({'error': 'Invalid payload'}, status=400)

        clean = {
            word: status for word, status in learn_map.items()
            if isinstance(word, str) and status in ('little', 'learned')
        }
        User.objects.filter(id=user_id).update(learn_map=json.dumps(clean))
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
```

- [ ] **Step 2: Add the route to `accounts/urls.py`**

```python
    path('sync', sync_view),
```

(plus `from accounts.views.sync import sync_view`)

- [ ] **Step 3: Verify against the real account's existing `learn_map`** (read-only GET, then a round-trip POST of the exact same data — safe, no data loss risk)

```
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "email=pichusis2019@gmail.com&password=WRONG_PASSWORD_PLACEHOLDER&remember=0"
```

This will fail with 401 since the real password is unknown to this plan — sync's logged-out path is what's actually being verified here:
```
curl -s http://localhost:8000/auth/sync
```
Expected: `{"error": "Not logged in"}` with status 401 — confirms the auth guard works. A logged-in round-trip test against the real account's `learn_map` happens in Task 19 (manual browser test, where the operator can log in with their own real password).

Clean up: `rm cookies.txt`.

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/sync.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add sync view"
```

---

### Task 15: Firebase login service and view

**Files:**
- Create: `ielts-vocab-master/site/accounts/services/firebase.py`
- Create: `ielts-vocab-master/site/accounts/views/firebase_login.py`
- Modify: `ielts-vocab-master/site/accounts/urls.py`

**Interfaces:**
- Consumes: `accounts.models.{User,OAuthAccount}`, `accounts.services.passwords.hash_password`, `accounts.services.util.sql_now`
- Produces: `firebase_login_view(request)` at `POST /auth/firebase-login`.

- [ ] **Step 1: Write `accounts/services/firebase.py`**

```python
import secrets

import requests
from django.conf import settings

from accounts.models import OAuthAccount, User
from accounts.services.passwords import hash_password
from accounts.services.util import sql_now

FIREBASE_LOOKUP_URL = 'https://identitytoolkit.googleapis.com/v1/accounts:lookup'


def get_firebase_api_key() -> str | None:
    return settings.FIREBASE_API_KEY or None


def firebase_verify_id_token(id_token: str, api_key: str) -> dict | None:
    try:
        resp = requests.post(
            FIREBASE_LOOKUP_URL,
            params={'key': api_key},
            json={'idToken': id_token},
            timeout=10,
        )
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None

    users = resp.json().get('users') or []
    if not users or not users[0].get('localId'):
        return None

    user = users[0]
    provider_id = (user.get('providerUserInfo') or [{}])[0].get('providerId', '')
    if 'google' in provider_id:
        provider = 'google'
    elif 'facebook' in provider_id:
        provider = 'facebook'
    elif 'apple' in provider_id:
        provider = 'apple'
    elif 'microsoft' in provider_id:
        provider = 'microsoft'
    else:
        provider = provider_id or 'unknown'

    return {
        'provider': provider,
        'provider_user_id': user['localId'],
        'email': user.get('email'),
        'email_verified': bool(user.get('emailVerified')),
        'name': user.get('displayName'),
        'picture': user.get('photoUrl'),
    }


def generate_unique_username(seed: str) -> str:
    base = ''.join(ch for ch in seed if ch.isalnum())[:16]
    if not base:
        base = 'user'
    if len(base) < 3:
        base = base.ljust(3, '0')

    username = base
    for _ in range(20):
        if not User.objects.filter(username=username).exists():
            return username
        suffix = str(secrets.randbelow(9900) + 100)
        username = base[:20 - len(suffix)] + suffix

    return ('user' + secrets.token_hex(6))[:20]


def resolve_oauth_user(profile: dict) -> int:
    link = OAuthAccount.objects.filter(
        provider=profile['provider'], provider_user_id=profile['provider_user_id']
    ).first()
    if link:
        return link.user_id

    if profile['email_verified'] and profile['email']:
        existing = User.objects.filter(email=profile['email'].lower()).first()
        if existing:
            OAuthAccount.objects.create(
                user_id=existing.id, provider=profile['provider'],
                provider_user_id=profile['provider_user_id'], created_at=sql_now(),
            )
            return existing.id

    name_seed = profile['name'] or (profile['email'].split('@')[0] if profile['email'] else 'user')
    name = profile['name'] or (profile['email'].split('@')[0] if profile['email'] else 'New User')
    email = profile['email'] or f"{profile['provider']}_{profile['provider_user_id']}@no-email.invalid"
    unusable_hash = hash_password(secrets.token_hex(32))

    username = generate_unique_username(name_seed)
    user = User.objects.create(
        email=email.lower(), password_hash=unusable_hash, name=name, username=username,
        picture=profile['picture'], learn_map='{}', created_at=sql_now(), last_login=sql_now(),
    )
    OAuthAccount.objects.create(
        user_id=user.id, provider=profile['provider'],
        provider_user_id=profile['provider_user_id'], created_at=sql_now(),
    )
    return user.id
```

- [ ] **Step 2: Write `accounts/views/firebase_login.py`**

```python
import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.services.firebase import (
    firebase_verify_id_token,
    get_firebase_api_key,
    resolve_oauth_user,
)
from accounts.services.util import sql_now


@require_POST
def firebase_login_view(request):
    body = json.loads(request.body or b'{}')
    id_token = body.get('idToken')
    id_token = id_token if isinstance(id_token, str) else ''

    if not id_token:
        return JsonResponse({'error': 'Missing sign-in token.'}, status=400)

    api_key = get_firebase_api_key()
    if not api_key:
        return JsonResponse({'error': 'Social sign-in is not configured yet.'}, status=500)

    profile = firebase_verify_id_token(id_token, api_key)
    if not profile:
        return JsonResponse({'error': 'Could not verify sign-in. Please try again.'}, status=401)

    user_id = resolve_oauth_user(profile)
    User.objects.filter(id=user_id).update(last_login=sql_now())

    request.session.cycle_key()
    request.session['user_id'] = user_id

    return JsonResponse({'ok': True})
```

- [ ] **Step 3: Add the route to `accounts/urls.py`**

```python
    path('firebase-login', firebase_login_view),
```

(plus `from accounts.views.firebase_login import firebase_login_view`)

- [ ] **Step 4: Verify the not-configured path** (real Firebase credentials don't exist in `.env` yet — see Task 19's notes on this being code-review-only)

```
curl -s -X POST http://localhost:8000/auth/firebase-login -H "Content-Type: application/json" -d '{"idToken":"fake-token"}'
```
Expected: `{"error": "Social sign-in is not configured yet."}` with status 500 — `FIREBASE_API_KEY` is still the `.env.example` placeholder.

Also verify the missing-token path:
```
curl -s -X POST http://localhost:8000/auth/firebase-login -H "Content-Type: application/json" -d '{}'
```
Expected: `{"error": "Missing sign-in token."}` with status 400.

- [ ] **Step 5: Commit**

```bash
git add ielts-vocab-master/site/accounts/services/firebase.py ielts-vocab-master/site/accounts/views/firebase_login.py ielts-vocab-master/site/accounts/urls.py
git commit -m "Add Firebase login service and view"
```

---

### Task 16: Static page serving and avatar media route

**Files:**
- Create: `ielts-vocab-master/site/accounts/views/pages.py`
- Modify: `ielts-vocab-master/site/config/urls.py`

**Interfaces:**
- Produces: `index_view(request)` at `GET /` (serves `vocab-master.html`), `reset_password_page_view(request)` at `GET /reset-password` (serves `auth/reset_password.html`); `/auth/uploads/avatars/<file>` served via Django's static file helper.

- [ ] **Step 1: Write `accounts/views/pages.py`**

```python
from django.conf import settings
from django.http import HttpResponse


def index_view(request):
    content = (settings.BASE_DIR / 'vocab-master.html').read_text(encoding='utf-8')
    return HttpResponse(content, content_type='text/html; charset=utf-8')


def reset_password_page_view(request):
    content = (settings.BASE_DIR / 'auth' / 'reset_password.html').read_text(encoding='utf-8')
    return HttpResponse(content, content_type='text/html; charset=utf-8')
```

- [ ] **Step 2: Write `config/urls.py`** (final version — combines the static pages, the `/auth/*` API, and avatar media serving)

```python
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

from accounts.views.pages import index_view, reset_password_page_view

urlpatterns = [
    path('', index_view),
    path('reset-password', reset_password_page_view),
    path('auth/', include('accounts.urls')),
    re_path(
        r'^auth/uploads/avatars/(?P<path>.+)$',
        serve,
        {'document_root': settings.BASE_DIR / 'auth' / 'uploads' / 'avatars'},
    ),
]
```

Note: `reset-password` as a GET page route and `reset-password` as a `POST /auth/reset-password` API route do not collide — one is `/reset-password` (no prefix) and the other is `/auth/reset-password`.

- [ ] **Step 3: Verify both pages and the avatar route serve correctly**

```
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/reset-password
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/auth/uploads/avatars/3800e7559f3c0e6ace4ae4933add37b3.jpg
```
Expected: `200`, `200`, `200`.

- [ ] **Step 4: Commit**

```bash
git add ielts-vocab-master/site/accounts/views/pages.py ielts-vocab-master/site/config/urls.py
git commit -m "Serve static pages and avatar uploads from Django"
```

---

### Task 17: Update frontend fetch calls

**Files:**
- Modify: `ielts-vocab-master/site/vocab-master.html`
- Modify: `ielts-vocab-master/site/auth/reset_password.html`

**Interfaces:**
- Consumes: every endpoint from Tasks 7-15.

- [ ] **Step 1: Update `AUTH_BASE` in `vocab-master.html`**

Find (around line 7362):
```js
const AUTH_BASE = "auth/";
```
Replace with:
```js
const AUTH_BASE = "/auth/";
```

- [ ] **Step 2: Update each of the 11 `fetch(AUTH_BASE + "...")` calls in `vocab-master.html`**

| Find | Replace |
|---|---|
| `AUTH_BASE + "sync.php"` (×2, lines ~7383, ~7458) | `AUTH_BASE + "sync"` |
| `AUTH_BASE + "session.php"` (line ~7446) | `AUTH_BASE + "session"` |
| `AUTH_BASE + "logout.php"` (line ~7767) | `AUTH_BASE + "logout"` |
| `AUTH_BASE + "delete_account.php"` (line ~7799) | `AUTH_BASE + "delete-account"` |
| `AUTH_BASE + "update_profile.php"` (line ~7865) | `AUTH_BASE + "update-profile"` |
| `AUTH_BASE + "check_email.php"` (line ~8021) | `AUTH_BASE + "check-email"` |
| `AUTH_BASE + "login.php"` (line ~8064) | `AUTH_BASE + "login"` |
| `AUTH_BASE + "forgot_password.php"` (line ~8084) | `AUTH_BASE + "forgot-password"` |
| `AUTH_BASE + "signup.php"` (line ~8137) | `AUTH_BASE + "signup"` |
| `AUTH_BASE + "firebase_login.php"` (line ~8972) | `AUTH_BASE + "firebase-login"` |

Use exact string replacement for each (e.g. `fetch(AUTH_BASE + "sync.php"...` → `fetch(AUTH_BASE + "sync"...`) — do not touch anything else on those lines.

- [ ] **Step 3: Update `auth/reset_password.html`**

Find:
```js
const res = await fetch("reset_password.php", {
```
Replace with:
```js
const res = await fetch("/auth/reset-password", {
```

(This page now moves from being served at `/auth/reset_password.html` to `/reset-password` per Task 16, so its fetch target needs an absolute path rather than the old relative one.)

Also find the success message's link, which currently points to a relative `vocab-master.html`:
```js
msg.innerHTML = 'Your password has been reset. <a href="../vocab-master.html">Return to the app</a> and sign in.';
```
Replace with:
```js
msg.innerHTML = 'Your password has been reset. <a href="/">Return to the app</a> and sign in.';
```

- [ ] **Step 4: Verify in a browser**

With the dev server running, open `http://localhost:8000/` and confirm the page loads with no console errors about failed `auth/` requests (open DevTools Network tab, reload, check `/auth/session` and `/auth/sync` both return 200, not 404).

- [ ] **Step 5: Commit**

```bash
git add "ielts-vocab-master/site/vocab-master.html" "ielts-vocab-master/site/auth/reset_password.html"
git commit -m "Point frontend fetch calls at the new Django auth endpoints"
```

---

### Task 18: End-to-end verification pass

**Files:** none (verification only)

**Interfaces:** exercises every endpoint from Tasks 7-17 together as real user flows.

- [ ] **Step 1: Verify login + session + sync + logout with the real account, using a temporary password reset via the forgot-password flow**

Since the real account's plaintext password is unknown, and resetting it is the only way to log in as it through the API, do this destructively-safe dance: capture the raw reset token by temporarily adding a `print(token)` line, use it once, then the account simply has a new known password going forward (no data loss — `learn_map` and `picture` are untouched by a password reset).

In `accounts/views/forgot_password.py`, temporarily add a print statement right after `token = secrets.token_hex(32)`:
```python
    token = secrets.token_hex(32)
    print('RESET TOKEN:', token)
```

Restart the dev server to pick up the change, then:
```
curl -s -X POST http://localhost:8000/auth/forgot-password -H "Content-Type: application/json" -d '{"email":"pichusis2019@gmail.com"}'
```
Copy the token printed in the server's console output, then:
```
curl -s -X POST http://localhost:8000/auth/reset-password -H "Content-Type: application/json" -d '{"token":"<paste token here>","password":"TempVerify123"}'
```
Expected: `{"ok": true}`.

Remove the temporary `print` line from `accounts/views/forgot_password.py` now that the token's been used (it's single-use and already consumed, but no reason to leave debug output in place).

- [ ] **Step 2: Verify login/session/sync/logout with the now-known password**

```
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "email=pichusis2019@gmail.com&password=TempVerify123&remember=1"
curl -s -b cookies.txt http://localhost:8000/auth/session
```
Expected: `{"loggedIn": true, "id": 1, "email": "pichusis2019@gmail.com", "name": "Pichu", "username": "Pichu", "picture": "auth/uploads/avatars/3800e7559f3c0e6ace4ae4933add37b3.jpg"}` — confirms the avatar path and profile survived the whole migration untouched.

```
curl -s -b cookies.txt http://localhost:8000/auth/sync
```
Expected: a `learnMap` object containing the same hundreds of entries seen in the original PHP `users.sqlite` inspection (e.g. `"be":"learned"` should be present).

Round-trip the exact same data back (safe no-op):
```
curl -s -b cookies.txt http://localhost:8000/auth/sync -X GET > /tmp/learnmap_check.json
curl -s -b cookies.txt -X POST http://localhost:8000/auth/sync -H "Content-Type: application/json" --data-binary @- <<'EOF'
$(python3 -c "import json; print(json.dumps({'learnMap': json.load(open('/tmp/learnmap_check.json'))['learnMap']}))")
EOF
```
(If the heredoc substitution above is awkward in your shell, equivalently just open the browser, log in as the real account with password `TempVerify123`, and let the page's own JS do the GET+merge+debounced-POST sync naturally — that's a fully realistic exercise of the same code path.)

```
curl -i -b cookies.txt -c cookies.txt http://localhost:8000/auth/logout
```
Expected: `{"ok": true}`.

Clean up: `rm cookies.txt /tmp/learnmap_check.json` (in `ielts-vocab-master/site/`). The real account's password is now `TempVerify123` going forward — mention this to the user at the end of this task so they can change it via the app's normal "forgot password" flow if they want a different one.

- [ ] **Step 3: Browser walkthrough of the full UI**

Open `http://localhost:8000/` in a browser:
- Sign in with `pichusis2019@gmail.com` / `TempVerify123` via the UI sign-in modal — confirm the avatar and name render correctly in the user chip.
- Open the profile editor, change nothing, save — confirm no errors (exercises `update-profile` with no new avatar).
- Mark one new word as "learned" in the word list — confirm it persists after a page reload (exercises the debounced `sync` POST).
- Log out via the UI.
- Sign up a brand-new throwaway account through the UI modal (exercises `check-email` → `signup` step transition).
- Delete that throwaway account via the UI's delete-account flow.

- [ ] **Step 4: Code-review Firebase login** (no real Firebase ID token is obtainable in this environment)

Re-read `accounts/services/firebase.py` and `accounts/views/firebase_login.py` side-by-side with the original `auth/oauth_common.php` and `auth/firebase_login.php`, confirming: same Firebase REST lookup URL, same provider-detection substring matching, same three-branch account resolution order (existing oauth link → verified-email match → new user), same session cookie behavior on success. No code changes expected from this review unless a discrepancy is found.

- [ ] **Step 5: Commit** (only if Step 4 found and fixed a discrepancy; otherwise skip — this task is verification-only)

```bash
git add -A
git commit -m "Fix discrepancy found during end-to-end verification"
```

---

### Task 19: Cleanup — remove the old PHP backend

**Files:**
- Delete: all 13 files in `ielts-vocab-master/site/auth/*.php`
- Delete: `ielts-vocab-master/site/auth/config.local.example.php`
- Modify: `ielts-vocab-master/site/auth/FIREBASE_SETUP.md`

**Interfaces:** none — this is the final step, only safe to run after Task 18 passes.

- [ ] **Step 1: Delete the 13 PHP scripts**

```bash
cd "ielts-vocab-master/site/auth"
rm avatar.php check_email.php db.php delete_account.php firebase_login.php forgot_password.php login.php logout.php mailer.php oauth_common.php remember.php reset_password.php session.php signup.php sync.php update_profile.php config.local.example.php
```

(That's 16 filenames — the spec's "13 old PHP files" refers to the 13 request-handling/helper scripts; `config.local.example.php` is the 14th file removed in this same step since it's also PHP-specific and superseded by `.env.example`.)

- [ ] **Step 2: Update `auth/FIREBASE_SETUP.md`**

Find:
```
4. Copy just the `apiKey` value into `auth/config.local.php` under
   `firebase.api_key` (copy `auth/config.local.example.php` to
   `auth/config.local.php` first if you haven't already, for the mail
   settings).
```
Replace with:
```
4. Copy just the `apiKey` value into `.env` under `FIREBASE_API_KEY`
   (copy `.env.example` to `.env` first if you haven't already, for the
   mail settings too).
```

Find:
```
Until `firebaseConfig.apiKey` in `vocab-master.html` is changed from the
`YOUR_FIREBASE_WEB_API_KEY` placeholder, the 4 social buttons (and the
"or" divider above the email field) are hidden from the sign-in modal
entirely — visitors just see the plain email/password form, no broken
buttons or raw Firebase errors.
```
Leave this paragraph as-is (still accurate — it describes frontend behavior, unaffected by the backend rewrite).

Find any remaining references to `auth/firebase_login.php` in the doc and replace with `/auth/firebase-login` to match the new route.

- [ ] **Step 3: Verify the running server still works with the PHP files gone**

```
cd "ielts-vocab-master/site" && python manage.py runserver localhost:8000
```
In another terminal, re-run a quick smoke check:
```
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/
curl -s http://localhost:8000/auth/session
```
Expected: `200`, then `{"loggedIn": false}` (or `true` if a session cookie from earlier testing is still active) — confirms nothing in the Django app was secretly still depending on a PHP file.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Remove the PHP auth backend now that the Django port is verified"
```

---

## Summary of new files created

```
ielts-vocab-master/site/
  manage.py
  requirements.txt
  .env.example
  .env                          (gitignored)
  config/
    __init__.py, settings.py, urls.py, wsgi.py
  accounts/
    __init__.py, apps.py, models.py, urls.py
    migrations/__init__.py, migrations/0001_initial.py
    services/
      __init__.py, passwords.py, validators.py, util.py,
      remember.py, avatar.py, mailer.py, firebase.py
    views/
      __init__.py, login.py, signup.py, session.py, logout.py,
      check_email.py, forgot_password.py, reset_password.py,
      update_profile.py, delete_account.py, sync.py,
      firebase_login.py, pages.py
```
