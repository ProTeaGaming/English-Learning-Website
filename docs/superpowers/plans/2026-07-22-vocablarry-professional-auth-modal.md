# VocabLarry Professional Environment — Auth Modal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace VLPE's plain `<a href="{% url 'account_login' %}">` sign-in link with a real JS-driven modal (`#authOverlay`) matching production's exact architecture — same states (email → login/signup → mfa/reset/forgot), same `allauth.headless` API calls, same 4 social providers (Google/Facebook/Microsoft/Apple) — fulfilling `FIXES-NEEDED.md` items 1-5.

**Architecture:** Enable `allauth.headless` alongside VLPE's existing classic `allauth.account` mount (both stay active, matching production's own three-routes-simultaneously pattern). Port production's `#authOverlay` HTML/CSS/JS onto VLPE's own element IDs and endpoints, with two intentional adaptations: (1) `closeAuthModal(); await initAuth();` (an SPA-style client-state refresh) becomes `closeAuthModal(); window.location.reload();` because VLPE is a server-rendered multi-page app where the nav's logged-in state already comes from `{% if user.is_authenticated %}` on the next page load; (2) `initAuth()` itself is trimmed to only the piece that has no Django-side equivalent — auto-opening the modal to a "check your email" screen when the session has a pending `verify_email` flow — dropping all of production's `renderAuthUI()`/localStorage/streak/profile-modal logic, none of which exists in VLPE (progress lives server-side on the user model, there's no profile-modal, no localStorage learn-map).

**Tech Stack:** Django 5, django-allauth (`allauth.account` classic + `allauth.headless` JSON API), vanilla JS (no build step, matches existing `static/js/*.js` files), pytest + Django test client.

## Global Constraints

- Exactly 4 social providers: Google, Facebook, Microsoft, Apple. **No GitHub** — `FIXES-NEEDED.md` item 3 is based on inaccurate information (confirmed with the user); do not add a GitHub button or `allauth.socialaccount.providers.github`.
- `HEADLESS_FRONTEND_URLS` must be exactly: `{'account_confirm_email': '/verify-email/{key}', 'account_reset_password_from_key': '/reset-password/{key}'}` — verbatim, matching production.
- The existing classic `path('accounts/', include('allauth.urls'))` mount in `config/urls.py` **stays, unchanged** — needed for OAuth provider redirect/callback infrastructure even though the UI no longer links to its pages directly.
- No changes to `accounts/views.py` or `accounts/urls.py` — VLPE's `session/`, `sync/`, `update-profile/`, `delete-account/`, `check-email/` endpoints already match what the modal's JS calls; this is a frontend + settings/URL wiring task only.
- CSS custom property gotcha (established elsewhere in this project): `--violet` is a space-separated RGB triplet — always write `rgb(var(--violet) / X)`, never `rgba(var(--violet), X)`.
- Out of scope (do not build): MFA enrollment/setup UI, the Profile management overlay, the Delete-account overlay, the mode-picker overlay. Only the sign-in/sign-up/reset/mfa-authenticate modal itself.
- Every dynamic string the modal shows must go through the project's `t(key)` i18n helper (new) so English/Vietnamese both work, matching how every other VLPE JS file already handles user-facing text via `data-i18n`.

---

### Task 1: `allauth.headless` wiring + email-verify/password-reset deep-link pages

**Files:**
- Modify: `config/settings.py:28-49` (`INSTALLED_APPS`), add `HEADLESS_FRONTEND_URLS` near the other allauth settings (`config/settings.py:97-106`)
- Modify: `config/urls.py`
- Modify: `config/views.py`
- Create: `templates/auth_deep_link.html`
- Test: `tests/test_auth_api.py`

**Interfaces:**
- Produces: `/_allauth/` route (mounts `allauth.headless.urls`), `/verify-email/<key>/` and `/reset-password/<key>/` routes rendering `auth_deep_link.html` (a bare `base.html` extension with an empty content block — the actual UI comes from `auth-modal.js`'s `handleAuthDeepLinks()`, built in Task 3, which reads the key straight out of `window.location.pathname` the same way production's does).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_auth_api.py`:

```python
def test_headless_app_installed():
    from django.conf import settings
    assert 'allauth.headless' in settings.INSTALLED_APPS


def test_headless_frontend_urls_configured():
    from django.conf import settings
    assert settings.HEADLESS_FRONTEND_URLS == {
        'account_confirm_email': '/verify-email/{key}',
        'account_reset_password_from_key': '/reset-password/{key}',
    }


@pytest.mark.django_db
def test_headless_route_mounted():
    c = Client()
    r = c.get('/_allauth/browser/v1/auth/session')
    assert r.status_code != 404


@pytest.mark.django_db
def test_verify_email_deep_link_page_renders():
    c = Client()
    r = c.get('/verify-email/sometestkey123/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()


@pytest.mark.django_db
def test_reset_password_deep_link_page_renders():
    c = Client()
    r = c.get('/reset-password/sometestkey456/')
    assert r.status_code == 200
    assert 'site-nav' in r.content.decode()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth_api.py -k "headless or deep_link" -v`
Expected: FAIL — `allauth.headless` not in `INSTALLED_APPS`, `HEADLESS_FRONTEND_URLS` doesn't exist (AttributeError), `/_allauth/...` and `/verify-email/...`/`/reset-password/...` all 404.

- [ ] **Step 3: Add `allauth.headless` and `HEADLESS_FRONTEND_URLS` to settings**

In `config/settings.py`, change `INSTALLED_APPS` (lines 28-49) — add `'allauth.headless'` right after `'allauth.socialaccount.providers.apple'`:

```python
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
    'allauth.mfa',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.apple',
    'allauth.headless',
    'accounts',
    'vocab',
    'grammar',
    'api',
    'dashboard',
]
```

Then add this immediately after `ACCOUNT_SESSION_REMEMBER = None  # show "Remember me" checkbox` (currently `config/settings.py:106`):

```python

# Headless JSON API — powers the JS-driven auth modal (auth-modal.js).
# The classic allauth.urls mount below stays active too: OAuth provider
# redirects/callbacks need it even though the UI no longer links to its pages.
HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': '/verify-email/{key}',
    'account_reset_password_from_key': '/reset-password/{key}',
}
```

- [ ] **Step 4: Add the `/_allauth/` route**

In `config/urls.py`, add `path('_allauth/', include('allauth.headless.urls'))` right after the existing classic mount:

```python
    path('accounts/', include('allauth.urls')),
    path('_allauth/', include('allauth.headless.urls')),
    path('auth/', include('accounts.urls')),
```

- [ ] **Step 5: Run tests to verify the headless tests pass**

Run: `pytest tests/test_auth_api.py -k "headless" -v`
Expected: PASS (the two deep-link tests still fail — routes don't exist yet)

- [ ] **Step 6: Add the two deep-link views**

In `config/views.py`, add at the end:

```python

def verify_email(request, key):
    return render(request, 'auth_deep_link.html')


def reset_password(request, key):
    return render(request, 'auth_deep_link.html')
```

Create `templates/auth_deep_link.html`:

```html
{% extends "base.html" %}
{% block title %}VocabLarry{% endblock %}
{% block content %}{% endblock %}
```

In `config/urls.py`, update the import and add the two routes:

```python
from config.views import home, reading, writing, listening, speaking, verify_email, reset_password
```

```python
    path('verify-email/<str:key>/', verify_email, name='verify_email'),
    path('reset-password/<str:key>/', reset_password, name='reset_password'),
```

Place these two new routes right after the `speaking` route and before the `accounts/` include.

- [ ] **Step 7: Run all tests in this task to verify they pass**

Run: `pytest tests/test_auth_api.py -v`
Expected: PASS, all tests including the pre-existing ones in this file.

- [ ] **Step 8: Commit**

```bash
git add config/settings.py config/urls.py config/views.py templates/auth_deep_link.html tests/test_auth_api.py
git commit -m "feat(vlpe): wire up allauth.headless + email-verify/reset-password deep links"
```

---

### Task 2: Auth modal HTML, CSS, i18n strings, and nav trigger

**Files:**
- Modify: `static/js/i18n.js`
- Create: `templates/partials/auth_modal.html`
- Modify: `templates/base.html`
- Modify: `templates/partials/nav.html`
- Modify: `static/css/base.css`
- Test: `tests/test_pages.py`

**Interfaces:**
- Consumes: nothing from Task 1 directly (this task is pure markup/CSS/strings) — Task 3's JS is what will call the endpoints Task 1 wired up.
- Produces: `#authOverlay` markup present on every page (element IDs: `authOverlay`, `authClose`, `authTitle`, `authRegisterHint`, `authRegisterLink`, `authSocialHint`, the 4 `.auth-social-btn[data-provider]` buttons, `authError`, `authInfo`, `authForm`, `authEmailGroup`, `authEmail`, `authPasswordGroup`, `authPassword`, `authPwToggle`, `authRememberMe`, `authForgotWrap`, `authForgotLink`, `authSignupExtra`, `authName`, `authUsername`, `authPicture`, `authAvatarPreviewWrap`, `authAvatarPreview`, `authMfaGroup`, `authMfaCode`, `authResetGroup`, `authResetPassword`, `authResetPassword2`, `authSubmitBtn`, `authSwitch`) — Task 3's `auth-modal.js` binds to these exact IDs, so do not rename any of them. A single `#signInBtn` button in the nav (replacing the old two `<a>` links). A global `window.t(key)` function in `i18n.js` that Task 3's JS will call.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_nav_has_single_signin_button_when_logged_out():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert '<button type="button" class="btn btn-primary" id="signInBtn" data-i18n="nav.signIn">Sign In</button>' in html


@pytest.mark.django_db
def test_nav_no_longer_links_directly_to_classic_login_signup():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'href="/accounts/login/"' not in html
    assert 'href="/accounts/signup/"' not in html


@pytest.mark.django_db
def test_auth_modal_renders_on_home_page():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    for element_id in (
        'authOverlay', 'authClose', 'authTitle', 'authForm',
        'authEmailGroup', 'authEmail', 'authPasswordGroup', 'authPassword',
        'authPwToggle', 'authRememberMe', 'authForgotWrap', 'authForgotLink',
        'authSignupExtra', 'authName', 'authUsername', 'authPicture',
        'authMfaGroup', 'authMfaCode', 'authResetGroup', 'authResetPassword',
        'authResetPassword2', 'authSubmitBtn', 'authSwitch', 'authError', 'authInfo',
    ):
        assert f'id="{element_id}"' in html, element_id


@pytest.mark.django_db
def test_auth_modal_has_exactly_4_social_providers_no_github():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'data-provider="google"' in html
    assert 'data-provider="facebook"' in html
    assert 'data-provider="microsoft"' in html
    assert 'data-provider="apple"' in html
    assert 'data-provider="github"' not in html


@pytest.mark.django_db
def test_eye_icon_symbols_present_for_password_toggle():
    from django.test import Client
    c = Client()
    r = c.get('/')
    html = r.content.decode()
    assert 'id="i-eye"' in html
    assert 'id="i-eye-off"' in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pages.py -k "signin_button or classic_login_signup or auth_modal or eye_icon" -v`
Expected: FAIL — none of this markup exists yet.

- [ ] **Step 3: Add the `auth.*` translation strings and `t()`/`data-i18n-html` support to `i18n.js`**

In `static/js/i18n.js`, add the following keys to the `en` object (insert right before the closing `},` of `en` at line 53):

```javascript
      "auth.signInTitle": "Sign in",
      "auth.subtitle": "Get access to more learning features",
      "auth.registerHintHtml": "Don't have an account? <a href=\"#\" id=\"authRegisterLink\">Register</a>",
      "auth.email": "Email",
      "auth.password": "Password",
      "auth.rememberMe": "Remember me",
      "auth.forgotPassword": "Forgot your password?",
      "auth.fullName": "Full name",
      "auth.username": "Username",
      "auth.profilePictureOptionalHtml": "Profile picture <small>(optional)</small>",
      "auth.authCode": "Authentication code",
      "auth.mfaPlaceholder": "6-digit code",
      "auth.newPassword": "New password",
      "auth.confirmNewPassword": "Confirm new password",
      "auth.continue": "Continue",
      "auth.or": "or",
      "auth.createAccountTitle": "Create your account",
      "auth.createAccountBtn": "Create account",
      "auth.resetPasswordTitle": "Reset your password",
      "auth.sendResetLink": "Send reset link",
      "auth.willEmailResetLink": "We'll email a reset link to {email}.",
      "auth.alreadyHaveAccount": "Already have an account?",
      "auth.useDifferentEmail": "Use a different email",
      "auth.notYou": "Not you?",
      "auth.twoFactorTitle": "Two-factor authentication",
      "auth.mfaInfo": "Enter the 6-digit code from your authenticator app.",
      "auth.verify": "Verify",
      "auth.networkError": "Could not reach the server.",
      "auth.incorrectCredentials": "Incorrect email or password.",
      "auth.enterMfaCode": "Please enter your 2FA code.",
      "auth.invalidMfaCode": "Invalid 2FA code.",
      "auth.passwordTooShort": "Password must be at least 8 characters.",
      "auth.passwordMismatch": "Passwords do not match.",
      "auth.resetFailed": "Could not reset password. The link may have expired.",
      "auth.checkEmailTitle": "Check your email",
      "auth.orSignInSocial": "Or sign in with a social account you may have used:",
      "auth.resetSentInfo": "If an account exists for {email}, a reset link is on its way.",
      "auth.backToSignIn": "Back to sign in",
      "auth.enterEmail": "Please enter your email address.",
      "auth.nameLettersOnly": "Full name can only contain letters and spaces.",
      "auth.usernameFormat": "Username must be 3–20 characters, letters and numbers only (no spaces or symbols).",
      "auth.accountCreatedInfo": "Account created — please check your email to verify your address.",
      "auth.emailNotVerifiedInfo": "This account's email hasn't been verified yet. Check your inbox for the confirmation link, then try signing in again.",
      "auth.createAccountFailed": "Could not create account.",
      "auth.setNewPasswordTitle": "Set a new password",
      "auth.resetPasswordBtn": "Reset password",
      "auth.chooseNewPasswordInfo": "Choose a new password for your account.",
      "auth.somethingWrong": "Something went wrong.",
      "auth.openingProviderSignIn": "Opening {provider} sign-in…",
      "auth.passwordResetSuccess": "Password reset successful. You can now sign in.",
      "auth.emailVerified": "Email verified! You can now sign in.",
      "auth.verifyLinkInvalid": "This verification link is invalid or has expired.",
      "auth.verifyFailed": "Could not verify your email — please try again.",
```

Add the matching keys to the `vi` object (insert right before the closing `},` of `vi` at line 104):

```javascript
      "auth.signInTitle": "Đăng nhập",
      "auth.subtitle": "Truy cập thêm các tính năng học tập",
      "auth.registerHintHtml": "Chưa có tài khoản? <a href=\"#\" id=\"authRegisterLink\">Đăng ký</a>",
      "auth.email": "Email",
      "auth.password": "Mật khẩu",
      "auth.rememberMe": "Ghi nhớ đăng nhập",
      "auth.forgotPassword": "Quên mật khẩu?",
      "auth.fullName": "Họ và tên",
      "auth.username": "Tên đăng nhập",
      "auth.profilePictureOptionalHtml": "Ảnh đại diện <small>(không bắt buộc)</small>",
      "auth.authCode": "Mã xác thực",
      "auth.mfaPlaceholder": "Mã 6 chữ số",
      "auth.newPassword": "Mật khẩu mới",
      "auth.confirmNewPassword": "Xác nhận mật khẩu mới",
      "auth.continue": "Tiếp tục",
      "auth.or": "hoặc",
      "auth.createAccountTitle": "Tạo tài khoản của bạn",
      "auth.createAccountBtn": "Tạo tài khoản",
      "auth.resetPasswordTitle": "Đặt lại mật khẩu",
      "auth.sendResetLink": "Gửi liên kết đặt lại",
      "auth.willEmailResetLink": "Chúng tôi sẽ gửi liên kết đặt lại tới {email}.",
      "auth.alreadyHaveAccount": "Đã có tài khoản?",
      "auth.useDifferentEmail": "Dùng email khác",
      "auth.notYou": "Không phải bạn?",
      "auth.twoFactorTitle": "Xác thực hai yếu tố",
      "auth.mfaInfo": "Nhập mã 6 chữ số từ ứng dụng xác thực của bạn.",
      "auth.verify": "Xác minh",
      "auth.networkError": "Không thể kết nối đến máy chủ.",
      "auth.incorrectCredentials": "Email hoặc mật khẩu không đúng.",
      "auth.enterMfaCode": "Vui lòng nhập mã 2FA của bạn.",
      "auth.invalidMfaCode": "Mã 2FA không hợp lệ.",
      "auth.passwordTooShort": "Mật khẩu phải có ít nhất 8 ký tự.",
      "auth.passwordMismatch": "Mật khẩu không khớp.",
      "auth.resetFailed": "Không thể đặt lại mật khẩu. Liên kết có thể đã hết hạn.",
      "auth.checkEmailTitle": "Kiểm tra email của bạn",
      "auth.orSignInSocial": "Hoặc đăng nhập bằng tài khoản mạng xã hội bạn có thể đã dùng:",
      "auth.resetSentInfo": "Nếu tồn tại tài khoản cho {email}, liên kết đặt lại đang được gửi tới.",
      "auth.backToSignIn": "Quay lại đăng nhập",
      "auth.enterEmail": "Vui lòng nhập địa chỉ email của bạn.",
      "auth.nameLettersOnly": "Họ và tên chỉ được chứa chữ cái và khoảng trắng.",
      "auth.usernameFormat": "Tên đăng nhập phải dài 3–20 ký tự, chỉ gồm chữ cái và số (không dấu cách hoặc ký hiệu).",
      "auth.accountCreatedInfo": "Đã tạo tài khoản — vui lòng kiểm tra email để xác minh địa chỉ của bạn.",
      "auth.emailNotVerifiedInfo": "Email của tài khoản này chưa được xác minh. Vui lòng kiểm tra hộp thư để lấy liên kết xác nhận, sau đó thử đăng nhập lại.",
      "auth.createAccountFailed": "Không thể tạo tài khoản.",
      "auth.setNewPasswordTitle": "Đặt mật khẩu mới",
      "auth.resetPasswordBtn": "Đặt lại mật khẩu",
      "auth.chooseNewPasswordInfo": "Chọn mật khẩu mới cho tài khoản của bạn.",
      "auth.somethingWrong": "Đã xảy ra lỗi.",
      "auth.openingProviderSignIn": "Đang mở đăng nhập {provider}…",
      "auth.passwordResetSuccess": "Đặt lại mật khẩu thành công. Bây giờ bạn có thể đăng nhập.",
      "auth.emailVerified": "Email đã được xác minh! Bây giờ bạn có thể đăng nhập.",
      "auth.verifyLinkInvalid": "Liên kết xác minh này không hợp lệ hoặc đã hết hạn.",
      "auth.verifyFailed": "Không thể xác minh email của bạn — vui lòng thử lại.",
```

Now remove the now-unused `"nav.signUp"` key from both `en` and `vi` objects (nav.html will no longer render a separate Sign Up link after Step 6 below):

```
Remove this line from `en`:      "nav.signUp": "Sign Up",
Remove this line from `vi`:      "nav.signUp": "Đăng ký",
```

Add `data-i18n-html` support to `applyLang()` — insert right after the existing `data-i18n-placeholder` block, still inside `applyLang(lang)`:

```javascript
    document.querySelectorAll("[data-i18n-html]").forEach(function(el){
      var key = el.getAttribute("data-i18n-html");
      if (dict[key]) el.innerHTML = dict[key];
    });
```

Finally, expose a global `t(key)` helper — add this right after the `applyLang` function definition, still inside the outer IIFE, before the `var saved = "en";` line:

```javascript
  function t(key){
    var current = document.documentElement.getAttribute("lang") || "en";
    var dict = STRINGS[current] || STRINGS.en;
    return dict[key] || STRINGS.en[key] || key;
  }
  window.t = t;
```

- [ ] **Step 4: Add the `i-eye`/`i-eye-off` icon symbols to `base.html`**

In `templates/base.html`, add these two `<symbol>` elements to the sprite `<svg>` block, right after the existing `<symbol id="i-moon" ...>` line (`templates/base.html:17`):

```html
  <symbol id="i-eye" viewBox="0 0 24 24"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></symbol>
  <symbol id="i-eye-off" viewBox="0 0 24 24"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></symbol>
```

- [ ] **Step 5: Create the auth modal partial**

Create `templates/partials/auth_modal.html`:

```html
<div class="auth-modal-overlay" id="authOverlay">
  <div class="auth-modal auth-modal-lg">
    <button class="auth-modal-close" id="authClose" aria-label="Close">&times;</button>
    <h2 class="auth-modal-title" id="authTitle" data-i18n="auth.signInTitle">Sign in</h2>
    <p class="auth-modal-subtitle" data-i18n="auth.subtitle">Get access to more learning features</p>
    <p class="auth-switch" id="authRegisterHint" data-i18n-html="auth.registerHintHtml">Don't have an account? <a href="#" id="authRegisterLink">Register</a></p>

    <p class="auth-modal-subtitle auth-hidden" id="authSocialHint"></p>
    <div class="auth-social-row">
      <button type="button" class="auth-social-btn" data-provider="google" title="Continue with Google">
        <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#4285F4" d="M23.49 12.27c0-.82-.07-1.42-.22-2.04H12v3.91h6.4c-.13 1.06-.83 2.66-2.39 3.74l-.02.14 3.47 2.69.24.02c2.21-2.04 3.79-5.04 3.79-8.46Z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.07 7.93-2.91l-3.78-2.93c-1.02.71-2.38 1.21-4.15 1.21-3.16 0-5.84-2.07-6.79-4.96l-.14.01-3.6 2.78-.05.13C3.4 21.3 7.36 24 12 24Z"/><path fill="#FBBC05" d="M5.21 14.41A7.4 7.4 0 0 1 4.8 12c0-.84.15-1.65.4-2.41l-.01-.16-3.65-2.83-.12.06A11.97 11.97 0 0 0 0 12c0 1.93.47 3.76 1.42 5.34l3.79-2.93Z"/><path fill="#EA4335" d="M12 4.75c2.26 0 3.78.97 4.65 1.79l3.39-3.31C17.94 1.19 15.24 0 12 0 7.36 0 3.4 2.7 1.42 6.66l3.78 2.93C6.16 6.7 8.84 4.75 12 4.75Z"/></svg>
      </button>
      <button type="button" class="auth-social-btn" data-provider="facebook" title="Continue with Facebook">
        <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </button>
      <button type="button" class="auth-social-btn" data-provider="microsoft" title="Continue with Microsoft">
        <svg viewBox="0 0 24 24" width="22" height="22"><path fill="#F25022" d="M1 1h10.3v10.3H1z"/><path fill="#7FBA00" d="M12.7 1H23v10.3H12.7z"/><path fill="#00A4EF" d="M1 12.7h10.3V23H1z"/><path fill="#FFB900" d="M12.7 12.7H23V23H12.7z"/></svg>
      </button>
      <button type="button" class="auth-social-btn" data-provider="apple" title="Continue with Apple">
        <svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M16.365 1.43c0 1.14-.415 2.05-1.245 2.735-.83.685-1.83 1.08-2.996 1.18-.03-.06-.06-.19-.06-.4 0-1.1.42-2.05 1.26-2.85.42-.4.9-.71 1.44-.94.54-.23 1.05-.36 1.53-.4.02.2.03.4.03.6zm3.75 5.85c-.06.05-1.845 1.08-1.845 3.3 0 2.565 2.25 3.475 2.31 3.5-.01.06-.36 1.235-1.19 2.44-.74 1.06-1.51 2.115-2.72 2.135-1.19.02-1.57-.705-2.93-.705-1.365 0-1.79.685-2.915.725-1.17.04-2.06-1.15-2.81-2.205-1.53-2.16-2.7-6.1-1.13-8.755.78-1.32 2.175-2.155 3.69-2.175 1.15-.02 2.23.775 2.93.775.695 0 1.995-.955 3.365-.815.575.025 2.19.235 3.245 1.78z"/></svg>
      </button>
    </div>
    <div class="auth-divider"><span data-i18n="auth.or">or</span></div>

    <p class="auth-modal-error" id="authError"></p>
    <p class="auth-modal-info auth-hidden" id="authInfo"></p>
    <form id="authForm">
      <label class="auth-field" id="authEmailGroup">
        <span data-i18n="auth.email">Email</span>
        <input type="email" id="authEmail" required autocomplete="email">
      </label>
      <div id="authPasswordGroup" class="auth-hidden">
        <label class="auth-field">
          <span data-i18n="auth.password">Password</span>
          <div class="auth-password-wrap">
            <input type="password" id="authPassword" autocomplete="current-password">
            <button type="button" class="auth-pw-toggle" id="authPwToggle" aria-label="Show password"><svg class="ico" aria-hidden="true"><use href="#i-eye"/></svg></button>
          </div>
        </label>
        <div class="auth-options-row">
          <label class="auth-remember-me">
            <input type="checkbox" id="authRememberMe">
            <span data-i18n="auth.rememberMe">Remember me</span>
          </label>
          <p class="auth-forgot-link auth-hidden" id="authForgotWrap"><a href="#" id="authForgotLink" data-i18n="auth.forgotPassword">Forgot your password?</a></p>
        </div>
      </div>
      <div id="authSignupExtra" class="auth-hidden">
        <label class="auth-field">
          <span data-i18n="auth.fullName">Full name</span>
          <input type="text" id="authName" autocomplete="name">
        </label>
        <label class="auth-field">
          <span data-i18n="auth.username">Username</span>
          <input type="text" id="authUsername" autocomplete="username">
        </label>
        <label class="auth-field">
          <span data-i18n-html="auth.profilePictureOptionalHtml">Profile picture <small>(optional)</small></span>
          <input type="file" id="authPicture" accept="image/png,image/jpeg,image/gif,image/webp">
        </label>
        <div class="avatar-preview-wrap auth-hidden" id="authAvatarPreviewWrap">
          <img id="authAvatarPreview" alt="Profile picture preview">
        </div>
      </div>
      <div id="authMfaGroup" class="auth-hidden">
        <label class="auth-field">
          <span data-i18n="auth.authCode">Authentication code</span>
          <input type="text" id="authMfaCode" inputmode="numeric" autocomplete="one-time-code" placeholder="6-digit code" data-i18n-placeholder="auth.mfaPlaceholder">
        </label>
      </div>
      <div id="authResetGroup" class="auth-hidden">
        <label class="auth-field">
          <span data-i18n="auth.newPassword">New password</span>
          <input type="password" id="authResetPassword" autocomplete="new-password">
        </label>
        <label class="auth-field">
          <span data-i18n="auth.confirmNewPassword">Confirm new password</span>
          <input type="password" id="authResetPassword2" autocomplete="new-password">
        </label>
      </div>
      <button type="submit" class="auth-submit-btn" id="authSubmitBtn" data-i18n="auth.continue">Continue</button>
    </form>
    <p class="auth-switch auth-hidden" id="authSwitch"></p>
  </div>
</div>
```

- [ ] **Step 6: Include the partial in `base.html` and update `nav.html`**

In `templates/base.html`, add the include right after `{% include "partials/nav.html" %}` (line 103):

```html
{% include "partials/nav.html" %}
{% include "partials/auth_modal.html" %}
```

In `templates/partials/nav.html`, replace lines 43-50 (the `{% if user.is_authenticated %}...{% endif %}` block inside `.nav-actions`):

```html
    {% if user.is_authenticated %}
      <span>{{ user.username }}</span>
      <a class="btn" href="{% url 'account_logout' %}" data-i18n="nav.signOut">Sign Out</a>
    {% else %}
      <button type="button" class="btn btn-primary" id="signInBtn" data-i18n="nav.signIn">Sign In</button>
    {% endif %}
```

- [ ] **Step 7: Add the auth-modal CSS to `base.css`**

Append to the end of `static/css/base.css`:

```css

/* Auth modal (sign in / sign up / MFA / password reset) — ported from
   production's #authOverlay. Uses rgb(var(--violet) / X), not
   rgba(var(--violet), X) — --violet is a space-separated RGB triplet. */
.auth-hidden{display:none !important;}

.auth-modal-overlay{
  display:none; position:fixed; inset:0; background:rgba(0,0,0,.6); backdrop-filter:blur(6px); -webkit-backdrop-filter:blur(6px);
  align-items:center; justify-content:center; z-index:200; padding:16px;
}
.auth-modal-overlay.open{display:flex;}
.auth-modal{
  position:relative; width:100%; max-width:380px; max-height:85vh; overflow-y:auto;
  background:rgba(22,26,35,.95); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
  border:1px solid rgb(var(--violet) / .25); border-radius:20px; padding:28px 24px;
  box-shadow:0 24px 64px rgba(0,0,0,.5);
}
[data-theme="light"] .auth-modal{background:rgba(255,255,255,.96);}
.auth-modal-lg{max-width:440px; padding:36px 32px;}
.auth-modal-lg .auth-modal-title{margin-bottom:6px;}
.auth-modal-subtitle{margin:0 0 14px; font-size:.92rem; color:var(--muted); text-align:center;}
#authRegisterHint{margin:0 0 22px;}
.auth-social-row{display:flex; gap:10px; justify-content:center; margin-bottom:20px;}
.auth-social-btn{
  flex:1; max-width:80px; aspect-ratio:1; display:flex; align-items:center; justify-content:center;
  border:1px solid rgb(var(--violet) / .2); border-radius:12px; background:rgb(var(--violet) / .07); color:var(--text);
  cursor:pointer; transition:border-color .15s ease, background .15s ease, transform .2s cubic-bezier(.25,.46,.45,.94);
}
.auth-social-btn:hover{border-color:rgb(var(--violet) / .5); background:rgb(var(--violet) / .14); transform:translateY(-1px);}
.auth-divider{display:flex; align-items:center; gap:10px; margin:0 0 20px; color:var(--muted); font-size:.8rem; font-family:'JetBrains Mono',monospace;}
.auth-divider::before, .auth-divider::after{content:""; flex:1; height:1px; background:rgb(var(--violet) / .2);}
.auth-password-wrap{position:relative;}
.auth-password-wrap input{padding-right:42px;}
.auth-pw-toggle{
  position:absolute; right:6px; top:50%; transform:translateY(-50%); width:30px; height:30px;
  border:none; background:transparent; cursor:pointer; font-size:1rem; color:var(--muted);
  display:flex; align-items:center; justify-content:center; border-radius:6px;
}
.auth-pw-toggle:hover{background:var(--card-bg);}
.avatar-preview-wrap{display:flex; justify-content:center; margin-bottom:14px;}
.avatar-preview-wrap img{
  width:84px; height:84px; border-radius:50%; object-fit:cover; border:2px solid var(--border);
}
.auth-modal-close{
  position:absolute; top:14px; right:14px; width:28px; height:28px; border-radius:50%;
  border:none; background:transparent; color:var(--muted); font-size:1.3rem; line-height:1;
  cursor:pointer; display:flex; align-items:center; justify-content:center;
}
.auth-modal-close:hover{background:var(--card-bg); color:var(--text);}
.auth-modal-title{margin:0 0 18px; font-size:1.25rem; font-weight:800; color:var(--text); text-align:center;}
.auth-modal-error{
  margin:0 0 14px; padding:9px 12px; border-radius:8px; background:rgba(220,38,38,.1);
  border:1px solid rgba(220,38,38,.35); color:#dc2626; font-size:.82rem; font-weight:600;
}
.auth-modal-error:empty{display:none;}
.auth-field{display:block; margin-bottom:14px;}
.auth-field span{display:block; margin-bottom:6px; font-size:.82rem; font-weight:700; color:var(--text);}
.auth-field small{font-weight:400; color:var(--muted);}
.auth-field input{
  width:100%; padding:10px 12px; border-radius:10px; border:1px solid rgb(var(--violet) / .22);
  background:rgb(var(--violet) / .07); color:var(--text); font-size:.92rem; box-sizing:border-box;
  font-family:'Plus Jakarta Sans','Inter',sans-serif; transition:border-color .18s, box-shadow .18s;
}
.auth-field input:focus{outline:none; border-color:rgb(var(--violet) / .6); box-shadow:0 0 0 3px rgb(var(--violet) / .12);}
.auth-submit-btn{
  width:100%; padding:11px; border-radius:10px; border:none;
  background:linear-gradient(135deg,#7c3aed,#6d28d9);
  color:#fff; font-size:.92rem; font-weight:700; cursor:pointer;
  box-shadow:0 4px 14px rgb(var(--violet) / .35);
  transition:transform .2s cubic-bezier(.25,.46,.45,.94), box-shadow .2s ease;
}
.auth-submit-btn:hover{transform:translateY(-1px); box-shadow:0 6px 20px rgb(var(--violet) / .45);}
.auth-submit-btn:disabled{opacity:.6; cursor:not-allowed; transform:none; box-shadow:none;}
.auth-switch{margin:16px 0 0; text-align:center; font-size:.82rem; color:var(--muted);}
.auth-switch a{color:rgb(var(--violet)); font-weight:700; text-decoration:none; cursor:pointer;}
.auth-switch a:hover{text-decoration:underline;}
.auth-modal-info{
  margin:0 0 14px; padding:9px 12px; border-radius:10px; background:rgb(var(--violet) / .1);
  border:1px solid rgb(var(--violet) / .3); color:var(--text); font-size:.82rem; font-weight:600;
}
.auth-modal-info:empty{display:none;}
.auth-options-row{display:flex; align-items:center; justify-content:space-between; gap:10px; margin:-6px 0 14px;}
.auth-forgot-link{margin:0; font-size:.8rem;}
.auth-forgot-link a{color:rgb(var(--violet)); font-weight:600; text-decoration:none; cursor:pointer;}
.auth-forgot-link a:hover{text-decoration:underline;}
.auth-remember-me{display:flex; align-items:center; gap:6px; font-size:.8rem; color:var(--muted); cursor:pointer; user-select:none;}
.auth-remember-me input{width:14px; height:14px; accent-color:rgb(var(--violet)); cursor:pointer;}
```

- [ ] **Step 8: Run all tests in this task to verify they pass**

Run: `pytest tests/test_pages.py -v`
Expected: PASS, all tests including pre-existing ones (check especially `test_home_page_has_nav_and_hero`, `test_login_page_uses_site_layout`, `test_signup_page_uses_site_layout` still pass — they only assert `'Sign In'` substring presence, which the new button still satisfies).

- [ ] **Step 9: Commit**

```bash
git add static/js/i18n.js templates/partials/auth_modal.html templates/base.html templates/partials/nav.html static/css/base.css tests/test_pages.py
git commit -m "feat(vlpe): add auth modal markup, CSS, and i18n strings; collapse nav to single Sign In trigger"
```

---

### Task 3: `auth-modal.js` state machine

**Files:**
- Create: `static/js/auth-modal.js`
- Modify: `templates/base.html`
- Test: `tests/test_pages.py`

**Interfaces:**
- Consumes: `window.t(key)` from Task 2's `i18n.js`; the element IDs from Task 2's `auth_modal.html`; `/_allauth/browser/v1/auth/*` endpoints from Task 1; VLPE's existing `/auth/check-email/`, `/auth/update-profile/` endpoints (already built, `accounts/urls.py`/`accounts/views.py` — no changes).
- Produces: `openAuthModal()`/`closeAuthModal()` (called by the nav's `#signInBtn` and by deep-link/flash handling), all bound at load time inside a single IIFE (no other file calls into this one).

- [ ] **Step 1: Write the failing test**

Append to `tests/test_pages.py`:

```python
@pytest.mark.django_db
def test_auth_modal_js_included_on_every_page():
    from django.test import Client
    c = Client()
    r = c.get('/')
    assert 'auth-modal.js' in r.content.decode()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pages.py::test_auth_modal_js_included_on_every_page -v`
Expected: FAIL — script not included yet.

- [ ] **Step 3: Create `static/js/auth-modal.js`**

```javascript
(function(){
  const ALLAUTH_BASE = '/_allauth/browser/v1';
  const AUTH_BASE = '/auth';

  function getCsrf(){
    return document.cookie.split(';').map(c => c.trim())
      .find(c => c.startsWith('csrftoken='))?.split('=')[1] ?? '';
  }

  function authFetch(url, opts = {}){
    return fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json', ...(opts.headers ?? {}) },
      ...opts,
    });
  }

  const authState = { step: "email", email: "", resetKey: null };

  function resetAuthForm(){
    authState.step = "email";
    authState.email = "";
    document.getElementById("authEmail").value = "";
    document.getElementById("authEmail").disabled = false;
    document.getElementById("authPassword").value = "";
    document.getElementById("authPassword").type = "password";
    document.getElementById("authPwToggle").innerHTML = `<svg class="ico" aria-hidden="true"><use href="#i-eye"/></svg>`;
    document.getElementById("authRememberMe").checked = false;
    document.getElementById("authName").value = "";
    document.getElementById("authUsername").value = "";
    document.getElementById("authPicture").value = "";
    document.getElementById("authAvatarPreviewWrap").classList.add("auth-hidden");
    document.getElementById("authAvatarPreview").src = "";
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.add("auth-hidden");
    document.getElementById("authMfaGroup").classList.add("auth-hidden");
    document.getElementById("authMfaCode").value = "";
    document.getElementById("authResetGroup").classList.add("auth-hidden");
    document.getElementById("authResetPassword").value = "";
    document.getElementById("authResetPassword2").value = "";
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.add("auth-hidden");
    document.getElementById("authRegisterHint").classList.remove("auth-hidden");
    document.getElementById("authEmailGroup").classList.remove("auth-hidden");
    document.getElementById("authSocialHint").classList.add("auth-hidden");
    document.getElementById("authError").textContent = "";
    showAuthInfo("");
    document.getElementById("authTitle").textContent = t("auth.signInTitle");
    document.getElementById("authSubmitBtn").textContent = t("auth.continue");
    document.getElementById("authSubmitBtn").disabled = false;
    document.getElementById("authSubmitBtn").classList.remove("auth-hidden");
  }

  function openAuthModal(){
    resetAuthForm();
    document.getElementById("authOverlay").classList.add("open");
    document.getElementById("authEmail").focus();
    document.body.style.overflow = "hidden";
  }

  function closeAuthModal(){
    document.getElementById("authOverlay").classList.remove("open");
    document.body.style.overflow = "";
  }

  function showAuthError(msg){
    document.getElementById("authError").textContent = msg;
  }

  function showAuthInfo(msg){
    const el = document.getElementById("authInfo");
    el.textContent = msg;
    el.classList.toggle("auth-hidden", !msg);
  }

  function showCheckEmailScreen(infoText){
    document.getElementById("authTitle").textContent = t("auth.checkEmailTitle");
    document.getElementById("authEmailGroup").classList.add("auth-hidden");
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.add("auth-hidden");
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSubmitBtn").classList.add("auth-hidden");
    document.getElementById("authRegisterHint").classList.add("auth-hidden");
    const socialHint = document.getElementById("authSocialHint");
    socialHint.textContent = t("auth.orSignInSocial");
    socialHint.classList.remove("auth-hidden");
    document.getElementById("authSwitch").classList.remove("auth-hidden");
    document.getElementById("authSwitch").innerHTML = `<a href="#" id="authBackLink">${t("auth.backToSignIn")}</a>`;
    showAuthInfo(infoText);
  }

  function previewAvatarFile(file, wrapId, imgId){
    const wrap = document.getElementById(wrapId);
    const img = document.getElementById(imgId);
    if (!file){ wrap.classList.add("auth-hidden"); img.src = ""; return; }
    const reader = new FileReader();
    reader.onload = () => { img.src = reader.result; wrap.classList.remove("auth-hidden"); };
    reader.readAsDataURL(file);
  }

  function socialLogin(provider, process){
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/_allauth/browser/v1/auth/provider/redirect';
    const fields = {
      provider: provider,
      callback_url: window.location.origin + '/',
      process: process || 'login',
      csrfmiddlewaretoken: getCsrf()
    };
    for (const [name, value] of Object.entries(fields)) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
  }

  // Trimmed down from production's initAuth(): VLPE is server-rendered, so
  // the nav's logged-in state already comes from {% if user.is_authenticated %}
  // on the next page load (see the login/mfa/signup success handlers below,
  // which reload the page instead of refreshing client-side state). The one
  // piece with no server-side equivalent is auto-opening the modal when a
  // session has a pending, not-yet-verified signup.
  async function initAuth(){
    try {
      const res = await fetch(`${ALLAUTH_BASE}/auth/session`, { credentials: 'same-origin' });
      const data = await res.json();
      const flows = data?.data?.flows || [];
      const pendingVerifyEmail = !(data?.data?.user) && flows.some(f => f.id === "verify_email" && f.is_pending);
      if (pendingVerifyEmail){
        openAuthModal();
        showCheckEmailScreen(t("auth.emailNotVerifiedInfo"));
      }
    } catch(e){}
  }

  // Handle allauth email links that land here:
  //   /verify-email/<key>/   → POST the key to the headless verify endpoint
  //   /reset-password/<key>/ → show a set-new-password form
  async function handleAuthDeepLinks(){
    const verifyMatch = window.location.pathname.match(/^\/verify-email\/([^/]+)\/?$/);
    const resetMatch  = window.location.pathname.match(/^\/reset-password\/([^/]+)\/?$/);

    if (verifyMatch){
      const key = decodeURIComponent(verifyMatch[1]);
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/email/verify`, {
          method: 'POST',
          body: JSON.stringify({ key }),
        });
        const data = await res.json().catch(() => ({}));
        const ok = res.status === 200 || data.status === 200;
        try {
          sessionStorage.setItem("vlpe_flash", ok
            ? t("auth.emailVerified")
            : t("auth.verifyLinkInvalid"));
        } catch(e){}
      } catch(e){
        try { sessionStorage.setItem("vlpe_flash", t("auth.verifyFailed")); } catch(_){}
      }
      window.location.href = "/";
      return;
    }

    if (resetMatch){
      authState.resetKey = decodeURIComponent(resetMatch[1]);
      openAuthModal();
      authState.step = "reset";
      document.getElementById("authTitle").textContent = t("auth.setNewPasswordTitle");
      document.getElementById("authEmail").closest("label").classList.add("auth-hidden");
      document.getElementById("authPasswordGroup").classList.add("auth-hidden");
      document.getElementById("authSignupExtra").classList.add("auth-hidden");
      document.getElementById("authRegisterHint").classList.add("auth-hidden");
      document.getElementById("authResetGroup").classList.remove("auth-hidden");
      document.getElementById("authSubmitBtn").textContent = t("auth.resetPasswordBtn");
      showAuthInfo(t("auth.chooseNewPasswordInfo"));
    }
  }

  document.getElementById("signInBtn").addEventListener("click", openAuthModal);
  document.getElementById("authClose").addEventListener("click", closeAuthModal);
  document.getElementById("authOverlay").addEventListener("click", (e) => {
    if (e.target.id === "authOverlay") closeAuthModal();
  });

  document.getElementById("authSwitch").addEventListener("click", (e) => {
    if (e.target.id === "authBackLink"){
      e.preventDefault();
      resetAuthForm();
      document.getElementById("authEmail").focus();
    }
  });

  document.getElementById("authRegisterHint").addEventListener("click", (e) => {
    if (e.target.id !== "authRegisterLink") return;
    e.preventDefault();
    authState.step = "signup";
    showAuthError("");
    showAuthInfo("");
    document.getElementById("authTitle").textContent = t("auth.createAccountTitle");
    document.getElementById("authPasswordGroup").classList.remove("auth-hidden");
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.remove("auth-hidden");
    document.getElementById("authRegisterHint").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.remove("auth-hidden");
    document.getElementById("authSwitch").innerHTML = `${t("auth.alreadyHaveAccount")} <a href="#" id="authBackLink">${t("auth.signInTitle")}</a>`;
    document.getElementById("authSubmitBtn").textContent = t("auth.createAccountBtn");
    document.getElementById("authEmail").focus();
  });

  document.getElementById("authForgotLink").addEventListener("click", (e) => {
    e.preventDefault();
    authState.step = "forgot";
    showAuthError("");
    document.getElementById("authTitle").textContent = t("auth.resetPasswordTitle");
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.add("auth-hidden");
    showAuthInfo(t("auth.willEmailResetLink").replace("{email}", authState.email));
    document.getElementById("authSubmitBtn").textContent = t("auth.sendResetLink");
  });

  document.getElementById("authPwToggle").addEventListener("click", () => {
    const input = document.getElementById("authPassword");
    const toggle = document.getElementById("authPwToggle");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.innerHTML = `<svg class="ico" aria-hidden="true"><use href="#${show ? "i-eye-off" : "i-eye"}"/></svg>`;
  });

  document.getElementById("authPicture").addEventListener("change", (e) => {
    previewAvatarFile(e.target.files[0], "authAvatarPreviewWrap", "authAvatarPreview");
  });

  document.querySelectorAll(".auth-social-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      showAuthError("");
      showAuthInfo(t("auth.openingProviderSignIn").replace("{provider}", btn.dataset.provider));
      socialLogin(btn.dataset.provider);
    });
  });

  document.getElementById("authForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthError("");
    const submitBtn = document.getElementById("authSubmitBtn");

    if (authState.step === "email"){
      const email = document.getElementById("authEmail").value.trim();
      if (!email) return;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${AUTH_BASE}/check-email/`, {
          method: 'POST',
          body: JSON.stringify({ email }),
        });
        const data = await res.json();
        if (!res.ok){ showAuthError(data.error || t("auth.somethingWrong")); return; }

        authState.email = email;
        document.getElementById("authEmail").disabled = true;
        document.getElementById("authPasswordGroup").classList.remove("auth-hidden");
        document.getElementById("authSwitch").classList.remove("auth-hidden");
        document.getElementById("authSwitch").innerHTML = `${t("auth.notYou")} <a href="#" id="authBackLink">${t("auth.useDifferentEmail")}</a>`;
        document.getElementById("authRegisterHint").classList.add("auth-hidden");
        showAuthInfo("");

        if (data.exists){
          authState.step = "login";
          document.getElementById("authTitle").textContent = t("auth.signInTitle");
          document.getElementById("authSignupExtra").classList.add("auth-hidden");
          document.getElementById("authForgotWrap").classList.remove("auth-hidden");
          submitBtn.textContent = t("auth.signInTitle");
        } else {
          authState.step = "signup";
          document.getElementById("authTitle").textContent = t("auth.createAccountTitle");
          document.getElementById("authSignupExtra").classList.remove("auth-hidden");
          document.getElementById("authForgotWrap").classList.add("auth-hidden");
          submitBtn.textContent = t("auth.createAccountBtn");
        }
        document.getElementById("authPassword").focus();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "login"){
      const password = document.getElementById("authPassword").value;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/login`, {
          method: 'POST',
          body: JSON.stringify({ email: authState.email, password }),
        });
        const data = await res.json();
        // MFA-enabled account: allauth returns 401 with a pending
        // mfa_authenticate flow. Switch to the 2FA code step instead of erroring.
        const flows = data?.data?.flows || [];
        if (res.status === 401 && flows.some(f => f.id === "mfa_authenticate")){
          authState.step = "mfa";
          document.getElementById("authTitle").textContent = t("auth.twoFactorTitle");
          document.getElementById("authPasswordGroup").classList.add("auth-hidden");
          document.getElementById("authForgotWrap").classList.add("auth-hidden");
          document.getElementById("authMfaGroup").classList.remove("auth-hidden");
          showAuthInfo(t("auth.mfaInfo"));
          submitBtn.textContent = t("auth.verify");
          document.getElementById("authMfaCode").focus();
          return;
        }
        // The password was correct (allauth got as far as flagging a pending
        // verify_email flow, not just re-showing "login") but the account's
        // email isn't verified yet — show the real reason instead of falling
        // through to "incorrect credentials".
        if (res.status === 401 && flows.some(f => f.id === "verify_email")){
          showCheckEmailScreen(t("auth.emailNotVerifiedInfo"));
          return;
        }
        if (data.status !== 200){ showAuthError((data.errors?.[0]?.message) || t("auth.incorrectCredentials")); return; }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "mfa"){
      const code = document.getElementById("authMfaCode").value.trim();
      if (!code){ showAuthError(t("auth.enterMfaCode")); return; }
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/2fa/authenticate`, {
          method: 'POST',
          body: JSON.stringify({ code }),
        });
        const data = await res.json();
        if (data.status !== 200){ showAuthError(t("auth.invalidMfaCode")); return; }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "reset"){
      const pw1 = document.getElementById("authResetPassword").value;
      const pw2 = document.getElementById("authResetPassword2").value;
      if (!pw1 || pw1.length < 8){ showAuthError(t("auth.passwordTooShort")); return; }
      if (pw1 !== pw2){ showAuthError(t("auth.passwordMismatch")); return; }
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/password/reset`, {
          method: 'POST',
          body: JSON.stringify({ key: authState.resetKey, password: pw1 }),
        });
        const data = await res.json();
        if (res.status !== 200 && data.status !== 200){
          showAuthError((data.errors?.[0]?.message) || t("auth.resetFailed"));
          return;
        }
        sessionStorage.setItem("vlpe_flash", t("auth.passwordResetSuccess"));
        window.location.href = "/";
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "forgot"){
      submitBtn.disabled = true;
      try {
        await authFetch(`${ALLAUTH_BASE}/auth/password/request`, {
          method: 'POST',
          body: JSON.stringify({ email: authState.email }),
        });
        authState.step = "forgot-sent";
        document.getElementById("authTitle").textContent = t("auth.checkEmailTitle");
        showAuthInfo(t("auth.resetSentInfo").replace("{email}", authState.email));
        submitBtn.classList.add("auth-hidden");
        document.getElementById("authSwitch").innerHTML = `<a href="#" id="authBackLink">${t("auth.backToSignIn")}</a>`;
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "forgot-sent"){
      return;
    }

    if (authState.step === "signup"){
      const email = document.getElementById("authEmail").value.trim();
      const password = document.getElementById("authPassword").value;
      const name = document.getElementById("authName").value.trim();
      const username = document.getElementById("authUsername").value.trim();
      const pictureInput = document.getElementById("authPicture");

      if (!email){
        showAuthError(t("auth.enterEmail"));
        return;
      }
      if (!/^[\p{L}\s]{1,60}$/u.test(name)){
        showAuthError(t("auth.nameLettersOnly"));
        return;
      }
      if (!/^[A-Za-z0-9]{3,20}$/.test(username)){
        showAuthError(t("auth.usernameFormat"));
        return;
      }

      authState.email = email;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/signup`, {
          method: 'POST',
          body: JSON.stringify({ email, username, password }),
        });
        const data = await res.json();
        // Mandatory email verification: allauth returns 401 with a pending
        // verify_email flow. The account WAS created — don't treat it as an error.
        const flows = data?.data?.flows || [];
        if (res.status === 401 && flows.some(f => f.id === "verify_email")){
          showCheckEmailScreen(t("auth.accountCreatedInfo"));
          return;
        }
        if (data.status !== 200){ showAuthError((data.errors?.[0]?.message) || t("auth.createAccountFailed")); return; }
        // Allauth headless doesn't accept name/picture — save them now that the account exists
        if (name || pictureInput.files[0]) {
          const pf = new FormData();
          if (name) pf.append('name', name);
          if (pictureInput.files[0]) pf.append('picture', pictureInput.files[0]);
          await fetch(`${AUTH_BASE}/update-profile/`, {
            method: 'POST', credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCsrf() }, body: pf,
          }).catch(() => {});
        }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }
  });

  // Show any one-shot flash message stashed before a redirect (e.g. password reset).
  (function showPendingFlash(){
    let msg = null;
    try { msg = sessionStorage.getItem("vlpe_flash"); sessionStorage.removeItem("vlpe_flash"); } catch(e){}
    if (msg){ openAuthModal(); showAuthInfo(msg); }
  })();

  initAuth();
  handleAuthDeepLinks();
})();
```

- [ ] **Step 4: Include the script in `base.html`**

In `templates/base.html`, add the script tag right after `<script src="{% static 'js/nav.js' %}" defer></script>` (line 114):

```html
<script src="{% static 'js/auth-modal.js' %}" defer></script>
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_pages.py::test_auth_modal_js_included_on_every_page -v`
Expected: PASS

- [ ] **Step 6: Run the full test suite**

Run: `pytest -q`
Expected: PASS, no regressions anywhere in the project.

- [ ] **Step 7: Commit**

```bash
git add static/js/auth-modal.js templates/base.html tests/test_pages.py
git commit -m "feat(vlpe): add auth-modal.js state machine (login/signup/mfa/reset/forgot + 4 social providers)"
```

---

### Task 4: Manual verification against real accounts (not Python-testable)

This task has no code changes. Per this project's standing rule ("manual verification is not optional for anything touching rendering/interaction") and the spec's own Testing section, the login/signup/MFA/social-redirect behavior is a real state machine driving real network calls — Python tests only prove the plumbing exists (routes resolve, markup renders), not that the flows actually work end to end.

- [ ] **Step 1: Start the dev server**

Run: `python manage.py runserver` (from `VocabLarry Professional Environment/`)

- [ ] **Step 2: Email + password sign-up flow**

Using the Chrome browser tools, navigate to `http://127.0.0.1:8000/`, click "Sign In", type a brand-new email, submit, confirm it switches to the "Create your account" step, fill in password/full name/username, submit. Confirm the "Check your email" screen appears (since `ACCOUNT_EMAIL_VERIFICATION` defaults to `mandatory`). Check the console-backend email output in the terminal running `runserver` for the verification link, open it, confirm `/verify-email/<key>/` shows the "Email verified!" flash on redirect to `/`.

- [ ] **Step 3: Email + password sign-in flow**

Sign in with the account created in Step 2 (now verified). Confirm the modal closes and the page reloads showing the username + Sign Out in the nav.

- [ ] **Step 4: Password reset flow**

Click "Sign In" → enter the same email → click "Forgot your password?" → submit. Check the console-backend email output for the reset link, open it, confirm the modal opens directly to "Set a new password", submit a new password, confirm the "Password reset successful" flash appears on `/` and the new password signs in.

- [ ] **Step 5: MFA-enabled account**

Using an existing account with `allauth.mfa` TOTP enabled (create one via Django admin or the classic `/accounts/2fa/` flow if none exists yet), sign in with email+password and confirm the modal switches to the "Two-factor authentication" step; enter the code and confirm successful sign-in.

- [ ] **Step 6: One real social-provider round trip**

Using whichever of Google/Facebook/Microsoft/Apple has real OAuth credentials configured in `.env` for this environment, click that provider's button in the modal and confirm the redirect completes and returns the user signed in.

- [ ] **Step 7: Update `FIXES-NEEDED.md`**

Check off items 1-5 in `VocabLarry Professional Environment/FIXES-NEEDED.md` (adjust item 3's text to note the GitHub correction, since it was based on inaccurate information):

```markdown
- [x] **1. Sign-in modal missing.** ...
- [x] **2. `allauth.headless` missing from `INSTALLED_APPS`** ...
- [x] **3. ~~GitHub login provider missing.~~ Corrected: production has no GitHub provider at all (verified directly against `vocablarry.html` and its settings) — built the real 4 providers (Google/Facebook/Microsoft/Apple) instead.**
- [x] **4. `HEADLESS_FRONTEND_URLS` missing** ...
- [x] **5. `/_allauth/` route missing** ...
```

- [ ] **Step 8: Commit the checklist update**

```bash
git add "VocabLarry Professional Environment/FIXES-NEEDED.md"
git commit -m "docs(vlpe): check off FIXES-NEEDED items 1-5 (auth modal), verified against real accounts"
```
