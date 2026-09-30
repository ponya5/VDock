"""Authentication routes."""
import time
from threading import Lock

from flask import Blueprint, request, jsonify
from auth import AuthManager

auth_bp = Blueprint('auth', __name__)

# Login throttling — the docstring has always promised it; now it's real.
# In-memory sliding window per client IP: 5 failures/minute → 429.
_MAX_ATTEMPTS = 5
_WINDOW_S = 60
_attempts_lock = Lock()
_attempts: dict[str, list[float]] = {}


def _throttled(ip: str) -> bool:
    """True when this IP has burned through its failure allowance."""
    now = time.time()
    with _attempts_lock:
        window = [t for t in _attempts.get(ip, []) if now - t < _WINDOW_S]
        _attempts[ip] = window
        return len(window) >= _MAX_ATTEMPTS


def _record_failure(ip: str) -> None:
    with _attempts_lock:
        _attempts.setdefault(ip, []).append(time.time())


def _clear_failures(ip: str) -> None:
    with _attempts_lock:
        _attempts.pop(ip, None)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate and get a token.

    Rate limited to 5 failed attempts per minute per IP address —
    anything beyond that gets a 429 without even checking the password.
    """
    ip = request.remote_addr or 'unknown'
    if _throttled(ip):
        return jsonify({
            'error': 'Too many attempts — wait a minute and try again',
            'success': False,
        }), 429

    data = request.json
    password = data.get('password', '') if data else ''

    if not password:
        return jsonify({'error': 'Password is required', 'success': False}), 400

    token = AuthManager.authenticate(password)
    if token:
        _clear_failures(ip)
        return jsonify({'token': token, 'success': True})

    _record_failure(ip)
    return jsonify({'error': 'Invalid password', 'success': False}), 401


@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify if the current token is valid."""
    from auth import require_auth

    @require_auth
    def _verify():
        return jsonify({'valid': True})

    return _verify()
