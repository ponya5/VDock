"""User UI settings persistence (background, layout, touch mode, etc.)."""
import json
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from config import Config
from auth import require_auth

user_settings_bp = Blueprint('user_settings', __name__)

USER_SETTINGS_FILE: Path = Config.DATA_DIR / 'user_settings.json'

ALLOWED_USER_SETTING_KEYS = {
    'buttonSize',
    'buttonTransparency',
    'showLabels',
    'showTooltips',
    'animationsEnabled',
    'editModeWiggle',
    'tiltEffectEnabled',
    'dockedSidebarEnabled',
    'dockedSidebarWidth',
    'dockedButtonHeight',
    'buttonDefaultAnimation',
    'buttonDefaultIconLoop',
    'buttonDefaultEffect',
    'background',
    'uiBrightness',
    'toastLevel',
    # DL-076 follow-up marker: separates inherited 'all' from a deliberate
    # post-migration "All" pick so the one-shot migration fires only once.
    'toastLevelMigrated',
    'touchMode',
    'minimumTouchTargetSize',
    'defaultGridRows',
    'defaultGridCols',
    'openSettingsInNewTab',
    'recentActions',
    'weatherLocationMode',
    'weatherManualCity',
    'screensaverTimeout',
    'autoCloseLauncher',
    # Screensaver widgets. 'screensaverWidgets' was read by ScreenSaver.vue but
    # never allowlisted here, so the user's choice was dropped on every save.
    'screensaverWidgets',
    # The clock is toggleable via its own flag rather than a widgets-array
    # entry — saved lists predate 'clock', so gating on the array would hide
    # the clock for every existing user (DL-098).
    'screensaverClockEnabled',
    'screensaverWeatherSize',
    'newsFeeds',
    'sportsFeeds',
    'newsRotateSeconds',
    'newsApiKey',
    'worldClockTimezones',
    'marketCoins',
    'marketTickers',
    'marketApiKey',
    'screensaverWidgetSize',
    'screensaverBackground',
    'screensaverLayout',
    # DL-142: independent widget layout for the Spectrum saver.
    'screensaverSpectrumLayout',
    # DL-123: fullscreen spectrum saver — style, skin, shuffle, media bar.
    # DL-133: + the Shuffle type's rotation cadence.
    'screensaverStyle',
    'screensaverShuffleMinutes',
    'spectrumSkin',
    'spectrumShuffle',
    'spectrumShuffleMinutes',
    'spectrumMediaBar',
    # DL-135: info widgets can overlay the spectrum stage.
    'screensaverSpectrumWidgets',
    'dashboardFont',
    'tutorialCompleted',
    # Id of the profile most recently loaded on any window/device — lets a
    # second device (e.g. a phone connecting for the first time) land on
    # the same profile instead of guessing. See frontend DL-061 follow-up.
    'activeProfileId',
    'appScanningEnabled',
    'agentAlertsEnabled',
    # DL-119: waiting glow on/off + style, and the pinned waiting-dock chips.
    'agentWaitingGlowEnabled',
    'agentWaitingGlowStyle',
    'agentWaitingDockEnabled',
    # DL-121: MCP server on/off (routes/mcp.py reads it back per request).
    'mcpEnabled',
    'pressSoundEnabled',
    'pressSoundStyle',
}


def _load_user_settings_file() -> Dict[str, Any]:
    if not USER_SETTINGS_FILE.exists():
        return {}

    try:
        with open(USER_SETTINGS_FILE, 'r', encoding='utf-8') as settings_file:
            stored_settings = json.load(settings_file)
            if isinstance(stored_settings, dict):
                return stored_settings
    except (json.JSONDecodeError, OSError):
        pass

    return {}


def _save_user_settings_file(settings: Dict[str, Any]) -> None:
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USER_SETTINGS_FILE, 'w', encoding='utf-8') as settings_file:
        json.dump(settings, settings_file, indent=2)


def _sanitize_user_settings(raw_settings: Dict[str, Any]) -> Dict[str, Any]:
    sanitized_settings: Dict[str, Any] = {}

    for key, value in raw_settings.items():
        if key not in ALLOWED_USER_SETTING_KEYS:
            continue
        sanitized_settings[key] = value

    return sanitized_settings


@user_settings_bp.route('/api/user-settings', methods=['GET'])
@require_auth
def get_user_settings():
    """Return persisted UI settings for the local VDock install."""
    settings = _load_user_settings_file()
    return jsonify({'success': True, 'settings': settings})


@user_settings_bp.route('/api/user-settings', methods=['PUT'])
@require_auth
def update_user_settings():
    """Persist UI settings to disk.

    DL-138: clients send only the keys they changed (per-field last-write-
    wins), so the incoming payload merges into the stored file rather than
    replacing it — a partial write must not drop every unsent key, and a
    stale client's save can no longer resurrect old values for untouched
    fields.
    """
    payload = request.get_json(silent=True) or {}
    incoming_settings = payload.get('settings')

    if not isinstance(incoming_settings, dict):
        return jsonify({'success': False, 'error': 'settings object is required'}), 400

    sanitized_settings = _sanitize_user_settings(incoming_settings)
    merged_settings = _load_user_settings_file()
    merged_settings.update(sanitized_settings)
    _save_user_settings_file(merged_settings)

    return jsonify({'success': True, 'settings': merged_settings})
