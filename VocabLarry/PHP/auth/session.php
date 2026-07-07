<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/remember.php';

$pdo = get_db();

if (!isset($_SESSION['user_id'])) {
    $userId = consume_remember_cookie($pdo);
    if (!$userId) {
        echo json_encode(['loggedIn' => false]);
        exit;
    }
    session_regenerate_id(true);
    $_SESSION['user_id'] = $userId;
}

$stmt = $pdo->prepare('SELECT id, email, name, username, picture FROM users WHERE id = ?');
$stmt->execute([$_SESSION['user_id']]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$user) {
    unset($_SESSION['user_id']);
    echo json_encode(['loggedIn' => false]);
    exit;
}

echo json_encode([
    'loggedIn' => true,
    'id'       => $user['id'],
    'email'    => $user['email'],
    'name'     => $user['name'],
    'username' => $user['username'],
    'picture'  => $user['picture'],
]);
