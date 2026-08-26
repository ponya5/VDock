"""User UI settings persistence (background, layout, touch mode, etc.)."""
import json
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from config import Config

user_settings_bp = Blueprint('user_settings', __name__)

USER_SETTINGS_FILE: Path = Config.DATA_DIR / 'user_settings.json'

ALLOWED_USER_SETTING_KEYS = {
    'buttonSize',
    'showLabels',
    'showTooltips',
    'animationsEnabled',
    'tiltEffectEnabled',
    'dockedSidebarEnabled',
    'dockedSidebarWidth',
    'dashboardBackground',
    'backgroundPreference',
    'uiBrightness',
    'toastLevel',
    'touchMode',
    'minimumTouchTargetSize',
    'defaultGridRows',
    'defaultGridCols',
    'startOnBoot',
    'openSettingsInNewTab',
    'recentActions',
    'weatherLocationMode',
    'weatherManualCity',
    'screensaverTimeout',
    'autoCloseLauncher',
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
def get_user_settings():
    """Return persisted UI settings for the local VDock install."""
    settings = _load_user_settings_file()
    return jsonify({'success': True, 'settings': settings})


@user_settings_bp.route('/api/user-settings', methods=['PUT'])
def update_user_settings():
    """Persist UI settings to disk."""
    payload = request.get_json(silent=True) or {}
    incoming_settings = payload.get('settings')

    if not isinstance(incoming_settings, dict):
        return jsonify({'success': False, 'error': 'settings object is required'}), 400

    sanitized_settings = _sanitize_user_settings(incoming_settings)
    _save_user_settings_file(sanitized_settings)

    return jsonify({'success': True, 'settings': sanitized_settings})
