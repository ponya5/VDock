"""Every key in the frontend's settings payload must survive PUT/GET.

DL-124: `_sanitize_user_settings` allowlists keys server-side; DL-119..123
added settings that were never allowlisted, so server sync silently dropped
them (spectrum saver reverted to the widget dashboard on reload, the MCP
toggle never persisted, waiting-dock/glow prefs vanished). This round-trips
the complete `buildSettingsPayload()` key set from stores/settings.ts — when
a new persisted key is added frontend-side, add it here.
"""
import pytest

from app import app
from config import Config

# Mirror of PersistedUserSettings / buildSettingsPayload() (stores/settings.ts).
# Values match each key's type; the test asserts presence, not semantics.
FULL_SETTINGS_PAYLOAD = {
    'buttonSize': 1.0,
    'buttonTransparency': 0,
    'showLabels': True,
    'showTooltips': True,
    'animationsEnabled': True,
    'editModeWiggle': False,
    'tiltEffectEnabled': False,
    'dockedSidebarEnabled': True,
    'dockedSidebarWidth': 190,
    'dockedButtonHeight': 84,
    'background': 'default',
    'uiBrightness': 100,
    'toastLevel': 'errors-only',
    'toastLevelMigrated': True,
    'touchMode': 'normal',
    'minimumTouchTargetSize': 44,
    'defaultGridRows': 3,
    'defaultGridCols': 5,
    'openSettingsInNewTab': False,
    'autoCloseLauncher': True,
    'recentActions': ['media_play_pause'],
    'weatherLocationMode': 'auto',
    'weatherManualCity': '',
    'screensaverTimeout': 120,
    'buttonDefaultAnimation': 'none',
    'buttonDefaultIconLoop': 'none',
    'buttonDefaultEffect': 'none',
    'screensaverWidgets': ['weather', 'news', 'market'],
    'screensaverClockEnabled': True,
    'screensaverWeatherSize': 1.0,
    'newsApiKey': '',
    'newsFeeds': '',
    'sportsFeeds': '',
    'newsRotateSeconds': 30,
    'marketApiKey': '',
    'marketTickers': '',
    'worldClockTimezones': '',
    'screensaverWidgetSize': 1.0,
    'screensaverBackground': 'default',
    'screensaverStyle': 'spectrum',
    'screensaverShuffleMinutes': 5,
    'spectrumSkin': 'aurora',
    'spectrumShuffle': True,
    'spectrumShuffleMinutes': 5,
    'spectrumMediaBar': True,
    'dashboardFont': 'mono',
    'appScanningEnabled': True,
    'agentAlertsEnabled': True,
    'agentWaitingGlowEnabled': True,
    'agentWaitingGlowStyle': 'pulse',
    'agentWaitingDockEnabled': True,
    'mcpEnabled': False,
    'tutorialCompleted': True,
    'activeProfileId': 'abc123',
    'pressSoundEnabled': True,
    'pressSoundStyle': 'click',
    'screensaverLayout': {'order': [], 'hidden': []},
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_DIR', tmp_path)
    import routes.user_settings as us
    monkeypatch.setattr(us, 'USER_SETTINGS_FILE', tmp_path / 'user_settings.json')
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


def test_full_settings_payload_round_trips(client):
    put = client.put('/api/user-settings', json={'settings': FULL_SETTINGS_PAYLOAD})
    assert put.status_code == 200
    returned = put.get_json()['settings']
    missing = set(FULL_SETTINGS_PAYLOAD) - set(returned)
    assert not missing, f'server dropped settings keys on PUT: {sorted(missing)}'

    stored = client.get('/api/user-settings').get_json()['settings']
    missing_after_reload = set(FULL_SETTINGS_PAYLOAD) - set(stored)
    assert not missing_after_reload, (
        f'server dropped settings keys on GET: {sorted(missing_after_reload)}'
    )
    for key, value in FULL_SETTINGS_PAYLOAD.items():
        assert stored[key] == value, f'{key} changed across the round-trip'


def test_partial_put_merges_into_existing_settings(client):
    """DL-138: clients send only changed keys — a partial PUT must merge
    into the stored file, never replace it, so untouched settings survive
    and a stale client cannot wipe fields it didn't send."""
    client.put('/api/user-settings', json={'settings': FULL_SETTINGS_PAYLOAD})

    patch = client.put('/api/user-settings', json={'settings': {'spectrumSkin': 'ember'}})
    assert patch.status_code == 200

    stored = client.get('/api/user-settings').get_json()['settings']
    assert stored['spectrumSkin'] == 'ember'
    # Every unsent key is still there with its earlier value.
    for key, value in FULL_SETTINGS_PAYLOAD.items():
        if key == 'spectrumSkin':
            continue
        assert stored[key] == value, f'{key} lost on partial PUT'
