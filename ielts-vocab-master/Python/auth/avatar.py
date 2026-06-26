import os
import secrets


_MAGIC = {
    b'\xff\xd8':                         'jpg',
    b'\x89PNG\r\n\x1a\n':               'png',
    b'GIF87a':                           'gif',
    b'GIF89a':                           'gif',
}


def _detect_image_type(data: bytes) -> str | None:
    for magic, ext in _MAGIC.items():
        if data[:len(magic)] == magic:
            return ext
    if len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    return None


def store_avatar_upload(file_storage) -> dict:
    data = file_storage.read()
    file_storage.seek(0)

    ext = _detect_image_type(data)
    if ext is None:
        return {'ok': False, 'error': 'Profile picture must be a JPG, PNG, GIF, or WEBP image.'}

    if len(data) > 2 * 1024 * 1024:
        return {'ok': False, 'error': 'Profile picture must be under 2MB.'}

    filename = secrets.token_hex(16) + '.' + ext
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)

    file_storage.seek(0)
    file_storage.save(os.path.join(upload_dir, filename))

    return {'ok': True, 'path': f'auth/uploads/avatars/{filename}'}


def delete_avatar_file(relative_path: str | None) -> None:
    if not relative_path:
        return
    path = os.path.join(os.path.dirname(__file__), '..', relative_path)
    if os.path.isfile(path):
        os.remove(path)
