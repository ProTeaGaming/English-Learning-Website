"""
Flask entry point.

Run:
    python auth/app.py
Or:
    flask --app auth/app.py run --port 8000

Requires: Flask, Werkzeug  (pip install flask)
Copy auth/config.local.example.py -> auth/config.local.py and fill in values.
"""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, send_from_directory

from check_email import check_email_bp
from db import close_db
from delete_account import delete_account_bp
from firebase_login import firebase_login_bp
from forgot_password import forgot_password_bp
from login import login_bp
from logout import logout_bp
from reset_password import reset_password_bp
from session import session_bp
from signup import signup_bp
from sync import sync_bp
from update_profile import update_profile_bp


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), 'config.local.py')
    if not os.path.exists(path):
        return {}
    spec = importlib.util.spec_from_file_location('config_local', path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, 'CONFIG', {})


def create_app() -> Flask:
    app    = Flask(__name__, static_folder='..', static_url_path='')
    config = _load_config()

    app.secret_key = config.get('secret_key') or os.urandom(24)
    app.teardown_appcontext(close_db)

    blueprints = (
        session_bp, login_bp, signup_bp, logout_bp, check_email_bp,
        forgot_password_bp, reset_password_bp, update_profile_bp,
        sync_bp, delete_account_bp, firebase_login_bp,
    )
    for bp in blueprints:
        app.register_blueprint(bp, url_prefix='/auth')

    @app.route('/')
    def index():
        return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), 'vocab-master.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
