import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import request

REMEMBER_COOKIE_NAME = 'remember_token'
REMEMBER_TTL_DAYS = 30


def create_remember_cookie(conn: sqlite3.Connection, user_id: int, response) -> None:
    selector = secrets.token_hex(8)
    validator = secrets.token_hex(32)
    validator_hash = hashlib.sha256(validator.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REMEMBER_TTL_DAYS)

    conn.execute(
        'INSERT INTO remember_tokens (user_id, selector, validator_hash, expires_at) VALUES (?, ?, ?, ?)',
        (user_id, selector, validator_hash, expires_at.strftime('%Y-%m-%d %H:%M:%S')),
    )
    conn.commit()

    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        f'{selector}:{validator}',
        max_age=REMEMBER_TTL_DAYS * 86400,
        path='/',
        httponly=True,
        samesite='Lax',
    )


def consume_remember_cookie(conn: sqlite3.Connection, response) -> int | None:
    cookie = request.cookies.get(REMEMBER_COOKIE_NAME)
    if not cookie:
        return None

    parts = cookie.split(':', 1)
    if len(parts) != 2:
        return None

    selector, validator = parts

    row = conn.execute(
        'SELECT * FROM remember_tokens WHERE selector = ?', (selector,)
    ).fetchone()
    if not row:
        return None

    conn.execute('DELETE FROM remember_tokens WHERE id = ?', (row['id'],))
    conn.commit()

    stored_expires = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    if stored_expires < datetime.now(timezone.utc):
        return None

    expected_hash = hashlib.sha256(validator.encode()).hexdigest()
    if not hmac.compare_digest(row['validator_hash'], expected_hash):
        return None

    user_id = row['user_id']
    create_remember_cookie(conn, user_id, response)
    return user_id


def clear_remember_cookie(conn: sqlite3.Connection, response) -> None:
    cookie = request.cookies.get(REMEMBER_COOKIE_NAME)
    if cookie:
        parts = cookie.split(':', 1)
        if len(parts) == 2:
            conn.execute('DELETE FROM remember_tokens WHERE selector = ?', (parts[0],))
            conn.commit()

    response.set_cookie(
        REMEMBER_COOKIE_NAME,
        '',
        max_age=0,
        expires=0,
        path='/',
        httponly=True,
        samesite='Lax',
    )


def clear_all_remember_tokens(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute('DELETE FROM remember_tokens WHERE user_id = ?', (user_id,))
    conn.commit()
