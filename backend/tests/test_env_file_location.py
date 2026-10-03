"""One env-file location (DL-146 Task 2.1).

Nothing here may touch the real backend/.env: every path is a tmp_path.
"""
import logging
import sys
from pathlib import Path

import pytest

import config as config_module
from config import backend_dir, env_file, migrate_legacy_env, read_env_key


def test_source_run_uses_backend_env(monkeypatch):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    assert env_file() == backend_dir() / '.env'


def test_frozen_run_uses_data_dir_env(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    assert env_file() == tmp_path / '.env'


def test_migration_copies_cwd_env_once(monkeypatch, tmp_path, caplog):
    data = tmp_path / 'data'
    install = tmp_path / 'install'
    install.mkdir()
    (install / '.env').write_text('GITHUB_TOKEN=ghp_legacy_value_123\n')
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('DATA_DIR', str(data))
    monkeypatch.chdir(install)

    with caplog.at_level(logging.INFO):
        assert migrate_legacy_env() is True

    assert read_env_key(data / '.env', 'GITHUB_TOKEN') == 'ghp_legacy_value_123'
    assert 'Migrated .env' in caplog.text
    assert 'ghp_legacy_value_123' not in caplog.text


def test_migration_never_overwrites_existing_target(monkeypatch, tmp_path):
    data = tmp_path / 'data'
    data.mkdir()
    (data / '.env').write_text('PORT=6000\n')
    install = tmp_path / 'install'
    install.mkdir()
    (install / '.env').write_text('PORT=5000\n')
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setenv('DATA_DIR', str(data))
    monkeypatch.chdir(install)

    assert migrate_legacy_env() is False
    assert read_env_key(data / '.env', 'PORT') == '6000'


def test_migration_is_a_noop_for_source_runs(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, 'frozen', raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.env').write_text('PORT=1\n')
    assert migrate_legacy_env() is False


def test_password_write_lands_in_env_file(monkeypatch, tmp_path):
    """routes/config.py must write through env_file(), not backend_dir()."""
    source = (Path(config_module.__file__).parent / 'routes' / 'config.py').read_text()
    assert "backend_dir() / '.env'" not in source
    assert 'env_file()' in source


def test_system_ports_route_writes_through_env_file():
    source = (Path(config_module.__file__).parent / 'routes' / 'system.py').read_text()
    assert "_backend_dir() / '.env'" not in source
