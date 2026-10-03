"""Settings "Test" button: one minimal call per key, never echoing the key."""
from unittest.mock import MagicMock

import pytest

from config import Config
from services import key_check, secrets

SECRET = 'ghp_SuperSecretValue1234567890abcdef'


def _resp(status, payload=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload if payload is not None else {}
    return r


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ('GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY'):
        monkeypatch.delenv(name, raising=False)


def _stub(monkeypatch, response):
    seen = {}

    def fake_get(url, **kwargs):
        seen['url'] = url
        seen['kwargs'] = kwargs
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(key_check.requests, 'get', fake_get)
    return seen


# --- GitHub ------------------------------------------------------------------

def test_github_valid_reports_the_account(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    seen = _stub(monkeypatch, _resp(200, {'login': 'octocat'}))
    out = key_check.check(secrets.GITHUB_TOKEN)
    assert out['ok'] is True and out['status'] == 'valid'
    assert out['account'] == 'octocat' and 'octocat' in out['message']
    assert seen['url'] == 'https://api.github.com/user'
    assert seen['kwargs']['headers']['Authorization'] == f'Bearer {SECRET}'


@pytest.mark.parametrize('code,status', [(401, 'invalid'), (403, 'limited'), (429, 'limited'), (500, 'invalid')])
def test_github_failures_are_classified(monkeypatch, code, status):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    _stub(monkeypatch, _resp(code))
    out = key_check.check(secrets.GITHUB_TOKEN)
    assert out['ok'] is False and out['status'] == status


def test_offline_is_unreachable_not_invalid(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    _stub(monkeypatch, key_check.requests.ConnectionError('offline'))
    out = key_check.check(secrets.GITHUB_TOKEN)
    assert out['status'] == 'unreachable' and out['ok'] is False


def test_unset_key_is_reported_without_any_network_call(monkeypatch):
    def boom(*a, **k):
        raise AssertionError('no request expected')

    monkeypatch.setattr(key_check.requests, 'get', boom)
    assert key_check.check(secrets.GITHUB_TOKEN)['status'] == 'unset'
    assert key_check.check(secrets.ANTHROPIC_API_KEY)['status'] == 'unset'


# --- Anthropic / WeatherAPI --------------------------------------------------

def test_anthropic_valid_and_invalid(monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-realish-key-123')
    seen = _stub(monkeypatch, _resp(200))
    assert key_check.check(secrets.ANTHROPIC_API_KEY)['status'] == 'valid'
    assert seen['kwargs']['headers']['x-api-key'] == 'sk-ant-realish-key-123'
    _stub(monkeypatch, _resp(401))
    assert key_check.check(secrets.ANTHROPIC_API_KEY)['status'] == 'invalid'


def test_weatherapi_valid_invalid_and_quota(monkeypatch):
    monkeypatch.setenv('WEATHERAPI_KEY', 'abc123realkey')
    _stub(monkeypatch, _resp(200))
    assert key_check.check(secrets.WEATHERAPI_KEY)['status'] == 'valid'
    _stub(monkeypatch, _resp(401))
    assert key_check.check(secrets.WEATHERAPI_KEY)['status'] == 'invalid'
    _stub(monkeypatch, _resp(403))
    assert key_check.check(secrets.WEATHERAPI_KEY)['status'] == 'limited'


def test_weatherapi_without_a_key_tests_the_builtin_provider(monkeypatch):
    seen = _stub(monkeypatch, _resp(200))
    out = key_check.check(secrets.WEATHERAPI_KEY)
    assert out['ok'] is True and out['status'] == 'builtin'
    assert 'open-meteo' in seen['url']


def test_message_never_contains_the_key(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    for response in (_resp(200, {'login': 'octocat'}), _resp(401), _resp(403),
                     key_check.requests.ConnectionError(SECRET)):
        _stub(monkeypatch, response)
        assert SECRET not in str(key_check.check(secrets.GITHUB_TOKEN))


# --- route -------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    from app import app
    app.config['TESTING'] = True
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', False)
    return app.test_client()


def test_route_returns_the_check_and_never_the_key(client, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    _stub(monkeypatch, _resp(200, {'login': 'octocat'}))
    resp = client.post('/api/config/integrations/GITHUB_TOKEN/test')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'valid'
    assert SECRET not in resp.get_data(as_text=True)


def test_route_unknown_key_is_404(client):
    assert client.post('/api/config/integrations/NOT_A_KEY/test').status_code == 404


def test_route_refuses_other_devices(client, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', SECRET)
    resp = client.post('/api/config/integrations/GITHUB_TOKEN/test',
                       environ_overrides={'REMOTE_ADDR': '192.168.1.50'})
    assert resp.status_code == 403
