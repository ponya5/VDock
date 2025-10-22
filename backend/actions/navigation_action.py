"""Navigation actions for page and scene navigation."""
from typing import Dict, Any
from .base_action import BaseAction, ActionResult


class NavigationAction(BaseAction):
    """Action for page and scene navigation."""

    VALID_ACTIONS = [
        'next_page', 'previous_page', 'go_to_page', 'next_scene', 'previous_scene', 'go_to_scene'
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize navigation action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that action type is provided and valid."""
        action_type = self.config.get('action_type')
        if not action_type:
            # For backward compatibility, check if this is a direct navigation action
            return True
        return action_type in self.VALID_ACTIONS

    def execute(self) -> ActionResult:
        """Execute the navigation action."""
        # Navigation actions are handled by the frontend, not the backend
        # Return success to indicate the action was processed
        action_type = self.config.get('action_type', 'navigation')
        
        return ActionResult(
            True,
            f'Navigation action: {action_type}',
            {
                'action_type': action_type,
                'frontend_handled': True,
                'config': self.config
            }
        )

    def get_description(self) -> str:
        """Get action description."""
        action_type = self.config.get('action_type', 'navigation')
        return f"Navigation: {action_type.replace('_', ' ').title()}"
