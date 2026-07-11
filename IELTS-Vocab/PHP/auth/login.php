<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/remember.php';

$email    = isset($_POST['email']) ? trim(strtolower($_POST['email'])) : '';
$password = $_POST['password'] ?? '';
$remember = !empty($_POST['remember']) && $_POST['remember'] !== '0';

$pdo = get_db();
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = ?');
$stmt->execute([$email]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$user || !password_verify($password, $user['password_hash'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Incorrect email or password.']);
    exit;
}

$pdo->prepare("UPDATE users SET last_login = datetime('now') WHERE id = ?")->execute([$user['id']]);

session_regenerate_id(true);
$_SESSION['user_id'] = $user['id'];

if ($remember) {
    create_remember_cookie($pdo, $user['id']);
}

echo json_encode(['ok' => true]);
