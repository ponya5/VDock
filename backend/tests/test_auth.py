"""Tests for authentication."""
import pytest
from auth import AuthManager


def test_hash_password():
    """Test password hashing."""
    password = 'test123'
    hashed = AuthManager.hash_password(password)
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password():
    """Test password verification."""
    password = 'test123'
    hashed = AuthManager.hash_password(password)
    assert AuthManager.verify_password(password, hashed) is True
    assert AuthManager.verify_password('wrong', hashed) is False


def test_generate_token():
    """Test token generation."""
    data = {'user': 'test'}
    token = AuthManager.generate_token(data)
    assert token is not None
    assert len(token) > 0


def test_verify_token():
    """Test token verification."""
    data = {'user': 'test'}
    token = AuthManager.generate_token(data, expires_in=3600)
    
    payload = AuthManager.verify_token(token)
    assert payload is not None
    assert payload['user'] == 'test'


def test_verify_invalid_token():
    """Test verification of invalid token."""
    payload = AuthManager.verify_token('invalid_token')
    assert payload is None


def test_token_expiration():
    """Test token expiration."""
    data = {'user': 'test'}
    # Token expires immediately
    token = AuthManager.generate_token(data, expires_in=-1)
    
    payload = AuthManager.verify_token(token)
    assert payload is None

