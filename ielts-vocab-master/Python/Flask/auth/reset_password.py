import hashlib

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from db import get_db

reset_password_bp = Blueprint('reset_password', __name__)


@reset_password_bp.route('/reset_password', methods=['POST'])
def reset_password():
    body     = request.get_json(silent=True) or {}
    token    = body.get('token', '').strip()
    password = body.get('password', '')

    if not token:
        return jsonify({'error': 'Missing reset token.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE reset_token = ? AND reset_token_expires > datetime('now')",
        (token_hash,),
    ).fetchone()

    if not user:
        return jsonify({'error': 'This reset link is invalid or has expired.'}), 400

    conn.execute(
        'UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?',
        (generate_password_hash(password), user['id']),
    )
    conn.commit()
    return jsonify({'ok': True})
