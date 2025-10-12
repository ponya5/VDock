"""Program launching action."""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any
from .base_action import BaseAction, ActionResult


class ProgramAction(BaseAction):
    """Launches a program or opens a file."""
    
    def validate(self) -> bool:
        """Validate that path is provided."""
        return 'path' in self.config and isinstance(self.config['path'], str)
    
    def execute(self) -> ActionResult:
        """Launch the program."""
        if not self.validate():
            return ActionResult(False, 'Invalid configuration: Path is required')
        
        path = self.config['path']
        args = self.config.get('args', [])
        working_dir = self.config.get('working_dir')
        
        try:
            # Check if path exists
            if not Path(path).exists():
                return ActionResult(False, f'Path does not exist: {path}')
            
            # Build command
            cmd = [path] + (args if isinstance(args, list) else [])
            
            # Launch process
            if os.name == 'nt':  # Windows
                # Use shell=True for Windows to handle file associations
                subprocess.Popen(
                    cmd if Path(path).suffix == '.exe' else f'"{path}"',
                    cwd=working_dir,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            return ActionResult(True, f'Launched: {Path(path).name}')
        except Exception as e:
            return ActionResult(False, f'Failed to launch program: {str(e)}')
    
    def get_description(self) -> str:
        """Get action description."""
        path = self.config.get('path', 'unknown')
        return f"Launch: {Path(path).name}"

