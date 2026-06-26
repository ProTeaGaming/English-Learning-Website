from flask import Blueprint, jsonify, make_response, request, session
from werkzeug.security import check_password_hash

from db import get_db
from remember import create_remember_cookie

login_bp = Blueprint('login', __name__)


@login_bp.route('/login', methods=['POST'])
def login():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    remember = request.form.get('remember', '') not in ('', '0')

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Incorrect email or password.'}), 401

    conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user['id'],))
    conn.commit()

    session.clear()
    session['user_id'] = user['id']

    resp = make_response(jsonify({'ok': True}))
    if remember:
        create_remember_cookie(conn, user['id'], resp)
    return resp
