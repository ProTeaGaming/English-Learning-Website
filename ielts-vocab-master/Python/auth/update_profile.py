import re
import unicodedata

from flask import Blueprint, jsonify, request, session

from avatar import delete_avatar_file, store_avatar_upload
from db import get_db

update_profile_bp = Blueprint('update_profile', __name__)


def _valid_name(name: str) -> bool:
    return (1 <= len(name) <= 60 and
            all(unicodedata.category(c).startswith('L') or c.isspace() for c in name))


def _valid_username(username: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9]{3,20}', username))


@update_profile_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in.'}), 401

    name     = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()

    if not _valid_name(name):
        return jsonify({'error': 'Full name can only contain letters and spaces.'}), 400
    if not _valid_username(username):
        return jsonify({'error': 'Username must be 3-20 characters, letters and numbers only (no spaces or symbols).'}), 400

    conn = get_db()

    if conn.execute(
        'SELECT id FROM users WHERE username = ? AND id != ?', (username, session['user_id'])
    ).fetchone():
        return jsonify({'error': 'This username is already taken.'}), 409

    current = conn.execute(
        'SELECT picture FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    picture = current['picture'] if current else None

    file = request.files.get('picture')
    if file and file.filename:
        upload = store_avatar_upload(file)
        if not upload['ok']:
            return jsonify({'error': upload['error']}), 400
        delete_avatar_file(picture)
        picture = upload['path']

    conn.execute(
        'UPDATE users SET name = ?, username = ?, picture = ? WHERE id = ?',
        (name, username, picture, session['user_id']),
    )
    conn.commit()
    return jsonify({'ok': True, 'name': name, 'username': username, 'picture': picture})
