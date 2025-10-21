"""Base action class."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ActionResult:
    """Result of an action execution."""
    
    def __init__(
        self, 
        success: bool, 
        message: str = '', 
        data: Optional[Dict[str, Any]] = None,
        error_code: Optional[int] = None,
        details: Optional[str] = None
    ):
        self.success = success
        self.message = message
        self.data = data or {}
        self.error_code = error_code
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'success': self.success,
            'message': self.message,
            'data': self.data
        }
        
        if self.error_code is not None:
            result['error_code'] = self.error_code
        
        if self.details:
            result['details'] = self.details
        
        return result


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

