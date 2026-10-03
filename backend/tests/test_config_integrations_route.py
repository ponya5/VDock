"""GET /api/config/integrations (DL-146 Task 2.7). Status only, never values."""
import pytest

from config import Config


@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def restore_config():
    saved = (Config.ALLOW_LAN, Config.REQUIRE_AUTH, Config.AUTH_PASSWORD)
    yield
    Config.ALLOW_LAN, Config.REQUIRE_AUTH, Config.AUTH_PASSWORD = saved


def _items(body):
    return {item['id']: item for item in body['items']}


def test_shape(client, monkeypatch):
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    Config.REQUIRE_AUTH = False
    resp = client.get('/api/config/integrations')
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {'env_file', 'items', 'security'}
    items = _items(body)
    assert {'GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY', 'gh_cli', 'claude_cli'} <= set(items)
    gh = items['GITHUB_TOKEN']
    assert gh['kind'] == 'secret' and gh['configured'] is False
    assert 'GITHUB_TOKEN' in gh['reason']
    assert gh['help_url'].startswith('https://')
    assert gh['unlocks']
    assert items['gh_cli']['kind'] == 'cli'
    assert isinstance(items['gh_cli']['configured'], bool)
    assert set(body['security']) == {'allow_lan', 'require_auth', 'lan_without_password'}


@pytest.mark.parametrize('junk', ['demo-key-replace-with-your-own', 'your-github-token-here', 'changeme'])
def test_template_placeholders_do_not_count_as_configured(client, monkeypatch, junk):
    monkeypatch.setenv('WEATHERAPI_KEY', junk)
    items = _items(client.get('/api/config/integrations').get_json())
    assert items['WEATHERAPI_KEY']['configured'] is False


def test_env_file_is_a_display_path_without_user_name(client):
    import getpass
    body = client.get('/api/config/integrations').get_json()
    assert body['env_file'].endswith('.env')
    assert getpass.getuser().lower() not in body['env_file'].lower()


def test_values_are_never_returned(client, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_SECRETVALUE1234567890')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-SECRETVALUE')
    monkeypatch.setenv('WEATHERAPI_KEY', 'weather-SECRETVALUE')
    resp = client.get('/api/config/integrations')
    assert 'SECRETVALUE' not in resp.get_data(as_text=True)
    assert _items(resp.get_json())['GITHUB_TOKEN']['configured'] is True


def test_requires_auth_when_enabled(client):
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'a-real-password'
    assert client.get('/api/config/integrations').status_code == 401


@pytest.mark.parametrize('lan,auth,pw,expected', [
    (True, False, '', True),
    (True, True, 'pw', False),
    (True, True, '', True),
    (False, False, '', False),
    (False, True, 'pw', False),
])
def test_lan_without_password_truth_table(client, lan, auth, pw, expected):
    Config.ALLOW_LAN, Config.REQUIRE_AUTH, Config.AUTH_PASSWORD = lan, auth, pw
    if auth and not pw:
        # auth-on-without-password is refused at boot; the route must still
        # report the risk truthfully if it ever happens.
        Config.REQUIRE_AUTH = False
    from auth.auth_manager import AuthManager
    headers = {'Authorization': f"Bearer {AuthManager.generate_token({'authenticated': True})}"}
    sec = client.get('/api/config/integrations', headers=headers).get_json()['security']
    assert sec['allow_lan'] is lan
    assert sec['lan_without_password'] is expected


def test_health_has_version_and_uptime_only(client):
    body = client.get('/api/health').get_json()
    assert isinstance(body['uptime_s'], int) and body['uptime_s'] >= 0
    text = str(body).lower()
    assert 'env' not in text and 'token' not in text
