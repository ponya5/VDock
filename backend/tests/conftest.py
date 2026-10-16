"""Shared test fixtures and isolation guards.

Config is process-wide class state, so a test that flips a flag on it affects
every test that runs afterwards. That happened: test_properties.py set
Config.REQUIRE_AUTH = True and never restored it, and every later test that
called a @require_auth route silently got 401 instead of its real response.
The failure surfaced only when a new route test happened to sort after it.

This fixture makes that class of leak impossible rather than relying on each
test to clean up after itself.
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # noqa: E402

_GUARDED_SETTINGS = (
    'REQUIRE_AUTH',
    'AUTH_PASSWORD',
    'ALLOW_COMMAND_EXECUTION',
    'REQUIRE_COMMAND_CONFIRMATION',
    'ENABLE_PLUGINS',
    'RATELIMIT_ENABLED',
    'ALLOW_LAN',
    'HOST',
    'DECK_HOST',
    'APP_PATHS',
)


@pytest.fixture(autouse=True)
def restore_config():
    """Start every test from a clean auth baseline, restore flags after.

    Config now reads the developer's real backend/.env and data/config.json
    (saved require_auth + AUTH_PASSWORD). Tests must not depend on them, so
    auth starts off with no password; tests that need auth set it themselves.
    """
    Config.REQUIRE_AUTH = False
    Config.AUTH_PASSWORD = ''
    saved = {name: getattr(Config, name) for name in _GUARDED_SETTINGS}
    yield
    for name, value in saved.items():
        setattr(Config, name, value)


# The user's real backend/.env holds their keys and signing secret. No test may
# write it (Phase 1 had one rewrite SECRET_KEY): snapshot, compare, and put the
# original bytes back before failing so a single offender does no lasting harm.
_REAL_ENV = Path(__file__).resolve().parents[1] / '.env'


@pytest.fixture(autouse=True)
def real_env_file_is_never_written():
    before = _REAL_ENV.read_bytes() if _REAL_ENV.exists() else None
    yield
    after = _REAL_ENV.read_bytes() if _REAL_ENV.exists() else None
    if after != before:
        if before is None:
            _REAL_ENV.unlink()
        else:
            _REAL_ENV.write_bytes(before)
        pytest.fail('A test modified the real backend/.env; point it at tmp_path / monkeypatch env_file.')


@pytest.fixture(autouse=True)
def assume_macos_accessibility_granted():
    """Hotkey tests use a fake keyboard; don't let the host Mac's real
    Accessibility permission decide whether they pass.

    Deliberately not built on ``monkeypatch``: requesting it from an autouse
    fixture changes teardown order and breaks real_env_file_is_never_written.
    """
    with mock.patch(
        'actions.macos_controls.is_accessibility_trusted', return_value=True
    ), mock.patch(
        # Nor the host Mac's lock screen (DL-009) - a locked dev machine
        # would refuse every keystroke test.
        'utils.window_focus._macos_screen_locked', return_value=False
    ):
        yield


_STABLE_HOOK_DIR = Path(tempfile.mkdtemp(prefix='vdock-test-hook-'))


@pytest.fixture(autouse=True)
def hook_copy_never_lands_in_real_home():
    """install_hook copies the hook script under ~/.vdock (DL-009); tests
    must never write the developer's home. Same no-monkeypatch rule."""
    with mock.patch('integrations.agent_hooks.stable_hook_dir', return_value=_STABLE_HOOK_DIR):
        yield


_AGENT_HOME = Path(tempfile.mkdtemp(prefix='vdock-test-agents-'))


@pytest.fixture(autouse=True)
def agent_settings_never_touch_real_home():
    """Every agent's settings file lives in a temp home for every test.

    refresh_installed_hooks() walks ALL agents; a test that redirected only
    Claude's file rewrote the developer's real ~/.cursor/hooks.json (DL-009).
    Tests that need their own paths still override these per test.
    """
    import dataclasses
    from integrations import agent_hooks
    redirected = {
        name: dataclasses.replace(target, path=(lambda name=name, rel=rel: _AGENT_HOME / name / rel))
        for name, target, rel in (
            (n, t, t.path().name) for n, t in agent_hooks._TARGETS.items()
        )
    }
    with mock.patch.dict(agent_hooks._TARGETS, redirected), \
            mock.patch('integrations.agent_hooks.codex_config_path',
                       return_value=_AGENT_HOME / 'codex' / 'config.toml'):
        yield


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'real_trusted_host: use the real DL-008 "this computer is trusted" rule',
    )


@pytest.fixture(autouse=True)
def test_client_is_another_device(request):
    """The Flask test client calls from 127.0.0.1 with ``Host: localhost`` -
    exactly the computer DL-008 trusts - so every "requires auth" test would
    sail through. Treat test requests as another device on the Wi-Fi unless a
    test opts into the real rule with ``@pytest.mark.real_trusted_host``.
    Same no-monkeypatch rule as above.
    """
    if request.node.get_closest_marker('real_trusted_host'):
        yield
        return
    with mock.patch('auth.auth_manager.is_trusted_local_request', return_value=False), \
            mock.patch('auth.is_trusted_local_request', return_value=False):
        yield


@pytest.fixture
def windows_keymaps():
    """Evaluate keymaps as on Windows, for tests that assert Ctrl chords.

    macOS runs remap VS Code-family shortcuts to Cmd; those are covered in
    test_macos_agent_interactions.py.
    """
    windows_platform = mock.Mock(system=lambda: 'Windows')
    with mock.patch('integrations.keymaps.base.platform', windows_platform), \
            mock.patch('utils.host_os.platform', windows_platform):
        yield
