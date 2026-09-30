"""DL-128: media_play_stop is a state-split transport — it must dispatch
``media_stop`` only while the SMTC snapshot says something is playing, and
``media_play_pause`` otherwise (paused session, empty snapshot, or a
now-playing service that can't be read). The split runs backend-side so
triggers and MCP run_action get the same behaviour as a deck press.
"""
import pytest

from actions.cross_platform_action import CrossPlatformAction, ActionResult
from services import now_playing


@pytest.fixture
def called(monkeypatch):
    calls = []
    monkeypatch.setattr(
        CrossPlatformAction, '_media_stop',
        lambda self: calls.append('stop') or ActionResult(True, 'stopped'))
    monkeypatch.setattr(
        CrossPlatformAction, '_media_play_pause',
        lambda self: calls.append('play_pause') or ActionResult(True, 'played'))
    return calls


def _act():
    return CrossPlatformAction({'action': 'media_play_stop'})


def test_playing_state_sends_stop(called, monkeypatch):
    monkeypatch.setattr(now_playing, 'snapshot', lambda: {'playing': True})
    result = _act().execute()
    assert result.success
    assert called == ['stop']


def test_paused_state_sends_play_pause(called, monkeypatch):
    monkeypatch.setattr(
        now_playing, 'snapshot', lambda: {'playing': False, 'title': 'T'})
    _act().execute()
    assert called == ['play_pause']


def test_no_snapshot_sends_play_pause(called, monkeypatch):
    monkeypatch.setattr(now_playing, 'snapshot', lambda: None)
    _act().execute()
    assert called == ['play_pause']


def test_unreadable_snapshot_sends_play_pause(called, monkeypatch):
    def boom():
        raise RuntimeError('smtc gone')
    monkeypatch.setattr(now_playing, 'snapshot', boom)
    _act().execute()
    assert called == ['play_pause']


def test_is_a_valid_cross_platform_action():
    assert 'media_play_stop' in CrossPlatformAction.VALID_ACTIONS
    assert _act().validate() is True
