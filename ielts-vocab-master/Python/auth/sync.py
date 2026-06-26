import json

from flask import Blueprint, jsonify, request, session

from db import get_db

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/sync', methods=['GET', 'POST'])
def sync():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db()

    if request.method == 'GET':
        row = conn.execute(
            'SELECT learn_map FROM users WHERE id = ?', (session['user_id'],)
        ).fetchone()
        learn_map = json.loads(row['learn_map']) if row and row['learn_map'] else {}
        return jsonify({'learnMap': learn_map or {}})

    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get('learnMap'), dict):
        return jsonify({'error': 'Invalid payload'}), 400

    clean = {
        word: status
        for word, status in body['learnMap'].items()
        if isinstance(word, str) and status in ('little', 'learned')
    }

    conn.execute(
        'UPDATE users SET learn_map = ? WHERE id = ?',
        (json.dumps(clean), session['user_id']),
    )
    conn.commit()
    return jsonify({'ok': True})
