"""Stale-agent-state pruning (DL-080 follow-up #5).

A killed session never posts 'ended'; without liveness pruning its `ready`
entry told every surface "waiting for input" for up to the 30-min TTL — and
forever on clients that never re-synced. snapshot() now drops marker-backed
sources whose process is provably dead (with grace periods so a flaky scan
can never kill a live alert).
"""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from integrations import agent_state, sessions  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    agent_state.reset()
    yield
    agent_state.reset()


def _age_entry(source: str, age_seconds: float) -> None:
    """Backdate a recorded entry as if it were posted long ago."""
    for entry in agent_state._sessions_by_source[source].values():
        entry['ts'] = time.time() - age_seconds


def test_dead_process_prunes_old_ready(monkeypatch):
    agent_state.record('claude', 'ready')
    _age_entry('claude', agent_state._LIVENESS_GRACE_SECONDS + 5)
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: False)

    agent_state._dead_since['claude'] = time.time() - agent_state._LIVENESS_DEAD_SECONDS - 1
    assert 'claude' not in agent_state.snapshot()


def test_fresh_entry_survives_a_dead_scan(monkeypatch):
    """A just-posted ready beats a scanner that hasn't caught up."""
    agent_state.record('claude', 'ready')
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: False)

    assert 'claude' in agent_state.snapshot()


def test_live_process_keeps_old_ready(monkeypatch):
    agent_state.record('claude', 'ready')
    _age_entry('claude', agent_state._LIVENESS_GRACE_SECONDS + 5)
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: True)

    assert 'claude' in agent_state.snapshot()


def test_dead_scan_must_persist_before_pruning(monkeypatch):
    """One missed scan never drops a session — only continuous deadness."""
    agent_state.record('claude', 'ready')
    _age_entry('claude', agent_state._LIVENESS_GRACE_SECONDS + 5)
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: False)

    assert 'claude' in agent_state.snapshot()  # first dead reading: kept
    agent_state._dead_since['claude'] = time.time() - agent_state._LIVENESS_DEAD_SECONDS - 1
    assert 'claude' not in agent_state.snapshot()  # dead ≥60s: pruned


def test_live_scan_resets_the_dead_clock(monkeypatch):
    agent_state.record('claude', 'ready')
    _age_entry('claude', agent_state._LIVENESS_GRACE_SECONDS + 5)
    alive = {'v': False}
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: alive['v'])

    agent_state.snapshot()  # starts the dead clock
    alive['v'] = True
    agent_state._alive_cache.pop('claude', None)  # bypass the 10s cache
    agent_state.snapshot()  # live reading clears it
    assert 'claude' not in agent_state._dead_since
    alive['v'] = False
    agent_state._alive_cache.pop('claude', None)
    assert 'claude' in agent_state.snapshot()  # clock restarted, entry kept


def test_generic_source_is_ttl_only(monkeypatch):
    """'generic' has no process marker — TTL is its only expiry."""
    agent_state.record('generic', 'ready')
    _age_entry('generic', agent_state._LIVENESS_GRACE_SECONDS + 5)
    monkeypatch.setattr(sessions, 'session_alive', lambda marker: False)
    agent_state._dead_since['generic'] = time.time() - 9999

    assert 'generic' in agent_state.snapshot()


def test_ttl_still_expires():
    agent_state.record('claude', 'ready')
    _age_entry('claude', agent_state.STATE_TTL_SECONDS + 5)
    assert 'claude' not in agent_state.snapshot()
