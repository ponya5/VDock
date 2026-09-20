"""Production-hardening regression tests.

Feature: production-security-hardening — the catch-all static route and the
upload/asset routes must never serve or write files outside their roots, and
every mutating/config route must respect REQUIRE_AUTH.

These tests exist because /..%2F..%2Fbackend%2F.env once returned HTTP 200
with the env file's contents on a live server.
"""
import io
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from config import Config  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


# --- catch-all traversal ------------------------------------------------------

def test_encoded_traversal_does_not_serve_env(client):
    """Regression: this exact request returned backend/.env with HTTP 200."""
    resp = client.get('/..%2F..%2Fbackend%2F.env')
    assert resp.status_code == 404
    assert b'SECRET' not in resp.data


def test_encoded_traversal_does_not_serve_config(client):
    resp = client.get('/..%2Fbackend%2Fconfig.py')
    assert resp.status_code == 404
    assert b'class Config' not in resp.data


def test_backslash_traversal_blocked(client):
    resp = client.get('/..%5C..%5Cbackend%5C.env')
    assert resp.status_code == 404


def test_dotfile_names_cannot_escape(client):
    # Flask normalizes plain '..' out of PATH_INFO, but the guard must still
    # hold for anything that reaches the handler.
    resp = client.get('/%2E%2E%2F%2E%2E%2Fbackend%2F.env')
    assert resp.status_code == 404


def test_spa_fallback_still_works(client):
    """A dot-less path must still fall through to index.html when dist exists."""
    dist_index = BACKEND.parent / 'frontend' / 'dist' / 'index.html'
    resp = client.get('/settings')
    if dist_index.exists():
        assert resp.status_code == 200
        assert b'<div id="app">' in resp.data or b'id="app"' in resp.data
    else:
        assert resp.status_code == 404


# --- uploads containment -------------------------------------------------------

def test_upload_serving_traversal_blocked(client):
    resp = client.get('/api/uploads/..%2F..%2Fconfig.py')
    assert resp.status_code in (400, 404)


def test_oversize_upload_rejected_by_max_content_length(client):
    """MAX_CONTENT_LENGTH must reject before the route runs."""
    big = io.BytesIO(b'x' * (17 * 1024 * 1024))
    resp = client.post('/api/upload',
                       data={'file': (big, 'big.png'), 'type': 'backgrounds'},
                       content_type='multipart/form-data')
    assert resp.status_code in (400, 413)


# --- assets upload sanitization -----------------------------------------------

def test_asset_upload_rejects_traversal_category(client, tmp_path,
                                                 monkeypatch):
    monkeypatch.setattr('routes.assets.FRONTEND_ASSETS_DIR', tmp_path)
    png = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'0' * 16)
    resp = client.post(
        '/api/assets/upload',
        data={'file': (png, 'evil.png'), 'type': 'icons',
              'category': '../../../backend'},
        content_type='multipart/form-data')
    # Sanitized into the assets tree or rejected — never escapes tmp_path.
    assert resp.status_code in (200, 201, 400)
    if resp.status_code in (200, 201):
        assert (tmp_path / 'icons' / 'backend' / 'evil.png').exists()
    assert not (BACKEND / 'evil.png').exists()
    assert not (tmp_path.parent / 'evil.png').exists()


def test_asset_upload_rejects_traversal_filename(client, tmp_path,
                                                 monkeypatch):
    monkeypatch.setattr('routes.assets.FRONTEND_ASSETS_DIR', tmp_path)
    png = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'0' * 16)
    resp = client.post(
        '/api/assets/upload',
        data={'file': (png, '../../evil.png'), 'type': 'icons',
              'category': 'custom'},
        content_type='multipart/form-data')
    assert resp.status_code in (200, 201, 400)
    if resp.status_code in (200, 201):
        # secure_filename('..\\..\\evil.png') -> 'evil.png' stays in category.
        assert (tmp_path / 'icons' / 'custom' / 'evil.png').exists()
    for escaped_dir in (tmp_path.parent, BACKEND, BACKEND.parent):
        assert not (escaped_dir / 'evil.png').exists()


def test_asset_upload_rejects_bad_type(client):
    png = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'0' * 16)
    resp = client.post(
        '/api/assets/upload',
        data={'file': (png, 'x.png'), 'type': '../../backend',
              'category': 'custom'},
        content_type='multipart/form-data')
    assert resp.status_code == 400


# --- auth coverage --------------------------------------------------------------

def test_config_requires_auth_when_enabled(client):
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'test-pw'
    assert client.get('/api/config').status_code == 401
    assert client.put('/api/config', json={'require_auth': False}).status_code == 401


def test_config_accessible_with_token(client):
    from auth.auth_manager import AuthManager
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'test-pw'
    token = AuthManager.generate_token({'authenticated': True})
    headers = {'Authorization': f'Bearer {token}'}
    assert client.get('/api/config', headers=headers).status_code == 200


def test_malformed_auth_header_rejected(client):
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'test-pw'
    for bad in ('token', 'Bearer', 'Bearer  ', 'Basic abc'):
        assert client.get('/api/config',
                          headers={'Authorization': bad}).status_code == 401


def test_assets_upload_requires_auth_when_enabled(client):
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'test-pw'
    png = io.BytesIO(b'\x89PNG\r\n\x1a\n' + b'0' * 16)
    resp = client.post('/api/assets/upload',
                       data={'file': (png, 'x.png')},
                       content_type='multipart/form-data')
    assert resp.status_code == 401


def test_auth_disabled_keeps_routes_open(client):
    Config.REQUIRE_AUTH = False
    assert client.get('/api/config').status_code == 200


def test_config_rejects_non_boolean_toggles(client):
    """'require_auth: "false"' would reload as a truthy string — refuse it."""
    resp = client.put('/api/config', json={'require_auth': 'false'})
    assert resp.status_code == 400
    resp = client.put('/api/config', json={'allow_lan': 1})
    assert resp.status_code == 400
    resp = client.put('/api/config', json={'enable_plugins': True})
    assert resp.status_code == 200
