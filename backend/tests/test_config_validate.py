"""Boot validator + configuration report (DL-146 Task 2.3)."""
import logging

import pytest

from config import Config

ATTRS = (
    'DEBUG', 'ALLOW_LAN', 'HOST', 'PORT', 'REQUIRE_AUTH', 'AUTH_PASSWORD',
    'USE_SSL', 'SSL_CERT_PATH', 'SSL_KEY_PATH',
)


@pytest.fixture(autouse=True)
def restore_config():
    saved = {a: getattr(Config, a) for a in ATTRS}
    Config.DEBUG = False
    Config.ALLOW_LAN = False
    Config.HOST = '127.0.0.1'
    Config.REQUIRE_AUTH = False
    Config.AUTH_PASSWORD = ''
    Config.USE_SSL = False
    yield
    for attr, value in saved.items():
        setattr(Config, attr, value)


def test_debug_with_lan_is_refused():
    Config.DEBUG = True
    Config.ALLOW_LAN = True
    with pytest.raises(RuntimeError, match='DEBUG'):
        Config.validate()


def test_debug_with_non_loopback_host_is_refused():
    Config.DEBUG = True
    Config.HOST = '0.0.0.0'
    with pytest.raises(RuntimeError, match='DEBUG'):
        Config.validate()


def test_debug_on_loopback_is_fine():
    Config.DEBUG = True
    Config.validate()


def test_lan_without_debug_is_fine():
    Config.ALLOW_LAN = True
    Config.validate()


def test_ssl_with_missing_files_names_the_path(tmp_path):
    Config.USE_SSL = True
    Config.SSL_CERT_PATH = str(tmp_path / 'nope-cert.pem')
    Config.SSL_KEY_PATH = str(tmp_path / 'nope-key.pem')
    with pytest.raises(RuntimeError, match='nope-cert.pem'):
        Config.validate()


def test_ssl_with_files_present_is_fine(tmp_path):
    cert, key = tmp_path / 'c.pem', tmp_path / 'k.pem'
    cert.write_text('x')
    key.write_text('x')
    Config.USE_SSL = True
    Config.SSL_CERT_PATH, Config.SSL_KEY_PATH = str(cert), str(key)
    Config.validate()


@pytest.mark.parametrize('pw', ['ChangeThisToAStrongPassword123!', 'your-secure-password-here', 'admin'])
def test_auth_with_example_password_is_refused(pw):
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = pw
    with pytest.raises(RuntimeError, match='example'):
        Config.validate()


def test_example_password_is_fine_while_auth_is_off():
    Config.AUTH_PASSWORD = 'admin'
    Config.validate()


def test_report_lines_describe_bind_auth_and_integrations():
    lines = Config.report()
    joined = '\n'.join(lines)
    assert lines[0].startswith('Bind: 127.0.0.1:')
    assert '(LAN off)' in lines[0]
    assert any(line.startswith('Auth: off') for line in lines)
    assert 'GitHub token' in joined and 'Anthropic key' in joined


def test_report_shows_lan_on_and_auth_on():
    Config.ALLOW_LAN = True
    Config.REQUIRE_AUTH = True
    Config.AUTH_PASSWORD = 'x-real-password'
    lines = Config.report()
    assert '(LAN on)' in lines[0]
    assert any(line.startswith('Auth: on') for line in lines)


def test_lan_without_auth_logs_a_warning(caplog):
    Config.ALLOW_LAN = True
    with caplog.at_level(logging.WARNING, logger='vdock.config'):
        Config.report()
    assert any(
        r.levelno == logging.WARNING and 'Allow LAN is on without a deck password' in r.getMessage()
        for r in caplog.records
    )


def test_no_lan_warning_when_local_only(caplog):
    with caplog.at_level(logging.WARNING, logger='vdock.config'):
        Config.report()
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_report_never_contains_secret_values(monkeypatch, caplog):
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_test1234567890abcdefSECRET')
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'sk-ant-test-SECRETVALUE')
    monkeypatch.setenv('WEATHERAPI_KEY', 'weather-SECRETVALUE')
    Config.AUTH_PASSWORD = 'pw-SECRETVALUE'
    Config.REQUIRE_AUTH = True
    with caplog.at_level(logging.DEBUG):
        lines = Config.report()
    blob = '\n'.join(lines) + caplog.text
    for secret in ('ghp_test', 'sk-ant', 'weather-SECRET', 'pw-SECRET'):
        assert secret not in blob
    assert 'GitHub token ✓' in blob
