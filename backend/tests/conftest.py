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
from pathlib import Path

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
    """Restore mutated Config flags after every test."""
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
