# IELTS Vocab Master — Django Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ielts-vocab-master/Python/Django/` — a Django app with database-backed vocabulary, a staff/admin dashboard for managing words/categories/colors/CEFR levels, professional auth (django-allauth + 2FA + RBAC), and a single `runserver` command that serves everything.

**Architecture:** Four Django apps (`accounts`, `vocab`, `dashboard`, `api`) plus allauth headless for JSON auth endpoints. Vocabulary data moves from static JS files into SQLite via a management command. The existing Flask app moves into `Python/Flask/` unchanged.

**Tech Stack:** Django 5.x, django-allauth 65.x (with `[mfa]` extra), python-dotenv, Pillow, json5, pytest-django, Bootstrap 5 (CDN)

## Global Constraints

- Python 3.11+; Django `>=5.0,<6.0`; django-allauth `>=65.0` with `[mfa]` extra
- `AUTH_USER_MODEL = 'accounts.CustomUser'` set in settings before any migration
- All migrations run from `ielts-vocab-master/Python/Django/`
- Allauth headless endpoints mount at `/_allauth/browser/v1/…` (no custom auth views for login/signup/logout/password-reset — allauth handles those)
- Dashboard routes protected by `@role_required('staff')` or `@role_required('admin')` wrapping `@login_required`
- Staff and admin users must have 2FA active to reach `/dashboard/` — enforced in `DashboardMFAMiddleware`
- CSRF: frontend fetch calls include `X-CSRFToken` header read from `csrftoken` cookie (`CSRF_COOKIE_HTTPONLY = False`)
- Avatar uploads stored under `media/avatars/`, served at `/media/avatars/` in dev
- Word model has fields the spec omitted but the JS data requires: `pos`, `synonyms`, `antonyms`, `gap`
- Category model has fields the spec omitted: `slug` (unique, e.g. `"neg-intensity"`), `icon` (emoji)
- No automated UI tests; use `pytest-django` for models and JSON API views only
- All paths below are relative to `ielts-vocab-master/Python/Django/` unless stated otherwise

---

## File Map

```
[repo root]/ielts-vocab-master/Python/
  Flask/                        ← moved here in Task 1 (was Python/ directly)
    auth/
    vocab-master.html

  Django/                       ← created Tasks 2–13
    manage.py
    pytest.ini
    conftest.py
    requirements.txt
    .env.example
    db.sqlite3                  ← created by migrate (gitignored)
    media/                      ← created by avatar upload (gitignored)

    config/
      __init__.py
      settings.py
      urls.py

    accounts/
      __init__.py
      models.py                 ← CustomUser(AbstractUser) with role field
      adapters.py               ← AccountAdapter: username gen, role init
      decorators.py             ← @role_required(role)
      middleware.py             ← DashboardMFAMiddleware
      views.py                  ← sync, update_profile, delete_account, check_email
      urls.py
      migrations/
        __init__.py

    vocab/
      __init__.py
      models.py                 ← CEFRLevel, Color, Category, Word
      admin.py                  ← register models (emergency access only)
      migrations/
        __init__.py
      management/
        __init__.py
        commands/
          __init__.py
          import_vocab.py       ← parse 11 JS files, seed DB

    api/
      __init__.py
      views.py                  ← /api/words/, /api/categories/, /api/cefr-levels/
      urls.py

    dashboard/
      __init__.py
      forms.py                  ← WordForm, CategoryForm, ColorForm, CEFRForm, UserRoleForm
      views.py                  ← all dashboard views
      urls.py
      templates/
        dashboard/
          base.html
          index.html
          words/
            list.html
            form.html
          categories/
            list.html
            form.html
          colors/
            list.html
            form.html
          cefr/
            list.html
          users/
            list.html
            detail.html

    templates/
      base.html                 ← project-level base (used by dashboard base)

    vocab-master.html           ← rewritten to fetch from Django API

    tests/
      __init__.py
      test_models.py
      test_auth_api.py
      test_vocab_api.py
      test_dashboard.py
```

---

## Task 1: Restructure Python → Flask subfolder

**Files:**
- Rename (git mv): `Python/auth/` → `Python/Flask/auth/`
- Rename (git mv): `Python/vocab-master.html` → `Python/Flask/vocab-master.html`
- Rename (git mv): `Python/data/` → `Python/Flask/data/` (if exists)

- [ ] **Step 1: Move tracked files with git mv**

Run from repo root `D:\IT RELATED\CLAUDE BOMBASTIC AI`:
```bash
mkdir -p ielts-vocab-master/Python/Flask
git mv ielts-vocab-master/Python/auth ielts-vocab-master/Python/Flask/auth
git mv ielts-vocab-master/Python/vocab-master.html ielts-vocab-master/Python/Flask/vocab-master.html
```
If `Python/data/` exists and is tracked:
```bash
git mv ielts-vocab-master/Python/data ielts-vocab-master/Python/Flask/data
```

- [ ] **Step 2: Verify the move**

```bash
ls ielts-vocab-master/Python/Flask/
```
Expected output: `auth/  vocab-master.html` (plus `data/` if it existed)

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move Flask app into Python/Flask/ subfolder"
```

---

## Task 2: Django project scaffold + config

**Files:**
- Create: `manage.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: `conftest.py`
- Create: `config/__init__.py`
- Create: `config/settings.py`
- Create: `config/urls.py`

- [ ] **Step 1: Create the Django folder and install dependencies**

```bash
mkdir -p ielts-vocab-master/Python/Django
cd ielts-vocab-master/Python/Django
pip install "django>=5.0,<6.0" "django-allauth[mfa]>=65.0" python-dotenv Pillow json5 pytest-django
```

- [ ] **Step 2: Scaffold the project**

```bash
django-admin startproject config .
```

This creates `manage.py` and `config/` with default files. We will overwrite `settings.py` and `urls.py` in the next steps.

- [ ] **Step 3: Write requirements.txt**

`requirements.txt`:
```
django>=5.0,<6.0
django-allauth[mfa]>=65.0
python-dotenv>=1.0
Pillow>=10.0
json5>=0.9
pytest-django>=4.8
```

- [ ] **Step 4: Write .env.example**

`.env.example`:
```
DJANGO_SECRET_KEY=change-me-to-a-long-random-string
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youraccount@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
FROM_EMAIL=youraccount@gmail.com
FROM_NAME=IELTS Vocab Master
APP_BASE_URL=http://localhost:8000
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
```

Copy to `.env` and fill in real values before running the server. `.env` is gitignored.

- [ ] **Step 5: Write config/settings.py**

`config/settings.py`:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.headless',
    'allauth.mfa',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.microsoft',
    'accounts',
    'vocab',
    'api',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.DashboardMFAMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# django-allauth
ACCOUNT_ADAPTER = 'accounts.adapters.AccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_SESSION_REMEMBER = None  # show "Remember me" checkbox

HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': '/verify-email/{key}',
    'account_reset_password_from_key': '/reset-password/{key}',
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASS', '')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = (
    f"{os.environ.get('FROM_NAME', 'IELTS Vocab Master')} "
    f"<{os.environ.get('FROM_EMAIL', '')}>"
)

# Media (user uploads)
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Static
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF: allow JS to read cookie so fetch() can send X-CSRFToken header
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

- [ ] **Step 6: Write config/urls.py** (stub — will be expanded in later tasks)

`config/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 7: Write pytest.ini and conftest.py**

`pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
pythonpath = .
```

`conftest.py`:
```python
import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def User():
    return get_user_model()


@pytest.fixture
def regular_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='user@example.com', username='regularuser',
        password='testpass123', role='user',
    )


@pytest.fixture
def staff_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='staff@example.com', username='staffuser',
        password='testpass123', role='staff',
    )


@pytest.fixture
def admin_user(db):
    U = get_user_model()
    return U.objects.create_user(
        email='admin@example.com', username='adminuser',
        password='testpass123', role='admin',
    )
```

- [ ] **Step 8: Create stub app directories and stub middleware/adapter files**

```bash
python manage.py startapp accounts
python manage.py startapp vocab
python manage.py startapp api
python manage.py startapp dashboard
```

This creates default files we'll overwrite. Delete the auto-generated `tests.py` and `views.py` in each app — we'll write our own.

`settings.py` references `accounts.middleware.DashboardMFAMiddleware` and `accounts.adapters.AccountAdapter` before Task 5 creates them. Create stubs now so `manage.py check` passes:

`accounts/middleware.py` (stub — replaced in Task 5):
```python
class DashboardMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)
```

`accounts/adapters.py` (stub — replaced in Task 5):
```python
from allauth.account.adapter import DefaultAccountAdapter

class AccountAdapter(DefaultAccountAdapter):
    pass
```

- [ ] **Step 9: Verify Django check passes**

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`
(Will show migration warnings — that's fine; we haven't run migrate yet.)

- [ ] **Step 10: Commit**

```bash
git add ielts-vocab-master/Python/Django/
git commit -m "feat: scaffold Django project with settings and app stubs"
```

---

## Task 3: CustomUser model

**Files:**
- Create: `accounts/models.py`
- Create: `accounts/migrations/__init__.py` (empty)
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces: `CustomUser` with fields `email`, `username`, `name`, `picture`, `role`, `learn_map`; `Role.USER / STAFF / ADMIN` choices; `USERNAME_FIELD = 'email'`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
def test_custom_user_email_is_username_field():
    User = get_user_model()
    assert User.USERNAME_FIELD == 'email'


@pytest.mark.django_db
def test_create_user_sets_default_role(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='test@example.com', username='tester', password='pw123456'
    )
    assert u.role == 'user'


@pytest.mark.django_db
def test_learn_map_defaults_to_empty_dict(db):
    User = get_user_model()
    u = User.objects.create_user(
        email='map@example.com', username='mapper', password='pw123456'
    )
    assert u.learn_map == {}


@pytest.mark.django_db
def test_role_choices_exist():
    User = get_user_model()
    roles = [r[0] for r in User.Role.choices]
    assert 'user' in roles
    assert 'staff' in roles
    assert 'admin' in roles
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```
Expected: `ERRORS` — `CustomUser` model not yet defined / migration missing.

- [ ] **Step 3: Write accounts/models.py**

`accounts/models.py`:
```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER  = 'user',  'User'
        STAFF = 'staff', 'Staff'
        ADMIN = 'admin', 'Admin'

    email    = models.EmailField(unique=True)
    username = models.CharField(max_length=20, unique=True)
    name     = models.CharField(max_length=60, blank=True)
    picture  = models.ImageField(upload_to='avatars/', blank=True)
    role     = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    learn_map = models.JSONField(default=dict)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
```

- [ ] **Step 4: Create and run the migration**

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

Expected: migration `accounts/0001_initial.py` created, all tables created.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```
Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add accounts/ tests/ migrations/
git commit -m "feat: add CustomUser model with role and learn_map fields"
```

---

## Task 4: Vocab models

**Files:**
- Create: `vocab/models.py`
- Create: `vocab/admin.py`
- Modify: `tests/test_models.py` (append vocab model tests)

**Interfaces:**
- Produces: `CEFRLevel(code, name, order)`, `Color(name, bg_hex, text_hex)`, `Category(slug, name, icon, cefr_level, color, order)`, `Word(word, pos, definition, synonyms, antonyms, example, gap, category, cefr_level, order)`

- [ ] **Step 1: Write the failing tests** (append to `tests/test_models.py`)

```python
import pytest
from vocab.models import CEFRLevel, Color, Category, Word


@pytest.mark.django_db
def test_cefr_level_str():
    level = CEFRLevel.objects.create(code='B2', name='Upper-Intermediate', order=4)
    assert str(level) == 'B2'


@pytest.mark.django_db
def test_category_requires_unique_slug(db):
    from django.db import IntegrityError
    CEFRLevel.objects.create(code='A1', name='Beginner', order=1)
    Category.objects.create(slug='test-cat', name='Test')
    with pytest.raises(IntegrityError):
        Category.objects.create(slug='test-cat', name='Duplicate')


@pytest.mark.django_db
def test_word_synonyms_defaults_to_list(db):
    level = CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)
    cat = Category.objects.create(slug='test', name='Test')
    w = Word.objects.create(
        word='Tenacious', definition='Not giving up easily.', category=cat
    )
    assert w.synonyms == []
    assert w.antonyms == []


@pytest.mark.django_db
def test_deleting_category_cascades_to_words(db):
    cat = Category.objects.create(slug='cascade-test', name='Cascade')
    Word.objects.create(word='Example', definition='A word.', category=cat)
    cat.delete()
    assert Word.objects.count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v -k "cefr or category or word or synonyms or cascade"
```
Expected: `ERROR` — `vocab.models` not yet defined.

- [ ] **Step 3: Write vocab/models.py**

`vocab/models.py`:
```python
from django.db import models


class CEFRLevel(models.Model):
    code  = models.CharField(max_length=2, unique=True)
    name  = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.code


class Color(models.Model):
    name     = models.CharField(max_length=50)
    bg_hex   = models.CharField(max_length=7)
    text_hex = models.CharField(max_length=7)

    def __str__(self):
        return self.name


class Category(models.Model):
    slug       = models.SlugField(max_length=100, unique=True)
    name       = models.CharField(max_length=100)
    icon       = models.CharField(max_length=10, blank=True)
    cefr_level = models.ForeignKey(
        CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL
    )
    color = models.ForeignKey(
        Color, null=True, blank=True, on_delete=models.SET_NULL
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Word(models.Model):
    word       = models.CharField(max_length=200)
    pos        = models.CharField(max_length=20, blank=True)
    definition = models.TextField()
    synonyms   = models.JSONField(default=list)
    antonyms   = models.JSONField(default=list)
    example    = models.TextField(blank=True)
    gap        = models.TextField(blank=True)
    category   = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='words'
    )
    cefr_level = models.ForeignKey(
        CEFRLevel, null=True, blank=True, on_delete=models.SET_NULL
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.word
```

- [ ] **Step 4: Write vocab/admin.py**

`vocab/admin.py`:
```python
from django.contrib import admin
from .models import CEFRLevel, Color, Category, Word

admin.site.register(CEFRLevel)
admin.site.register(Color)
admin.site.register(Category)
admin.site.register(Word)
```

- [ ] **Step 5: Create and run the migration**

```bash
python manage.py makemigrations vocab
python manage.py migrate
```

Expected: `vocab/0001_initial.py` created, vocab tables created.

- [ ] **Step 6: Run all model tests**

```bash
pytest tests/test_models.py -v
```
Expected: all tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add vocab/ tests/test_models.py
git commit -m "feat: add vocab models (CEFRLevel, Color, Category, Word)"
```

---

## Task 5: Allauth setup + AccountAdapter + decorators + middleware

**Files:**
- Create: `accounts/adapters.py`
- Create: `accounts/decorators.py`
- Create: `accounts/middleware.py`
- Create: `accounts/urls.py` (stub, expanded in Task 6)

**Interfaces:**
- Produces: `AccountAdapter` (auto-generates username on OAuth, sets role=USER); `@role_required('staff')` decorator; `DashboardMFAMiddleware` (redirects dashboard requests to 2FA setup if MFA not active)

- [ ] **Step 1: Run initial migrations for allauth**

```bash
python manage.py migrate
```
Expected: allauth tables (`socialaccount_*`, `account_*`, `mfa_*`, `django_site`) created.

- [ ] **Step 2: Create the default Site record**

```bash
python manage.py shell -c "
from django.contrib.sites.models import Site
Site.objects.update_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'IELTS Vocab Master'})
"
```

- [ ] **Step 3: Write accounts/adapters.py**

`accounts/adapters.py`:
```python
import re
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.auth import get_user_model


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        user.role = 'user'
        if commit:
            user.save()
        return user

    def populate_username(self, request, user):
        email = user.email or ''
        base = re.sub(r'[^a-z0-9_]', '_', email.split('@')[0].lower())[:18]
        base = base or 'user'
        username = base
        User = get_user_model()
        n = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{n}'
            n += 1
        user.username = username
```

- [ ] **Step 4: Write accounts/decorators.py**

`accounts/decorators.py`:
```python
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

_ROLE_ORDER = {'user': 0, 'staff': 1, 'admin': 2}


def role_required(min_role: str):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            user_level = _ROLE_ORDER.get(getattr(request.user, 'role', 'user'), 0)
            required_level = _ROLE_ORDER.get(min_role, 99)
            if user_level < required_level:
                return HttpResponseForbidden('Access denied.')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
```

- [ ] **Step 5: Write accounts/middleware.py**

`accounts/middleware.py`:
```python
from django.http import HttpResponseForbidden
from django.urls import reverse


class DashboardMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/dashboard/') and request.user.is_authenticated:
            role = getattr(request.user, 'role', 'user')
            if role in ('staff', 'admin'):
                from allauth.mfa.adapter import get_adapter
                adapter = get_adapter()
                if not adapter.is_mfa_enabled(request.user):
                    return HttpResponseForbidden(
                        'Dashboard requires 2FA. Enable it in your profile settings first.'
                    )
        return self.get_response(request)
```

- [ ] **Step 6: Write accounts/urls.py stub**

`accounts/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = []
```

- [ ] **Step 7: Run Django check**

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 8: Commit**

```bash
git add accounts/
git commit -m "feat: add allauth adapter, role_required decorator, dashboard MFA middleware"
```

---

## Task 6: Custom auth API views (sync, update-profile, delete-account, check-email)

**Files:**
- Modify: `accounts/views.py`
- Modify: `accounts/urls.py`
- Modify: `config/urls.py`
- Create: `tests/test_auth_api.py`

**Interfaces:**
- Consumes: `CustomUser.learn_map` (JSONField); `CustomUser.picture` (ImageField); `CustomUser.role`
- Produces:
  - `GET /auth/sync/` → `{"learn_map": {...}}`
  - `POST /auth/sync/` body `{"learn_map": {...}}` → `{"ok": true}`
  - `POST /auth/update-profile/` multipart → `{"ok": true}`
  - `POST /auth/delete-account/` body `{"password": "..."}` → `{"ok": true}`
  - `POST /auth/check-email/` body `{"email": "..."}` → `{"exists": true|false}`

- [ ] **Step 1: Write the failing tests**

`tests/test_auth_api.py`:
```python
import json
import pytest
from django.test import Client


@pytest.mark.django_db
def test_sync_get_requires_login():
    c = Client()
    r = c.get('/auth/sync/')
    assert r.status_code == 401


@pytest.mark.django_db
def test_sync_get_returns_learn_map(regular_user):
    regular_user.learn_map = {'42': 1700000000}
    regular_user.save()
    c = Client()
    c.force_login(regular_user)
    r = c.get('/auth/sync/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert data['learn_map'] == {'42': 1700000000}


@pytest.mark.django_db
def test_sync_post_updates_learn_map(regular_user):
    c = Client()
    c.force_login(regular_user)
    payload = json.dumps({'learn_map': {'7': 1700000001}})
    r = c.post('/auth/sync/', payload, content_type='application/json')
    assert r.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.learn_map == {'7': 1700000001}


@pytest.mark.django_db
def test_check_email_returns_false_for_unknown():
    c = Client()
    payload = json.dumps({'email': 'nobody@example.com'})
    r = c.post('/auth/check-email/', payload, content_type='application/json',
               HTTP_X_CSRFTOKEN='test', enforce_csrf_checks=False)
    assert r.status_code == 200
    assert json.loads(r.content) == {'exists': False}


@pytest.mark.django_db
def test_check_email_returns_true_for_existing(regular_user):
    c = Client()
    payload = json.dumps({'email': regular_user.email})
    r = c.post('/auth/check-email/', payload, content_type='application/json',
               enforce_csrf_checks=False)
    assert r.status_code == 200
    assert json.loads(r.content) == {'exists': True}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth_api.py -v
```
Expected: all fail with 404 (routes not defined yet).

- [ ] **Step 3: Write accounts/views.py**

`accounts/views.py`:
```python
import json
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

User = get_user_model()


def _require_auth(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not logged in.'}, status=401)
    return None


@require_http_methods(['GET', 'POST'])
def sync(request):
    err = _require_auth(request)
    if err:
        return err
    if request.method == 'GET':
        return JsonResponse({'learn_map': request.user.learn_map})
    body = json.loads(request.body or '{}')
    request.user.learn_map = body.get('learn_map', {})
    request.user.save(update_fields=['learn_map'])
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def update_profile(request):
    err = _require_auth(request)
    if err:
        return err
    user = request.user
    name = request.POST.get('name', '').strip()
    username = request.POST.get('username', '').strip()

    if name:
        if len(name) > 60:
            return JsonResponse({'error': 'Name too long (max 60 chars).'}, status=400)
        user.name = name

    if username:
        if not (3 <= len(username) <= 20) or not username.isalnum():
            return JsonResponse(
                {'error': 'Username must be 3–20 alphanumeric characters.'}, status=400
            )
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            return JsonResponse({'error': 'Username already taken.'}, status=409)
        user.username = username

    if 'picture' in request.FILES:
        f = request.FILES['picture']
        if f.size > 2 * 1024 * 1024:
            return JsonResponse({'error': 'Image must be under 2 MB.'}, status=400)
        if user.picture:
            user.picture.delete(save=False)
        user.picture = f

    user.save()
    return JsonResponse({'ok': True})


@require_http_methods(['POST'])
def delete_account(request):
    err = _require_auth(request)
    if err:
        return err
    body = json.loads(request.body or '{}')
    password = body.get('password', '')
    if not request.user.check_password(password):
        return JsonResponse({'error': 'Incorrect password.'}, status=401)
    if request.user.picture:
        request.user.picture.delete(save=False)
    request.user.delete()
    request.session.flush()
    return JsonResponse({'ok': True})


@csrf_exempt
@require_http_methods(['POST'])
def check_email(request):
    body = json.loads(request.body or '{}')
    email = body.get('email', '').strip().lower()
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})
```

- [ ] **Step 4: Write accounts/urls.py**

`accounts/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('sync/', views.sync, name='auth_sync'),
    path('update-profile/', views.update_profile, name='auth_update_profile'),
    path('delete-account/', views.delete_account, name='auth_delete_account'),
    path('check-email/', views.check_email, name='auth_check_email'),
]
```

- [ ] **Step 5: Mount in config/urls.py**

`config/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_auth_api.py -v
```
Expected: 5 PASSED.

- [ ] **Step 7: Commit**

```bash
git add accounts/ config/urls.py tests/test_auth_api.py
git commit -m "feat: add custom auth API views (sync, update-profile, delete-account, check-email)"
```

---

## Task 7: Vocab API views

**Files:**
- Create: `api/views.py`
- Create: `api/urls.py`
- Modify: `config/urls.py`
- Create: `tests/test_vocab_api.py`

**Interfaces:**
- Consumes: `vocab.models.Word`, `vocab.models.Category`, `vocab.models.CEFRLevel`
- Produces:
  - `GET /api/words/` → `[{"id":1,"word":"Heinous","pos":"adj","definition":"...","synonyms":[...],"antonyms":[...],"example":"...","gap":"...","category_id":1,"cefr_code":"C2","order":0}, ...]`
  - `GET /api/categories/` → `[{"id":1,"slug":"neg-intensity","name":"Negative Intensity","icon":"🔥","cefr_code":"C2","bg_hex":"#ef4444","text_hex":"#ffffff","order":0}, ...]`
  - `GET /api/cefr-levels/` → `[{"id":1,"code":"A1","name":"Beginner","order":1}, ...]`

- [ ] **Step 1: Write the failing tests**

`tests/test_vocab_api.py`:
```python
import json
import pytest
from django.test import Client
from vocab.models import CEFRLevel, Color, Category, Word


@pytest.fixture
def sample_data(db):
    level = CEFRLevel.objects.create(code='B2', name='Upper-Intermediate', order=4)
    color = Color.objects.create(name='Blue', bg_hex='#3b82f6', text_hex='#ffffff')
    cat = Category.objects.create(
        slug='strength', name='Strength', icon='💪', cefr_level=level, color=color
    )
    word = Word.objects.create(
        word='Tenacious', pos='adj', definition='Not giving up.',
        synonyms=['persistent'], antonyms=['weak'], example='She was tenacious.',
        gap='She was ___ in her pursuit.', category=cat, cefr_level=level, order=0
    )
    return {'level': level, 'color': color, 'cat': cat, 'word': word}


@pytest.mark.django_db
def test_words_endpoint_returns_list(sample_data):
    c = Client()
    r = c.get('/api/words/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert len(data) == 1
    assert data[0]['word'] == 'Tenacious'
    assert data[0]['pos'] == 'adj'
    assert data[0]['synonyms'] == ['persistent']
    assert data[0]['category_id'] == sample_data['cat'].id


@pytest.mark.django_db
def test_categories_endpoint_returns_list(sample_data):
    c = Client()
    r = c.get('/api/categories/')
    assert r.status_code == 200
    data = json.loads(r.content)
    assert len(data) == 1
    assert data[0]['slug'] == 'strength'
    assert data[0]['bg_hex'] == '#3b82f6'


@pytest.mark.django_db
def test_cefr_levels_endpoint_returns_ordered_list(db):
    CEFRLevel.objects.create(code='B1', name='Intermediate', order=3)
    CEFRLevel.objects.create(code='A1', name='Beginner', order=1)
    c = Client()
    r = c.get('/api/cefr-levels/')
    data = json.loads(r.content)
    assert data[0]['code'] == 'A1'
    assert data[1]['code'] == 'B1'
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_vocab_api.py -v
```
Expected: all fail with 404.

- [ ] **Step 3: Write api/views.py**

`api/views.py`:
```python
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from vocab.models import CEFRLevel, Category, Word


@require_GET
def words(request):
    qs = Word.objects.select_related('cefr_level', 'category').order_by('category__order', 'order')
    data = [
        {
            'id':          w.id,
            'word':        w.word,
            'pos':         w.pos,
            'definition':  w.definition,
            'synonyms':    w.synonyms,
            'antonyms':    w.antonyms,
            'example':     w.example,
            'gap':         w.gap,
            'category_id': w.category_id,
            'cefr_code':   w.cefr_level.code if w.cefr_level else None,
            'order':       w.order,
        }
        for w in qs
    ]
    return JsonResponse(data, safe=False)


@require_GET
def categories(request):
    qs = Category.objects.select_related('cefr_level', 'color').order_by('order')
    data = [
        {
            'id':       c.id,
            'slug':     c.slug,
            'name':     c.name,
            'icon':     c.icon,
            'cefr_code': c.cefr_level.code if c.cefr_level else None,
            'bg_hex':   c.color.bg_hex if c.color else None,
            'text_hex': c.color.text_hex if c.color else None,
            'order':    c.order,
        }
        for c in qs
    ]
    return JsonResponse(data, safe=False)


@require_GET
def cefr_levels(request):
    qs = CEFRLevel.objects.order_by('order')
    data = [{'id': l.id, 'code': l.code, 'name': l.name, 'order': l.order} for l in qs]
    return JsonResponse(data, safe=False)
```

- [ ] **Step 4: Write api/urls.py**

`api/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('words/', views.words, name='api_words'),
    path('categories/', views.categories, name='api_categories'),
    path('cefr-levels/', views.cefr_levels, name='api_cefr_levels'),
]
```

- [ ] **Step 5: Mount in config/urls.py**

Add `path('api/', include('api.urls')),` to `urlpatterns` in `config/urls.py`.

`config/urls.py` final:
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_vocab_api.py -v
```
Expected: 3 PASSED.

- [ ] **Step 7: Commit**

```bash
git add api/ config/urls.py tests/test_vocab_api.py
git commit -m "feat: add vocab API endpoints (words, categories, cefr-levels)"
```

---

## Task 8: import_vocab management command

**Files:**
- Create: `vocab/management/__init__.py`
- Create: `vocab/management/commands/__init__.py`
- Create: `vocab/management/commands/import_vocab.py`

**Interfaces:**
- Consumes: `../../React-Native/src/data/data-part1.js` … `data-part11.js` (relative to `Django/`)
- Produces: `CEFRLevel`, `Color`, `Category`, `Word` records in the DB; idempotent (skips existing by slug/code)

- [ ] **Step 1: Check unique theme values across all data files**

Run from `Django/` directory:
```bash
python -c "
import pathlib, re
data_dir = pathlib.Path('../../../React-Native/src/data')
themes = set()
for f in sorted(data_dir.glob('data-part*.js')):
    themes.update(re.findall(r'theme:\"(\w+)\"', f.read_text(encoding='utf-8')))
print(sorted(themes))
"
```
Note the output. Common values are `tr`, `tg`, `tro`, `tb` — add any extra ones to `THEME_MAP` in the next step.

- [ ] **Step 2: Write vocab/management/commands/import_vocab.py**

`vocab/management/commands/import_vocab.py`:
```python
import json5
import pathlib
import re
from django.core.management.base import BaseCommand
from vocab.models import CEFRLevel, Color, Category, Word

THEME_MAP = {
    'tr':  {'name': 'Red',    'bg_hex': '#ef4444', 'text_hex': '#ffffff'},
    'tg':  {'name': 'Green',  'bg_hex': '#22c55e', 'text_hex': '#ffffff'},
    'tro': {'name': 'Orange', 'bg_hex': '#f97316', 'text_hex': '#ffffff'},
    'tb':  {'name': 'Blue',   'bg_hex': '#3b82f6', 'text_hex': '#ffffff'},
    'tp':  {'name': 'Purple', 'bg_hex': '#a855f7', 'text_hex': '#ffffff'},
    'ty':  {'name': 'Yellow', 'bg_hex': '#eab308', 'text_hex': '#1a1a1a'},
    'tgy': {'name': 'Gray',   'bg_hex': '#6b7280', 'text_hex': '#ffffff'},
}

CEFR_META = [
    ('A1', 'Beginner', 1),
    ('A2', 'Elementary', 2),
    ('B1', 'Intermediate', 3),
    ('B2', 'Upper-Intermediate', 4),
    ('C1', 'Advanced', 5),
    ('C2', 'Proficient', 6),
]


class Command(BaseCommand):
    help = 'Seed DB from React-Native JS data files. Idempotent.'

    def handle(self, *args, **options):
        self._seed_cefr()
        self._seed_colors()

        data_dir = pathlib.Path(__file__).resolve().parents[5] / 'React-Native' / 'src' / 'data'
        files = sorted(data_dir.glob('data-part*.js'))
        if not files:
            self.stderr.write(f'No data files found in {data_dir}')
            return

        cat_order = 0
        for path in files:
            raw = path.read_text(encoding='utf-8')
            # Strip JS export wrapper: export const PARTX = [...];
            raw = re.sub(r'^export\s+const\s+\w+\s*=\s*', '', raw.strip())
            raw = raw.rstrip(';')
            categories = json5.loads(raw)
            for cat_data in categories:
                cat_order += 1
                self._import_category(cat_data, cat_order)

        self.stdout.write(self.style.SUCCESS(
            f'Done. Categories: {Category.objects.count()}, Words: {Word.objects.count()}'
        ))

    def _seed_cefr(self):
        for code, name, order in CEFR_META:
            CEFRLevel.objects.get_or_create(code=code, defaults={'name': name, 'order': order})

    def _seed_colors(self):
        for theme_code, attrs in THEME_MAP.items():
            Color.objects.get_or_create(name=attrs['name'], defaults={
                'bg_hex': attrs['bg_hex'], 'text_hex': attrs['text_hex']
            })

    def _import_category(self, data: dict, order: int):
        slug = data.get('id', '')
        if not slug:
            return

        theme = data.get('theme', '')
        color_name = THEME_MAP.get(theme, {}).get('name')
        color = Color.objects.filter(name=color_name).first() if color_name else None

        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name':  data.get('name', slug),
                'icon':  data.get('icon', ''),
                'color': color,
                'order': order,
            },
        )

        for word_order, w in enumerate(data.get('words', [])):
            cefr_code = w.get('cefr', '').rstrip('+')
            cefr = CEFRLevel.objects.filter(code=cefr_code).first()
            Word.objects.get_or_create(
                word=w.get('w', ''),
                category=cat,
                defaults={
                    'pos':        w.get('pos', ''),
                    'definition': w.get('def', ''),
                    'synonyms':   w.get('syn', []),
                    'antonyms':   w.get('ant', []),
                    'example':    w.get('ex', ''),
                    'gap':        w.get('gap', ''),
                    'cefr_level': cefr,
                    'order':      word_order,
                },
            )
```

- [ ] **Step 3: Run the command**

```bash
python manage.py import_vocab
```
Expected output:
```
Done. Categories: <N>, Words: <M>
```
Verify counts roughly match what you see in the JS files (there are 11 files, each with ~8-12 categories, ~12 words each → expect ~100 categories, ~1200 words).

- [ ] **Step 4: Verify via Django shell**

```bash
python manage.py shell -c "
from vocab.models import Word, Category, CEFRLevel
print('CEFRLevels:', CEFRLevel.objects.count())
print('Categories:', Category.objects.count())
print('Words:', Word.objects.count())
print('Sample:', Word.objects.first())
"
```

- [ ] **Step 5: Commit**

```bash
git add vocab/management/ vocab/management/commands/
git commit -m "feat: add import_vocab command to seed DB from React-Native JS data files"
```

---

## Task 9: Dashboard base + overview + access control tests

**Files:**
- Create: `dashboard/views.py` (overview only)
- Create: `dashboard/urls.py`
- Create: `dashboard/templates/dashboard/base.html`
- Create: `dashboard/templates/dashboard/index.html`
- Modify: `config/urls.py`
- Create: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `@role_required('staff')` from `accounts.decorators`; `Word`, `Category`, `CustomUser` counts
- Produces: `GET /dashboard/` → Bootstrap 5 page with word/category/user stats (staff+ only)

- [ ] **Step 1: Write the failing tests**

`tests/test_dashboard.py`:
```python
import pytest
from django.test import Client


@pytest.mark.django_db
def test_dashboard_anonymous_redirects_to_login():
    c = Client()
    r = c.get('/dashboard/')
    assert r.status_code == 302


@pytest.mark.django_db
def test_dashboard_regular_user_forbidden(regular_user):
    c = Client()
    c.force_login(regular_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_staff_user_forbidden_without_2fa(staff_user):
    # MFA not configured → middleware blocks it
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_dashboard_index_accessible_to_staff_with_2fa(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/')
    assert r.status_code == 200
    assert b'Dashboard' in r.content
```

Note: `mocker` comes from `pytest-mock` — add `pytest-mock` to `requirements.txt`.

- [ ] **Step 2: Add pytest-mock to requirements.txt**

Append to `requirements.txt`:
```
pytest-mock>=3.12
```
Install: `pip install pytest-mock`

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_dashboard.py -v
```
Expected: fail with 404 (route not mounted yet) or import errors.

- [ ] **Step 4: Write dashboard/views.py**

`dashboard/views.py`:
```python
from django.shortcuts import render
from accounts.decorators import role_required
from django.contrib.auth import get_user_model
from vocab.models import Word, Category, CEFRLevel, Color


@role_required('staff')
def index(request):
    context = {
        'word_count':     Word.objects.count(),
        'category_count': Category.objects.count(),
        'cefr_count':     CEFRLevel.objects.count(),
        'color_count':    Color.objects.count(),
        'user_count':     get_user_model().objects.count(),
    }
    return render(request, 'dashboard/index.html', context)
```

- [ ] **Step 5: Write dashboard/urls.py**

`dashboard/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
]
```

- [ ] **Step 6: Write dashboard/templates/dashboard/base.html**

`dashboard/templates/dashboard/base.html`:
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Dashboard{% endblock %} — IELTS Vocab Master</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-dark bg-dark px-3">
  <a class="navbar-brand" href="/dashboard/">Vocab Master Admin</a>
  <div class="d-flex gap-3 align-items-center">
    <a class="text-white text-decoration-none" href="/dashboard/words/">Words</a>
    <a class="text-white text-decoration-none" href="/dashboard/categories/">Categories</a>
    <a class="text-white text-decoration-none" href="/dashboard/colors/">Colors</a>
    <a class="text-white text-decoration-none" href="/dashboard/cefr/">CEFR</a>
    {% if request.user.role == 'admin' %}
    <a class="text-white text-decoration-none" href="/dashboard/users/">Users</a>
    {% endif %}
    <span class="text-secondary">{{ request.user.email }}</span>
  </div>
</nav>
<div class="container py-4">
  {% if messages %}
    {% for m in messages %}
      <div class="alert alert-{{ m.tags }} alert-dismissible" role="alert">
        {{ m }} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    {% endfor %}
  {% endif %}
  {% block content %}{% endblock %}
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

- [ ] **Step 7: Write dashboard/templates/dashboard/index.html**

`dashboard/templates/dashboard/index.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1 class="mb-4">Dashboard</h1>
<div class="row g-3">
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h2 class="card-title">{{ word_count }}</h2>
        <p class="card-text text-muted">Words</p>
        <a href="/dashboard/words/" class="btn btn-sm btn-primary">Manage</a>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h2 class="card-title">{{ category_count }}</h2>
        <p class="card-text text-muted">Categories</p>
        <a href="/dashboard/categories/" class="btn btn-sm btn-primary">Manage</a>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h2 class="card-title">{{ color_count }}</h2>
        <p class="card-text text-muted">Colors</p>
        <a href="/dashboard/colors/" class="btn btn-sm btn-primary">Manage</a>
      </div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="card text-center">
      <div class="card-body">
        <h2 class="card-title">{{ user_count }}</h2>
        <p class="card-text text-muted">Users</p>
        {% if request.user.role == 'admin' %}
        <a href="/dashboard/users/" class="btn btn-sm btn-secondary">Manage</a>
        {% endif %}
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 8: Mount dashboard in config/urls.py**

Add `path('dashboard/', include('dashboard.urls')),` to `urlpatterns`.

`config/urls.py` final:
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 9: Run tests**

```bash
pytest tests/test_dashboard.py -v
```
Expected: 4 PASSED.

- [ ] **Step 10: Commit**

```bash
git add dashboard/ config/urls.py tests/test_dashboard.py requirements.txt
git commit -m "feat: add dashboard base template and overview page with RBAC + MFA enforcement"
```

---

## Task 10: Dashboard — Words CRUD

**Files:**
- Create: `dashboard/forms.py`
- Modify: `dashboard/views.py` (add word views)
- Modify: `dashboard/urls.py`
- Create: `dashboard/templates/dashboard/words/list.html`
- Create: `dashboard/templates/dashboard/words/form.html`

- [ ] **Step 1: Write dashboard/forms.py**

`dashboard/forms.py`:
```python
from django import forms
from vocab.models import Word, Category, Color, CEFRLevel
from django.contrib.auth import get_user_model


class WordForm(forms.ModelForm):
    synonyms_text = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'comma-separated'}),
        required=False, label='Synonyms',
    )
    antonyms_text = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'comma-separated'}),
        required=False, label='Antonyms',
    )

    class Meta:
        model = Word
        fields = ['word', 'pos', 'definition', 'example', 'gap', 'category', 'cefr_level', 'order']
        widgets = {
            'definition': forms.Textarea(attrs={'rows': 3}),
            'example':    forms.Textarea(attrs={'rows': 2}),
            'gap':        forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['synonyms_text'].initial = ', '.join(self.instance.synonyms or [])
            self.fields['antonyms_text'].initial = ', '.join(self.instance.antonyms or [])

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.synonyms = [s.strip() for s in self.cleaned_data['synonyms_text'].split(',') if s.strip()]
        instance.antonyms = [s.strip() for s in self.cleaned_data['antonyms_text'].split(',') if s.strip()]
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['slug', 'name', 'icon', 'cefr_level', 'color', 'order']


class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'bg_hex', 'text_hex']
        widgets = {
            'bg_hex':   forms.TextInput(attrs={'type': 'color'}),
            'text_hex': forms.TextInput(attrs={'type': 'color'}),
        }


class CEFRForm(forms.ModelForm):
    class Meta:
        model = CEFRLevel
        fields = ['code', 'name', 'order']


class UserRoleForm(forms.Form):
    ROLE_CHOICES = [('user', 'User'), ('staff', 'Staff'), ('admin', 'Admin')]
    role        = forms.ChoiceField(choices=ROLE_CHOICES)
    is_active   = forms.BooleanField(required=False, label='Active')
```

- [ ] **Step 2: Add word views to dashboard/views.py**

Append to `dashboard/views.py`:
```python
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .forms import WordForm, CategoryForm, ColorForm, CEFRForm, UserRoleForm


@role_required('staff')
def word_list(request):
    category_id = request.GET.get('category')
    cefr_code   = request.GET.get('cefr')
    qs = Word.objects.select_related('category', 'cefr_level').order_by('category__order', 'order')
    if category_id:
        qs = qs.filter(category_id=category_id)
    if cefr_code:
        qs = qs.filter(cefr_level__code=cefr_code)
    context = {
        'words':      qs,
        'categories': Category.objects.all(),
        'cefr_levels': CEFRLevel.objects.all(),
        'selected_cat':  category_id,
        'selected_cefr': cefr_code,
    }
    return render(request, 'dashboard/words/list.html', context)


@role_required('staff')
def word_add(request):
    form = WordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Word added.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def word_edit(request, pk):
    word = get_object_or_404(Word, pk=pk)
    form = WordForm(request.POST or None, instance=word)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Word updated.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/form.html', {'form': form, 'action': 'Edit', 'obj': word})


@role_required('staff')
def word_delete(request, pk):
    word = get_object_or_404(Word, pk=pk)
    if request.method == 'POST':
        word.delete()
        messages.success(request, 'Word deleted.')
        return redirect('dashboard_word_list')
    return render(request, 'dashboard/words/list.html', {'confirm_delete': word})
```

- [ ] **Step 3: Add word URLs to dashboard/urls.py**

`dashboard/urls.py`:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('words/', views.word_list, name='dashboard_word_list'),
    path('words/add/', views.word_add, name='dashboard_word_add'),
    path('words/<int:pk>/edit/', views.word_edit, name='dashboard_word_edit'),
    path('words/<int:pk>/delete/', views.word_delete, name='dashboard_word_delete'),
]
```

- [ ] **Step 4: Write dashboard/templates/dashboard/words/list.html**

`dashboard/templates/dashboard/words/list.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Words{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
  <h1>Words</h1>
  <a href="{% url 'dashboard_word_add' %}" class="btn btn-success">+ Add Word</a>
</div>

<form class="row g-2 mb-3" method="get">
  <div class="col-md-4">
    <select name="category" class="form-select">
      <option value="">All categories</option>
      {% for cat in categories %}
        <option value="{{ cat.id }}" {% if selected_cat == cat.id|stringformat:"s" %}selected{% endif %}>{{ cat.name }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-md-3">
    <select name="cefr" class="form-select">
      <option value="">All CEFR levels</option>
      {% for level in cefr_levels %}
        <option value="{{ level.code }}" {% if selected_cefr == level.code %}selected{% endif %}>{{ level.code }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="col-auto"><button class="btn btn-outline-secondary">Filter</button></div>
</form>

{% if confirm_delete %}
<div class="alert alert-danger">
  Delete <strong>{{ confirm_delete.word }}</strong>?
  <form method="post" action="{% url 'dashboard_word_delete' confirm_delete.pk %}" class="d-inline">
    {% csrf_token %}<button class="btn btn-sm btn-danger ms-2">Yes, delete</button>
  </form>
  <a href="{% url 'dashboard_word_list' %}" class="btn btn-sm btn-secondary ms-1">Cancel</a>
</div>
{% endif %}

<table class="table table-striped table-hover">
  <thead><tr>
    <th>Word</th><th>POS</th><th>CEFR</th><th>Category</th><th>Definition</th><th></th>
  </tr></thead>
  <tbody>
    {% for w in words %}
    <tr>
      <td><strong>{{ w.word }}</strong></td>
      <td>{{ w.pos }}</td>
      <td>{{ w.cefr_level.code|default:"—" }}</td>
      <td>{{ w.category.name }}</td>
      <td class="text-truncate" style="max-width:300px">{{ w.definition }}</td>
      <td class="text-nowrap">
        <a href="{% url 'dashboard_word_edit' w.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
        <a href="{% url 'dashboard_word_delete' w.pk %}" class="btn btn-sm btn-outline-danger">Del</a>
      </td>
    </tr>
    {% empty %}
    <tr><td colspan="6" class="text-center text-muted">No words found.</td></tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}
```

- [ ] **Step 5: Write dashboard/templates/dashboard/words/form.html**

`dashboard/templates/dashboard/words/form.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Word{% endblock %}
{% block content %}
<h1>{{ action }} Word{% if obj %}: {{ obj.word }}{% endif %}</h1>
<form method="post" class="mt-3" style="max-width:700px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>
    {{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_word_list' %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

- [ ] **Step 6: Verify manually**

```bash
python manage.py runserver localhost:8000
```
Log in to `/django-admin/` as a superuser (create one: `python manage.py createsuperuser`). Then promote yourself to `admin` role via shell:
```bash
python manage.py shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.first()
u.role = 'admin'
u.save()
print(u.email, u.role)
"
```
Visit `http://localhost:8000/dashboard/words/` (after bypassing MFA middleware temporarily for manual testing — or set up TOTP via allauth MFA flow).

- [ ] **Step 7: Commit**

```bash
git add dashboard/
git commit -m "feat: add dashboard words CRUD (list, add, edit, delete)"
```

---

## Task 11: Dashboard — Categories, Colors, CEFR levels

**Files:**
- Modify: `dashboard/views.py` (add category, color, CEFR views)
- Modify: `dashboard/urls.py`
- Create: `dashboard/templates/dashboard/categories/list.html`
- Create: `dashboard/templates/dashboard/categories/form.html`
- Create: `dashboard/templates/dashboard/colors/list.html`
- Create: `dashboard/templates/dashboard/colors/form.html`
- Create: `dashboard/templates/dashboard/cefr/list.html`

- [ ] **Step 1: Append category/color/CEFR views to dashboard/views.py**

```python
# ── Categories ──────────────────────────────────────────────
@role_required('staff')
def category_list(request):
    cats = Category.objects.select_related('cefr_level', 'color').order_by('order')
    return render(request, 'dashboard/categories/list.html', {'categories': cats})


@role_required('staff')
def category_add(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/form.html', {'form': form, 'action': 'Add'})


@role_required('staff')
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/form.html', {'form': form, 'action': 'Edit', 'obj': cat})


@role_required('staff')
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if cat.words.exists():
        messages.error(request, f'Cannot delete — {cat.words.count()} words still use this category. Reassign or delete them first.')
        return redirect('dashboard_category_list')
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('dashboard_category_list')
    return render(request, 'dashboard/categories/list.html', {'categories': Category.objects.all(), 'confirm_delete': cat})


# ── Colors ──────────────────────────────────────────────────
@role_required('staff')
def color_list(request):
    colors = Color.objects.all()
    return render(request, 'dashboard/colors/list.html', {'colors': colors})


@role_required('staff')
def color_form(request, pk=None):
    instance = get_object_or_404(Color, pk=pk) if pk else None
    form = ColorForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Color saved.')
        return redirect('dashboard_color_list')
    return render(request, 'dashboard/colors/form.html', {'form': form, 'action': 'Edit' if pk else 'Add'})


# ── CEFR Levels ─────────────────────────────────────────────
@role_required('staff')
def cefr_list(request):
    levels = CEFRLevel.objects.order_by('order')
    forms  = {l.pk: CEFRForm(instance=l, prefix=str(l.pk)) for l in levels}
    if request.method == 'POST':
        pk = int(request.POST.get('level_pk'))
        level = get_object_or_404(CEFRLevel, pk=pk)
        f = CEFRForm(request.POST, instance=level, prefix=str(pk))
        if f.is_valid():
            f.save()
            messages.success(request, f'{level.code} updated.')
        return redirect('dashboard_cefr_list')
    return render(request, 'dashboard/cefr/list.html', {'levels': levels, 'forms': forms})
```

- [ ] **Step 2: Add URLs to dashboard/urls.py**

Append to `urlpatterns`:
```python
path('categories/', views.category_list, name='dashboard_category_list'),
path('categories/add/', views.category_add, name='dashboard_category_add'),
path('categories/<int:pk>/edit/', views.category_edit, name='dashboard_category_edit'),
path('categories/<int:pk>/delete/', views.category_delete, name='dashboard_category_delete'),
path('colors/', views.color_list, name='dashboard_color_list'),
path('colors/add/', views.color_form, name='dashboard_color_add'),
path('colors/<int:pk>/edit/', views.color_form, name='dashboard_color_edit'),
path('cefr/', views.cefr_list, name='dashboard_cefr_list'),
```

- [ ] **Step 3: Write categories templates**

`dashboard/templates/dashboard/categories/list.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Categories{% endblock %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
  <h1>Categories</h1>
  <a href="{% url 'dashboard_category_add' %}" class="btn btn-success">+ Add</a>
</div>
{% if confirm_delete %}
<div class="alert alert-danger">
  Delete <strong>{{ confirm_delete.name }}</strong>?
  <form method="post" action="{% url 'dashboard_category_delete' confirm_delete.pk %}" class="d-inline">
    {% csrf_token %}<button class="btn btn-sm btn-danger ms-2">Yes</button>
  </form>
  <a href="{% url 'dashboard_category_list' %}" class="btn btn-sm btn-secondary ms-1">Cancel</a>
</div>
{% endif %}
<table class="table table-hover">
  <thead><tr><th>Icon</th><th>Name</th><th>Slug</th><th>CEFR</th><th>Color</th><th>Words</th><th></th></tr></thead>
  <tbody>
  {% for c in categories %}
  <tr>
    <td>{{ c.icon }}</td>
    <td>{{ c.name }}</td>
    <td><code>{{ c.slug }}</code></td>
    <td>{{ c.cefr_level.code|default:"—" }}</td>
    <td>
      {% if c.color %}
        <span class="badge" style="background:{{ c.color.bg_hex }};color:{{ c.color.text_hex }}">{{ c.color.name }}</span>
      {% else %}—{% endif %}
    </td>
    <td>{{ c.words.count }}</td>
    <td class="text-nowrap">
      <a href="{% url 'dashboard_category_edit' c.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
      <a href="{% url 'dashboard_category_delete' c.pk %}" class="btn btn-sm btn-outline-danger">Del</a>
    </td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`dashboard/templates/dashboard/categories/form.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Category{% endblock %}
{% block content %}
<h1>{{ action }} Category</h1>
<form method="post" class="mt-3" style="max-width:500px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>{{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_category_list' %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

- [ ] **Step 4: Write colors templates**

`dashboard/templates/dashboard/colors/list.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Colors{% endblock %}
{% block content %}
<div class="d-flex justify-content-between mb-3">
  <h1>Colors</h1>
  <a href="{% url 'dashboard_color_add' %}" class="btn btn-success">+ Add</a>
</div>
<div class="row g-3">
  {% for color in colors %}
  <div class="col-md-3">
    <div class="card">
      <div class="card-body text-center" style="background:{{ color.bg_hex }};color:{{ color.text_hex }}">
        <strong>{{ color.name }}</strong><br>
        <small>{{ color.bg_hex }} / {{ color.text_hex }}</small>
      </div>
      <div class="card-footer text-center">
        <a href="{% url 'dashboard_color_edit' color.pk %}" class="btn btn-sm btn-outline-primary">Edit</a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
{% endblock %}
```

`dashboard/templates/dashboard/colors/form.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}{{ action }} Color{% endblock %}
{% block content %}
<h1>{{ action }} Color</h1>
<form method="post" class="mt-3" style="max-width:400px">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>{{ field }}
    {% if field.errors %}<div class="text-danger small">{{ field.errors }}</div>{% endif %}
  </div>
  {% endfor %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_color_list' %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

- [ ] **Step 5: Write CEFR template**

`dashboard/templates/dashboard/cefr/list.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}CEFR Levels{% endblock %}
{% block content %}
<h1 class="mb-3">CEFR Levels</h1>
<p class="text-muted">Edit level names inline. Codes and order are fixed.</p>
{% for level in levels %}
<form method="post" class="row g-2 align-items-center mb-2">
  {% csrf_token %}
  <input type="hidden" name="level_pk" value="{{ level.pk }}">
  {% with forms|dictsort:level.pk as f %}{% endwith %}
  {{ forms|dictsort }}
  <div class="col-auto"><span class="badge bg-secondary fs-6">{{ level.code }}</span></div>
  <div class="col-md-4">
    <input name="{{ level.pk }}-name" value="{{ level.name }}" class="form-control">
  </div>
  <div class="col-auto"><button class="btn btn-sm btn-outline-primary">Save</button></div>
</form>
{% endfor %}
{% endblock %}
```

Note: the CEFR template's form field names use the `prefix=str(pk)` pattern from the view. The `{{ forms|dictsort }}` line needs replacing with a manual render since Django template filters can't index dicts easily. Simplify the view instead:

Replace `cefr_list` view in `dashboard/views.py` with this simpler version that handles one form at a time:
```python
@role_required('staff')
def cefr_list(request):
    levels = list(CEFRLevel.objects.order_by('order'))
    if request.method == 'POST':
        pk = int(request.POST.get('level_pk'))
        level = get_object_or_404(CEFRLevel, pk=pk)
        level.name = request.POST.get('name', level.name).strip()
        level.save(update_fields=['name'])
        messages.success(request, f'{level.code} updated.')
        return redirect('dashboard_cefr_list')
    return render(request, 'dashboard/cefr/list.html', {'levels': levels})
```

And update `cefr/list.html` to match this simpler approach:
```html
{% extends "dashboard/base.html" %}
{% block title %}CEFR Levels{% endblock %}
{% block content %}
<h1 class="mb-3">CEFR Levels</h1>
{% for level in levels %}
<form method="post" class="row g-2 align-items-center mb-2">
  {% csrf_token %}
  <input type="hidden" name="level_pk" value="{{ level.pk }}">
  <div class="col-auto"><span class="badge bg-secondary fs-6">{{ level.code }}</span></div>
  <div class="col-md-4"><input name="name" value="{{ level.name }}" class="form-control"></div>
  <div class="col-auto"><button class="btn btn-sm btn-outline-primary">Save</button></div>
</form>
{% endfor %}
{% endblock %}
```

- [ ] **Step 6: Commit**

```bash
git add dashboard/
git commit -m "feat: add dashboard CRUD for categories, colors, and CEFR levels"
```

---

## Task 12: Dashboard — User management (admin role only)

**Files:**
- Modify: `dashboard/views.py`
- Modify: `dashboard/urls.py`
- Create: `dashboard/templates/dashboard/users/list.html`
- Create: `dashboard/templates/dashboard/users/detail.html`

- [ ] **Step 1: Write the failing test** (append to `tests/test_dashboard.py`)

```python
@pytest.mark.django_db
def test_users_list_forbidden_for_staff(staff_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(staff_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 403


@pytest.mark.django_db
def test_users_list_accessible_to_admin(admin_user, mocker):
    mocker.patch(
        'allauth.mfa.adapter.DefaultMFAAdapter.is_mfa_enabled',
        return_value=True,
    )
    c = Client()
    c.force_login(admin_user)
    r = c.get('/dashboard/users/')
    assert r.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_dashboard.py::test_users_list_forbidden_for_staff tests/test_dashboard.py::test_users_list_accessible_to_admin -v
```
Expected: 404 (route not yet defined).

- [ ] **Step 3: Append user views to dashboard/views.py**

```python
from accounts.decorators import role_required as _role_required


@role_required('admin')
def user_list(request):
    query = request.GET.get('q', '')
    User  = get_user_model()
    users = User.objects.order_by('email')
    if query:
        users = users.filter(email__icontains=query) | users.filter(username__icontains=query)
    return render(request, 'dashboard/users/list.html', {'users': users, 'query': query})


@role_required('admin')
def user_detail(request, pk):
    User       = get_user_model()
    target     = get_object_or_404(User, pk=pk)
    form       = UserRoleForm(request.POST or None, initial={
        'role': target.role, 'is_active': target.is_active
    })
    if request.method == 'POST' and form.is_valid():
        target.role      = form.cleaned_data['role']
        target.is_active = form.cleaned_data['is_active']
        target.save(update_fields=['role', 'is_active'])
        messages.success(request, f'{target.email} updated.')
        return redirect('dashboard_user_list')
    return render(request, 'dashboard/users/detail.html', {'target': target, 'form': form})
```

- [ ] **Step 4: Add URLs to dashboard/urls.py**

Append to `urlpatterns`:
```python
path('users/', views.user_list, name='dashboard_user_list'),
path('users/<int:pk>/', views.user_detail, name='dashboard_user_detail'),
```

- [ ] **Step 5: Write user templates**

`dashboard/templates/dashboard/users/list.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Users{% endblock %}
{% block content %}
<h1 class="mb-3">Users</h1>
<form class="row g-2 mb-3" method="get">
  <div class="col-md-4">
    <input name="q" value="{{ query }}" class="form-control" placeholder="Search email or username">
  </div>
  <div class="col-auto"><button class="btn btn-outline-secondary">Search</button></div>
</form>
<table class="table table-hover">
  <thead><tr><th>Email</th><th>Username</th><th>Role</th><th>Active</th><th>Joined</th><th></th></tr></thead>
  <tbody>
  {% for u in users %}
  <tr>
    <td>{{ u.email }}</td>
    <td>{{ u.username }}</td>
    <td><span class="badge {% if u.role == 'admin' %}bg-danger{% elif u.role == 'staff' %}bg-warning text-dark{% else %}bg-secondary{% endif %}">{{ u.role }}</span></td>
    <td>{% if u.is_active %}✓{% else %}<span class="text-danger">✗</span>{% endif %}</td>
    <td>{{ u.date_joined|date:"Y-m-d" }}</td>
    <td><a href="{% url 'dashboard_user_detail' u.pk %}" class="btn btn-sm btn-outline-primary">Edit</a></td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
```

`dashboard/templates/dashboard/users/detail.html`:
```html
{% extends "dashboard/base.html" %}
{% block title %}Edit User{% endblock %}
{% block content %}
<h1>Edit User</h1>
<p class="text-muted">{{ target.email }} · joined {{ target.date_joined|date:"Y-m-d" }}</p>
<form method="post" style="max-width:400px" class="mt-3">
  {% csrf_token %}
  {% for field in form %}
  <div class="mb-3">
    <label class="form-label">{{ field.label }}</label>{{ field }}
  </div>
  {% endfor %}
  <button class="btn btn-primary">Save</button>
  <a href="{% url 'dashboard_user_list' %}" class="btn btn-secondary ms-2">Cancel</a>
</form>
{% endblock %}
```

- [ ] **Step 6: Run all dashboard tests**

```bash
pytest tests/test_dashboard.py -v
```
Expected: all PASSED.

- [ ] **Step 7: Commit**

```bash
git add dashboard/ tests/test_dashboard.py
git commit -m "feat: add dashboard user management (admin-only: list, role change, deactivate)"
```

---

## Task 13: vocab-master.html + root URL + final URL wiring

**Files:**
- Create: `vocab-master.html` (rewritten for Django)
- Modify: `config/urls.py` (add root `/` view)

This task rewrites `vocab-master.html` to:
1. Fetch vocabulary from `/api/words/` and `/api/categories/` on load instead of reading embedded JS
2. Use allauth headless endpoints (`/_allauth/browser/v1/auth/…`) for login/signup/logout/session/password
3. Use custom endpoints for sync, update-profile, delete-account, check-email
4. Include CSRF token in every mutating fetch call

- [ ] **Step 1: Read the existing Flask vocab-master.html to understand structure**

```bash
# from Django/ directory:
cat ../Flask/vocab-master.html | head -200
```
Identify: where AUTH_BASE is set, how vocabulary arrays are declared, how `initAuth()` and the word-rendering loop work.

- [ ] **Step 2: Copy Flask HTML as starting point**

```bash
cp ../Flask/vocab-master.html ./vocab-master.html
```

- [ ] **Step 3: Update the API constants block**

Find the JS block that sets `AUTH_BASE` and `LEARN_STATE_KEY`. Replace it:

```javascript
// ── API config ───────────────────────────────────────────
const ALLAUTH_BASE   = '/_allauth/browser/v1';
const AUTH_BASE      = '/auth';
const API_BASE       = '/api';
const LEARN_STATE_KEY = 'ivm_learn_map';   // localStorage key for offline cache

function getCsrf() {
  return document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith('csrftoken='))?.split('=')[1] ?? '';
}

function authFetch(url, opts = {}) {
  return fetch(url, {
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json', ...(opts.headers ?? {}) },
    ...opts,
  });
}
```

- [ ] **Step 4: Remove embedded vocabulary data**

Delete all `const PART1 = [...]`, `const PART2 = [...]`, … `const PART11 = [...]` declarations and any `const ALL_WORDS = [...PART1, ...PART2, ...]` merging line. These will be replaced by an API call.

- [ ] **Step 5: Add vocab loader function**

Replace the vocabulary initialization (wherever `ALL_WORDS` / category arrays are built) with:

```javascript
let ALL_CATEGORIES = [];
let ALL_WORDS      = [];

async function loadVocab() {
  const [catRes, wordRes] = await Promise.all([
    fetch(`${API_BASE}/categories/`),
    fetch(`${API_BASE}/words/`),
  ]);
  ALL_CATEGORIES = await catRes.json();
  ALL_WORDS      = await wordRes.json();
  renderVocab();   // call whatever function draws the word lists
}
```

Call `loadVocab()` where previously the static data was immediately available.

- [ ] **Step 6: Update session check**

Replace `fetch(AUTH_BASE + 'session')` with:
```javascript
const r = await fetch(`${ALLAUTH_BASE}/auth/session`, { credentials: 'same-origin' });
const data = await r.json();
const user = data?.data?.user;   // allauth headless v1 shape
```
Map `user.display` (allauth) → `user.name` for display; `user.email` for email.

- [ ] **Step 7: Update login call**

Replace old login fetch with:
```javascript
const r = await authFetch(`${ALLAUTH_BASE}/auth/login`, {
  method: 'POST',
  body: JSON.stringify({ email, password }),
});
```
Allauth returns `{"status": 200, "data": {"user": {...}}}` on success, or `{"status": 400, "errors": [...]}` on failure.

- [ ] **Step 8: Update signup call**

```javascript
const r = await authFetch(`${ALLAUTH_BASE}/auth/signup`, {
  method: 'POST',
  body: JSON.stringify({ email, username, password1: password, password2: password }),
});
```

- [ ] **Step 9: Update logout call**

```javascript
await authFetch(`${ALLAUTH_BASE}/auth/session`, { method: 'DELETE' });
location.reload();
```

- [ ] **Step 10: Update forgot-password and reset-password calls**

```javascript
// Forgot password:
await authFetch(`${ALLAUTH_BASE}/auth/password/request`, {
  method: 'POST', body: JSON.stringify({ email }),
});

// Reset password (on reset page, token read from URL):
await authFetch(`${ALLAUTH_BASE}/auth/password/reset`, {
  method: 'POST', body: JSON.stringify({ key: token, password: newPassword }),
});
```

- [ ] **Step 11: Update sync, update-profile, delete-account, check-email calls**

```javascript
// sync GET:
const r = await fetch(`${AUTH_BASE}/sync/`, { credentials: 'same-origin' });

// sync POST:
await authFetch(`${AUTH_BASE}/sync/`, {
  method: 'POST', body: JSON.stringify({ learn_map: currentLearnMap }),
});

// update-profile (multipart — remove Content-Type so browser sets boundary):
const fd = new FormData();
fd.append('name', name);
const r = await fetch(`${AUTH_BASE}/update-profile/`, {
  method: 'POST', credentials: 'same-origin',
  headers: { 'X-CSRFToken': getCsrf() }, body: fd,
});

// delete-account:
await authFetch(`${AUTH_BASE}/delete-account/`, {
  method: 'POST', body: JSON.stringify({ password }),
});

// check-email:
const r = await fetch(`${AUTH_BASE}/check-email/`, {
  method: 'POST', credentials: 'same-origin',
  headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json' },
  body: JSON.stringify({ email }),
});
```

- [ ] **Step 12: Add root URL to config/urls.py**

`config/urls.py` — add before the static() line:
```python
from django.http import FileResponse
import os

def serve_vocab(request):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vocab-master.html')
    return FileResponse(open(path, 'rb'), content_type='text/html')

urlpatterns = [
    path('', serve_vocab),
    path('django-admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('dashboard/', include('dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 13: Run the full server and verify end-to-end**

```bash
python manage.py runserver localhost:8000
```

Verify manually:
1. `GET http://localhost:8000/` → vocab master HTML loads
2. `GET http://localhost:8000/api/words/` → JSON array of words
3. `GET http://localhost:8000/api/categories/` → JSON array with colors
4. `GET http://localhost:8000/_allauth/browser/v1/auth/session` → `{"status":401,...}` when logged out
5. Sign up with a new email → verification email sent (if SMTP configured) or accepted silently
6. Sign in → session established → `GET /auth/sync/` returns `{learn_map: {}}`
7. Mark a word as learned → `POST /auth/sync/` → refresh → word still learned
8. Update profile (name/username) → changes reflected on next session check
9. `GET http://localhost:8000/dashboard/` → blocked (2FA not set up) or visible (if 2FA active)

- [ ] **Step 14: Commit**

```bash
git add vocab-master.html config/urls.py
git commit -m "feat: rewrite vocab-master.html to use Django API and allauth headless auth"
```

---

## Task 14: Final wiring — .gitignore, run instructions

**Files:**
- Modify: `[repo root]/.gitignore`

- [ ] **Step 1: Update .gitignore**

Add to the root `.gitignore` (in addition to existing rules):
```
ielts-vocab-master/Python/Django/.env
ielts-vocab-master/Python/Django/db.sqlite3
ielts-vocab-master/Python/Django/media/
ielts-vocab-master/Python/Django/**/__pycache__/
ielts-vocab-master/Python/Django/**/*.pyc
```

- [ ] **Step 2: Run full test suite**

```bash
cd ielts-vocab-master/Python/Django
pytest -v
```
Expected: all tests PASSED with no errors.

- [ ] **Step 3: Final commit**

```bash
git add .gitignore
git commit -m "chore: gitignore Django env, db, media, pycache"
```

---

## Running the Django app

```bash
cd ielts-vocab-master/Python/Django
cp .env.example .env          # fill in DJANGO_SECRET_KEY and SMTP creds
python manage.py migrate
python manage.py import_vocab
python manage.py runserver localhost:8000
```

Visit `http://localhost:8000` — vocab master loads vocabulary from the database.
Visit `http://localhost:8000/dashboard/` — staff/admin management UI (requires 2FA).

To create the first admin user:
```bash
python manage.py createsuperuser  # creates a Django superuser
python manage.py shell -c "
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(email='YOUR_EMAIL')
u.role = 'admin'
u.save()
"
```
Then enable 2FA from your profile settings in the app to unlock `/dashboard/`.
