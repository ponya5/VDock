"""toastLevelMigrated must round-trip through the user-settings allowlist.

DL-076 follow-up: the marker rides every settings payload; if the backend
dropped it, each device would re-run the 'all' → 'errors-only' migration and
a deliberate "All" pick could never stick.
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


def test_toast_level_marker_round_trips(client):
    client.put('/api/user-settings', json={'settings': {
        'toastLevel': 'all',
        'toastLevelMigrated': True,
    }})
    stored = client.get('/api/user-settings').get_json()['settings']
    assert stored['toastLevel'] == 'all'
    assert stored['toastLevelMigrated'] is True
