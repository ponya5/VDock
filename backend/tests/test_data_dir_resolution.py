"""Where VDock keeps its runtime data (settings, profiles, uploads).

An empty ``DATA_DIR=`` line used to resolve to the backend working directory,
which dumped runtime state (including the "Allow LAN" toggle) next to the code
where git picked it up. These tests pin the corrected resolution rules.
"""
from pathlib import Path

import pytest

from config import _resolve_data_dir


@pytest.fixture
def backend_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_unset_data_dir_uses_the_data_subfolder(monkeypatch, backend_dir: Path):
    monkeypatch.delenv('DATA_DIR', raising=False)

    assert _resolve_data_dir(backend_dir) == backend_dir / 'data'


@pytest.mark.parametrize('empty_value', ['', '   '])
def test_empty_data_dir_counts_as_unset(monkeypatch, backend_dir: Path, empty_value: str):
    monkeypatch.setenv('DATA_DIR', empty_value)

    assert _resolve_data_dir(backend_dir) == backend_dir / 'data'


def test_explicit_data_dir_is_used_as_is(monkeypatch, backend_dir: Path, tmp_path: Path):
    custom_dir = tmp_path / 'custom-location'
    monkeypatch.setenv('DATA_DIR', str(custom_dir))

    assert _resolve_data_dir(backend_dir) == custom_dir


@pytest.mark.parametrize('legacy_file', ['config.json', 'user_settings.json'])
def test_existing_state_in_backend_dir_is_kept_in_place(monkeypatch, backend_dir: Path, legacy_file: str):
    monkeypatch.delenv('DATA_DIR', raising=False)
    (backend_dir / legacy_file).write_text('{}')

    assert _resolve_data_dir(backend_dir) == backend_dir


def test_existing_profiles_in_backend_dir_are_kept_in_place(monkeypatch, backend_dir: Path):
    monkeypatch.delenv('DATA_DIR', raising=False)
    (backend_dir / 'profiles').mkdir()
    (backend_dir / 'profiles' / 'my-deck.json').write_text('{}')

    assert _resolve_data_dir(backend_dir) == backend_dir


def test_data_subfolder_wins_once_it_holds_state(monkeypatch, backend_dir: Path):
    monkeypatch.delenv('DATA_DIR', raising=False)
    (backend_dir / 'config.json').write_text('{}')
    (backend_dir / 'data').mkdir()
    (backend_dir / 'data' / 'config.json').write_text('{}')

    assert _resolve_data_dir(backend_dir) == backend_dir / 'data'
