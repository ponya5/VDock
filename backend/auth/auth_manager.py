"""Authentication and authorization management."""
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
from config import Config


class AuthManager:
    """Manages authentication and JWT tokens."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return AuthManager.hash_password(password) == hashed
    
    @staticmethod
    def generate_token(data: Dict[str, Any], expires_in: Optional[int] = None) -> str:
        """Generate a JWT token.
        
        Args:
            data: Data to encode in the token
            expires_in: Token expiration time in seconds
            
        Returns:
            Encoded JWT token
        """
        if expires_in is None:
            expires_in = Config.TOKEN_EXPIRATION
        
        payload = {
            **data,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def authenticate(password: str) -> Optional[str]:
        """Authenticate a user with password.
        
        Args:
            password: Password to verify
            
        Returns:
            JWT token if authentication successful, None otherwise
        """
        if not Config.REQUIRE_AUTH:
            return AuthManager.generate_token({'authenticated': True})
        
        # For simplicity, we're using a single password from config
        # In production, this should use a proper user database
        if password == Config.AUTH_PASSWORD:
            return AuthManager.generate_token({'authenticated': True})
        
        return None


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_AUTH:
            return f(*args, **kwargs)
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        # Verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add payload to request context
        request.auth_data = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

