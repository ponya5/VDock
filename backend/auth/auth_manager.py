"""Authentication and authorization management."""
import hashlib
import hmac
import ipaddress
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
from config import Config

#: Host header names that can only mean "this computer" (DL-008).
_LOOPBACK_HOST_NAMES = ('localhost', '127.0.0.1', '::1')


def _host_name(host_header: str) -> str:
    """'localhost:5001' -> 'localhost', '[::1]:5001' -> '::1'."""
    host = (host_header or '').strip().lower()
    if host.startswith('['):
        return host[1:host.find(']')] if ']' in host else host[1:]
    return host.rsplit(':', 1)[0] if host.count(':') == 1 else host


def is_trusted_local_request(req=None) -> bool:
    """True for a request made on the computer VDock runs on (DL-008).

    The deck password keeps *other devices on the Wi-Fi* out; VDock's own
    window and anything else on this PC can already drive it (agent hooks are
    localhost-only by design), so locking them out only adds friction.

    All three must hold, so neither a web page nor a proxy can borrow it:
    the TCP peer is loopback; the Host header names a loopback host (a DNS
    rebinding page arrives as ``Host: evil.example`` even when it resolves to
    127.0.0.1); and nothing forwarded it (the Vite dev proxy rewrites Host to
    127.0.0.1 for a phone's request, but adds X-Forwarded-For).
    """
    req = req if req is not None else request
    try:
        if not ipaddress.ip_address(req.remote_addr or '').is_loopback:
            return False
    except ValueError:
        return False
    if _host_name(req.headers.get('Host', '')) not in _LOOPBACK_HOST_NAMES:
        return False
    return not (req.headers.get('X-Forwarded-For') or req.headers.get('Forwarded'))


def _password_fingerprint() -> Optional[str]:
    """Short keyed digest of the deck password; tokens carry it so a password
    change signs every device out. None when no password is set."""
    if not Config.AUTH_PASSWORD:
        return None
    digest = hmac.new(str(Config.SECRET_KEY).encode('utf-8'),
                      Config.AUTH_PASSWORD.encode('utf-8'), hashlib.sha256)
    return digest.hexdigest()[:16]


class AuthManager:
    """Manages authentication and JWT tokens."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt with salt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed: Hashed password to check against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
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
            'exp': datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            'iat': datetime.now(timezone.utc)
        }
        fingerprint = _password_fingerprint()
        if fingerprint:
            payload['pw'] = fingerprint
        
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
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        # Issued under another password -> that device was signed out by the
        # change. Tokens from older builds carry no 'pw' and simply expire.
        if 'pw' in payload and payload['pw'] != _password_fingerprint():
            return None
        # A revoked (or unknown) device id is signed out individually
        # (DL-154). Tokens from before device ids carry no 'did'.
        did = payload.get('did')
        if did:
            from services import devices
            if not devices.is_active(did):
                return None
        return payload
    
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
        
        # Constant-time compare — a plain == leaks match-prefix timing.
        if hmac.compare_digest(
            password.encode('utf-8'), Config.AUTH_PASSWORD.encode('utf-8')
        ):
            return AuthManager.generate_token({'authenticated': True})
        
        return None


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_AUTH or is_trusted_local_request():
            return f(*args, **kwargs)
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        # Extract token — require the exact "Bearer <token>" shape so junk
        # like "token <jwt>" or "Bearer  <jwt>" is never silently accepted.
        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0] != 'Bearer' or not parts[1]:
            return jsonify({'error': 'Invalid authorization header'}), 401
        token = parts[1]
        
        # Verify token
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add payload to request context
        request.auth_data = payload
        if payload.get('did'):
            from services import devices
            devices.touch(payload['did'], request.remote_addr or '')

        return f(*args, **kwargs)
    
    return decorated_function

