<?php
const REMEMBER_COOKIE_NAME = 'remember_token';
const REMEMBER_TTL_DAYS = 30;

function create_remember_cookie(PDO $pdo, int $userId): void {
    $selector = bin2hex(random_bytes(8));
    $validator = bin2hex(random_bytes(32));
    $validatorHash = hash('sha256', $validator);
    $expiresAt = time() + REMEMBER_TTL_DAYS * 86400;

    $pdo->prepare('INSERT INTO remember_tokens (user_id, selector, validator_hash, expires_at) VALUES (?, ?, ?, ?)')
        ->execute([$userId, $selector, $validatorHash, date('Y-m-d H:i:s', $expiresAt)]);

    setcookie(REMEMBER_COOKIE_NAME, $selector . ':' . $validator, [
        'expires'  => $expiresAt,
        'path'     => '/',
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

function consume_remember_cookie(PDO $pdo): ?int {
    if (empty($_COOKIE[REMEMBER_COOKIE_NAME])) {
        return null;
    }
    $parts = explode(':', $_COOKIE[REMEMBER_COOKIE_NAME], 2);
    if (count($parts) !== 2) {
        return null;
    }
    [$selector, $validator] = $parts;

    $stmt = $pdo->prepare('SELECT * FROM remember_tokens WHERE selector = ?');
    $stmt->execute([$selector]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$row) {
        return null;
    }

    $pdo->prepare('DELETE FROM remember_tokens WHERE id = ?')->execute([$row['id']]);

    if (strtotime($row['expires_at']) < time()) {
        return null;
    }
    if (!hash_equals($row['validator_hash'], hash('sha256', $validator))) {
        return null;
    }

    $userId = (int) $row['user_id'];
    create_remember_cookie($pdo, $userId);

    return $userId;
}

function clear_remember_cookie(PDO $pdo): void {
    if (!empty($_COOKIE[REMEMBER_COOKIE_NAME])) {
        $parts = explode(':', $_COOKIE[REMEMBER_COOKIE_NAME], 2);
        if (count($parts) === 2) {
            $pdo->prepare('DELETE FROM remember_tokens WHERE selector = ?')->execute([$parts[0]]);
        }
    }
    setcookie(REMEMBER_COOKIE_NAME, '', [
        'expires'  => time() - 3600,
        'path'     => '/',
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

function clear_all_remember_tokens(PDO $pdo, int $userId): void {
    $pdo->prepare('DELETE FROM remember_tokens WHERE user_id = ?')->execute([$userId]);
}
