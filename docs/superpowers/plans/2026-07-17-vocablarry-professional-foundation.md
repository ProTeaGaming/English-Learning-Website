# VocabLarry Professional Environment — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a new, parallel Django project — `VocabLarry Professional Environment/` — that recreates VocabLarry's home page and auth flows using real server-rendered templates instead of the current single-file SPA, proving out the architecture before Vocab/Grammar/Dashboard get ported in later sub-projects.

**Architecture:** Copy VocabLarry's Django backend (models, migrations, API views, `db.sqlite3`) unchanged into the new project. Replace the SPA's `serve_vocab` FileResponse hack with a real `home` view + template. Switch allauth from `allauth.headless` (JSON API) to its classic template-rendered views (`allauth.account.urls`, already partially wired for the OAuth redirect dance) by supplying one override template, `templates/allauth/layouts/base.html`, that plugs allauth's existing page content into our own site layout — every allauth page (login, signup, logout, password reset, email verify, social redirect) inherits our nav/branding automatically without needing a separate override file per page.

**Tech Stack:** Django 5.x, django-allauth (classic account app, not headless), pytest + pytest-django, SQLite.

## Global Constraints

- Reuse VocabLarry's existing models, migrations, and `api/` views byte-for-byte — no schema or business-logic changes in this plan.
- New project lives at `D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment\`, fully isolated from production (its own `db.sqlite3` copy, its own `.env`).
- Never commit real OAuth secrets into plan/spec/commit text — copy `.env` values via a script that reads-and-writes files, never by typing the secret into a command or document.
- Templates live in one project-level `templates/` directory (already the configured `TEMPLATES[0]['DIRS']` in `config/settings.py` — no settings change needed there).
- i18n in this phase is client-side only (`data-i18n` + a small JS dictionary), scoped to the templates this plan creates (nav, home). Allauth's own pages are not translated in this phase (would require Django's server-side i18n, explicitly out of scope per the design spec).
- Test with `pytest` (already configured via `pytest.ini`: `DJANGO_SETTINGS_MODULE=config.settings`, `--no-migrations`).

---

### Task 1: Scaffold the project copy and verify the baseline

**Files:**
- Create: entire `VocabLarry Professional Environment/` tree (copied from `VocabLarry/`)
- Create: `VocabLarry Professional Environment/.env`

**Interfaces:**
- Produces: a runnable, self-contained Django project at `VocabLarry Professional Environment/` with an unmodified copy of every app (`accounts`, `api`, `vocab`, `grammar`, `dashboard`), `db.sqlite3`, and the full `tests/` suite — used as the baseline every later task modifies.

- [ ] **Step 1: Copy the project tree, excluding SPA-only and secret artifacts**

Run from `D:\IT RELATED\CLAUDE BOMBASTIC AI`:

```bash
python -c "
import shutil, os

src = r'D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry'
dst = r'D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment'
exclude_dirs = {'__pycache__', '.pytest_cache', 'qr-codes'}
exclude_files = {
    '.env', 'admin-credentials.txt', 'vocablarry-deploy.zip',
    'vocablarry.html', 'vocablarry-qr.png', 'vocablarry-qr.svg',
    'vocablarry-qr-purple.png', 'DEPLOY-PYTHONANYWHERE.md',
}

os.makedirs(dst, exist_ok=True)
for dirpath, dirnames, filenames in os.walk(src):
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    rel = os.path.relpath(dirpath, src)
    target_dir = os.path.join(dst, rel) if rel != '.' else dst
    os.makedirs(target_dir, exist_ok=True)
    for fn in filenames:
        if fn in exclude_files:
            continue
        shutil.copy2(os.path.join(dirpath, fn), os.path.join(target_dir, fn))
print('copied to', dst)
"
```

- [ ] **Step 2: Create a fresh, isolated `.env` for the new project**

This must never contain real secrets typed directly into a command. Run:

```bash
python -c "
import secrets, os

src_env = r'D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry\.env'
dst_env = r'D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment\.env'

values = {}
with open(src_env, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            values[k.strip()] = v.strip()

lines = [
    f\"DJANGO_SECRET_KEY={secrets.token_urlsafe(50)}\",
    'EMAIL_VERIFICATION=optional',
    f\"GOOGLE_CLIENT_ID={values.get('GOOGLE_CLIENT_ID', '')}\",
    f\"GOOGLE_CLIENT_SECRET={values.get('GOOGLE_CLIENT_SECRET', '')}\",
    'FACEBOOK_CLIENT_ID=',
    'FACEBOOK_CLIENT_SECRET=',
    'MICROSOFT_CLIENT_ID=',
    'MICROSOFT_CLIENT_SECRET=',
    'MICROSOFT_TENANT=common',
    'APPLE_TEAM_ID=',
    'APPLE_CLIENT_ID=',
    'APPLE_KEY_ID=',
    'APPLE_PRIVATE_KEY=',
]
with open(dst_env, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
print('wrote', dst_env, '(secret values copied, not printed)')
"
```

- [ ] **Step 3: Verify the copy is self-consistent**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 4: Verify the baseline test suite passes unchanged**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `90 passed` (identical to production — nothing has been modified yet, this only proves the copy is intact).

- [ ] **Step 5: Commit**

This new project is a separate top-level folder in the same git repo as VocabLarry. Commit it as its own initial snapshot:

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): scaffold VocabLarry Professional Environment from VocabLarry

Verbatim copy of the Django backend (models, migrations, api/, db.sqlite3)
as the starting point for a template-based rebuild of the presentation
layer. .env is fresh/isolated (new secret key, Google OAuth creds copied
from VocabLarry/.env without ever being typed into this commit).
EOF
)"
```

---

### Task 2: Replace the SPA route with a real home view; drop headless auth

**Files:**
- Modify: `VocabLarry Professional Environment/config/settings.py`
- Modify: `VocabLarry Professional Environment/config/urls.py`
- Create: `VocabLarry Professional Environment/config/views.py`
- Create: `VocabLarry Professional Environment/templates/base.html` (minimal — Task 3 fleshes it out)
- Create: `VocabLarry Professional Environment/templates/home.html` (minimal — Task 3 fleshes it out)
- Test: `VocabLarry Professional Environment/tests/test_pages.py`

**Interfaces:**
- Produces: `config.views.home` — a view function taking `request`, returning `render(request, 'home.html')`.
- Produces: `GET /` → 200, renders `home.html`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_pages.py`:

```python
import pytest


@pytest.mark.django_db
def test_home_page_renders():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert r.status_code == 200
    assert 'text/html' in r['Content-Type']
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v
```

Expected: FAIL — current `urls.py` still serves the old SPA route (`serve_vocab`), which will 500 because `vocablarry.html` was excluded from the copy in Task 1.

- [ ] **Step 3: Create the minimal home view and templates**

Create `config/views.py`:

```python
from django.shortcuts import render


def home(request):
    return render(request, 'home.html')
```

Create `templates/base.html`:

```html
{% load static %}<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}VocabLarry{% endblock %}</title>
<link rel="stylesheet" href="{% static 'css/base.css' %}">
{% block extra_head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
<main class="page-content">
{% block content %}{% endblock %}
</main>
{% block extra_body %}{% endblock %}
</body>
</html>
```

Create `templates/home.html`:

```html
{% extends "base.html" %}
{% block title %}VocabLarry{% endblock %}
{% block content %}
<h1>VocabLarry</h1>
{% endblock %}
```

- [ ] **Step 4: Rewrite `config/urls.py`**

Replace the entire file:

```python
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from config.views import home

urlpatterns = [
    path('', home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('auth/', include('accounts.urls')),
    path('api/', include('api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

- [ ] **Step 5: Remove `allauth.headless` from `config/settings.py`**

In `INSTALLED_APPS`, remove the line `'allauth.headless',`.

Remove the `HEADLESS_FRONTEND_URLS` block entirely (it configures headless-only routing, now unused):

```python
HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': '/verify-email/{key}',
    'account_reset_password_from_key': '/reset-password/{key}',
}
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v
```

Expected: PASS.

- [ ] **Step 7: Adapt the two tests that hit the now-removed headless endpoint**

`tests/test_auth_api.py` has `test_connected_providers_list_and_disconnect` and
`test_cannot_disconnect_only_login_method_without_password`, both calling
`/_allauth/browser/v1/account/providers`, which no longer exists. Delete
both tests — the behavior they covered (listing/disconnecting a social
account, blocking disconnect-without-password) lives in
`accounts/adapters.py` and isn't part of this phase's scope; a later
sub-project that builds real account-management pages should re-add
equivalent coverage against those pages' classic routes instead.

Open `tests/test_auth_api.py` and remove these two test functions (lines
197–242 as copied):

```python
@pytest.mark.django_db
def test_connected_providers_list_and_disconnect(regular_user):
    ...

@pytest.mark.django_db
def test_cannot_disconnect_only_login_method_without_password(regular_user):
    ...
```

- [ ] **Step 8: Adapt the two signup tests that post to the headless endpoint**

Open `tests/test_email_deliverability.py`. Replace the two headless-based
tests with classic-form equivalents:

```python
@pytest.mark.django_db
def test_signup_rejects_undeliverable_email_domain(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=False)
    c = Client()
    r = c.post('/accounts/signup/', {
        'email': 'me@unpurchased-brand.com', 'username': 'branduser',
        'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
    })
    assert r.status_code == 200  # re-renders the form with an error
    assert 'This email domain cannot receive mail' in r.content.decode()
    assert not get_user_model().objects.filter(email='me@unpurchased-brand.com').exists()


@pytest.mark.django_db
def test_signup_with_deliverable_domain_still_works(mocker):
    mocker.patch('accounts.adapters.email_domain_accepts_mail', return_value=True)
    c = Client()
    r = c.post('/accounts/signup/', {
        'email': 'me@example.com', 'username': 'newuser',
        'password1': 'Str0ng-pass-123', 'password2': 'Str0ng-pass-123',
    })
    # Mandatory verification: account is created, redirected to the
    # "check your inbox" page rather than logged straight in.
    assert r.status_code == 302
    assert r['Location'] == '/accounts/confirm-email/'
    assert get_user_model().objects.filter(email='me@example.com').exists()
```

These replace the previous two functions of the same name (same file,
same position) — delete the old bodies, keep the new ones.

- [ ] **Step 9: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `89 passed` (90 minus the 2 deleted tests, plus the 1 new `test_pages.py` test, with the 2 email-deliverability tests adapted in place — net: same 89 total, all green).

- [ ] **Step 10: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): replace SPA route with a real home view, drop headless auth

config/urls.py no longer FileResponses a monolithic HTML file; GET /
now renders templates/home.html via a real view. allauth.headless is
removed from INSTALLED_APPS/settings since nothing in this project
drives auth through its JSON API anymore — the classic allauth.urls
routes (already mounted for the OAuth redirect dance) now serve
login/signup/logout/password-reset/email-verify directly.
EOF
)"
```

---

### Task 3: Build the real base layout, nav, and home page

**Files:**
- Create: `VocabLarry Professional Environment/static/css/base.css`
- Create: `VocabLarry Professional Environment/static/js/base.js`
- Create: `VocabLarry Professional Environment/static/js/i18n.js`
- Create: `VocabLarry Professional Environment/templates/partials/nav.html`
- Modify: `VocabLarry Professional Environment/templates/base.html`
- Modify: `VocabLarry Professional Environment/templates/home.html`
- Test: `VocabLarry Professional Environment/tests/test_pages.py`

**Interfaces:**
- Consumes: `templates/base.html`'s `{% block content %}`/`{% block body_class %}`/`{% block extra_head %}`/`{% block extra_body %}` from Task 2.
- Produces: `partials/nav.html` — included by `base.html`, reads `user.is_authenticated` from the standard Django auth context processor (already enabled in `TEMPLATES[0]['OPTIONS']['context_processors']`).

- [ ] **Step 1: Write the failing test**

Extend `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_home_page_has_nav_and_hero():
    from django.test import Client
    c = Client()
    r = c.get('/')
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body
    assert 'hero' in body
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py::test_home_page_has_nav_and_hero -v
```

Expected: FAIL — `templates/base.html` from Task 2 has no nav, `home.html` has no hero section.

- [ ] **Step 3: Create `static/css/base.css`**

```css
:root{
  --violet: 109 40 217;
  --bg: #ffffff;
  --text: #16161f;
  --muted: #6b7280;
  --border: #e5e7eb;
  --card-bg: #f9f9fc;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg: #0f1115;
    --text: #f2f2f7;
    --muted: #9ca3af;
    --border: #262633;
    --card-bg: #191922;
  }
}

*{ box-sizing: border-box; }
body{
  margin: 0;
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
}
a{ color: rgb(var(--violet)); }

.site-nav{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.site-nav .brand{
  font-weight: 800;
  font-size: 1.25rem;
  text-decoration: none;
  color: var(--text);
}
.site-nav .brand b{ color: rgb(var(--violet)); }
.nav-links{
  display: flex;
  gap: 18px;
  list-style: none;
  margin: 0;
  padding: 0;
  flex-wrap: wrap;
}
.nav-links a, .nav-links span{
  text-decoration: none;
  color: var(--text);
  font-weight: 600;
  font-size: 0.95rem;
}
.nav-links .disabled{ color: var(--muted); cursor: default; }
.nav-actions{ display: flex; align-items: center; gap: 12px; }

.btn{
  display: inline-block;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid rgb(var(--violet));
  color: rgb(var(--violet));
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
}
.btn-primary{
  background: rgb(var(--violet));
  color: #fff;
}
.btn.disabled{
  opacity: 0.5;
  pointer-events: none;
}

.page-content{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }

.hero{
  padding: 72px 0 48px;
  text-align: center;
}
.hero h1{ font-size: 2.6rem; margin: 0 0 12px; }
.hero p{ color: var(--muted); font-size: 1.1rem; max-width: 560px; margin: 0 auto 28px; }
.hero-actions{ display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }

/* Auth pages (allauth's classic views rendered inside body_class="auth-page") */
.auth-page .page-content{
  max-width: 420px;
  padding-top: 48px;
}
.auth-page h1{ font-size: 1.6rem; margin-bottom: 8px; }
.auth-page form{
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 20px;
}
.auth-page form p{ margin: 0; display: flex; flex-direction: column; gap: 6px; }
.auth-page form label{ font-weight: 600; font-size: 0.9rem; }
.auth-page form input{
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  font-size: 1rem;
}
.auth-page form button[type="submit"]{
  margin-top: 6px;
  padding: 11px 20px;
  border-radius: 8px;
  border: none;
  background: rgb(var(--violet));
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
}
```

- [ ] **Step 4: Create `static/js/base.js`**

```javascript
(function(){
  var STORAGE_KEY = "vlpe_theme";
  var root = document.documentElement;

  function applyTheme(theme){
    if (theme === "dark" || theme === "light"){
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  var saved = null;
  try { saved = localStorage.getItem(STORAGE_KEY); } catch(e) {}
  applyTheme(saved);

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle){
    toggle.addEventListener("click", function(){
      var current = root.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch(e) {}
    });
  }
})();
```

- [ ] **Step 5: Create `static/js/i18n.js`**

```javascript
(function(){
  var STRINGS = {
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.grammar": "Grammar",
      "nav.comingSoon": "Coming soon",
      "nav.signIn": "Sign In",
      "nav.signOut": "Sign Out",
      "nav.signUp": "Sign Up",
      "hero.title": "Master every word, say it till it stays.",
      "hero.subtitle": "Build vocabulary and grammar skills for IELTS, one focused session at a time.",
      "hero.start": "Start Learning",
      "hero.grammar": "Practice Grammar",
    },
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.grammar": "Ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
      "nav.signIn": "Đăng nhập",
      "nav.signOut": "Đăng xuất",
      "nav.signUp": "Đăng ký",
      "hero.title": "Học từng từ, ghi nhớ mãi mãi.",
      "hero.subtitle": "Xây dựng vốn từ vựng và ngữ pháp cho IELTS, từng buổi học tập trung.",
      "hero.start": "Bắt đầu học",
      "hero.grammar": "Luyện ngữ pháp",
    },
  };
  var STORAGE_KEY = "vlpe_lang";

  function applyLang(lang){
    var dict = STRINGS[lang] || STRINGS.en;
    document.querySelectorAll("[data-i18n]").forEach(function(el){
      var key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });
    document.documentElement.setAttribute("lang", lang);
  }

  var saved = "en";
  try { saved = localStorage.getItem(STORAGE_KEY) || "en"; } catch(e) {}
  applyLang(saved);

  var toggle = document.querySelector("[data-lang-toggle]");
  if (toggle){
    toggle.addEventListener("click", function(){
      var current = document.documentElement.getAttribute("lang") || "en";
      var next = current === "en" ? "vi" : "en";
      applyLang(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch(e) {}
    });
  }
})();
```

- [ ] **Step 6: Create `templates/partials/nav.html`**

```html
<nav class="site-nav">
  <a class="brand" href="{% url 'home' %}">Vocab<b>Larry</b></a>
  <ul class="nav-links">
    <li><span class="disabled" data-i18n="nav.vocabulary">Vocabulary</span> <small data-i18n="nav.comingSoon">Coming soon</small></li>
    <li><span class="disabled" data-i18n="nav.grammar">Grammar</span> <small data-i18n="nav.comingSoon">Coming soon</small></li>
  </ul>
  <div class="nav-actions">
    <button type="button" data-lang-toggle aria-label="Switch language">EN/VI</button>
    <button type="button" data-theme-toggle aria-label="Toggle theme">Theme</button>
    {% if user.is_authenticated %}
      <span>{{ user.username }}</span>
      <a class="btn" href="{% url 'account_logout' %}" data-i18n="nav.signOut">Sign Out</a>
    {% else %}
      <a class="btn" href="{% url 'account_login' %}" data-i18n="nav.signIn">Sign In</a>
      <a class="btn btn-primary" href="{% url 'account_signup' %}" data-i18n="nav.signUp">Sign Up</a>
    {% endif %}
  </div>
</nav>
```

- [ ] **Step 7: Update `templates/base.html`** to load static files and include the nav

```html
{% load static %}<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}VocabLarry{% endblock %}</title>
<link rel="stylesheet" href="{% static 'css/base.css' %}">
{% block extra_head %}{% endblock %}
</head>
<body class="{% block body_class %}{% endblock %}">
{% include "partials/nav.html" %}
<main class="page-content">
{% block content %}{% endblock %}
</main>
<script src="{% static 'js/i18n.js' %}" defer></script>
<script src="{% static 'js/base.js' %}" defer></script>
{% block extra_body %}{% endblock %}
</body>
</html>
```

- [ ] **Step 8: Update `templates/home.html`** with the real hero section

```html
{% extends "base.html" %}
{% block title %}VocabLarry{% endblock %}
{% block content %}
<section class="hero">
  <h1 data-i18n="hero.title">Master every word, say it till it stays.</h1>
  <p data-i18n="hero.subtitle">Build vocabulary and grammar skills for IELTS, one focused session at a time.</p>
  <div class="hero-actions">
    <span class="btn btn-primary disabled" data-i18n="hero.start">Start Learning</span>
    <span class="btn disabled" data-i18n="hero.grammar">Practice Grammar</span>
  </div>
</section>
{% endblock %}
```

- [ ] **Step 9: Run test to verify it passes**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v
```

Expected: PASS (both `test_home_page_renders` and `test_home_page_has_nav_and_hero`).

- [ ] **Step 10: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Open `http://localhost:8001/` — confirm the nav renders, the hero section shows, the theme toggle button flips light/dark, and the language toggle switches the hero text and nav labels between English and Vietnamese. Stop the server (Ctrl+C) when done.

- [ ] **Step 11: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): build base layout, nav, and home hero

static/css/base.css establishes the violet brand palette (light +
prefers-color-scheme dark) and shared nav/button/hero styles.
static/js/base.js + i18n.js add a theme toggle and a client-side
en/vi string swap scoped to this project's own templates (allauth's
pages aren't translated in this phase). Vocabulary/Grammar nav
entries and hero CTAs are marked disabled/coming-soon since those
pages don't exist yet.
EOF
)"
```

---

### Task 4: Brand the auth pages via one shared layout override

**Files:**
- Create: `VocabLarry Professional Environment/templates/allauth/layouts/base.html`
- Test: `VocabLarry Professional Environment/tests/test_pages.py`

**Interfaces:**
- Consumes: `templates/base.html`'s `content`/`body_class`/`title` blocks from Task 3; allauth's own `account/login.html`, `signup.html`, etc. (unmodified, installed with the `django-allauth` package) which fill the `head_title` and `content` blocks that this override exposes.
- Produces: every allauth account/socialaccount page renders inside VocabLarry's nav + `base.css` styling, with `<body class="auth-page">` for the auth-scoped CSS from Task 3.

- [ ] **Step 1: Write the failing test**

Extend `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_login_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/login/')
    assert r.status_code == 200
    body = r.content.decode()
    assert 'site-nav' in body
    assert 'Sign In' in body


@pytest.mark.django_db
def test_signup_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/signup/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_google_login_redirects_to_google():
    from django.test import Client
    c = Client()
    c.get('/accounts/google/login/')  # loads the CSRF-protected confirm page
    r = c.post('/accounts/google/login/')
    assert r.status_code == 302
    assert 'accounts.google.com' in r['Location']


@pytest.mark.django_db
def test_logout_confirm_page_uses_site_layout(regular_user):
    from django.test import Client
    c = Client()
    c.force_login(regular_user)
    r = c.get('/accounts/logout/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_password_reset_request_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/password/reset/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_email_verification_sent_page_uses_site_layout():
    from django.test import Client
    c = Client()
    r = c.get('/accounts/confirm-email/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -k "login_page or signup_page or google_login or logout_confirm or password_reset_request or email_verification_sent" -v
```

Expected: `test_login_page_uses_site_layout`, `test_signup_page_uses_site_layout`, `test_logout_confirm_page_uses_site_layout`, `test_password_reset_request_page_uses_site_layout`, and `test_email_verification_sent_page_uses_site_layout` all FAIL (no `site-nav` — allauth is still using its own bare default layout). `test_google_login_redirects_to_google` should already PASS (the redirect kickoff doesn't depend on templates).

- [ ] **Step 3: Create the layout override**

```bash
mkdir -p "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment\templates\allauth\layouts"
```

Create `templates/allauth/layouts/base.html`:

```html
{% extends "base.html" %}
{% block title %}{% block head_title %}{% endblock %} - VocabLarry{% endblock %}
{% block body_class %}auth-page{% endblock %}
{% block content %}{% endblock %}
```

This works because Django's template loader checks the project-level
`templates/` directory (`TEMPLATES[0]['DIRS']`) before each installed
app's own `templates/` directory, so this file shadows the identically-named
file inside the installed `allauth` package. Every allauth page template
(`account/login.html`, `account/signup.html`, `account/logout.html`,
`account/password_reset.html`, etc.) extends this file two or three levels
up its own inheritance chain, and each already overrides `content` and
`head_title` with its real markup — those overrides flow straight through
into this file's slots, which in turn flow into `base.html`'s `content`
block. No other allauth template needs to be copied or touched.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests/test_pages.py -v
```

Expected: all `test_pages.py` tests PASS.

- [ ] **Step 5: Run the full suite**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python -m pytest tests -q
```

Expected: `96 passed` (89 at the end of Task 2, +1 from Task 3's `test_home_page_has_nav_and_hero`, +6 from this task's new tests).

- [ ] **Step 6: Manually verify in a browser**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI\VocabLarry Professional Environment"
python manage.py runserver 8001
```

Click through, in order: home → Sign Up (create a throwaway account; with
`EMAIL_VERIFICATION=optional` in this project's `.env` you're logged in
immediately) → nav now shows your username and a Sign Out link → Sign Out
→ Sign In with the same credentials → Sign In page's "Sign in with Google"
button → confirm it lands on Google's real OAuth consent screen (you can
cancel out, the point is confirming the redirect fires) → back on the
site, visit `/accounts/password/reset/` and confirm it renders inside the
branded layout. Stop the server (Ctrl+C) when done.

- [ ] **Step 7: Commit**

```bash
cd "D:\IT RELATED\CLAUDE BOMBASTIC AI"
git add "VocabLarry Professional Environment"
git commit -m "$(cat <<'EOF'
feat(vlpe): brand all allauth pages via one shared layout override

templates/allauth/layouts/base.html extends the site's own base.html
and re-exposes allauth's head_title/content blocks, so login, signup,
logout, password-reset, and the Google OAuth redirect confirm page all
inherit VocabLarry's nav and auth-page styling without needing a
separate override per page.
EOF
)"
```

---

## Definition of Done

- `python manage.py check` is clean in `VocabLarry Professional Environment/`.
- `python -m pytest tests -q` is fully green.
- Manual browser check confirms: home page (nav, hero, theme toggle, language toggle), signup, login, logout, password-reset-request, and the Google sign-in redirect all render inside the shared VocabLarry-branded layout.
- Vocabulary/Grammar nav links and hero CTAs are visibly marked "coming soon" rather than dead-linking — this is the expected, explicitly out-of-scope gap that the next sub-project (Vocab) closes.
