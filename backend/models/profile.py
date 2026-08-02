"""Profile and page data models."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from .button import Button


@dataclass
class Page:
    """Represents a page of buttons."""
    id: str
    name: str
    buttons: List[Button] = field(default_factory=list)
    grid_config: Dict[str, int] = field(
        default_factory=lambda: {'rows': 3, 'cols': 5}
    )
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
class Scene:
    """Represents a scene with multiple pages."""
    id: str
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    pages: List[Page] = field(default_factory=list)
    background: Optional[Dict[str, Any]] = None
    isActive: bool = False
    buttonSize: Optional[float] = None
    triggeredByApp: Optional[str] = None
    autoCreated: Optional[bool] = None
    isDefault: Optional[bool] = None
    transition_style: Optional[str] = None
    stagger_order: Optional[str] = None
    overlay_style: Optional[str] = None
    overlay_mode: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'pages': [page.to_dict() for page in self.pages],
            'isActive': self.isActive
        }

        # Only include optional fields if they have values
        if self.icon is not None:
            result['icon'] = self.icon
        if self.color is not None:
            result['color'] = self.color
        if self.background is not None:
            result['background'] = self.background
        if self.buttonSize is not None:
            result['buttonSize'] = self.buttonSize
        if self.triggeredByApp is not None:
            result['triggeredByApp'] = self.triggeredByApp
        if self.autoCreated is not None:
            result['autoCreated'] = self.autoCreated
        if self.isDefault is not None:
            result['isDefault'] = self.isDefault
        if self.transition_style is not None:
            result['transition_style'] = self.transition_style
        if self.stagger_order is not None:
            result['stagger_order'] = self.stagger_order
        if self.overlay_style is not None:
            result['overlay_style'] = self.overlay_style
        if self.overlay_mode is not None:
            result['overlay_mode'] = self.overlay_mode
        if self.created_at is not None:
            result['created_at'] = self.created_at
        if self.updated_at is not None:
            result['updated_at'] = self.updated_at

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scene':
        """Create from dictionary."""
        pages = [Page.from_dict(page) for page in data.get('pages', [])]

        return cls(
            id=data['id'],
            name=data['name'],
            icon=data.get('icon'),
            color=data.get('color'),
            pages=pages,
            background=data.get('background'),
            isActive=data.get('isActive', False),
            buttonSize=data.get('buttonSize'),
            triggeredByApp=data.get('triggeredByApp'),
            autoCreated=data.get('autoCreated'),
            isDefault=data.get('isDefault'),
            transition_style=data.get('transition_style'),
            stagger_order=data.get('stagger_order'),
            overlay_style=data.get('overlay_style'),
            overlay_mode=data.get('overlay_mode'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )


@dataclass
class Profile:
    """Represents a complete deck profile."""
    id: str
    name: str
    description: str = ''
    icon: Optional[str] = None
    avatar: Optional[str] = None
    pages: List[Page] = field(default_factory=list)  # Backward compatibility
    scenes: List[Scene] = field(default_factory=list)  # New scenes structure
    dockedButtons: List[Button] = field(default_factory=list)  # Docked buttons
    theme: str = 'default'
    settings: Optional[ProfileSettings] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'pages': [page.to_dict() for page in self.pages],  # compat
            'scenes': [scene.to_dict() for scene in self.scenes],
            'dockedButtons': [btn.to_dict() for btn in self.dockedButtons],
            'theme': self.theme,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Only include optional fields if they have values
        if self.icon is not None:
            result['icon'] = self.icon
        if self.avatar is not None:
            result['avatar'] = self.avatar
        if self.settings is not None:
            result['settings'] = self.settings.__dict__

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create from dictionary."""
        pages = [Page.from_dict(page) for page in data.get('pages', [])]
        scenes = [Scene.from_dict(scene) for scene in data.get('scenes', [])]
        docked_buttons = [
            Button.from_dict(btn) for btn in data.get('dockedButtons', [])
        ]
        settings_data = data.get('settings')
        settings = ProfileSettings(**settings_data) if settings_data else None

        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon'),
            avatar=data.get('avatar'),
            pages=pages,  # Backward compatibility
            scenes=scenes,
            dockedButtons=docked_buttons,
            theme=data.get('theme', 'default'),
            settings=settings,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

