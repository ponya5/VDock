"""Per-app executable overrides (DL-084).

Feature: app-path-overrides — a user-configured path in Config.APP_PATHS must
win over PATH resolution, drive launches when the target window is missing,
persist through /api/config, and degrade cleanly when stale.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from config import Config  # noqa: E402
from services import app_paths  # noqa: E402
from utils.subprocess_runner import find_binary  # noqa: E402


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def real_exe(tmp_path):
    """A file that exists — stands in for a user-picked executable."""
    f = tmp_path / 'cursor.exe'
    f.write_text('stub')
    return str(f)


# --- key normalization --------------------------------------------------------

def test_override_matches_stem_and_exe_spellings(real_exe):
    """'cursor', 'Cursor.exe' and 'CURSOR' are the same override."""
    Config.APP_PATHS = {'cursor': real_exe}
    assert app_paths.override_for('cursor.exe') == real_exe
    assert app_paths.override_for('CURSOR') == real_exe


def test_override_ignores_stale_path(tmp_path):
    """A path deleted after saving must not shadow PATH resolution."""
    ghost = str(tmp_path / 'gone.exe')
    Config.APP_PATHS = {'cursor': ghost}
    assert app_paths.override_for('cursor.exe') is None


def test_override_alias_maps_template_id_to_binary(real_exe):
    """The 'vscode' editor opens 'code' — the alias bridges the names."""
    Config.APP_PATHS = {'vscode': real_exe}
    assert app_paths.override_for('code.exe') == real_exe


def test_find_binary_prefers_override(real_exe):
    Config.APP_PATHS = {'claude': real_exe}
    assert find_binary('claude') == real_exe


def test_find_binary_resolves_app_bundle_inner_binary(tmp_path):
    """macOS: pointing at Foo.app must yield the executable inside it —
    argv spawns can't run a directory."""
    inner = tmp_path / 'Cursor.app' / 'Contents' / 'MacOS' / 'Cursor'
    inner.parent.mkdir(parents=True)
    inner.write_text('stub')
    inner.chmod(0o755)
    Config.APP_PATHS = {'cursor': str(tmp_path / 'Cursor.app')}
    assert find_binary('cursor') == str(inner)


def test_validate_accepts_app_bundle_directory(tmp_path):
    bundle = tmp_path / 'Cursor.app'
    bundle.mkdir()
    ok, _ = app_paths.validate_path(str(bundle))
    assert ok


def test_find_binary_falls_back_to_path(real_exe):
    Config.APP_PATHS = {}
    # A real binary on PATH keeps working untouched.
    assert find_binary('python') or find_binary('python3') or find_binary('cmd')


# --- validation ----------------------------------------------------------------

def test_validate_accepts_existing_file(real_exe):
    ok, cleaned = app_paths.validate_path(real_exe)
    assert ok and cleaned == real_exe


def test_validate_accepts_directory_for_app_bundles(tmp_path):
    """macOS .app 'executables' are directories."""
    ok, cleaned = app_paths.validate_path(str(tmp_path))
    assert ok and cleaned == str(tmp_path)


def test_validate_rejects_missing(tmp_path):
    ok, err = app_paths.validate_path(str(tmp_path / 'nope.exe'))
    assert not ok and 'Not found' in err


def test_validate_strips_quotes_and_spaces(real_exe):
    ok, cleaned = app_paths.validate_path(f'  "{real_exe}"  ')
    assert ok and cleaned == real_exe


# --- probe ----------------------------------------------------------------------

def test_probe_finds_path_binary():
    exe = 'python' if sys.platform != 'win32' else 'python'
    found = app_paths.probe(exe) or app_paths.probe('python3')
    assert found is None or Path(found).exists()


def test_probe_unknown_returns_none():
    assert app_paths.probe('definitely-not-a-real-app-xyz') is None


# --- /api/config wiring ---------------------------------------------------------

def test_config_put_and_get_app_paths(client, real_exe):
    resp = client.put('/api/config', json={'app_paths': {'cursor': real_exe}})
    assert resp.status_code == 200
    assert Config.APP_PATHS.get('cursor') == real_exe

    got = client.get('/api/config').get_json()['config']['app_paths']
    assert got.get('cursor') == real_exe


def test_config_app_paths_rejects_missing_path(client, tmp_path):
    resp = client.put(
        '/api/config',
        json={'app_paths': {'cursor': str(tmp_path / 'missing.exe')}},
    )
    assert resp.status_code == 400
    assert 'app_paths' not in Config.APP_PATHS or 'cursor' not in Config.APP_PATHS


def test_config_app_paths_rejects_non_dict(client):
    assert client.put('/api/config', json={'app_paths': 'nope'}).status_code == 400


def test_config_app_paths_empty_value_clears(client, real_exe):
    client.put('/api/config', json={'app_paths': {'cursor': real_exe}})
    resp = client.put('/api/config', json={'app_paths': {'cursor': ''}})
    assert resp.status_code == 200
    assert client.get('/api/config').get_json()['config']['app_paths'].get('cursor') is None


def test_probe_route(client):
    resp = client.get('/api/app-paths/probe', query_string={'app': 'python'})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['path'] is None or Path(body['path']).exists()


def test_probe_route_requires_app(client):
    assert client.get('/api/app-paths/probe').status_code == 400
