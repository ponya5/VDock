"""Central action executor that routes actions to appropriate handlers."""
from typing import Dict, Any
from .base_action import ActionResult
from .url_action import URLAction
from .program_action import ProgramAction
from .command_action import CommandAction
from .hotkey_action import HotkeyAction
from .multi_action import MultiAction
from .system_action import SystemAction


class ActionExecutor:
    """Executes actions based on their type."""
    
    # Map action types to their classes
    ACTION_CLASSES = {
        'url': URLAction,
        'program': ProgramAction,
        'command': CommandAction,
        'hotkey': HotkeyAction,
        'multi_action': MultiAction,
        'system_control': SystemAction
    }
    
    def execute_action(self, action_data: Dict[str, Any]) -> ActionResult:
        """Execute an action based on its configuration.
        
        Args:
            action_data: Dictionary with 'type' and 'config' keys
            
        Returns:
            ActionResult from the executed action
        """
        action_type = action_data.get('type')
        config = action_data.get('config', {})
        
        if not action_type:
            return ActionResult(False, 'Action type not specified')
        
        if action_type not in self.ACTION_CLASSES:
            return ActionResult(False, f'Unknown action type: {action_type}')
        
        try:
            # Create action instance
            action_class = self.ACTION_CLASSES[action_type]
            action = action_class(config)
            
            # For multi-actions, set the executor reference
            if action_type == 'multi_action':
                action.executor = self
            
            # Validate and execute
            if not action.validate():
                return ActionResult(False, f'Invalid configuration for {action_type} action')
            
            return action.execute()
        except Exception as e:
            return ActionResult(False, f'Error executing action: {str(e)}')

