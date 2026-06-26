import os
import sqlite3
from flask import g


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.sqlite')
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        _init_schema(conn)
        g.db = conn
    return g.db


def close_db(e=None):
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()


def _init_schema(conn: sqlite3.Connection):
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        picture TEXT,
        learn_map TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_login TEXT NOT NULL DEFAULT (datetime('now'))
    )""")

    existing_cols = {row[1] for row in conn.execute('PRAGMA table_info(users)')}
    if 'reset_token' not in existing_cols:
        conn.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
    if 'reset_token_expires' not in existing_cols:
        conn.execute('ALTER TABLE users ADD COLUMN reset_token_expires TEXT')
    if 'username' not in existing_cols:
        conn.execute('ALTER TABLE users ADD COLUMN username TEXT')
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)')

    conn.execute("""CREATE TABLE IF NOT EXISTS remember_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        selector TEXT NOT NULL,
        validator_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )""")
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_remember_selector ON remember_tokens(selector)')

    conn.execute("""CREATE TABLE IF NOT EXISTS oauth_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        provider_user_id TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_provider_user ON oauth_accounts(provider, provider_user_id)')

    conn.commit()
