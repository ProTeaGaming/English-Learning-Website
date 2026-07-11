import importlib.util
import json
import os
import secrets
import sqlite3
import urllib.error
import urllib.parse
import urllib.request


def get_firebase_api_key() -> str | None:
    path = os.path.join(os.path.dirname(__file__), 'config.local.py')
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location('config_local', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    config = getattr(mod, 'CONFIG', {})
    return config.get('firebase', {}).get('api_key')


def generate_unique_username(conn: sqlite3.Connection, seed: str) -> str:
    import re
    base = re.sub(r'[^A-Za-z0-9]', '', seed)
    if not base:
        base = 'user'
    base = base[:16]
    if len(base) < 3:
        base = base.ljust(3, '0')

    username = base
    for _ in range(20):
        row = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if not row:
            return username
        suffix = str(secrets.randbelow(9900) + 100)
        username = base[:20 - len(suffix)] + suffix

    return ('user' + secrets.token_hex(6))[:20]


def firebase_verify_id_token(id_token: str, api_key: str) -> dict | None:
    """Verifies a Firebase ID token via Firebase's REST lookup endpoint and
    normalises the result to a provider profile dict. Returns None if invalid."""
    url = ('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key='
           + urllib.parse.quote(api_key, safe=''))
    payload = json.dumps({'idToken': id_token}).encode()
    req = urllib.request.Request(
        url, data=payload, headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None

    user = (data.get('users') or [None])[0]
    if not user or not user.get('localId'):
        return None

    provider_id = (user.get('providerUserInfo') or [{}])[0].get('providerId', '')
    if 'google' in provider_id:
        provider = 'google'
    elif 'facebook' in provider_id:
        provider = 'facebook'
    elif 'apple' in provider_id:
        provider = 'apple'
    elif 'microsoft' in provider_id:
        provider = 'microsoft'
    elif provider_id:
        provider = provider_id
    else:
        provider = 'unknown'

    return {
        'provider':         provider,
        'provider_user_id': user['localId'],
        'email':            user.get('email'),
        'email_verified':   bool(user.get('emailVerified')),
        'name':             user.get('displayName'),
        'picture':          user.get('photoUrl'),
    }


def resolve_oauth_user(conn: sqlite3.Connection, profile: dict) -> int:
    """Finds or creates a users row for the given OAuth profile and returns the user id."""
    from werkzeug.security import generate_password_hash

    row = conn.execute(
        'SELECT user_id FROM oauth_accounts WHERE provider = ? AND provider_user_id = ?',
        (profile['provider'], profile['provider_user_id']),
    ).fetchone()
    if row:
        return row['user_id']

    if profile['email_verified'] and profile['email']:
        existing = conn.execute(
            'SELECT id FROM users WHERE email = ?', (profile['email'].lower(),)
        ).fetchone()
        if existing:
            user_id = existing['id']
            conn.execute(
                'INSERT INTO oauth_accounts (user_id, provider, provider_user_id) VALUES (?, ?, ?)',
                (user_id, profile['provider'], profile['provider_user_id']),
            )
            conn.commit()
            return user_id

    email_local = profile['email'].split('@')[0] if profile['email'] else None
    name_seed = profile['name'] or email_local or 'user'
    username = generate_unique_username(conn, name_seed)
    name = profile['name'] or email_local or 'New User'
    email = (profile['email'] or
             f"{profile['provider']}_{profile['provider_user_id']}@no-email.invalid")
    unusable_hash = generate_password_hash(secrets.token_hex(32))

    conn.execute(
        'INSERT INTO users (email, password_hash, name, username, picture) VALUES (?, ?, ?, ?, ?)',
        (email.lower(), unusable_hash, name, username, profile['picture']),
    )
    user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    conn.execute(
        'INSERT INTO oauth_accounts (user_id, provider, provider_user_id) VALUES (?, ?, ?)',
        (user_id, profile['provider'], profile['provider_user_id']),
    )
    conn.commit()
    return user_id
