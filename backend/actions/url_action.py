"""URL opening action."""
import webbrowser
from typing import Dict, Any
from .base_action import BaseAction, ActionResult


class URLAction(BaseAction):
    """Opens a URL in the default browser."""
    
    def validate(self) -> bool:
        """Validate that URL is provided."""
        return 'url' in self.config and isinstance(self.config['url'], str)
    
    def execute(self) -> ActionResult:
        """Open the URL in default browser."""
        if not self.validate():
            return ActionResult(False, 'Invalid configuration: URL is required')
        
        url = self.config['url']
        
        try:
            # Ensure URL has a protocol
            if not url.startswith(('http://', 'https://', 'file://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            return ActionResult(True, f'Opened URL: {url}')
        except Exception as e:
            return ActionResult(False, f'Failed to open URL: {str(e)}')
    
    def get_description(self) -> str:
        """Get action description."""
        url = self.config.get('url', 'unknown')
        return f"Open URL: {url}"

