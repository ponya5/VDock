"""Base plugin class and interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class PluginInfo:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    author: str
    description: str
    actions: List[str]  # List of action IDs this plugin provides
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'actions': self.actions
        }


class BasePlugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        """Initialize the plugin."""
        self._enabled = False
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information.
        
        Returns:
            PluginInfo with metadata
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up plugin resources."""
        pass
    
    @abstractmethod
    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plugin action.
        
        Args:
            action_id: ID of the action to execute
            config: Action configuration
            
        Returns:
            Result dictionary with 'success' and 'message' keys
        """
        pass
    
    @abstractmethod
    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        """Get the configuration schema for an action.
        
        Args:
            action_id: ID of the action
            
        Returns:
            JSON schema for the action configuration
        """
        pass
    
    def enable(self):
        """Enable the plugin."""
        self._enabled = True
    
    def disable(self):
        """Disable the plugin."""
        self._enabled = False
    
    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

