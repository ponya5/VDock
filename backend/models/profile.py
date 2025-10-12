"""Profile and page data models."""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from .button import Button


@dataclass
class Page:
    """Represents a page of buttons."""
    id: str
    name: str
    buttons: List[Button] = field(default_factory=list)
    grid_config: Dict[str, int] = field(default_factory=lambda: {'rows': 3, 'cols': 5})
    background: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'buttons': [btn.to_dict() for btn in self.buttons],
            'grid_config': self.grid_config,
            'background': self.background
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Page':
        """Create from dictionary."""
        buttons = [Button.from_dict(btn) for btn in data.get('buttons', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            buttons=buttons,
            grid_config=data.get('grid_config', {'rows': 3, 'cols': 5}),
            background=data.get('background')
        )


@dataclass
class Profile:
    """Represents a complete deck profile."""
    id: str
    name: str
    description: str = ''
    icon: Optional[str] = None
    pages: List[Page] = field(default_factory=list)
    theme: str = 'dark'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'pages': [page.to_dict() for page in self.pages],
            'theme': self.theme,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from dictionary."""
        pages = [Page.from_dict(page) for page in data.get('pages', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon'),
            pages=pages,
            theme=data.get('theme', 'dark'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

