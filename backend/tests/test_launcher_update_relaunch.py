"""DL-150 follow-up: an updater relaunch restarts the backend only.

The window that triggered the update is still open and reloads itself once
the backend is back, so the launcher must not open a second Electron window
or browser tab.
"""
import importlib.util
import os
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parents[2] / 'scripts' / 'VDock-Launcher.py'


@pytest.fixture
def launcher():
    spec = importlib.util.spec_from_file_location('vdock_launcher_under_test', LAUNCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record_ui(monkeypatch, launcher):
    calls = []
    monkeypatch.setattr(launcher, 'launch_electron', lambda: calls.append('electron') or True)
    monkeypatch.setattr(launcher, 'open_browser', lambda: calls.append('browser'))
    return calls


def test_normal_launch_opens_electron(monkeypatch, launcher):
    calls = _record_ui(monkeypatch, launcher)
    assert launcher.open_ui(update_relaunch=False) is True
    assert calls == ['electron']


def test_update_relaunch_opens_no_window(monkeypatch, launcher):
    calls = _record_ui(monkeypatch, launcher)
    assert launcher.open_ui(update_relaunch=True) is None
    assert calls == []


def test_update_relaunch_flag_is_consumed(monkeypatch, launcher):
    monkeypatch.setenv('VDOCK_UPDATE_RELAUNCH', '1')
    assert launcher.consume_update_relaunch_flag() is True
    # Cleared before the backend is spawned, so it can't leak into a later launch.
    assert 'VDOCK_UPDATE_RELAUNCH' not in os.environ
    assert launcher.consume_update_relaunch_flag() is False
