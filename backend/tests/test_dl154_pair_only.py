"""DL-154: pair-only LAN access, revocable device list, network-profile parsing."""
import pytest

from app import app
from auth import AuthManager
from config import Config
from routes import auth as auth_routes
from services import devices, network_profile, pairing

pytestmark = pytest.mark.real_trusted_host

PHONE = {'REMOTE_ADDR': '192.168.0.52'}
IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit Mobile'


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Own data dir + .env so nothing touches the real config or password."""
    monkeypatch.setattr(Config, 'DATA_DIR', tmp_path)
    monkeypatch.setattr('routes.config.env_file', lambda: tmp_path / '.env')
    pairing._tokens.clear()
    auth_routes._attempts.clear()
    yield
    pairing._tokens.clear()
    auth_routes._attempts.clear()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def _enable_pair_only(client):
    res = client.put('/api/config', json={'allow_lan': True, 'pair_only': True})
    assert res.status_code == 200, res.get_json()


def _pair_phone(client):
    token = client.post('/api/auth/pair-token').get_json()['token']
    res = client.post(
        '/api/auth/pair', json={'token': token},
        headers={'User-Agent': IPHONE_UA}, environ_overrides=PHONE,
    )
    assert res.status_code == 200
    return res.get_json()['token']


# --- pair-only mode -------------------------------------------------------

def test_pair_only_generates_a_hidden_password(client):
    _enable_pair_only(client)
    assert Config.REQUIRE_AUTH is True
    assert len(Config.AUTH_PASSWORD) >= 24
    config = client.get('/api/config').get_json()['config']
    assert config['pair_only'] is True
    assert config['require_auth'] is True
    assert Config.AUTH_PASSWORD not in str(config)
    assert Config.AUTH_PASSWORD in (Config.DATA_DIR / '.env').read_text()


def test_pair_only_turns_off_when_a_password_is_typed(client):
    _enable_pair_only(client)
    assert client.put('/api/config', json={'auth_password': 'my-own-pass'}).status_code == 200
    assert client.get('/api/config').get_json()['config']['pair_only'] is False


def test_pair_only_refuses_to_replace_a_typed_password(client):
    assert client.put('/api/config', json={'auth_password': 'my-own-pass'}).status_code == 200
    res = client.put('/api/config', json={'pair_only': True})
    assert res.status_code == 400
    assert Config.AUTH_PASSWORD == 'my-own-pass'


def test_pair_only_must_be_a_boolean(client):
    assert client.put('/api/config', json={'pair_only': 'yes'}).status_code == 400


def test_phone_without_a_token_is_locked_out(client):
    _enable_pair_only(client)
    assert client.get('/api/auth/devices', environ_overrides=PHONE).status_code == 401


# --- device registry ------------------------------------------------------

def test_user_agent_labels():
    assert devices.label_from_user_agent(IPHONE_UA) == 'iPhone'
    assert devices.label_from_user_agent('Mozilla/5.0 (Linux; Android 14; Pixel) Mobile') == 'Android phone'
    assert devices.label_from_user_agent('Mozilla/5.0 (Linux; Android 14; Tab)') == 'Android tablet'
    assert devices.label_from_user_agent('Mozilla/5.0 (Windows NT 10.0)') == 'Windows PC'
    assert devices.label_from_user_agent('') == 'Device'


def test_pairing_registers_a_device_and_lists_it(client):
    _enable_pair_only(client)
    phone_token = _pair_phone(client)
    payload = AuthManager.verify_token(phone_token)
    assert payload and payload['did']

    rows = client.get('/api/auth/devices').get_json()['devices']
    assert [r['label'] for r in rows] == ['iPhone']
    assert rows[0]['ip'] == '192.168.0.52'
    assert 'user_agent' not in rows[0]

    own = client.get(
        '/api/auth/devices', headers={'Authorization': f'Bearer {phone_token}'},
        environ_overrides=PHONE,
    ).get_json()['devices']
    assert own[0]['current'] is True


def test_revoking_a_device_signs_only_it_out(client):
    _enable_pair_only(client)
    first, second = _pair_phone(client), _pair_phone(client)
    first_id = AuthManager.verify_token(first)['did']

    assert client.delete(f'/api/auth/devices/{first_id}').status_code == 200
    assert AuthManager.verify_token(first) is None
    assert AuthManager.verify_token(second) is not None
    assert client.delete(f'/api/auth/devices/{first_id}').status_code == 404


def test_revoke_all_signs_everyone_out(client):
    _enable_pair_only(client)
    tokens = [_pair_phone(client), _pair_phone(client)]
    res = client.delete('/api/auth/devices')
    assert res.get_json()['revoked'] == 2
    assert all(AuthManager.verify_token(t) is None for t in tokens)


def test_refresh_keeps_the_device_id(client):
    _enable_pair_only(client)
    old = _pair_phone(client)
    res = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {old}'})
    new = res.get_json()['token']
    assert AuthManager.verify_token(new)['did'] == AuthManager.verify_token(old)['did']


def test_password_login_registers_a_device(client):
    client.put('/api/config', json={'auth_password': 'my-own-pass', 'require_auth': True})
    res = client.post(
        '/api/auth/login', json={'password': 'my-own-pass'},
        headers={'User-Agent': IPHONE_UA}, environ_overrides=PHONE,
    )
    assert AuthManager.verify_token(res.get_json()['token'])['did']
    assert len(devices.list_devices()) == 1


def test_tokens_from_before_device_ids_still_work():
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'old-build-pass'
    legacy = AuthManager.generate_token({'authenticated': True})
    assert AuthManager.verify_token(legacy) is not None


def test_registry_survives_a_reload():
    device_id = devices.register(IPHONE_UA, '10.0.0.5')
    devices._state['path'] = None  # force a re-read from disk
    assert devices.is_active(device_id)


def test_registry_is_capped():
    for _ in range(devices.MAX_DEVICES + 3):
        devices.register(IPHONE_UA)
    assert len(devices.list_devices()) == devices.MAX_DEVICES


# --- network profile ------------------------------------------------------

def test_classify_categories():
    assert network_profile.classify('Public') == 'public'
    assert network_profile.classify('Private') == 'private'
    assert network_profile.classify('DomainAuthenticated') == 'domain'
    assert network_profile.classify('') == 'unknown'


def test_parse_single_object_and_list():
    one = '{"InterfaceAlias":"Wi-Fi","Category":"Public"}'
    many = '[{"InterfaceAlias":"Wi-Fi","Category":"Public"},{"InterfaceAlias":"Ethernet","Category":"Private"}]'
    assert network_profile.parse_profiles(one) == [('Wi-Fi', 'Public')]
    assert len(network_profile.parse_profiles(many)) == 2
    assert network_profile.parse_profiles('not json') == []


def test_profile_is_matched_to_the_lan_adapter():
    profiles = [('Wi-Fi', 'Public'), ('Ethernet', 'Private')]
    assert network_profile.pick_profile(profiles, 'wi-fi') == 'public'
    assert network_profile.pick_profile(profiles, 'Ethernet') == 'private'
    assert network_profile.pick_profile(profiles, 'Other') == 'unknown'
    assert network_profile.pick_profile(profiles, None) == 'unknown'


def test_non_windows_is_unknown(monkeypatch):
    monkeypatch.setattr(network_profile, 'host_os', lambda: 'macos')
    assert network_profile.network_profile() == 'unknown'


# --- lock-screen hint -----------------------------------------------------

def test_auth_mode_is_public_and_only_says_pair_only(client):
    assert client.get('/api/auth/mode', environ_overrides=PHONE).get_json() == {'pair_only': False}
    _enable_pair_only(client)
    res = client.get('/api/auth/mode', environ_overrides=PHONE)
    assert res.status_code == 200
    assert res.get_json() == {'pair_only': True}
