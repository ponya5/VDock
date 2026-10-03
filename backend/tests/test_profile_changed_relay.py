"""profile_changed relay (DL-147): other decks hear about a save, the sender does not.

Flask-SocketIO's test client cannot connect under the pinned Flask (its session
shim assigns a read-only property), so the handler is called directly with
``emit`` captured.
"""
import pytest

import app as app_module


@pytest.fixture
def emitted(monkeypatch):
    calls = []
    monkeypatch.setattr(app_module, 'emit', lambda *args, **kwargs: calls.append((args, kwargs)))
    return calls


def test_relays_the_id_to_everyone_but_the_sender(emitted):
    app_module.handle_profile_changed({'id': 'p1'})
    assert emitted == [(('profile_changed', {'id': 'p1'}), {'broadcast': True, 'include_self': False})]


@pytest.mark.parametrize('payload', [
    None, 'p1', [], {}, {'id': None}, {'id': 7}, {'id': ''}, {'id': 'x' * 129},
])
def test_malformed_payloads_are_not_relayed(emitted, payload):
    app_module.handle_profile_changed(payload)
    assert emitted == []


def test_only_the_id_is_relayed(emitted):
    app_module.handle_profile_changed({'id': 'p1', 'profile': {'secret': 1}})
    assert emitted[0][0][1] == {'id': 'p1'}


def test_id_of_exactly_the_limit_is_relayed(emitted):
    app_module.handle_profile_changed({'id': 'x' * 128})
    assert len(emitted) == 1
