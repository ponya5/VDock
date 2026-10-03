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
