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
class ProfileSettings:
    """Profile-specific settings."""
    defaultGridRows: int = 3
    defaultGridCols: int = 3
    buttonSize: float = 1.0
    showLabels: bool = True
    showTooltips: bool = True
    animationsEnabled: bool = True

@dataclass
class Profile:
    """Represents a complete deck profile."""
    id: str
    name: str
    description: str = ''
    icon: Optional[str] = None
    avatar: Optional[str] = None
    pages: List[Page] = field(default_factory=list)
    theme: str = 'default'
    settings: Optional[ProfileSettings] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'avatar': self.avatar,
            'pages': [page.to_dict() for page in self.pages],
            'theme': self.theme,
            'settings': self.settings.__dict__ if self.settings else None,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from dictionary."""
        pages = [Page.from_dict(page) for page in data.get('pages', [])]
        settings_data = data.get('settings')
        settings = ProfileSettings(**settings_data) if settings_data else None
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon'),
            avatar=data.get('avatar'),
            pages=pages,
            theme=data.get('theme', 'default'),
            settings=settings,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

