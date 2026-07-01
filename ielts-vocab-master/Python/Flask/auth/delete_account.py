import os

from flask import Blueprint, jsonify, make_response, request, session
from werkzeug.security import check_password_hash

from db import get_db
from remember import clear_all_remember_tokens, clear_remember_cookie

delete_account_bp = Blueprint('delete_account', __name__)


@delete_account_bp.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in.'}), 401

    password = request.form.get('password', '')
    conn     = get_db()
    user     = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Incorrect password.'}), 401

    if user['picture']:
        picture_path = os.path.join(os.path.dirname(__file__), '..', user['picture'])
        if os.path.isfile(picture_path):
            os.remove(picture_path)

    conn.execute('DELETE FROM users WHERE id = ?', (user['id'],))
    clear_all_remember_tokens(conn, user['id'])
    conn.commit()

    resp = make_response(jsonify({'ok': True}))
    clear_remember_cookie(conn, resp)
    session.clear()
    return resp
