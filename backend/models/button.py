"""Button and action data models."""
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Type, TypeVar, Union
from enum import Enum

logger = logging.getLogger('vdock')

E = TypeVar('E', bound=Enum)


def coerce_enum(enum_cls: Type[E], value: Any, default: E) -> Union[E, str]:
    """Coerce a persisted string to `enum_cls`, tolerating unknown values.

    These models sit on the profile save path (PUT /api/profiles/<id> rebuilds
    a Profile via from_dict and persists to_dict), so raising here turns any
    value the backend does not recognise into a 500 and loses the user's
    layout. Instead, keep the raw string and let the action executor decide at
    press time whether it can dispatch it -- the executor, not the persistence
    layer, is the authority on what is runnable.
    """
    if value is None:
        return default
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        logger.debug(
            "Unrecognised %s %r kept as a raw string",
            enum_cls.__name__, value
        )
        return value


def enum_value(value: Any) -> Any:
    """Unwrap an Enum to its value, passing raw strings through untouched."""
    return value.value if isinstance(value, Enum) else value


class ActionType(str, Enum):
    """Types of button actions."""
    URL = 'url'
    PROGRAM = 'program'
    COMMAND = 'command'
    HOTKEY = 'hotkey'
    MULTI_ACTION = 'multi_action'
    MACRO = 'macro'
    SYSTEM_CONTROL = 'system_control'
    SYSTEM = 'system'
    SYSTEM_METRIC = 'system_metric'
    UI_CONTROL = 'ui_control'
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
    METRIC_DISK = 'metric_disk'
    METRIC_NETWORK = 'metric_network'
    METRIC_TEMPERATURE = 'metric_temperature'
    METRIC_BATTERY = 'metric_battery'
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
    # Web requests
    HTTP_REQUEST = 'http_request'
    # OBS Studio
    OBS_START_RECORDING = 'obs_start_recording'
    OBS_STOP_RECORDING = 'obs_stop_recording'
    OBS_START_STREAMING = 'obs_start_streaming'
    OBS_STOP_STREAMING = 'obs_stop_streaming'
    OBS_SWITCH_SCENE = 'obs_switch_scene'
    OBS_TOGGLE_SOURCE = 'obs_toggle_source'
    OBS_TOGGLE_FILTER = 'obs_toggle_filter'
    # Composite actions
    TOGGLE = 'toggle'
    RANDOM = 'random'
    # Scene / page navigation
    GOTO_PAGE = 'goto_page'
    SWITCH_SCENE = 'switch_scene'
    NEXT_SCENE = 'next_scene'
    PREVIOUS_SCENE = 'previous_scene'
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
    HEXAGON = 'hexagon'
    DIAMOND = 'diamond'
    OCTAGON = 'octagon'


@dataclass
class ButtonAction:
    """Represents an action that a button can perform."""
    type: Union[ActionType, str]
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': enum_value(self.type),
            'config': self.config
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ButtonAction':
        """Create from dictionary."""
        return cls(
            type=coerce_enum(ActionType, data['type'], ActionType.CUSTOM),
            config=data.get('config', {})
        )


@dataclass
class Button:
    """Represents a button on the deck."""
    id: str
    label: str = ''
    secondary_label: str = ''
    # FontAwesome icons arrive as ['fas', 'home']; custom icons as a path.
    icon: Optional[Union[str, List[str]]] = None
    icon_type: str = 'fontawesome'  # fontawesome, material, custom
    media_url: Optional[str] = None  # For video/gif/image backgrounds
    media_type: Optional[str] = None  # video, gif, image
    action: Optional[ButtonAction] = None
    shape: Union[ButtonShape, str] = ButtonShape.ROUNDED
    position: Dict[str, int] = field(default_factory=lambda: {'row': 0, 'col': 0})
    size: Dict[str, int] = field(default_factory=lambda: {'rows': 1, 'cols': 1})
    style: Dict[str, Any] = field(default_factory=dict)
    # Visual layer model (fill / effect / icon / label / behaviour).
    layers: Optional[Dict[str, Any]] = None
    tooltip: str = ''
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['shape'] = enum_value(self.shape)
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
            shape=coerce_enum(
                ButtonShape, data.get('shape'), ButtonShape.ROUNDED
            ),
            position=data.get('position', {'row': 0, 'col': 0}),
            size=data.get('size', {'rows': 1, 'cols': 1}),
            style=data.get('style', {}),
            layers=data.get('layers'),
            tooltip=data.get('tooltip', ''),
            enabled=data.get('enabled', True)
        )

