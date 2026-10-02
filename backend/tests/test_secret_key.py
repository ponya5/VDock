"""SECRET_KEY must never be a published placeholder (DL-146 Phase 1).

``backend/.env.example`` used to ship a public placeholder and setup copied it
verbatim, so JWTs were signed with a key anyone could read on GitHub. The
startup guard replaces weak keys with a generated one and persists it.
"""
import logging

import pytest

import config as config_module
from config import (
    Config,
    KNOWN_PLACEHOLDER_SECRETS,
    env_file,
    is_weak_secret_key,
    read_env_key,
)

PLACEHOLDER = 'your-secret-key-here-change-this-to-random-string'
STRONG = 'a1' * 32  # 64 hex chars


@pytest.fixture
def env_path(tmp_path, monkeypatch):
    path = tmp_path / '.env'
    monkeypatch.setattr(config_module, 'env_file', lambda: path)
    saved = Config.SECRET_KEY
    yield path
    Config.SECRET_KEY = saved


@pytest.mark.parametrize('key', ['', None, 'short', PLACEHOLDER, 'x' * 31] + sorted(KNOWN_PLACEHOLDER_SECRETS))
def test_weak_keys_detected(key):
    assert is_weak_secret_key(key)


def test_strong_key_not_weak():
    assert not is_weak_secret_key(STRONG)


def test_placeholder_is_replaced_and_persisted(env_path, monkeypatch):
    env_path.write_text(f'PORT=5000\nSECRET_KEY={PLACEHOLDER}\n')
    monkeypatch.setenv('SECRET_KEY', PLACEHOLDER)

    assert Config.ensure_strong_secret_key() is True

    persisted = read_env_key(env_path, 'SECRET_KEY')
    assert persisted and persisted != PLACEHOLDER
    assert len(persisted) == 64
    assert Config.SECRET_KEY == persisted
    assert 'PORT=5000' in env_path.read_text()  # unrelated keys survive


def test_missing_key_is_generated_and_persisted(env_path, monkeypatch):
    monkeypatch.setenv('SECRET_KEY', '')  # empty == unset; monkeypatch restores it

    assert Config.ensure_strong_secret_key() is True
    assert len(read_env_key(env_path, 'SECRET_KEY')) == 64


def test_strong_key_is_left_untouched(env_path, monkeypatch):
    env_path.write_text(f'SECRET_KEY={STRONG}\n')
    monkeypatch.setenv('SECRET_KEY', STRONG)
    Config.SECRET_KEY = STRONG
    before = env_path.read_text()

    assert Config.ensure_strong_secret_key() is False

    assert Config.SECRET_KEY == STRONG
    assert env_path.read_text() == before


def test_write_failure_keeps_in_memory_key_and_warns(env_path, monkeypatch, caplog):
    monkeypatch.setenv('SECRET_KEY', PLACEHOLDER)

    def boom(*_a, **_k):
        raise OSError('read-only')

    monkeypatch.setattr(config_module, 'write_env_keys', boom)
    with caplog.at_level(logging.WARNING):
        assert Config.ensure_strong_secret_key() is True

    assert not is_weak_secret_key(Config.SECRET_KEY)
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_log_output_never_contains_the_key(env_path, monkeypatch, caplog):
    monkeypatch.setenv('SECRET_KEY', PLACEHOLDER)
    with caplog.at_level(logging.DEBUG):
        Config.ensure_strong_secret_key()

    assert Config.SECRET_KEY not in caplog.text
    assert read_env_key(env_path, 'SECRET_KEY') not in caplog.text


def test_token_survives_restart_with_persisted_key(env_path, monkeypatch):
    from auth.auth_manager import AuthManager  # noqa: PLC0415

    monkeypatch.setenv('SECRET_KEY', PLACEHOLDER)
    Config.ensure_strong_secret_key()
    token = AuthManager.generate_token({'authenticated': True})

    # "Restart": the next boot reads SECRET_KEY back from the env file.
    Config.SECRET_KEY = read_env_key(env_path, 'SECRET_KEY')
    assert AuthManager.verify_token(token)


def test_env_file_is_backend_env_for_source_runs(monkeypatch):
    monkeypatch.delattr('sys.frozen', raising=False)
    assert env_file() == config_module.backend_dir() / '.env'


def test_env_file_is_data_dir_env_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.frozen', True, raising=False)
    monkeypatch.setenv('DATA_DIR', str(tmp_path))
    assert env_file() == tmp_path / '.env'
