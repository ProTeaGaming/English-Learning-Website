<?php
function get_firebase_api_key(): ?string {
    $path = __DIR__ . '/config.local.php';
    if (!file_exists($path)) return null;
    $config = require $path;
    return $config['firebase']['api_key'] ?? null;
}

function generate_unique_username(PDO $pdo, string $seed): string {
    $base = preg_replace('/[^A-Za-z0-9]/', '', $seed);
    if ($base === '') $base = 'user';
    $base = substr($base, 0, 16);
    if (strlen($base) < 3) $base = str_pad($base, 3, '0');

    $stmt = $pdo->prepare('SELECT id FROM users WHERE username = ?');
    $username = $base;
    for ($attempt = 0; $attempt < 20; $attempt++) {
        $stmt->execute([$username]);
        if (!$stmt->fetch()) return $username;
        $suffix = (string) random_int(100, 9999);
        $username = substr($base, 0, 20 - strlen($suffix)) . $suffix;
    }
    return substr('user' . bin2hex(random_bytes(6)), 0, 20);
}

// Verifies a Firebase ID token via Firebase's REST lookup endpoint (no JWT
// signature verification needed locally) and normalizes the result to
// {provider, provider_user_id, email, email_verified, name, picture}.
// Returns null if the token is missing, expired, or otherwise invalid.
function firebase_verify_id_token(string $idToken, string $apiKey): ?array {
    $ch = curl_init('https://identitytoolkit.googleapis.com/v1/accounts:lookup?key=' . urlencode($apiKey));
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => json_encode(['idToken' => $idToken]),
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
    ]);
    $body = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($body === false || $httpCode !== 200) return null;

    $data = json_decode($body, true);
    $user = $data['users'][0] ?? null;
    if (!$user || empty($user['localId'])) return null;

    $providerId = $user['providerUserInfo'][0]['providerId'] ?? '';
    $provider = match (true) {
        str_contains($providerId, 'google')    => 'google',
        str_contains($providerId, 'facebook')  => 'facebook',
        str_contains($providerId, 'apple')     => 'apple',
        str_contains($providerId, 'microsoft') => 'microsoft',
        default => $providerId !== '' ? $providerId : 'unknown',
    };

    return [
        'provider'         => $provider,
        'provider_user_id' => $user['localId'],
        'email'            => $user['email'] ?? null,
        'email_verified'   => !empty($user['emailVerified']),
        'name'             => $user['displayName'] ?? null,
        'picture'          => $user['photoUrl'] ?? null,
    ];
}

// Resolves a normalized Firebase profile to a users.id, creating an account
// (and linking it via oauth_accounts) if no match is found. Returns the
// resolved user id.
function resolve_oauth_user(PDO $pdo, array $profile): int {
    $stmt = $pdo->prepare('SELECT user_id FROM oauth_accounts WHERE provider = ? AND provider_user_id = ?');
    $stmt->execute([$profile['provider'], $profile['provider_user_id']]);
    $link = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($link) return (int) $link['user_id'];

    if ($profile['email_verified'] && $profile['email']) {
        $stmt = $pdo->prepare('SELECT id FROM users WHERE email = ?');
        $stmt->execute([strtolower($profile['email'])]);
        $existing = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($existing) {
            $userId = (int) $existing['id'];
            $pdo->prepare('INSERT INTO oauth_accounts (user_id, provider, provider_user_id) VALUES (?, ?, ?)')
                ->execute([$userId, $profile['provider'], $profile['provider_user_id']]);
            return $userId;
        }
    }

    $nameSeed = $profile['name'] ?: ($profile['email'] ? strstr($profile['email'] . '@', '@', true) : 'user');
    $username = generate_unique_username($pdo, $nameSeed);
    $name = $profile['name'] ?: ($profile['email'] ? strstr($profile['email'] . '@', '@', true) : 'New User');
    $email = $profile['email'] ?: ($profile['provider'] . '_' . $profile['provider_user_id'] . '@no-email.invalid');
    $unusableHash = password_hash(bin2hex(random_bytes(32)), PASSWORD_DEFAULT);

    $pdo->prepare('INSERT INTO users (email, password_hash, name, username, picture) VALUES (?, ?, ?, ?, ?)')
        ->execute([strtolower($email), $unusableHash, $name, $username, $profile['picture']]);
    $userId = (int) $pdo->lastInsertId();

    $pdo->prepare('INSERT INTO oauth_accounts (user_id, provider, provider_user_id) VALUES (?, ?, ?)')
        ->execute([$userId, $profile['provider'], $profile['provider_user_id']]);

    return $userId;
}
