"""Central action executor that routes actions to appropriate handlers."""
from typing import Dict, Any
from .base_action import ActionResult
from .url_action import URLAction
from .program_action import ProgramAction
from .command_action import CommandAction
from .hotkey_action import HotkeyAction
from .multi_action import MultiAction
from .macro_action import MacroAction
from .system_action import SystemAction
from .cross_platform_action import CrossPlatformAction
from .metric_action import MetricAction
from .navigation_action import NavigationAction
from .time_action import TimeAction
from .weather_action import WeatherAction
from .ui_control_action import UIControlAction


class ActionExecutor:
    """Executes actions based on their type."""
    
    # Map action types to their classes
    ACTION_CLASSES = {
        'url': URLAction,
        'program': ProgramAction,
        'command': CommandAction,
        'hotkey': HotkeyAction,
        'multi_action': MultiAction,
        'macro': MacroAction,
        'system': SystemAction,
        'system_control': SystemAction,
        'cross_platform': CrossPlatformAction,
        'metric_cpu_usage': MetricAction,
        'metric_memory': MetricAction,
        'metric_disk': MetricAction,
        'metric_network': MetricAction,
        'metric_temperature': MetricAction,
        'metric_battery': MetricAction,
        'time_world_clock': TimeAction,
        'weather': WeatherAction,
        'next_page': NavigationAction,
        'previous_page': NavigationAction,
        'ui_control': UIControlAction
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
            
            # For metric actions, add the metric type to config
            if action_type.startswith('metric_'):
                config = config.copy()
                config['metric_type'] = action_type
            
            # For time actions, add the action type to config
            if action_type.startswith('time_'):
                config = config.copy()
                config['action_type'] = action_type.replace('time_', '')
            
            # For navigation actions, add the action type to config
            if action_type in ['next_page', 'previous_page']:
                config = config.copy()
                config['action_type'] = action_type
            
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

