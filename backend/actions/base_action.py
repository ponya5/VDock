"""Base action class."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ActionResult:
    """Result of an action execution."""
    
    def __init__(self, success: bool, message: str = '', data: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data
        }


class BaseAction(ABC):
    """Base class for all actions."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize action with configuration.
        
        Args:
            config: Action configuration dictionary
        """
        self.config = config
    
    @abstractmethod
    def execute(self) -> ActionResult:
        """Execute the action.
        
        Returns:
            ActionResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate action configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    def get_description(self) -> str:
        """Get human-readable description of the action.
        
        Returns:
            Action description
        """
        return f"{self.__class__.__name__} action"

