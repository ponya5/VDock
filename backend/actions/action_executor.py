"""Central action executor that routes actions to appropriate handlers."""
from typing import Any, Dict, Optional
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
from .http_request_action import HTTPRequestAction
from .obs_action import OBSAction


class ActionExecutor:
    """Executes actions based on their type.

    Unknown types fall through to the plugin manager, which is what makes the
    plugin system reachable at all: PluginManager.execute_plugin_action() was
    fully implemented but had no caller, so every plugin action returned
    "Unknown action type". Integration packs can now add actions without
    touching this dispatch table.
    """
    
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
        'ui_control': UIControlAction,
        'http_request': HTTPRequestAction,
        # OBSAction was written but never registered here, so the OBS entries
        # the picker offered all failed with "Unknown action type" while the
        # README advertised OBS support.
        'obs_start_recording': OBSAction,
        'obs_stop_recording': OBSAction,
        'obs_start_streaming': OBSAction,
        'obs_stop_streaming': OBSAction,
        'obs_switch_scene': OBSAction,
        'obs_toggle_source': OBSAction,
        'obs_toggle_filter': OBSAction,
    }
    
    def __init__(self, plugin_manager: Optional[Any] = None):
        """Initialize the executor.

        Args:
            plugin_manager: Optional PluginManager used to resolve action types
                this executor has no built-in handler for.
        """
        self.plugin_manager = plugin_manager

    def set_plugin_manager(self, plugin_manager: Any) -> None:
        """Attach a plugin manager after construction.

        app.py builds both singletons at import time; this avoids ordering
        constraints between them.
        """
        self.plugin_manager = plugin_manager

    def _execute_plugin_action(
        self, action_type: str, config: Dict[str, Any]
    ) -> Optional[ActionResult]:
        """Try to run `action_type` as a plugin action.

        Returns None when no plugin provides it, so the caller can report the
        original "unknown action type" error.
        """
        manager = self.plugin_manager
        if manager is None or not manager.handles(action_type):
            return None

        result = manager.execute_plugin_action(action_type, config)
        return ActionResult(
            success=bool(result.get('success')),
            message=result.get('message', ''),
            data=result.get('data') or {},
            details=result.get('details'),
        )

    def is_long_running(self, action_type: str) -> bool:
        """True when this action should run off the request thread.

        Built-in actions are quick. Pack actions that shell out to a CLI are
        not: claude_prompt routinely takes 30s and is allowed ten minutes,
        while the frontend's axios client times out at 30 -- so running one
        synchronously reports a timeout in the UI while the work carries on.
        """
        manager = self.plugin_manager
        if manager is None:
            return False
        try:
            for spec in manager.get_action_specs():
                if spec.action_type == action_type:
                    return spec.long_running
        except Exception:  # pragma: no cover - defensive
            return False
        return False

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
            plugin_result = self._execute_plugin_action(action_type, config)
            if plugin_result is not None:
                return plugin_result
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
            
            # OBS actions read the operation from config['action'].
            if action_type.startswith('obs_'):
                config = config.copy()
                config.setdefault('action', action_type)

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

