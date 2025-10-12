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
        media_volume_up = 'volume_up'
        media_volume_down = 'volume_down'
        media_volume_mute = 'volume_mute'
        media_play_pause = 'media_play_pause'
        media_next = 'media_next'
        media_previous = 'media_previous'


class HotkeyAction(BaseAction):
    """Sends keyboard hotkey combinations."""

    # Map of common key names to pynput Key enum
    KEY_MAP = {
        'ctrl': Key.ctrl,
        'control': Key.ctrl,
        'alt': Key.alt,
        'shift': Key.shift,
        'win': Key.cmd,
        'windows': Key.cmd,
        'cmd': Key.cmd,
        'super': Key.cmd,
        'enter': Key.enter,
        'return': Key.enter,
        'tab': Key.tab,
        'space': Key.space,
        'backspace': Key.backspace,
        'delete': Key.delete,
        'escape': Key.esc,
        'esc': Key.esc,
        'up': Key.up,
        'down': Key.down,
        'left': Key.left,
        'right': Key.right,
        'home': Key.home,
        'end': Key.end,
        'pageup': Key.page_up,
        'pagedown': Key.page_down,
        'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
        'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
        'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        # Media and volume keys
        'volume_up': Key.media_volume_up,
        'volume_down': Key.media_volume_down,
        'volume_mute': Key.media_volume_mute,
        'media_play_pause': Key.media_play_pause,
        'media_next': Key.media_next,
        'media_next_track': Key.media_next,
        'media_previous': Key.media_previous,
        'media_previous_track': Key.media_previous,
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialize hotkey action."""
        super().__init__(config)
        self.keyboard = Controller() if PYNPUT_AVAILABLE else None

    def validate(self) -> bool:
        """Validate that hotkey is provided."""
        if not PYNPUT_AVAILABLE:
            return False
        return ('keys' in self.config and
                isinstance(self.config['keys'], list))

    def _parse_key(self, key_str: str):
        """Parse a key string to a Key or character.

        Args:
            key_str: Key string (e.g., 'ctrl', 'a', 'f1')

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

        keys = self.config['keys']
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
