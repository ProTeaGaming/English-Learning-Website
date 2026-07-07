<?php
function store_avatar_upload(array $file): array {
    $allowed = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/gif' => 'gif', 'image/webp' => 'webp'];
    $info = getimagesize($file['tmp_name']);

    if ($info === false || !isset($allowed[$info['mime']])) {
        return ['ok' => false, 'error' => 'Profile picture must be a JPG, PNG, GIF, or WEBP image.'];
    }
    if ($file['size'] > 2 * 1024 * 1024) {
        return ['ok' => false, 'error' => 'Profile picture must be under 2MB.'];
    }

    $ext = $allowed[$info['mime']];
    $filename = bin2hex(random_bytes(16)) . '.' . $ext;
    $uploadDir = __DIR__ . '/uploads/avatars';
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }
    move_uploaded_file($file['tmp_name'], $uploadDir . '/' . $filename);

    return ['ok' => true, 'path' => 'auth/uploads/avatars/' . $filename];
}

function delete_avatar_file(?string $relativePath): void {
    if (!$relativePath) return;
    $path = __DIR__ . '/../' . $relativePath;
    if (is_file($path)) {
        unlink($path);
    }
}
