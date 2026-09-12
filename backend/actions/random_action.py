"""Pick one of several actions at random.

Stream Deck ships this; it is the basis of a soundboard's "random clip" key and
of shuffle-style buttons generally. Cheap to add once multi_action's pattern of
delegating back to the executor exists.
"""
import logging
import random
from typing import Any, Dict, Optional

from .base_action import BaseAction, ActionResult

logger = logging.getLogger('vdock')


class RandomAction(BaseAction):
    """Runs one randomly chosen action from a list."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.executor: Optional[Any] = None
        #: Remembers the last pick so repeats are avoided where possible.
        self._last_index: Optional[int] = None

    def validate(self) -> bool:
        actions = self.config.get('actions')
        return (
            isinstance(actions, list)
            and len(actions) > 0
            and all(isinstance(a, dict) and a.get('type') for a in actions)
        )

    def execute(self) -> ActionResult:
        if not self.validate():
            return ActionResult(
                False,
                'Invalid configuration: a non-empty list of actions is required'
            )

        if self.executor is None:
            return ActionResult(False, 'Random action has no executor')

        actions = self.config['actions']
        indices = list(range(len(actions)))

        # Avoid playing the same clip twice in a row when there is a choice.
        if (
            self.config.get('avoid_repeat', True)
            and len(indices) > 1
            and self._last_index is not None
            and self._last_index in indices
        ):
            indices.remove(self._last_index)

        index = random.choice(indices)
        self._last_index = index

        result = self.executor.execute_action(actions[index])
        return ActionResult(
            result.success,
            result.message,
            {**(result.data or {}), 'chosen_index': index},
            details=result.details,
        )

    def get_description(self) -> str:
        count = len(self.config.get('actions') or ())
        return f'Random action (1 of {count})'
