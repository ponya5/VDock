"""Socket.IO origins follow the scheme the backend serves (USE_SSL -> https)."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config  # noqa: E402


def test_http_origins_by_default(monkeypatch):
    monkeypatch.setattr(Config, 'USE_SSL', False)
    monkeypatch.setattr(Config, 'ALLOW_LAN', False)
    origins = Config.socket_origins()
    assert f'http://127.0.0.1:{Config.PORT}' in origins
    assert f'https://127.0.0.1:{Config.PORT}' not in origins


def test_https_origins_with_ssl(monkeypatch):
    monkeypatch.setattr(Config, 'USE_SSL', True)
    monkeypatch.setattr(Config, 'ALLOW_LAN', True)
    monkeypatch.setattr(Config, 'DECK_HOST', 'deck.local')
    origins = Config.socket_origins()
    assert f'https://localhost:{Config.PORT}' in origins
    assert f'https://deck.local:{Config.PORT}' in origins
    assert f'http://deck.local:{Config.PORT}' not in origins
