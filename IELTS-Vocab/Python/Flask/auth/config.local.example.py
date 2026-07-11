# Copy this file to config.local.py (gitignored) and fill in real values.
# smtp_pass must be a Gmail "App Password" (16 chars, generated at
# https://myaccount.google.com/apppasswords) — your normal Gmail password will NOT work.
CONFIG = {
    'smtp_host':    'smtp.gmail.com',
    'smtp_port':    587,
    'smtp_user':    'youraccount@gmail.com',
    'smtp_pass':    'xxxx xxxx xxxx xxxx',
    'from_email':   'youraccount@gmail.com',
    'from_name':    'IELTS Vocab Master',
    'app_base_url': 'http://localhost:8000',
    # Required by Flask for signing session cookies — set to a long random string.
    'secret_key':   'change-me-to-a-long-random-secret',
    # Web API key from Firebase console > Project settings > General.
    # Same value as `firebaseConfig.apiKey` in vocab-master.html — it's
    # public/client-safe, not a secret. See auth/FIREBASE_SETUP.md.
    'firebase': {
        'api_key': 'YOUR_FIREBASE_WEB_API_KEY',
    },
}
