<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/remember.php';

if (!isset($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Not logged in.']);
    exit;
}

$password = $_POST['password'] ?? '';

$pdo = get_db();
$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');
$stmt->execute([$_SESSION['user_id']]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$user || !password_verify($password, $user['password_hash'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Incorrect password.']);
    exit;
}

if ($user['picture']) {
    $picturePath = __DIR__ . '/../' . $user['picture'];
    if (is_file($picturePath)) {
        unlink($picturePath);
    }
}

$pdo->prepare('DELETE FROM users WHERE id = ?')->execute([$user['id']]);
clear_all_remember_tokens($pdo, $user['id']);
clear_remember_cookie($pdo);

$_SESSION = [];
session_destroy();

echo json_encode(['ok' => true]);
