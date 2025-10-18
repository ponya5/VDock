"""Button and action data models."""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from enum import Enum


class ActionType(str, Enum):
    """Types of button actions."""
    URL = 'url'
    PROGRAM = 'program'
    COMMAND = 'command'
    HOTKEY = 'hotkey'
    MULTI_ACTION = 'multi_action'
    MACRO = 'macro'
    SYSTEM_CONTROL = 'system_control'
    SYSTEM_METRIC = 'system_metric'
    CROSS_PLATFORM = 'cross_platform'
    FOLDER = 'folder'
    PLUGIN = 'plugin'
    CALENDAR = 'calendar'
    WEATHER = 'weather'
    # Individual performance metrics
    METRIC_MEMORY = 'metric_memory'
    METRIC_CPU_USAGE = 'metric_cpu_usage'
    METRIC_CPU_TEMPERATURE = 'metric_cpu_temperature'
    METRIC_CPU_FREQUENCY = 'metric_cpu_frequency'
    METRIC_CPU_POWER = 'metric_cpu_power'
    METRIC_INTERNET_SPEED = 'metric_internet_speed'
    METRIC_HARDDISK = 'metric_harddisk'
    METRIC_GPU_TEMPERATURE = 'metric_gpu_temperature'
    METRIC_GPU_FREQUENCY = 'metric_gpu_frequency'
    METRIC_GPU_USAGE = 'metric_gpu_usage'
    METRIC_GPU_MEMORY_FREQ = 'metric_gpu_memory_freq'
    METRIC_GPU_MEMORY_USAGE = 'metric_gpu_memory_usage'
    # Time options
    TIME_WORLD_CLOCK = 'time_world_clock'
    TIME_TIMER = 'time_timer'
    TIME_COUNTDOWN = 'time_countdown'
    # Navigation
    NEXT_PAGE = 'next_page'
    PREVIOUS_PAGE = 'previous_page'
    HOME_PAGE = 'home_page'
    # Screenshot
    SCREENSHOT = 'screenshot'
    # Custom (placeholder action type)
    CUSTOM = 'custom'


class SystemControlType(str, Enum):
    """Types of system control actions."""
    VOLUME_UP = 'volume_up'
    VOLUME_DOWN = 'volume_down'
    VOLUME_MUTE = 'volume_mute'
    MEDIA_PLAY_PAUSE = 'media_play_pause'
    MEDIA_NEXT = 'media_next'
    MEDIA_PREVIOUS = 'media_previous'
    BRIGHTNESS_UP = 'brightness_up'
    BRIGHTNESS_DOWN = 'brightness_down'


class ButtonShape(str, Enum):
    """Button shape options."""
    RECTANGLE = 'rectangle'
    ROUNDED = 'rounded'
    CIRCLE = 'circle'


@dataclass
class ButtonAction:
    """Represents an action that a button can perform."""
    type: ActionType
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'config': self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ButtonAction':
        """Create from dictionary."""
        return cls(
            type=ActionType(data['type']),
            config=data.get('config', {})
        )


@dataclass
class Button:
    """Represents a button on the deck."""
    id: str
    label: str = ''
    secondary_label: str = ''
    icon: Optional[str] = None
    icon_type: str = 'fontawesome'  # fontawesome, material, custom
    media_url: Optional[str] = None  # For video/gif/image backgrounds
    media_type: Optional[str] = None  # video, gif, image
    action: Optional[ButtonAction] = None
    shape: ButtonShape = ButtonShape.ROUNDED
    position: Dict[str, int] = field(default_factory=lambda: {'row': 0, 'col': 0})
    size: Dict[str, int] = field(default_factory=lambda: {'rows': 1, 'cols': 1})
    style: Dict[str, Any] = field(default_factory=dict)
    tooltip: str = ''
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['shape'] = self.shape.value
        if self.action:
            data['action'] = self.action.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Button':
        """Create from dictionary."""
        action_data = data.get('action')
        action = ButtonAction.from_dict(action_data) if action_data else None
        
        return cls(
            id=data['id'],
            label=data.get('label', ''),
            secondary_label=data.get('secondary_label', ''),
            icon=data.get('icon'),
            icon_type=data.get('icon_type', 'fontawesome'),
            media_url=data.get('media_url'),
            media_type=data.get('media_type'),
            action=action,
            shape=ButtonShape(data.get('shape', 'rounded')),
            position=data.get('position', {'row': 0, 'col': 0}),
            size=data.get('size', {'rows': 1, 'cols': 1}),
            style=data.get('style', {}),
            tooltip=data.get('tooltip', ''),
            enabled=data.get('enabled', True)
        )

