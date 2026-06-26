import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from db import get_db
from mailer import get_mail_config, smtp_send_mail

forgot_password_bp = Blueprint('forgot_password', __name__)


@forgot_password_bp.route('/forgot_password', methods=['POST'])
def forgot_password():
    body  = request.get_json(silent=True) or {}
    email = body.get('email', '').strip().lower()

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    conn = get_db()
    user = conn.execute('SELECT id, name FROM users WHERE email = ?', (email,)).fetchone()

    if user:
        token      = secrets.token_hex(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires    = (datetime.now(timezone.utc) + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')

        conn.execute(
            'UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?',
            (token_hash, expires, user['id']),
        )
        conn.commit()

        config   = get_mail_config() or {}
        base_url = config.get('app_base_url', 'http://localhost:8000')
        link     = base_url.rstrip('/') + '/auth/reset_password.html?token=' + token
        name     = user['name'] or 'there'

        body_text = (
            f'Hi {name},\n\n'
            'Someone requested a password reset for your IELTS Vocab Master account.\n\n'
            'Click the link below to set a new password. This link expires in 30 minutes.\n\n'
            f'{link}\n\n'
            "If you didn't request this, you can safely ignore this email.\n"
        )
        smtp_send_mail(email, 'Reset your IELTS Vocab Master password', body_text)

    # Always respond the same way whether or not the email exists, to avoid leaking account existence.
    return jsonify({'ok': True})
