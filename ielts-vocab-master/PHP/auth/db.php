<?php
function get_db(): PDO {
    static $pdo = null;
    if ($pdo) return $pdo;

    $dbPath = __DIR__ . '/../data/users.sqlite';
    if (!is_dir(dirname($dbPath))) {
        mkdir(dirname($dbPath), 0777, true);
    }

    $pdo = new PDO('sqlite:' . $dbPath);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec('CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        picture TEXT,
        learn_map TEXT NOT NULL DEFAULT \'{}\',
        created_at TEXT NOT NULL DEFAULT (datetime(\'now\')),
        last_login TEXT NOT NULL DEFAULT (datetime(\'now\'))
    )');

    $existingCols = $pdo->query('PRAGMA table_info(users)')->fetchAll(PDO::FETCH_COLUMN, 1);
    if (!in_array('reset_token', $existingCols, true)) {
        $pdo->exec('ALTER TABLE users ADD COLUMN reset_token TEXT');
    }
    if (!in_array('reset_token_expires', $existingCols, true)) {
        $pdo->exec('ALTER TABLE users ADD COLUMN reset_token_expires TEXT');
    }
    if (!in_array('username', $existingCols, true)) {
        $pdo->exec('ALTER TABLE users ADD COLUMN username TEXT');
    }
    $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)');

    $pdo->exec('CREATE TABLE IF NOT EXISTS remember_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        selector TEXT NOT NULL,
        validator_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )');
    $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_remember_selector ON remember_tokens(selector)');

    $pdo->exec('CREATE TABLE IF NOT EXISTS oauth_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        provider_user_id TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime(\'now\'))
    )');
    $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_provider_user ON oauth_accounts(provider, provider_user_id)');

    return $pdo;
}
