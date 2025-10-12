"""System control actions (volume, media, brightness)."""
import platform
from typing import Dict, Any
from .base_action import BaseAction, ActionResult

# Platform-specific imports
_system = platform.system()


class SystemAction(BaseAction):
    """Controls system functions like volume and media."""

    VALID_ACTIONS = [
        'volume_up', 'volume_down', 'volume_mute', 'volume_set',
        'media_play_pause', 'media_next', 'media_previous', 'media_stop'
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize system action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that action type is provided and valid."""
        action = self.config.get('action')
        return action in self.VALID_ACTIONS

    def _volume_up(self) -> ActionResult:
        """Increase volume using keyboard shortcut."""
        from .hotkey_action import HotkeyAction
        hotkey_config = {'keys': ['volume_up']}
        hotkey_action = HotkeyAction(hotkey_config)
        return hotkey_action.execute()

    def _volume_down(self) -> ActionResult:
        """Decrease volume using keyboard shortcut."""
        from .hotkey_action import HotkeyAction
        hotkey_config = {'keys': ['volume_down']}
        hotkey_action = HotkeyAction(hotkey_config)
        return hotkey_action.execute()

    def _volume_mute(self) -> ActionResult:
        """Toggle mute using keyboard shortcut."""
        from .hotkey_action import HotkeyAction
        hotkey_config = {'keys': ['volume_mute']}
        hotkey_action = HotkeyAction(hotkey_config)
        return hotkey_action.execute()

    def _volume_set(self) -> ActionResult:
        """Set volume to specific level (not supported via keyboard)."""
        return ActionResult(
            False,
            'Volume set requires direct audio control. '
            'Use volume_up/down instead.'
        )

    def _media_control(self, action: str) -> ActionResult:
        """Control media playback."""
        from .hotkey_action import HotkeyAction

        media_keys = {
            'media_play_pause': ['media_play_pause'],
            'media_next': ['media_next_track'],
            'media_previous': ['media_previous_track'],
            'media_stop': ['media_stop']
        }

        if action not in media_keys:
            return ActionResult(False, f'Unknown media action: {action}')

        hotkey_config = {'keys': media_keys[action]}
        hotkey_action = HotkeyAction(hotkey_config)
        return hotkey_action.execute()

    def execute(self) -> ActionResult:
        """Execute the system action."""
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: Valid action required'
            )

        action = self.config['action']

        if action == 'volume_up':
            return self._volume_up()
        elif action == 'volume_down':
            return self._volume_down()
        elif action == 'volume_mute':
            return self._volume_mute()
        elif action == 'volume_set':
            return self._volume_set()
        elif action.startswith('media_'):
            return self._media_control(action)
        else:
            return ActionResult(False, f'Unknown action: {action}')

    def get_description(self) -> str:
        """Get action description."""
        action = self.config.get('action', 'unknown')
        return f"System: {action.replace('_', ' ').title()}"
