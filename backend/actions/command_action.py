"""Shell command execution action."""
import subprocess
import shlex
from typing import Dict, Any
from .base_action import BaseAction, ActionResult
from config import Config


class CommandAction(BaseAction):
    """Executes a shell command with security restrictions."""
    
    def validate(self) -> bool:
        """Validate that command is provided and allowed."""
        if 'command' not in self.config or not isinstance(self.config['command'], str):
            return False
        
        command = self.config['command'].strip()
        
        # Check if command execution is enabled
        if not Config.ALLOW_COMMAND_EXECUTION:
            return False
        
        # Check if command is in allowed list
        if Config.ALLOWED_COMMAND_PATTERNS:
            # Extract the base command (first word)
            base_command = command.split()[0] if command else ''
            if base_command not in Config.ALLOWED_COMMAND_PATTERNS:
                return False
        
        return True
    
    def execute(self) -> ActionResult:
        """Execute the shell command with security checks."""
        if not self.validate():
            return ActionResult(
                False,
                'Command execution is disabled or command is not allowed. Only predefined safe commands are permitted.'
            )
        
        command = self.config['command'].strip()
        require_confirmation = self.config.get('require_confirmation', Config.REQUIRE_COMMAND_CONFIRMATION)
        
        # Security check - if confirmation required and not provided
        if require_confirmation and not self.config.get('confirmed', False):
            return ActionResult(
                False,
                'Command requires confirmation',
                {'requires_confirmation': True, 'command': command}
            )
        
        try:
            # Use shlex.split for safer command parsing (avoid shell injection)
            # Note: For predefined commands, this is safer than shell=True
            cmd_args = shlex.split(command)
            
            # Execute command without shell=True for better security
            result = subprocess.run(
                cmd_args,
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

