import re
import unicodedata

from flask import Blueprint, jsonify, make_response, request, session
from werkzeug.security import generate_password_hash

from avatar import store_avatar_upload
from db import get_db
from remember import create_remember_cookie

signup_bp = Blueprint('signup', __name__)


def _valid_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


def _valid_name(name: str) -> bool:
    return (1 <= len(name) <= 60 and
            all(unicodedata.category(c).startswith('L') or c.isspace() for c in name))


def _valid_username(username: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z0-9]{3,20}', username))


@signup_bp.route('/signup', methods=['POST'])
def signup():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    name     = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    remember = request.form.get('remember', '') not in ('', '0')

    if not _valid_email(email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if not _valid_name(name):
        return jsonify({'error': 'Full name can only contain letters and spaces.'}), 400
    if not _valid_username(username):
        return jsonify({'error': 'Username must be 3-20 characters, letters and numbers only (no spaces or symbols).'}), 400

    conn = get_db()

    if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return jsonify({'error': 'An account with this email already exists.'}), 409
    if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
        return jsonify({'error': 'This username is already taken.'}), 409

    picture = None
    file = request.files.get('picture')
    if file and file.filename:
        upload = store_avatar_upload(file)
        if not upload['ok']:
            return jsonify({'error': upload['error']}), 400
        picture = upload['path']

    password_hash = generate_password_hash(password)
    conn.execute(
        'INSERT INTO users (email, password_hash, name, username, picture) VALUES (?, ?, ?, ?, ?)',
        (email, password_hash, name, username, picture),
    )
    conn.commit()
    user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

    session.clear()
    session['user_id'] = user_id

    resp = make_response(jsonify({'ok': True}))
    if remember:
        create_remember_cookie(conn, user_id, resp)
    return resp
