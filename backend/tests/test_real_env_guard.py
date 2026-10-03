"""The conftest guard really catches a write to the real backend/.env."""
import pytest

from tests import conftest as guard


def test_guard_restores_and_fails_when_real_env_is_modified(tmp_path, monkeypatch):
    fake_real = tmp_path / '.env'
    fake_real.write_text('SECRET_KEY=original\n')
    monkeypatch.setattr(guard, '_REAL_ENV', fake_real)

    gen = guard.real_env_file_is_never_written.__wrapped__() \
        if hasattr(guard.real_env_file_is_never_written, '__wrapped__') else None
    if gen is None:
        pytest.skip('fixture wrapper not introspectable on this pytest version')
    next(gen)
    fake_real.write_text('SECRET_KEY=clobbered\n')
    with pytest.raises(pytest.fail.Exception):
        next(gen)
    assert fake_real.read_text() == 'SECRET_KEY=original\n'
