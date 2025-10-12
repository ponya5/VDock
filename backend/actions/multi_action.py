"""Multi-action executor for sequential actions."""
import time
from typing import Dict, Any, List
from .base_action import BaseAction, ActionResult


class MultiAction(BaseAction):
    """Executes multiple actions in sequence."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize multi-action.
        
        Args:
            config: Configuration with 'actions' list
        """
        super().__init__(config)
        self.executor = None  # Will be set by ActionExecutor
    
    def validate(self) -> bool:
        """Validate that actions list is provided."""
        return 'actions' in self.config and isinstance(self.config['actions'], list)
    
    def execute(self) -> ActionResult:
        """Execute all actions in sequence."""
        if not self.validate():
            return ActionResult(False, 'Invalid configuration: Actions list is required')
        
        if not self.executor:
            return ActionResult(False, 'ActionExecutor not set for MultiAction')
        
        actions = self.config['actions']
        delay_between = self.config.get('delay', 0.1)  # Default 100ms delay
        stop_on_error = self.config.get('stop_on_error', False)
        
        results = []
        
        for i, action_config in enumerate(actions):
            try:
                # Execute action using the executor
                result = self.executor.execute_action(action_config)
                results.append({
                    'index': i,
                    'success': result.success,
                    'message': result.message
                })
                
                if not result.success and stop_on_error:
                    return ActionResult(
                        False,
                        f'Multi-action stopped at step {i + 1}: {result.message}',
                        {'results': results}
                    )
                
                # Delay between actions (except after last one)
                if i < len(actions) - 1:
                    time.sleep(delay_between)
            except Exception as e:
                error_result = {
                    'index': i,
                    'success': False,
                    'message': str(e)
                }
                results.append(error_result)
                
                if stop_on_error:
                    return ActionResult(
                        False,
                        f'Multi-action failed at step {i + 1}: {str(e)}',
                        {'results': results}
                    )
        
        # Check if all succeeded
        all_success = all(r['success'] for r in results)
        return ActionResult(
            all_success,
            f'Executed {len(actions)} actions, {sum(r["success"] for r in results)} succeeded',
            {'results': results}
        )
    
    def get_description(self) -> str:
        """Get action description."""
        action_count = len(self.config.get('actions', []))
        return f"Multi-action: {action_count} steps"

