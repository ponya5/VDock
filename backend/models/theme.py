"""Theme data model."""
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Theme:
    """Represents a visual theme."""
    id: str
    name: str
    colors: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'colors': self.colors
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            colors=data.get('colors', {})
        )


# Built-in themes
BUILTIN_THEMES = {
    'dark': Theme(
        id='dark',
        name='Dark',
        colors={
            'background': '#1a1a1a',
            'surface': '#2d2d2d',
            'primary': '#4a90e2',
            'secondary': '#7c7c7c',
            'text': '#ffffff',
            'text-secondary': '#b0b0b0',
            'border': '#404040',
            'accent': '#f39c12'
        }
    ),
    'light': Theme(
        id='light',
        name='Light',
        colors={
            'background': '#f5f5f5',
            'surface': '#ffffff',
            'primary': '#2196f3',
            'secondary': '#9e9e9e',
            'text': '#212121',
            'text-secondary': '#757575',
            'border': '#e0e0e0',
            'accent': '#ff9800'
        }
    ),
    'high-contrast': Theme(
        id='high-contrast',
        name='High Contrast',
        colors={
            'background': '#000000',
            'surface': '#1a1a1a',
            'primary': '#00ff00',
            'secondary': '#ffffff',
            'text': '#ffffff',
            'text-secondary': '#cccccc',
            'border': '#ffffff',
            'accent': '#ffff00'
        }
    )
}

