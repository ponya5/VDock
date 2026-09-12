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

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # noqa: E402

_GUARDED_SETTINGS = (
    'REQUIRE_AUTH',
    'ALLOW_COMMAND_EXECUTION',
    'REQUIRE_COMMAND_CONFIRMATION',
    'ENABLE_PLUGINS',
    'RATELIMIT_ENABLED',
)


@pytest.fixture(autouse=True)
def restore_config():
    """Restore mutated Config flags after every test."""
    saved = {name: getattr(Config, name) for name in _GUARDED_SETTINGS}
    yield
    for name, value in saved.items():
        setattr(Config, name, value)
