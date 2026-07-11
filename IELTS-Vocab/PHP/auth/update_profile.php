<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/avatar.php';

if (!isset($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Not logged in.']);
    exit;
}

$name     = isset($_POST['name']) ? trim($_POST['name']) : '';
$username = isset($_POST['username']) ? trim($_POST['username']) : '';

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
$stmt = $pdo->prepare('SELECT id FROM users WHERE username = ? AND id != ?');
$stmt->execute([$username, $_SESSION['user_id']]);
if ($stmt->fetch()) {
    http_response_code(409);
    echo json_encode(['error' => 'This username is already taken.']);
    exit;
}

$stmt = $pdo->prepare('SELECT picture FROM users WHERE id = ?');
$stmt->execute([$_SESSION['user_id']]);
$current = $stmt->fetch(PDO::FETCH_ASSOC);
$picture = $current['picture'];

if (isset($_FILES['picture']) && $_FILES['picture']['error'] === UPLOAD_ERR_OK) {
    $upload = store_avatar_upload($_FILES['picture']);
    if (!$upload['ok']) {
        http_response_code(400);
        echo json_encode(['error' => $upload['error']]);
        exit;
    }
    delete_avatar_file($picture);
    $picture = $upload['path'];
}

$pdo->prepare('UPDATE users SET name = ?, username = ?, picture = ? WHERE id = ?')
    ->execute([$name, $username, $picture, $_SESSION['user_id']]);

echo json_encode(['ok' => true, 'name' => $name, 'username' => $username, 'picture' => $picture]);
