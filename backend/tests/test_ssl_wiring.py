"""USE_SSL is wired into the server start (DL-147 D3)."""
from app import ssl_run_kwargs
from config import Config


def test_plain_http_by_default(monkeypatch):
    monkeypatch.setattr(Config, 'USE_SSL', False)
    assert ssl_run_kwargs() == {}


def test_https_context_when_enabled(monkeypatch):
    monkeypatch.setattr(Config, 'USE_SSL', True)
    monkeypatch.setattr(Config, 'SSL_CERT_PATH', 'c.pem')
    monkeypatch.setattr(Config, 'SSL_KEY_PATH', 'k.pem')
    assert ssl_run_kwargs() == {'ssl_context': ('c.pem', 'k.pem')}
