"""PUT/DELETE /api/config/integrations/<id> (DL-146 follow-up): save keys in-app."""
import logging
import os

import pytest

from config import Config

SECRET = 'ghp_SuperSecretValue1234567890abcdef'
URL = '/api/config/integrations/GITHUB_TOKEN'


@pytest.fixture
def client():
    from app import app
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def env(monkeypatch, tmp_path):
    target = tmp_path / '.env'
    monkeypatch.setattr('config.env_file', lambda: target)
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', False)
    for name in ('GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY'):
        monkeypatch.setenv(name, '')
        monkeypatch.delenv(name)
    yield target
    for name in ('GITHUB_TOKEN', 'ANTHROPIC_API_KEY', 'WEATHERAPI_KEY'):
        os.environ.pop(name, None)


def _status(client, id_='GITHUB_TOKEN'):
    items = {i['id']: i for i in client.get('/api/config/integrations').get_json()['items']}
    return items[id_]['configured']


def test_save_replace_remove_preserves_other_lines(client, env):
    env.write_bytes(b'# my comment\r\nPORT=5000\r\nGITHUB_TOKEN=old\r\n\r\nSECRET_KEY=abc\r\n')
    resp = client.put(URL, json={'value': SECRET})
    assert resp.status_code == 200
    assert resp.get_json() == {'id': 'GITHUB_TOKEN', 'configured': True}
    assert env.read_bytes() == (
        f'# my comment\r\nPORT=5000\r\nGITHUB_TOKEN={SECRET}\r\n\r\nSECRET_KEY=abc\r\n'.encode()
    )
    assert os.environ['GITHUB_TOKEN'] == SECRET
    assert _status(client) is True

    resp = client.delete(URL)
    assert resp.get_json() == {'id': 'GITHUB_TOKEN', 'configured': False}
    assert env.read_bytes() == b'# my comment\r\nPORT=5000\r\n\r\nSECRET_KEY=abc\r\n'
    assert 'GITHUB_TOKEN' not in os.environ
    assert _status(client) is False


def test_creates_missing_file_and_appends(client, env):
    assert not env.exists()
    assert client.put('/api/config/integrations/WEATHERAPI_KEY', json={'value': 'abc123'}).status_code == 200
    assert env.read_text() == 'WEATHERAPI_KEY=abc123\n'
    assert not (env.parent / '.env.tmp').exists()


def test_empty_value_removes(client, env):
    env.write_text('A=1\nGITHUB_TOKEN=x\n')
    assert client.put(URL, json={'value': '  '}).get_json()['configured'] is False
    assert env.read_text() == 'A=1\n'


@pytest.mark.parametrize('bad', [
    'a\nINJECTED=1', 'a\rb', 'has space', 'q"uote', "q'uote", 'back\\slash', 'x#y', 'a\x00b', 'a' * 513, 5, ['x'],
])
def test_invalid_values_rejected(client, env, bad):
    resp = client.put(URL, json={'value': bad})
    assert resp.status_code == 400
    assert not env.exists() and 'GITHUB_TOKEN' not in os.environ


def test_body_must_have_value(client, env):
    assert client.put(URL, json={'nope': 1}).status_code == 400


@pytest.mark.parametrize('bad_id', ['SECRET_KEY', 'AUTH_PASSWORD', 'PATH', 'github_token'])
def test_unknown_id_404(client, env, bad_id):
    assert client.put(f'/api/config/integrations/{bad_id}', json={'value': 'abc'}).status_code == 404
    assert not env.exists()


def test_lan_refused(client, env):
    for method in (client.put, client.delete):
        kwargs = {'json': {'value': SECRET}} if method == client.put else {}
        resp = method(URL, environ_overrides={'REMOTE_ADDR': '192.168.1.50'}, **kwargs)
        assert resp.status_code == 403
    assert not env.exists() and 'GITHUB_TOKEN' not in os.environ


def test_requires_auth_when_enabled(client, env, monkeypatch):
    monkeypatch.setattr(Config, 'REQUIRE_AUTH', True)
    assert client.put(URL, json={'value': SECRET}).status_code == 401
    assert not env.exists()


def test_secret_never_in_response_or_logs(client, env, caplog):
    caplog.set_level(logging.DEBUG)
    ok = client.put(URL, json={'value': SECRET})
    bad = client.put(URL, json={'value': SECRET + ' "'})
    status = client.get('/api/config/integrations')
    removed = client.delete(URL)
    for resp in (ok, bad, status, removed):
        assert SECRET not in resp.get_data(as_text=True)
    assert SECRET not in caplog.text
