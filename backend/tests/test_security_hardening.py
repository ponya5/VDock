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


def test_config_deck_host_override(client):
    resp = client.put('/api/config', json={'deck_host': 'deck.local'})
    assert resp.status_code == 200
    assert Config.DECK_HOST == 'deck.local'
    resp = client.get('/api/config')
    assert resp.get_json()['config']['deck_host'] == 'deck.local'
    client.put('/api/config', json={'deck_host': ''})


def test_config_deck_host_rejects_full_urls(client):
    """The QR already prepends http:// and appends the bind port — a value
    carrying either would double them up, so only bare hostnames/IPs pass."""
    for bad in ('http://deck.local', 'deck.local:4444', 'de ck', 'host/path', 123):
        resp = client.put('/api/config', json={'deck_host': bad})
        assert resp.status_code == 400, bad
    resp = client.get('/api/config')
    assert resp.get_json()['config']['deck_host'] is None


def test_config_deck_host_clear_restores_auto(client):
    assert client.put('/api/config', json={'deck_host': '192.168.9.9'}).status_code == 200
    assert client.put('/api/config', json={'deck_host': ''}).status_code == 200
    assert Config.DECK_HOST == ''
    resp = client.get('/api/config')
    assert resp.get_json()['config']['deck_host'] is None


# ---------------------------------------------------------------------------
# DL-126 — usable authentication: set/change the password and toggle
# require_auth from the Settings UI without a restart, with the bootstrap
# ordering that keeps the enabling session valid. .env writes are redirected
# to tmp_path so tests never touch the repo's real env file.
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    monkeypatch.setattr('routes.config.backend_dir', lambda: tmp_path)
    # PUT /api/config persists to the real data/config.json — restore it
    # after the test so require_auth doesn't leak onto disk.
    saved_config = Config.load_config()
    import routes.auth as auth_routes
    auth_routes._attempts.clear()
    yield tmp_path
    auth_routes._attempts.clear()
    Config.save_config(saved_config)


def test_config_exposes_auth_password_set(client, auth_env):
    resp = client.get('/api/config')
    assert resp.status_code == 200
    assert resp.get_json()['config']['auth_password_set'] is False


def test_set_password_persists_env_and_applies(client, auth_env):
    resp = client.put('/api/config', json={'auth_password': 'deck1234'})
    assert resp.status_code == 200
    assert Config.AUTH_PASSWORD == 'deck1234'
    env = (auth_env / '.env').read_text()
    assert 'AUTH_PASSWORD=deck1234' in env
    # The signing key is persisted alongside it so tokens outlive restarts.
    assert 'SECRET_KEY=' in env
    # The password itself is never returned by GET — only the flag.
    body = client.get('/api/config').get_json()
    assert body['config']['auth_password_set'] is True
    assert 'auth_password' not in body['config']


def test_enable_auth_without_password_rejected(client, auth_env):
    resp = client.put('/api/config', json={'require_auth': True})
    assert resp.status_code == 400
    assert 'password' in resp.get_json()['error'].lower()
    assert Config.REQUIRE_AUTH is False
    # …and nothing was persisted either.
    assert 'require_auth' not in Config.load_config() or \
        Config.load_config()['require_auth'] is not True


def test_password_and_enable_in_one_request(client, auth_env):
    resp = client.put('/api/config',
                      json={'auth_password': 'deck1234',
                            'require_auth': True})
    assert resp.status_code == 200
    assert Config.REQUIRE_AUTH is True
    assert Config.AUTH_PASSWORD == 'deck1234'


def test_bootstrap_session_stays_valid(client, auth_env):
    """The device that enables auth can immediately log in and keep
    calling protected routes — no locked-out gap."""
    client.put('/api/config',
               json={'auth_password': 'deck1234', 'require_auth': True})
    # Unauthenticated writes now 401…
    assert client.put('/api/config', json={}).status_code == 401
    # …but the password just set logs straight in.
    token = client.post('/api/auth/login',
                        json={'password': 'deck1234'}).get_json()['token']
    resp = client.put('/api/config', json={'allow_lan': True},
                      headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert Config.ALLOW_LAN is True


def test_disable_auth_with_token(client, auth_env):
    client.put('/api/config',
               json={'auth_password': 'deck1234', 'require_auth': True})
    token = client.post('/api/auth/login',
                        json={'password': 'deck1234'}).get_json()['token']
    resp = client.put('/api/config', json={'require_auth': False},
                      headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert Config.REQUIRE_AUTH is False
    assert client.put('/api/config', json={}).status_code == 200


def test_change_password_while_enabled(client, auth_env):
    client.put('/api/config',
               json={'auth_password': 'deck1234', 'require_auth': True})
    token = client.post('/api/auth/login',
                        json={'password': 'deck1234'}).get_json()['token']
    resp = client.put('/api/config', json={'auth_password': 'newpass9'},
                      headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert Config.AUTH_PASSWORD == 'newpass9'
    assert Config.REQUIRE_AUTH is True
    # Old password rejected, new one accepted.
    assert client.post('/api/auth/login',
                       json={'password': 'deck1234'}).status_code == 401
    assert client.post('/api/auth/login',
                       json={'password': 'newpass9'}).status_code == 200


@pytest.mark.parametrize('bad', ['', '   ', 'abc', 123, None, 'x' * 129])
def test_password_validation(client, auth_env, bad):
    resp = client.put('/api/config', json={'auth_password': bad})
    assert resp.status_code == 400
    assert Config.AUTH_PASSWORD == ''


def test_login_rate_limited(client, auth_env):
    client.put('/api/config',
               json={'auth_password': 'deck1234', 'require_auth': True})
    for _ in range(5):
        assert client.post('/api/auth/login',
                           json={'password': 'wrong'}).status_code == 401
    # Sixth attempt is throttled before the password is even checked.
    assert client.post('/api/auth/login',
                       json={'password': 'wrong'}).status_code == 429
    assert client.post('/api/auth/login',
                       json={'password': 'deck1234'}).status_code == 429


def test_login_success_clears_throttle_window(client, auth_env):
    client.put('/api/config',
               json={'auth_password': 'deck1234', 'require_auth': True})
    for _ in range(4):
        client.post('/api/auth/login', json={'password': 'wrong'})
    assert client.post('/api/auth/login',
                       json={'password': 'deck1234'}).status_code == 200


# ---------------------------------------------------------------------------
# lan_ip() — must advertise a phone-reachable address (DL-056 follow-up).
# A VPN/overlay adapter that captures the default route makes the UDP
# probe answer with a tunnel IP; the fix prefers the physical NIC.
# ---------------------------------------------------------------------------
import config as config_mod  # noqa: E402


def test_lan_ip_probe_on_physical_iface_wins(mocker):
    mocker.patch.object(config_mod, '_probe_ip', return_value='192.168.1.110')
    mocker.patch.object(config_mod, '_iface_candidates', return_value=[
        ('Wi-Fi', '192.168.1.110'),
        ('vEthernet (WSL (Hyper-V firewall))', '192.168.112.1'),
    ])
    assert config_mod.lan_ip() == '192.168.1.110'


def test_lan_ip_probe_on_vpn_falls_back_to_physical(mocker):
    """Full-tunnel WireGuard captures the default route — the probe IP is
    the tunnel address a phone on Wi-Fi cannot reach."""
    mocker.patch.object(config_mod, '_probe_ip', return_value='10.255.4.170')
    mocker.patch.object(config_mod, '_iface_candidates', return_value=[
        ('Wi-Fi', '192.168.1.110'),
        ('P81_Securitiz_WG_8RiPKjInQi', '10.255.4.170'),
        ('vEthernet (Default Switch)', '172.19.96.1'),
    ])
    assert config_mod.lan_ip() == '192.168.1.110'


def test_lan_ip_overlay_only_host_keeps_probe(mocker):
    """A box whose only address is an overlay (Tailscale) still answers —
    a device on the same overlay can reach it."""
    mocker.patch.object(config_mod, '_probe_ip', return_value='100.64.1.5')
    mocker.patch.object(config_mod, '_iface_candidates', return_value=[
        ('Tailscale', '100.64.1.5'),
    ])
    assert config_mod.lan_ip() == '100.64.1.5'


def test_lan_ip_prefers_192_168_over_10(mocker):
    """Two physical NICs — the typical home-LAN class wins the guess."""
    mocker.patch.object(config_mod, '_probe_ip', return_value=None)
    mocker.patch.object(config_mod, '_iface_candidates', return_value=[
        ('Ethernet', '10.20.30.40'),
        ('Wi-Fi', '192.168.1.110'),
    ])
    assert config_mod.lan_ip() == '192.168.1.110'


def test_lan_ip_no_candidates_falls_to_hostname(mocker):
    mocker.patch.object(config_mod, '_probe_ip', return_value=None)
    mocker.patch.object(config_mod, '_iface_candidates', return_value=[])
    mocker.patch.object(config_mod.socket, 'gethostbyname',
                        return_value='192.168.1.50')
    assert config_mod.lan_ip() == '192.168.1.50'
