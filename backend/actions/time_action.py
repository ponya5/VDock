"""Time and clock actions for displaying time information."""
from typing import Dict, Any
from datetime import datetime
import pytz
from .base_action import BaseAction, ActionResult


class TimeAction(BaseAction):
    """Action for displaying time and clock information."""

    VALID_ACTIONS = [
        'world_clock', 'timer', 'countdown', 'stopwatch'
    ]

    def __init__(self, config: Dict[str, Any]):
        """Initialize time action."""
        super().__init__(config)

    def validate(self) -> bool:
        """Validate that action type is provided and valid."""
        action_type = self.config.get('action_type')
        if not action_type:
            # For backward compatibility, assume world_clock
            return True
        return action_type in self.VALID_ACTIONS

    def execute(self) -> ActionResult:
        """Execute the time action."""
        action_type = self.config.get('action_type', 'world_clock')
        
        if action_type == 'world_clock':
            return self._get_world_clock()
        elif action_type == 'timer':
            return self._get_timer()
        elif action_type == 'countdown':
            return self._get_countdown()
        elif action_type == 'stopwatch':
            return self._get_stopwatch()
        else:
            return ActionResult(False, f'Unknown time action: {action_type}')

    def _get_world_clock(self) -> ActionResult:
        """Get world clock time."""
        timezone = self.config.get('timezone', 'local')
        font_size = self.config.get('font_size', 1.0)
        
        try:
            if timezone == 'local':
                current_time = datetime.now()
                timezone_name = 'Local Time'
            else:
                tz = pytz.timezone(timezone)
                current_time = datetime.now(tz)
                timezone_name = timezone
            
            # Format time
            time_str = current_time.strftime('%H:%M:%S')
            date_str = current_time.strftime('%a, %b %d, %Y')
            
            return ActionResult(
                True,
                f'{time_str}',
                {
                    'time': time_str,
                    'date': date_str,
                    'timezone': timezone_name,
                    'font_size': font_size,
                    'timestamp': current_time.isoformat(),
                    'display_type': 'world_clock'
                }
            )
        except Exception as e:
            return ActionResult(False, f'Failed to get time: {str(e)}')

    def _get_timer(self) -> ActionResult:
        """Get timer information."""
        duration = self.config.get('duration', 300)  # 5 minutes default
        
        return ActionResult(
            True,
            'Timer ready',
            {
                'duration': duration,
                'display_type': 'timer',
                'frontend_handled': True
            }
        )

    def _get_countdown(self) -> ActionResult:
        """Get countdown information."""
        target_time = self.config.get('target_time')
        
        if not target_time:
            return ActionResult(False, 'Target time not specified for countdown')
        
        return ActionResult(
            True,
            'Countdown active',
            {
                'target_time': target_time,
                'display_type': 'countdown',
                'frontend_handled': True
            }
        )

    def _get_stopwatch(self) -> ActionResult:
        """Get stopwatch information."""
        return ActionResult(
            True,
            'Stopwatch ready',
            {
                'display_type': 'stopwatch',
                'frontend_handled': True
            }
        )

    def get_description(self) -> str:
        """Get action description."""
        action_type = self.config.get('action_type', 'world_clock')
        return f"Time: {action_type.replace('_', ' ').title()}"
