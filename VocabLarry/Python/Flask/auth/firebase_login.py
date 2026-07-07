from flask import Blueprint, jsonify, request, session

from db import get_db
from oauth_common import firebase_verify_id_token, get_firebase_api_key, resolve_oauth_user

firebase_login_bp = Blueprint('firebase_login', __name__)


@firebase_login_bp.route('/firebase_login', methods=['POST'])
def firebase_login():
    body     = request.get_json(silent=True) or {}
    id_token = body.get('idToken', '')

    if not isinstance(id_token, str) or not id_token:
        return jsonify({'error': 'Missing sign-in token.'}), 400

    api_key = get_firebase_api_key()
    if not api_key:
        return jsonify({'error': 'Social sign-in is not configured yet.'}), 500

    profile = firebase_verify_id_token(id_token, api_key)
    if not profile:
        return jsonify({'error': 'Could not verify sign-in. Please try again.'}), 401

    conn    = get_db()
    user_id = resolve_oauth_user(conn, profile)

    conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,))
    conn.commit()

    session.clear()
    session['user_id'] = user_id
    return jsonify({'ok': True})
