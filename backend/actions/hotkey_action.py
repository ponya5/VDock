"""Hotkey sending action."""
import time
from typing import Dict, Any
from .base_action import BaseAction, ActionResult

try:
    from pynput.keyboard import Controller, Key
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    # Create dummy Key class for when pynput is not available
    class Key:
        ctrl = 'ctrl'
        alt = 'alt'
        shift = 'shift'
        cmd = 'cmd'
        enter = 'enter'
        tab = 'tab'
        space = 'space'
        backspace = 'backspace'
        delete = 'delete'
        esc = 'esc'
        up = 'up'
        down = 'down'
        left = 'left'
        right = 'right'
        home = 'home'
        end = 'end'
        page_up = 'page_up'
        page_down = 'page_down'
        f1 = 'f1'
        f2 = 'f2'
        f3 = 'f3'
        f4 = 'f4'
        f5 = 'f5'
        f6 = 'f6'
        f7 = 'f7'
        f8 = 'f8'
        f9 = 'f9'
        f10 = 'f10'
        f11 = 'f11'
        f12 = 'f12'
        insert = 'insert'
        media_volume_up = 'volume_up'
        media_volume_down = 'volume_down'
        media_volume_mute = 'volume_mute'
        media_play_pause = 'media_play_pause'
        media_next = 'media_next'
        media_previous = 'media_previous'


# hotkey name -> pynput Key attribute. Resolved via getattr because
# pynput's Key enum is platform-specific: e.g. macOS has no Insert key,
# so `Key.insert` doesn't exist there and a bare attribute reference in
# a dict literal crashes the whole backend at import.
_KEY_ATTRS = {
    'ctrl': 'ctrl',
    'control': 'ctrl',
    'alt': 'alt',
    'shift': 'shift',
    'win': 'cmd',
    'windows': 'cmd',
    'cmd': 'cmd',
    'super': 'cmd',
    'enter': 'enter',
    'return': 'enter',
    'tab': 'tab',
    'space': 'space',
    'backspace': 'backspace',
    'delete': 'delete',
    'escape': 'esc',
    'esc': 'esc',
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
    'home': 'home',
    'end': 'end',
    'pageup': 'page_up',
    'pagedown': 'page_down',
    'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
    'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
    'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
    'insert': 'insert',
    'volume_up': 'media_volume_up',
    'volume_down': 'media_volume_down',
    'volume_mute': 'media_volume_mute',
    'media_play_pause': 'media_play_pause',
    'media_next': 'media_next',
    'media_next_track': 'media_next',
    'media_previous': 'media_previous',
    'media_previous_track': 'media_previous',
}


def _build_key_map():
    return {
        name: getattr(Key, attr)
        for name, attr in _KEY_ATTRS.items()
        if hasattr(Key, attr)
    }


class HotkeyAction(BaseAction):
    """Sends keyboard hotkey combinations."""

    # Map of common key names to pynput Key enum — keys the host
    # platform doesn't have simply drop out of the map.
    KEY_MAP = _build_key_map()

    def __init__(self, config: Dict[str, Any]):
        """Initialize hotkey action."""
        super().__init__(config)
        self.keyboard = Controller() if PYNPUT_AVAILABLE else None

    def validate(self) -> bool:
        """Validate that hotkey is provided."""
        if not PYNPUT_AVAILABLE:
            return False
        # Support both 'keys' (array) and 'hotkey' (string) formats
        return (('keys' in self.config and isinstance(self.config['keys'], list)) or
                ('hotkey' in self.config and isinstance(self.config['hotkey'], str)))

    def _parse_key(self, key_str: str):
        """Parse a key string to a Key or character.

        Args:
            key_str: Key string (e.g., 'ctrl', 'Ctrl', 'a', 'f1')

        Returns:
            pynput Key or character
        """
        key_lower = key_str.lower()
        if key_lower in self.KEY_MAP:
            return self.KEY_MAP[key_lower]
        return key_str  # Return as character if not a special key

    def execute(self) -> ActionResult:
        """Send the hotkey combination."""
        if not PYNPUT_AVAILABLE:
            return ActionResult(False, 'pynput library not available')

        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: Keys are required'
            )

        # Support both 'keys' array and 'hotkey' string formats
        if 'keys' in self.config:
            keys = self.config['keys']
        elif 'hotkey' in self.config:
            # Parse hotkey string (e.g., "Ctrl+Shift+P" -> ["Ctrl", "Shift", "P"])
            hotkey_str = self.config['hotkey']
            keys = [k.strip() for k in hotkey_str.split('+')]
        else:
            return ActionResult(False, 'No keys or hotkey specified')

        # Small delay between key presses
        delay = self.config.get('delay', 0.05)

        try:
            # Parse all keys
            parsed_keys = [self._parse_key(k) for k in keys]

            # Press all keys in order
            for key in parsed_keys:
                self.keyboard.press(key)
                time.sleep(delay)

            # Release all keys in reverse order
            for key in reversed(parsed_keys):
                self.keyboard.release(key)
                time.sleep(delay)

            key_combo = '+'.join(keys)
            return ActionResult(True, f'Sent hotkey: {key_combo}')
        except Exception as e:
            return ActionResult(False, f'Failed to send hotkey: {str(e)}')

    def get_description(self) -> str:
        """Get action description."""
        keys = self.config.get('keys', [])
        key_combo = '+'.join(keys)
        return f"Hotkey: {key_combo}"
