<?php
header('Content-Type: application/json');
require __DIR__ . '/db.php';

$body = json_decode(file_get_contents('php://input'), true);
$token = isset($body['token']) ? trim($body['token']) : '';
$password = $body['password'] ?? '';

if ($token === '') {
    http_response_code(400);
    echo json_encode(['error' => 'Missing reset token.']);
    exit;
}
if (strlen($password) < 8) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must be at least 8 characters.']);
    exit;
}

$pdo = get_db();
$tokenHash = hash('sha256', $token);
$stmt = $pdo->prepare("SELECT id FROM users WHERE reset_token = ? AND reset_token_expires > datetime('now')");
$stmt->execute([$tokenHash]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$user) {
    http_response_code(400);
    echo json_encode(['error' => 'This reset link is invalid or has expired.']);
    exit;
}

$hash = password_hash($password, PASSWORD_DEFAULT);
$pdo->prepare('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?')
    ->execute([$hash, $user['id']]);

echo json_encode(['ok' => true]);
