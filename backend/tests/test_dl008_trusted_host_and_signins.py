"""DL-008 - the computer VDock runs on is trusted; sign-ins last and renew;
a password change signs every device out."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config as config_module  # noqa: E402
from app import app  # noqa: E402
from auth import AuthManager  # noqa: E402
from config import Config  # noqa: E402

pytestmark = pytest.mark.real_trusted_host


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    monkeypatch.setattr(Config, 'AUTH_PASSWORD', 'deckpass')
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def _get(client, remote='127.0.0.1', host='localhost:5001', headers=None):
    return client.get('/api/config', headers={'Host': host, **(headers or {})},
                      environ_base={'REMOTE_ADDR': remote})


def test_vdock_window_on_this_computer_needs_no_password(client):
    assert _get(client).status_code == 200
    assert _get(client, remote='::1', host='[::1]:5001').status_code == 200
    assert _get(client, host='127.0.0.1:5001').status_code == 200


def test_phone_on_the_wifi_still_needs_it(client):
    assert _get(client, remote='192.168.0.50', host='192.168.0.14:5001').status_code == 401


def test_dns_rebinding_page_is_not_trusted(client):
    """A web page whose hostname resolves to 127.0.0.1 still sends its own Host."""
    assert _get(client, host='evil.example:5001').status_code == 401


def test_dev_proxy_cannot_launder_a_phone(client):
    """Vite's changeOrigin rewrites Host to 127.0.0.1; xfwd adds X-Forwarded-For."""
    response = _get(client, host='127.0.0.1:5001',
                    headers={'X-Forwarded-For': '192.168.0.50'})
    assert response.status_code == 401
    assert _get(client, headers={'Forwarded': 'for=192.168.0.50'}).status_code == 401


def test_signed_in_phone_works_and_renews(client):
    token = AuthManager.generate_token({'authenticated': True})
    headers = {'Authorization': f'Bearer {token}'}
    assert _get(client, remote='192.168.0.50', host='192.168.0.14:5001',
                headers=headers).status_code == 200
    renewed = client.post('/api/auth/refresh', headers=headers,
                          environ_base={'REMOTE_ADDR': '192.168.0.50'}).get_json()
    assert renewed['success'] is True
    assert AuthManager.verify_token(renewed['token'])


def test_refresh_needs_a_valid_token(client):
    assert client.post('/api/auth/refresh').status_code == 401
    assert client.post('/api/auth/refresh',
                       headers={'Authorization': 'Bearer junk'}).status_code == 401


def test_password_change_signs_every_device_out(client, monkeypatch):
    token = AuthManager.generate_token({'authenticated': True})
    assert AuthManager.verify_token(token)
    monkeypatch.setattr(Config, 'AUTH_PASSWORD', 'new-pass')
    assert AuthManager.verify_token(token) is None


def test_tokens_from_older_builds_stay_valid_until_they_expire(client):
    import jwt
    from datetime import datetime, timedelta, timezone
    legacy = jwt.encode({'authenticated': True,
                         'exp': datetime.now(timezone.utc) + timedelta(hours=1)},
                        Config.SECRET_KEY, algorithm='HS256')
    assert AuthManager.verify_token(legacy)


@pytest.mark.parametrize('raw,seconds', [
    (None, 30 * 86400), ('', 30 * 86400),
    ('86400', 30 * 86400),        # the value every old .env got from the template
    ('7200', 7200), ('junk', 30 * 86400), ('5', 60),
])
def test_sign_in_lifetime(raw, seconds):
    assert config_module._token_expiration(raw) == seconds
