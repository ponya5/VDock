"""QR pairing tokens (DL-147): single-use, short-lived, in-memory, never logged."""
import logging

import pytest

from app import app
from auth import AuthManager
from config import Config
from routes import auth as auth_routes
from services import pairing


@pytest.fixture(autouse=True)
def clean_state():
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


@pytest.fixture
def locked_deck():
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'correct horse battery'
    return {'Authorization': f"Bearer {AuthManager.authenticate('correct horse battery')}"}


def test_token_is_32_bytes_urlsafe():
    token = pairing.issue()
    assert len(token) >= 43
    assert all(c.isalnum() or c in '-_' for c in token)


def test_token_is_single_use():
    token = pairing.issue()
    assert pairing.redeem(token) is True
    assert pairing.redeem(token) is False


def test_token_expires_after_ttl():
    token = pairing.issue(clock=lambda: 1000.0)
    assert pairing.redeem(token, clock=lambda: 1000.0 + pairing.TTL_S) is False


def test_token_valid_just_before_ttl():
    token = pairing.issue(clock=lambda: 1000.0)
    assert pairing.redeem(token, clock=lambda: 1000.0 + pairing.TTL_S - 1) is True


def test_oldest_token_is_evicted_beyond_the_cap():
    tokens = [pairing.issue() for _ in range(pairing.MAX_LIVE + 1)]
    assert pairing.redeem(tokens[0]) is False
    assert pairing.redeem(tokens[-1]) is True


def test_pair_token_requires_sign_in(client, locked_deck):
    assert client.post('/api/auth/pair-token').status_code == 401
    res = client.post('/api/auth/pair-token', headers=locked_deck)
    assert res.status_code == 200
    assert res.get_json()['ttl_s'] == pairing.TTL_S


def test_pair_token_is_409_when_auth_is_off(client):
    Config.REQUIRE_AUTH = False
    assert client.post('/api/auth/pair-token').status_code == 409


def test_exchange_returns_a_token_the_server_accepts(client, locked_deck):
    token = client.post('/api/auth/pair-token', headers=locked_deck).get_json()['token']
    res = client.post('/api/auth/pair', json={'token': token})
    assert res.status_code == 200
    assert AuthManager.verify_token(res.get_json()['token']) is not None


def test_second_exchange_is_rejected(client, locked_deck):
    token = client.post('/api/auth/pair-token', headers=locked_deck).get_json()['token']
    assert client.post('/api/auth/pair', json={'token': token}).status_code == 200
    assert client.post('/api/auth/pair', json={'token': token}).status_code == 401


def test_missing_token_is_a_400(client, locked_deck):
    assert client.post('/api/auth/pair', json={}).status_code == 400
    assert client.post('/api/auth/pair', json={'token': 5}).status_code == 400


def test_unknown_tokens_count_toward_the_throttle(client, locked_deck):
    for _ in range(5):
        assert client.post('/api/auth/pair', json={'token': 'nope'}).status_code == 401
    assert client.post('/api/auth/pair', json={'token': 'nope'}).status_code == 429


def test_nothing_is_exchanged_when_auth_is_off(client):
    token = pairing.issue()
    Config.REQUIRE_AUTH = False
    assert client.post('/api/auth/pair', json={'token': token}).status_code == 401


def test_tokens_never_reach_the_logs(client, locked_deck, caplog):
    with caplog.at_level(logging.DEBUG):
        token = client.post('/api/auth/pair-token', headers=locked_deck).get_json()['token']
        client.post('/api/auth/pair', json={'token': token})
        client.post('/api/auth/pair', json={'token': token})
    assert token not in caplog.text


def test_paired_device_starts_unnamed_and_can_be_renamed(client, locked_deck):
    token = client.post('/api/auth/pair-token', headers=locked_deck).get_json()['token']
    env = {'REMOTE_ADDR': '192.168.1.50'}
    login = client.post('/api/auth/pair', json={'token': token}, environ_overrides=env).get_json()
    phone = {'Authorization': f"Bearer {login['token']}"}
    rows = client.get('/api/auth/devices', headers=phone).get_json()['devices']
    me = next(d for d in rows if d['current'])
    assert me['named'] is False
    assert client.patch(f"/api/auth/devices/{me['id']}", json={'label': ''}, headers=phone).status_code == 400
    assert client.patch(f"/api/auth/devices/{me['id']}", json={'label': ' Dan  iPhone '}, headers=phone).status_code == 200
    rows = client.get('/api/auth/devices', headers=phone).get_json()['devices']
    me = next(d for d in rows if d['current'])
    assert (me['label'], me['named']) == ('Dan iPhone', True)


def test_phone_is_listed_when_auth_is_off_and_a_revoke_sticks_when_on(client):
    from services import devices
    env = {'REMOTE_ADDR': '192.168.1.60'}
    hdr = {'X-Device-Id': 'phone-abc-12345', 'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S918B) Mobile'}
    Config.REQUIRE_AUTH = False
    client.get('/api/health', headers=hdr, environ_overrides=env)
    row = next(d for d in devices.list_devices() if d['id'] == 'phone-abc-12345')
    assert row['label'] == 'Android (SM-S918B)' and row['named'] is False
    # local requests are never listed
    client.get('/api/health', headers={'X-Device-Id': 'desktop-xyz-12345'})
    assert all(d['id'] != 'desktop-xyz-12345' for d in devices.list_devices())
    # auth on: a revoked id is not resurrected by plain traffic
    Config.REQUIRE_AUTH = True
    devices.revoke('phone-abc-12345')
    client.get('/api/health', headers=hdr, environ_overrides=env)
    assert all(d['id'] != 'phone-abc-12345' for d in devices.list_devices())
    Config.REQUIRE_AUTH = False
