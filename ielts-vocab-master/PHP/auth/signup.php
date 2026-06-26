<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/avatar.php';
require __DIR__ . '/remember.php';

$email    = isset($_POST['email']) ? trim(strtolower($_POST['email'])) : '';
$password = $_POST['password'] ?? '';
$name     = isset($_POST['name']) ? trim($_POST['name']) : '';
$username = isset($_POST['username']) ? trim($_POST['username']) : '';
$remember = !empty($_POST['remember']) && $_POST['remember'] !== '0';

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Please enter a valid email address.']);
    exit;
}
if (strlen($password) < 8) {
    http_response_code(400);
    echo json_encode(['error' => 'Password must be at least 8 characters.']);
    exit;
}
if (!preg_match('/^[\p{L}\s]{1,60}$/u', $name)) {
    http_response_code(400);
    echo json_encode(['error' => 'Full name can only contain letters and spaces.']);
    exit;
}
if (!preg_match('/^[A-Za-z0-9]{3,20}$/', $username)) {
    http_response_code(400);
    echo json_encode(['error' => 'Username must be 3-20 characters, letters and numbers only (no spaces or symbols).']);
    exit;
}

$pdo = get_db();
$stmt = $pdo->prepare('SELECT id FROM users WHERE email = ?');
$stmt->execute([$email]);
if ($stmt->fetch()) {
    http_response_code(409);
    echo json_encode(['error' => 'An account with this email already exists.']);
    exit;
}

$stmt = $pdo->prepare('SELECT id FROM users WHERE username = ?');
$stmt->execute([$username]);
if ($stmt->fetch()) {
    http_response_code(409);
    echo json_encode(['error' => 'This username is already taken.']);
    exit;
}

$picture = null;
if (isset($_FILES['picture']) && $_FILES['picture']['error'] === UPLOAD_ERR_OK) {
    $upload = store_avatar_upload($_FILES['picture']);
    if (!$upload['ok']) {
        http_response_code(400);
        echo json_encode(['error' => $upload['error']]);
        exit;
    }
    $picture = $upload['path'];
}

$hash = password_hash($password, PASSWORD_DEFAULT);
$pdo->prepare('INSERT INTO users (email, password_hash, name, username, picture) VALUES (?, ?, ?, ?, ?)')
    ->execute([$email, $hash, $name, $username, $picture]);

session_regenerate_id(true);
$userId = (int) $pdo->lastInsertId();
$_SESSION['user_id'] = $userId;

if ($remember) {
    create_remember_cookie($pdo, $userId);
}

echo json_encode(['ok' => true]);
