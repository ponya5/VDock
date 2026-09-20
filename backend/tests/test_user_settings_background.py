"""The unified `background` key must round-trip, and the legacy pair must not.

Feature: unified-background. The two legacy keys were mutually exclusive and
are migrated client-side; persisting them again would let a stale value
resurface after the migration had already run.
"""
import pytest

from app import app
from config import Config


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_DIR', tmp_path)
    import routes.user_settings as us
    monkeypatch.setattr(us, 'USER_SETTINGS_FILE', tmp_path / 'user_settings.json')
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_background_round_trips(client):
    client.put('/api/user-settings', json={'settings': {'background': 'aurora'}})
    stored = client.get('/api/user-settings').get_json()
    assert stored['settings']['background'] == 'aurora'


def test_legacy_keys_are_not_persisted(client):
    client.put('/api/user-settings', json={'settings': {
        'background': 'aurora',
        'backgroundPreference': 'silk',
        'dashboardBackground': 'starfield',
    }})
    stored = client.get('/api/user-settings').get_json()['settings']
    assert 'backgroundPreference' not in stored
    assert 'dashboardBackground' not in stored
