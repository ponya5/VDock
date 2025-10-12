"""Shell command execution action."""
import subprocess
from typing import Dict, Any
from .base_action import BaseAction, ActionResult
from config import Config


class CommandAction(BaseAction):
    """Executes a shell command."""
    
    def validate(self) -> bool:
        """Validate that command is provided."""
        return 'command' in self.config and isinstance(self.config['command'], str)
    
    def execute(self) -> ActionResult:
        """Execute the shell command."""
        if not self.validate():
            return ActionResult(False, 'Invalid configuration: Command is required')
        
        command = self.config['command']
        require_confirmation = self.config.get('require_confirmation', Config.REQUIRE_COMMAND_CONFIRMATION)
        
        # Security check - if confirmation required and not provided
        if require_confirmation and not self.config.get('confirmed', False):
            return ActionResult(
                False,
                'Command requires confirmation',
                {'requires_confirmation': True, 'command': command}
            )
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode == 0:
                return ActionResult(
                    True,
                    f'Command executed successfully',
                    {'stdout': result.stdout, 'returncode': result.returncode}
                )
            else:
                return ActionResult(
                    False,
                    f'Command failed with code {result.returncode}',
                    {'stderr': result.stderr, 'returncode': result.returncode}
                )
        except subprocess.TimeoutExpired:
            return ActionResult(False, 'Command execution timed out')
        except Exception as e:
            return ActionResult(False, f'Failed to execute command: {str(e)}')
    
    def get_description(self) -> str:
        """Get action description."""
        command = self.config.get('command', 'unknown')
        return f"Run command: {command[:50]}..."

