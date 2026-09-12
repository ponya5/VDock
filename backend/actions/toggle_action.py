"""Two-state toggle button (Stream Deck's "Multi Action Switch").

One button, two actions, alternating on each press: mute then unmute, start
then stop recording, lights on then off. Without it every on/off pair costs two
buttons on a grid where space is the scarce resource.

The current side is server state rather than client state, so two VDock windows
showing the same deck agree on which way the switch is set, and the state
survives a page reload. It is deliberately not written into the profile: which
way a switch happens to be flipped is a moment, not configuration.
"""
import logging
import threading
from typing import Any, Dict, Optional

from .base_action import BaseAction, ActionResult

logger = logging.getLogger('vdock')

#: button id -> side index. Process-wide; reset when the backend restarts.
_sides: Dict[str, int] = {}
_lock = threading.Lock()


def current_side(toggle_id: str) -> int:
    with _lock:
        return _sides.get(toggle_id, 0)


def reset_all() -> None:
    with _lock:
        _sides.clear()


class ToggleAction(BaseAction):
    """Alternates between two configured actions."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        #: Injected by ActionExecutor so nested actions dispatch normally.
        self.executor: Optional[Any] = None

    def _toggle_id(self) -> str:
        # Falls back to the action's shape so an unsaved button still toggles.
        return str(
            self.config.get('toggle_id')
            or self.config.get('button_id')
            or id(self.config)
        )

    def validate(self) -> bool:
        on = self.config.get('on_action')
        off = self.config.get('off_action')
        return isinstance(on, dict) and isinstance(off, dict) and bool(
            on.get('type') and off.get('type')
        )

    def execute(self) -> ActionResult:
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: on_action and off_action are both '
                'required, each with a type'
            )

        if self.executor is None:
            return ActionResult(False, 'Toggle action has no executor')

        toggle_id = self._toggle_id()
        with _lock:
            side = _sides.get(toggle_id, 0)
            next_side = 1 - side
            _sides[toggle_id] = next_side

        action = self.config['on_action'] if side == 0 else self.config['off_action']
        label = (
            self.config.get('on_label', 'On') if side == 0
            else self.config.get('off_label', 'Off')
        )

        result = self.executor.execute_action(action)

        if not result.success:
            # Leave the switch where it was; a failed action did not change
            # the world, so the button should not claim it did.
            with _lock:
                _sides[toggle_id] = side
            return ActionResult(
                False,
                result.message,
                {**(result.data or {}), 'side': side, 'sublabel': label},
                details=result.details,
            )

        return ActionResult(
            True,
            f'{label}: {result.message}' if result.message else label,
            {
                **(result.data or {}),
                'side': next_side,
                'sublabel': (
                    self.config.get('off_label', 'Off') if next_side == 1
                    else self.config.get('on_label', 'On')
                ),
            },
        )

    def get_description(self) -> str:
        return 'Toggle between two actions'
