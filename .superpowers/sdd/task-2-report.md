## Task 2 Report: Django project scaffold + config

**Status:** DONE_WITH_CONCERNS

---

### Commit SHAs

1. `a7291e8` — feat: scaffold Django project with settings and app stubs
2. `1ccd3f9` — chore: add Python/Django gitignore rules and remove pycache from tracking

---

### `python manage.py check` output

```
System check identified no issues (0 silenced).
```

---

### Issues encountered

**1. Apps created manually (not via `manage.py startapp`)**

The brief says to run `python manage.py startapp accounts` etc., but since `settings.py` already lists `accounts`, `vocab`, `api`, `dashboard` in `INSTALLED_APPS`, Django fails to initialise before the directories exist. The app directories were created manually with the same structure `startapp` would produce (`__init__.py`, `apps.py`, `models.py`, `admin.py`, `migrations/__init__.py`).

**2. Stub `CustomUser` model needed for the check to pass**

`AUTH_USER_MODEL = 'accounts.CustomUser'` causes Django to fail startup if the model doesn't exist. A minimal stub was added to `accounts/models.py`:

```python
class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
```

Task 3 will replace this with the full model. This is forward-compatible.

**3. allauth 65.x deprecation warnings → settings updated**

The brief specified three deprecated allauth settings:
- `ACCOUNT_AUTHENTICATION_METHOD = 'email'`
- `ACCOUNT_EMAIL_REQUIRED = True`
- `ACCOUNT_USERNAME_REQUIRED = True`

These produce warnings in allauth 65.18.0. They were replaced with the new equivalents:
- `ACCOUNT_LOGIN_METHODS = {'email'}`
- `ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']`

This is required for the check to return "0 issues" as specified.

**4. Extra pip installs required**

`requests` and `PyJWT` were not installed as transitive dependencies of `django-allauth[mfa]` in this environment. Both were installed manually. They are implicit allauth deps and do not need to be added to `requirements.txt`.

**5. `__pycache__` committed in first commit**

Pycache files were accidentally included in the first commit. A second commit removed them from tracking and added Python/Django rules to the root `.gitignore`.

---

### Files created

- `ielts-vocab-master/Python/Django/manage.py`
- `ielts-vocab-master/Python/Django/requirements.txt`
- `ielts-vocab-master/Python/Django/.env.example`
- `ielts-vocab-master/Python/Django/pytest.ini`
- `ielts-vocab-master/Python/Django/conftest.py`
- `ielts-vocab-master/Python/Django/config/__init__.py`
- `ielts-vocab-master/Python/Django/config/settings.py`
- `ielts-vocab-master/Python/Django/config/urls.py`
- `ielts-vocab-master/Python/Django/config/asgi.py`
- `ielts-vocab-master/Python/Django/config/wsgi.py`
- `ielts-vocab-master/Python/Django/accounts/` (middleware.py, adapters.py, models.py stub, apps.py, admin.py, migrations/)
- `ielts-vocab-master/Python/Django/vocab/` (apps.py, models.py, admin.py, migrations/)
- `ielts-vocab-master/Python/Django/api/` (apps.py, models.py, admin.py, migrations/)
- `ielts-vocab-master/Python/Django/dashboard/` (apps.py, models.py, admin.py, migrations/)
