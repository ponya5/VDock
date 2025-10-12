"""Authentication routes."""
from flask import Blueprint, request, jsonify
from auth import AuthManager

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate and get a token."""
    data = request.json
    password = data.get('password', '') if data else ''
    
    token = AuthManager.authenticate(password)
    if token:
        return jsonify({'token': token, 'success': True})
    
    return jsonify({'error': 'Invalid password', 'success': False}), 401


@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Verify if the current token is valid."""
    from auth import require_auth
    
    @require_auth
    def _verify():
        return jsonify({'valid': True})
    
    return _verify()
