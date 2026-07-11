from flask import Blueprint, jsonify, make_response, session

from db import get_db
from remember import clear_remember_cookie

logout_bp = Blueprint('logout', __name__)


@logout_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    conn = get_db()
    resp = make_response(jsonify({'ok': True}))
    clear_remember_cookie(conn, resp)
    session.clear()
    return resp
