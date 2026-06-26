import re

from flask import Blueprint, jsonify, request

from db import get_db

check_email_bp = Blueprint('check_email', __name__)


@check_email_bp.route('/check_email', methods=['POST'])
def check_email():
    body  = request.get_json(silent=True) or {}
    email = body.get('email', '').strip().lower()

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'error': 'Please enter a valid email address.'}), 400

    conn = get_db()
    row  = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    return jsonify({'exists': row is not None})
