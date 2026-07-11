<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';

if (!isset($_SESSION['user_id'])) {
    http_response_code(401);
    echo json_encode(['error' => 'Not logged in']);
    exit;
}

$pdo = get_db();
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $stmt = $pdo->prepare('SELECT learn_map FROM users WHERE id = ?');
    $stmt->execute([$_SESSION['user_id']]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    $learnMap = $row ? json_decode($row['learn_map'], true) : [];
    echo json_encode(['learnMap' => $learnMap ?: []]);
    exit;
}

if ($method === 'POST') {
    $body = json_decode(file_get_contents('php://input'), true);
    if (!is_array($body) || !isset($body['learnMap']) || !is_array($body['learnMap'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid payload']);
        exit;
    }

    $clean = [];
    foreach ($body['learnMap'] as $word => $status) {
        if (is_string($word) && in_array($status, ['little', 'learned'], true)) {
            $clean[$word] = $status;
        }
    }

    $pdo->prepare('UPDATE users SET learn_map = ? WHERE id = ?')
        ->execute([json_encode($clean), $_SESSION['user_id']]);
    echo json_encode(['ok' => true]);
    exit;
}

http_response_code(405);
echo json_encode(['error' => 'Method not allowed']);
