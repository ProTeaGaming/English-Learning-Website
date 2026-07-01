<?php
session_start();
header('Content-Type: application/json');
require __DIR__ . '/db.php';
require __DIR__ . '/remember.php';

clear_remember_cookie(get_db());

$_SESSION = [];
session_destroy();
echo json_encode(['ok' => true]);
