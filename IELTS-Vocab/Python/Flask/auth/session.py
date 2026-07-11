import json

from flask import Blueprint, jsonify, make_response, session

from db import get_db
from remember import consume_remember_cookie

session_bp = Blueprint('session_check', __name__)


@session_bp.route('/session')
def check_session():
    conn = get_db()

    if 'user_id' not in session:
        placeholder = make_response()
        user_id = consume_remember_cookie(conn, placeholder)
        if not user_id:
            return jsonify({'loggedIn': False})
        session.clear()
        session['user_id'] = user_id
        extra_cookies = placeholder.headers.getlist('Set-Cookie')
    else:
        user_id = session['user_id']
        extra_cookies = []

    row = conn.execute(
        'SELECT id, email, name, username, picture FROM users WHERE id = ?', (user_id,)
    ).fetchone()

    if not row:
        session.pop('user_id', None)
        return jsonify({'loggedIn': False})

    resp = make_response(jsonify({
        'loggedIn':  True,
        'id':        row['id'],
        'email':     row['email'],
        'name':      row['name'],
        'username':  row['username'],
        'picture':   row['picture'],
    }))
    for cookie in extra_cookies:
        resp.headers.add('Set-Cookie', cookie)
    return resp
