"""Atomic writes + daily profile backup (DL-146 Task 2.5)."""
import json
import os
from datetime import date, timedelta

import pytest

import config as config_module
from utils import atomic
from utils.atomic import atomic_write_text
from utils.file_manager import FileManager


def test_atomic_write_creates_file_and_leaves_no_tmp(tmp_path):
    target = tmp_path / 'sub' / 'a.json'
    atomic_write_text(target, '{"a": 1}')
    assert target.read_text(encoding='utf-8') == '{"a": 1}'
    assert not list(target.parent.glob('*.tmp'))


def test_crash_during_replace_keeps_original_and_cleans_tmp(tmp_path, monkeypatch):
    target = tmp_path / 'a.json'
    target.write_text('ORIGINAL', encoding='utf-8')

    def boom(*_a, **_k):
        raise OSError('simulated crash')

    monkeypatch.setattr(atomic.os, 'replace', boom)
    with pytest.raises(OSError):
        atomic_write_text(target, 'NEW')
    assert target.read_text(encoding='utf-8') == 'ORIGINAL'
    assert not list(tmp_path.glob('*.tmp'))

    monkeypatch.undo()
    atomic_write_text(target, 'NEW')
    assert target.read_text(encoding='utf-8') == 'NEW'
    assert not list(tmp_path.glob('*.tmp'))


def test_replace_retries_permission_error(tmp_path, monkeypatch):
    target = tmp_path / 'a.txt'
    real_replace = os.replace
    calls = {'n': 0}

    def flaky(src, dst):
        calls['n'] += 1
        if calls['n'] < 3:
            raise PermissionError('locked by AV')
        real_replace(src, dst)

    monkeypatch.setattr(atomic.os, 'replace', flaky)
    monkeypatch.setattr(atomic, '_REPLACE_DELAY_S', 0)
    atomic_write_text(target, 'ok')
    assert target.read_text() == 'ok'
    assert calls['n'] == 3


def test_save_json_output_format_is_unchanged(tmp_path):
    data = {'name': 'caf\u00e9', 'nested': {'a': [1, 2]}}
    target = tmp_path / 'p.json'
    assert FileManager.save_json(target, data) is True
    assert target.read_text(encoding='utf-8') == json.dumps(data, indent=2, ensure_ascii=False)


def test_save_json_failure_returns_false_and_keeps_original(tmp_path, monkeypatch):
    target = tmp_path / 'p.json'
    FileManager.save_json(target, {'v': 1})
    monkeypatch.setattr(atomic.os, 'replace', lambda *a, **k: (_ for _ in ()).throw(OSError('x')))
    assert FileManager.save_json(target, {'v': 2}) is False
    assert json.loads(target.read_text(encoding='utf-8')) == {'v': 1}


def test_save_config_is_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module.Config, 'DATA_DIR', tmp_path)
    config_module.Config.save_config({'port': 5000})
    assert json.loads((tmp_path / 'config.json').read_text()) == {'port': 5000}
    assert not list(tmp_path.glob('*.tmp'))


def test_write_env_keys_is_atomic(tmp_path):
    env = tmp_path / '.env'
    config_module.write_env_keys(env, {'A': '1'})
    assert env.read_text() == 'A=1\n'
    assert not list(tmp_path.glob('*.tmp'))


# --- daily profile backup ------------------------------------------------

def _seed_profiles(data_dir):
    profiles = data_dir / 'profiles'
    profiles.mkdir(parents=True)
    (profiles / 'one.json').write_text('{"id": "one"}', encoding='utf-8')
    (profiles / 'two.json').write_text('{"id": "two"}', encoding='utf-8')
    return profiles


def test_backup_created_once_per_day(tmp_path):
    _seed_profiles(tmp_path)
    assert FileManager.backup_profiles(tmp_path) is True
    assert FileManager.backup_profiles(tmp_path) is False  # same day: no-op
    folders = list((tmp_path / 'backups').iterdir())
    assert len(folders) == 1
    assert folders[0].name == f'profiles-{date.today():%Y%m%d}'
    assert sorted(p.name for p in folders[0].iterdir()) == ['one.json', 'two.json']


def test_backup_prunes_to_newest_seven(tmp_path):
    _seed_profiles(tmp_path)
    backups = tmp_path / 'backups'
    backups.mkdir()
    for i in range(1, 10):
        old = backups / f'profiles-{date.today() - timedelta(days=i):%Y%m%d}'
        old.mkdir()
    FileManager.backup_profiles(tmp_path)
    names = sorted(p.name for p in backups.iterdir())
    assert len(names) == 7
    assert f'profiles-{date.today():%Y%m%d}' in names
    # the oldest ones were removed
    assert f'profiles-{date.today() - timedelta(days=9):%Y%m%d}' not in names


def test_backup_failure_never_fails_the_save(tmp_path, monkeypatch):
    profiles = _seed_profiles(tmp_path)
    monkeypatch.setattr('utils.file_manager.shutil.copy2',
                        lambda *a, **k: (_ for _ in ()).throw(OSError('disk full')))
    assert FileManager.backup_profiles(tmp_path) is False
    target = profiles / 'one.json'
    assert FileManager.save_profile(target, {'id': 'one', 'v': 2}) is True
    assert json.loads(target.read_text(encoding='utf-8'))['v'] == 2


def test_save_profile_backs_up_before_overwriting(tmp_path):
    profiles = _seed_profiles(tmp_path)
    assert FileManager.save_profile(profiles / 'one.json', {'id': 'one', 'v': 2}) is True
    backup = tmp_path / 'backups' / f'profiles-{date.today():%Y%m%d}' / 'one.json'
    assert json.loads(backup.read_text(encoding='utf-8')) == {'id': 'one'}
