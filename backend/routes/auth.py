"""Authentication routes."""
import time
from threading import Lock

from flask import Blueprint, request, jsonify
from auth import AuthManager
from config import Config
from services import pairing

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


@auth_bp.route('/api/auth/pair-token', methods=['POST'])
def create_pair_token():
    """Mint a single-use token for the Connect page's QR (needs a signed-in caller)."""
    from auth import require_auth

    @require_auth
    def _create():
        if not Config.REQUIRE_AUTH:
            return jsonify({
                'error': 'Pairing is only needed when a deck password is set',
                'success': False,
            }), 409
        return jsonify({'token': pairing.issue(), 'ttl_s': pairing.TTL_S, 'success': True})

    return _create()


@auth_bp.route('/api/auth/pair', methods=['POST'])
def pair():
    """Trade a pairing token for a normal login token. Same throttle as login."""
    ip = request.remote_addr or 'unknown'
    if _throttled(ip):
        return jsonify({
            'error': 'Too many attempts — wait a minute and try again',
            'success': False,
        }), 429

    data = request.get_json(silent=True)
    pair_token = data.get('token') if isinstance(data, dict) else None
    if not isinstance(pair_token, str) or not pair_token:
        return jsonify({'error': 'Token is required', 'success': False}), 400

    if Config.REQUIRE_AUTH and pairing.redeem(pair_token):
        _clear_failures(ip)
        token = AuthManager.generate_token({'authenticated': True})
        return jsonify({'token': token, 'success': True})

    _record_failure(ip)
    return jsonify({'error': 'Invalid or expired pairing code', 'success': False}), 401


@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify if the current token is valid."""
    from auth import require_auth

    @require_auth
    def _verify():
        return jsonify({'valid': True})

    return _verify()
