<?php
header('Content-Type: application/json');
require __DIR__ . '/db.php';

$body = json_decode(file_get_contents('php://input'), true);
$email = isset($body['email']) ? trim(strtolower($body['email'])) : '';

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Please enter a valid email address.']);
    exit;
}

$pdo = get_db();
$stmt = $pdo->prepare('SELECT id FROM users WHERE email = ?');
$stmt->execute([$email]);
echo json_encode(['exists' => (bool) $stmt->fetch()]);
