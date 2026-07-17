import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ALLOWED_HOSTS += [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

# Django rejects HTTPS POSTs unless the origin is trusted, so production
# needs the full scheme+host here (e.g. https://vocablarry.pythonanywhere.com)
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

if not DEBUG:
    # PythonAnywhere terminates TLS at its load balancer and forwards the
    # original scheme in this header; without it Django thinks every request
    # is plain http and the secure cookies below would never be sent.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

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
    'accounts',
    'vocab',
    'grammar',
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
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.SocialAccountAdapter'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
# 'mandatory' blocks sign-in until the email is verified — set the env var
# to 'optional' on hosts where no SMTP account is configured yet, otherwise
# new users can never finish signing up.
ACCOUNT_EMAIL_VERIFICATION = os.environ.get('EMAIL_VERIFICATION', 'mandatory')
ACCOUNT_SESSION_REMEMBER = None  # show "Remember me" checkbox

# Social login — each provider is a no-op (button shows, click fails with a
# provider-side error) until real credentials are filled in via .env. Get
# credentials from each platform's own developer console — see .env.example
# for a link + what each value corresponds to. Apple's "secret" is its Key
# ID (not a real secret) and "certificate_key" is the .p8 private key's
# contents — see allauth's apple provider client.py for why.
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        },
    },
    'facebook': {
        'APP': {
            'client_id': os.environ.get('FACEBOOK_CLIENT_ID', ''),
            'secret': os.environ.get('FACEBOOK_CLIENT_SECRET', ''),
        },
    },
    'microsoft': {
        'APP': {
            'client_id': os.environ.get('MICROSOFT_CLIENT_ID', ''),
            'secret': os.environ.get('MICROSOFT_CLIENT_SECRET', ''),
        },
        # 'common' accepts both personal Microsoft accounts and any Azure AD
        # tenant — the right default for a public sign-in button.
        'TENANT': os.environ.get('MICROSOFT_TENANT', 'common'),
    },
    'apple': {
        'APP': {
            'client_id': os.environ.get('APPLE_CLIENT_ID', ''),      # Services ID
            'secret': os.environ.get('APPLE_KEY_ID', ''),            # Key ID, not a real secret
            'key': os.environ.get('APPLE_TEAM_ID', ''),               # Team ID
            'settings': {
                # Contents of the downloaded .p8 private key file, verbatim.
                'certificate_key': os.environ.get('APPLE_PRIVATE_KEY', ''),
            },
        },
    },
}

# Email — real SMTP once credentials exist, otherwise print to console so
# local signup flows stay testable without a mail account.
if os.environ.get('SMTP_USER'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASS', '')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = (
    f"{os.environ.get('FROM_NAME', 'VocabLarry')} "
    f"<{os.environ.get('FROM_EMAIL', '')}>"
)

# Media (user uploads)
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Static
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
# collectstatic target — the production web server serves this directory
# directly (PythonAnywhere: map /static/ to it in the Web tab).
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF: allow JS to read cookie so fetch() can send X-CSRFToken header
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
