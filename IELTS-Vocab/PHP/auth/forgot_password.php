<?php
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/mailer.php';

$body = json_decode(file_get_contents('php://input'), true);
$email = isset($body['email']) ? trim(strtolower($body['email'])) : '';

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Please enter a valid email address.']);
    exit;
}

$pdo = get_db();
$stmt = $pdo->prepare('SELECT id, name FROM users WHERE email = ?');
$stmt->execute([$email]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if ($user) {
    $token = bin2hex(random_bytes(32));
    $tokenHash = hash('sha256', $token);
    $expires = date('Y-m-d H:i:s', time() + 1800);

    $pdo->prepare('UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?')
        ->execute([$tokenHash, $expires, $user['id']]);

    $config = get_mail_config();
    $baseUrl = $config['app_base_url'] ?? 'http://localhost:8000';
    $link = rtrim($baseUrl, '/') . '/auth/reset_password.html?token=' . $token;
    $name = $user['name'] ?: 'there';

    $bodyText = "Hi {$name},\n\n"
        . "Someone requested a password reset for your IELTS Vocab Master account.\n\n"
        . "Click the link below to set a new password. This link expires in 30 minutes.\n\n"
        . "{$link}\n\n"
        . "If you didn't request this, you can safely ignore this email.\n";

    smtp_send_mail($email, 'Reset your IELTS Vocab Master password', $bodyText);
}

// Always respond the same way whether or not the email exists, to avoid leaking account existence.
echo json_encode(['ok' => true]);
