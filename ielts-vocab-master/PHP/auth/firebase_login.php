<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/oauth_common.php';

$input = json_decode(file_get_contents('php://input'), true) ?? [];
$idToken = is_string($input['idToken'] ?? null) ? $input['idToken'] : '';

if ($idToken === '') {
    http_response_code(400);
    echo json_encode(['error' => 'Missing sign-in token.']);
    exit;
}

$apiKey = get_firebase_api_key();
if (!$apiKey) {
    http_response_code(500);
    echo json_encode(['error' => 'Social sign-in is not configured yet.']);
    exit;
}

$profile = firebase_verify_id_token($idToken, $apiKey);
if (!$profile) {
    http_response_code(401);
    echo json_encode(['error' => 'Could not verify sign-in. Please try again.']);
    exit;
}

$pdo = get_db();
$userId = resolve_oauth_user($pdo, $profile);

$pdo->prepare("UPDATE users SET last_login = datetime('now') WHERE id = ?")->execute([$userId]);

session_regenerate_id(true);
$_SESSION['user_id'] = $userId;

echo json_encode(['ok' => true]);
