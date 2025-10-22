"""UI Control Actions for dashboard interface settings."""

from .base_action import BaseAction, ActionResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


class UIControlAction(BaseAction):
    """Handle UI control actions like brightness adjustment."""

    def validate(self) -> bool:
        """Validate UI control action configuration."""
        action = self.config.get('action')
        valid_actions = [
            'ui_brightness_up',
            'ui_brightness_down',
            'ui_brightness_set',
            'toggle_header'
        ]
        return action in valid_actions

    def execute(self) -> ActionResult:
        """Execute UI control action."""
        action = self.config.get('action')

        if action == 'ui_brightness_up':
            return self._brightness_up()
        elif action == 'ui_brightness_down':
            return self._brightness_down()
        elif action == 'ui_brightness_set':
            return self._brightness_set()
        elif action == 'toggle_header':
            return self._toggle_header()
        else:
            return ActionResult(False, f'Unknown UI control action: {action}')

    def _brightness_up(self) -> ActionResult:
        """Increase UI brightness."""
        step = self.config.get('step', 10)
        logger.info(f"UI brightness up by {step}%")
        return ActionResult(
            True,
            f'UI brightness increased by {step}%',
            {'action': 'ui_brightness_up', 'step': step}
        )

    def _brightness_down(self) -> ActionResult:
        """Decrease UI brightness."""
        step = self.config.get('step', 10)
        logger.info(f"UI brightness down by {step}%")
        return ActionResult(
            True,
            f'UI brightness decreased by {step}%',
            {'action': 'ui_brightness_down', 'step': step}
        )

    def _brightness_set(self) -> ActionResult:
        """Set UI brightness to specific value."""
        value = self.config.get('value', 100)
        logger.info(f"UI brightness set to {value}%")
        return ActionResult(
            True,
            f'UI brightness set to {value}%',
            {'action': 'ui_brightness_set', 'value': value}
        )

    def _toggle_header(self) -> ActionResult:
        """Toggle dashboard header visibility."""
        logger.info("Toggling dashboard header")
        return ActionResult(
            True,
            'Header visibility toggled',
            {'action': 'toggle_header'}
        )
