"""Authentication module for VDock."""
from .auth_manager import AuthManager, is_trusted_local_request, require_auth

__all__ = ['AuthManager', 'is_trusted_local_request', 'require_auth']
