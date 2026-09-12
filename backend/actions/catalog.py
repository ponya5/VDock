"""The action catalog: one declarative source of truth for every button action.

Why this exists
---------------
Adding an action used to mean editing five places -- the ``ActionType`` enum in
``models/button.py``, ``ActionExecutor.ACTION_CLASSES``, the ``ActionType`` union
in ``frontend/src/types/index.ts``, a hardcoded ``<button>`` in
``ButtonActionsSidebar.vue``, and a ``v-if`` config block in ``ButtonEditor.vue``.
Nothing kept those in step, so they drifted badly: 22 of the 46 entries the
sidebar offered dispatched to an action type the backend had no handler for and
failed on press.

Most of those were not missing features. ``volume_up``, ``media_play_pause``,
``screenshot`` and friends were already implemented in
``CrossPlatformAction.VALID_ACTIONS`` -- the sidebar just emitted them as bare
action *types* when they are really the ``cross_platform`` type carrying a
config. That is the distinction this catalog makes explicit::

    entry id  ->  (action_type, default_config)

A catalog entry is "a thing the user can put on a button". Several entries map
onto the same ``action_type`` with different configs. ``GET /api/actions/catalog``
serves this list, so the picker and the button editor are generated from it and
cannot drift from what the backend can actually run.

``ActionType`` in ``models/button.py`` stays hand-written for IDE support;
``tests/test_catalog.py`` asserts the two agree.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

# Where an action actually runs.
RUNS_BACKEND = 'backend'    # POST /api/actions/execute
RUNS_FRONTEND = 'frontend'  # handled in the client, never dispatched
RUNS_WIDGET = 'widget'      # renders live data; pressing it does nothing


@dataclass(frozen=True)
class ConfigField:
    """One field in an action's configuration form."""
    name: str
    label: str
    type: str = 'text'  # text|textarea|number|select|boolean|keys|steps|path|url
    required: bool = False
    default: Any = None
    options: Tuple[Dict[str, str], ...] = ()
    placeholder: str = ''
    help: str = ''

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'required': self.required,
        }
        if self.default is not None:
            data['default'] = self.default
        if self.options:
            data['options'] = list(self.options)
        if self.placeholder:
            data['placeholder'] = self.placeholder
        if self.help:
            data['help'] = self.help
        return data


@dataclass(frozen=True)
class ActionSpec:
    """A single entry in the action catalog."""
    id: str
    label: str
    category: str
    icon: Tuple[str, str]
    action_type: str
    description: str = ''
    default_config: Mapping[str, Any] = field(default_factory=dict)
    config_fields: Tuple[ConfigField, ...] = ()
    runs_on: str = RUNS_BACKEND
    long_running: bool = False
    keywords: Tuple[str, ...] = ()
    # Set when an entry is listed but not usable yet, e.g. its integration is
    # not configured. The picker shows it greyed out with this reason.
    unavailable_reason: Optional[str] = None

    @property
    def display_only(self) -> bool:
        """True when pressing the button should not dispatch anything."""
        return self.runs_on == RUNS_WIDGET

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            'id': self.id,
            'label': self.label,
            'category': self.category,
            'icon': list(self.icon),
            'action_type': self.action_type,
            'description': self.description,
            'default_config': dict(self.default_config),
            'config_fields': [f.to_dict() for f in self.config_fields],
            'runs_on': self.runs_on,
            'display_only': self.display_only,
            'long_running': self.long_running,
            'keywords': list(self.keywords),
        }
        if self.unavailable_reason:
            data['unavailable_reason'] = self.unavailable_reason
        return data


@dataclass(frozen=True)
class CategorySpec:
    """A picker category, in display order."""
    id: str
    label: str
    icon: Tuple[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {'id': self.id, 'label': self.label, 'icon': list(self.icon)}


CATEGORIES: Tuple[CategorySpec, ...] = (
    CategorySpec('system', 'System', ('fas', 'desktop')),
    CategorySpec('navigation', 'Navigation', ('fas', 'compass')),
    CategorySpec('media', 'Media Control', ('fas', 'music')),
    CategorySpec('web', 'Web & Apps', ('fas', 'globe')),
    CategorySpec('text', 'Text & Clipboard', ('fas', 'font')),
    CategorySpec('metrics', 'System Metrics', ('fas', 'chart-line')),
    CategorySpec('time', 'Time', ('fas', 'clock')),
    CategorySpec('weather', 'Weather', ('fas', 'cloud-sun')),
    CategorySpec('streaming', 'Streaming', ('fas', 'video')),
    CategorySpec('ai', 'AI Assistants', ('fas', 'robot')),
    CategorySpec('dev', 'Developer', ('fas', 'code')),
    CategorySpec('custom', 'Custom', ('fas', 'puzzle-piece')),
)


def _xp(action: str, **extra: Any) -> Dict[str, Any]:
    """Build a CrossPlatformAction config."""
    return {'action': action, **extra}


# --- System ------------------------------------------------------------------

_SYSTEM: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='program', label='Launch Program', category='system',
        icon=('fas', 'rocket'), action_type='program',
        description='Start an application from its executable path.',
        keywords=('app', 'exe', 'launch', 'open'),
        config_fields=(
            ConfigField('path', 'Program path', 'path', required=True,
                        placeholder='C:\\Program Files\\App\\app.exe'),
            ConfigField('args', 'Arguments', 'text',
                        placeholder='--flag value'),
        ),
    ),
    ActionSpec(
        id='command', label='Run Command', category='system',
        icon=('fas', 'terminal'), action_type='command',
        description='Run a shell command. Disabled unless '
                    'ALLOW_COMMAND_EXECUTION is enabled.',
        keywords=('shell', 'cmd', 'bash', 'terminal'),
        config_fields=(
            ConfigField('command', 'Command', 'text', required=True,
                        placeholder='shutdown /s /t 0'),
        ),
    ),
    ActionSpec(
        id='hotkey', label='Send Hotkey', category='system',
        icon=('fas', 'keyboard'), action_type='hotkey',
        description='Send a keyboard shortcut to the focused window.',
        keywords=('shortcut', 'keys', 'keyboard'),
        config_fields=(
            ConfigField('keys', 'Keys', 'keys', required=True,
                        placeholder='Ctrl+Shift+P'),
        ),
    ),
    ActionSpec(
        id='macro', label='Macro', category='system',
        icon=('fas', 'list'), action_type='macro',
        description='Run a sequence of keystrokes, text, clicks and delays.',
        keywords=('sequence', 'automation', 'steps'),
        config_fields=(ConfigField('steps', 'Steps', 'steps', required=True),),
    ),
    ActionSpec(
        id='shutdown', label='Shut Down', category='system',
        icon=('fas', 'power-off'), action_type='cross_platform',
        default_config=_xp('shutdown'), description='Shut the computer down.',
        keywords=('power', 'off'),
    ),
    ActionSpec(
        id='restart', label='Restart', category='system',
        icon=('fas', 'redo'), action_type='cross_platform',
        default_config=_xp('restart'), description='Restart the computer.',
        keywords=('reboot', 'power'),
    ),
    ActionSpec(
        id='sleep', label='Sleep', category='system',
        icon=('fas', 'moon'), action_type='cross_platform',
        default_config=_xp('sleep'), description='Put the computer to sleep.',
        keywords=('suspend', 'power'),
    ),
    ActionSpec(
        id='lock_screen', label='Lock Screen', category='system',
        icon=('fas', 'lock'), action_type='cross_platform',
        default_config=_xp('lock_screen'), description='Lock the session.',
        keywords=('lock', 'security'),
    ),
    ActionSpec(
        id='screenshot', label='Screenshot', category='system',
        icon=('fas', 'camera'), action_type='cross_platform',
        default_config=_xp('screenshot'),
        description='Capture the screen to an image file.',
        keywords=('capture', 'screen', 'grab'),
    ),
    ActionSpec(
        id='empty_recycle_bin', label='Empty Recycle Bin', category='system',
        icon=('fas', 'trash'), action_type='cross_platform',
        default_config=_xp('empty_recycle_bin'),
        description='Permanently delete everything in the recycle bin.',
        keywords=('trash', 'bin', 'delete'),
    ),
    ActionSpec(
        id='brightness_up', label='Brightness Up', category='system',
        icon=('fas', 'sun'), action_type='cross_platform',
        default_config=_xp('brightness_up'),
        description='Raise display brightness.',
        keywords=('screen', 'display'),
    ),
    ActionSpec(
        id='brightness_down', label='Brightness Down', category='system',
        icon=('fas', 'moon'), action_type='cross_platform',
        default_config=_xp('brightness_down'),
        description='Lower display brightness.',
        keywords=('screen', 'display'),
    ),
    ActionSpec(
        id='ui_brightness', label='Deck Brightness', category='system',
        icon=('fas', 'lightbulb'), action_type='ui_control',
        default_config={'action': 'ui_brightness_down', 'step': 10},
        runs_on=RUNS_FRONTEND,
        description="Dim or brighten VDock's own interface.",
        keywords=('ui', 'dim', 'deck'),
        config_fields=(
            ConfigField('action', 'Adjustment', 'select', required=True,
                        default='ui_brightness_down', options=(
                            {'value': 'ui_brightness_up', 'label': 'Brighter'},
                            {'value': 'ui_brightness_down', 'label': 'Dimmer'},
                            {'value': 'ui_brightness_set',
                             'label': 'Set to value'},
                        )),
            ConfigField('step', 'Step (%)', 'number', default=10),
            ConfigField('value', 'Value (%)', 'number', default=100,
                        help='Used by "Set to value".'),
        ),
    ),
    ActionSpec(
        id='toggle_header', label='Toggle Header', category='system',
        icon=('fas', 'window-maximize'), action_type='ui_control',
        default_config={'action': 'toggle_header'}, runs_on=RUNS_FRONTEND,
        description="Show or hide VDock's header bar.",
        keywords=('ui', 'chrome', 'hide'),
    ),
)

# --- Navigation --------------------------------------------------------------

_NAVIGATION: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='next_page', label='Next Page', category='navigation',
        icon=('fas', 'chevron-right'), action_type='next_page',
        runs_on=RUNS_FRONTEND,
        description='Go to the next page in this scene.',
        keywords=('page', 'forward'),
    ),
    ActionSpec(
        id='previous_page', label='Previous Page', category='navigation',
        icon=('fas', 'chevron-left'), action_type='previous_page',
        runs_on=RUNS_FRONTEND, description='Go to the previous page.',
        keywords=('page', 'back'),
    ),
    ActionSpec(
        id='home_page', label='Home', category='navigation',
        icon=('fas', 'home'), action_type='home_page',
        runs_on=RUNS_FRONTEND, description='Jump to the first page.',
        keywords=('page', 'first', 'home'),
    ),
)

# --- Media -------------------------------------------------------------------

_MEDIA: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='media_play_pause', label='Play / Pause', category='media',
        icon=('fas', 'play'), action_type='cross_platform',
        default_config=_xp('media_play_pause'),
        description='Toggle playback in the active media app.',
        keywords=('music', 'video', 'pause', 'play'),
    ),
    ActionSpec(
        id='media_next', label='Next Track', category='media',
        icon=('fas', 'forward'), action_type='cross_platform',
        default_config=_xp('media_next'),
        description='Skip to the next track.', keywords=('music', 'skip'),
    ),
    ActionSpec(
        id='media_previous', label='Previous Track', category='media',
        icon=('fas', 'backward'), action_type='cross_platform',
        default_config=_xp('media_previous'),
        description='Go back to the previous track.',
        keywords=('music', 'back'),
    ),
    ActionSpec(
        id='media_stop', label='Stop', category='media',
        icon=('fas', 'stop'), action_type='cross_platform',
        default_config=_xp('media_stop'), description='Stop playback.',
        keywords=('music', 'halt'),
    ),
    ActionSpec(
        id='volume_up', label='Volume Up', category='media',
        icon=('fas', 'volume-up'), action_type='cross_platform',
        default_config=_xp('volume_up'), description='Raise system volume.',
        keywords=('sound', 'louder', 'audio'),
    ),
    ActionSpec(
        id='volume_down', label='Volume Down', category='media',
        icon=('fas', 'volume-down'), action_type='cross_platform',
        default_config=_xp('volume_down'), description='Lower system volume.',
        keywords=('sound', 'quieter', 'audio'),
    ),
    ActionSpec(
        id='volume_mute', label='Mute', category='media',
        icon=('fas', 'volume-mute'), action_type='cross_platform',
        default_config=_xp('volume_mute'), description='Mute system audio.',
        keywords=('sound', 'silence', 'audio'),
    ),
    ActionSpec(
        id='microphone_mute', label='Mute Microphone', category='media',
        icon=('fas', 'microphone-slash'), action_type='cross_platform',
        default_config=_xp('microphone_mute'),
        description='Mute the default microphone.',
        keywords=('mic', 'mute', 'meeting'),
    ),
    ActionSpec(
        id='microphone_unmute', label='Unmute Microphone', category='media',
        icon=('fas', 'microphone'), action_type='cross_platform',
        default_config=_xp('microphone_unmute'),
        description='Unmute the default microphone.',
        keywords=('mic', 'unmute', 'meeting'),
    ),
)

# --- Web & apps --------------------------------------------------------------

_WEB: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='url', label='Open URL', category='web',
        icon=('fas', 'globe'), action_type='url',
        description='Open a web address in the default browser.',
        keywords=('web', 'link', 'browser', 'site'),
        config_fields=(
            ConfigField('url', 'URL', 'url', required=True,
                        placeholder='https://example.com'),
        ),
    ),
    ActionSpec(
        id='open_app', label='Open Application', category='web',
        icon=('fas', 'window-restore'), action_type='cross_platform',
        default_config=_xp('open_app'),
        description='Open an application by name or path.',
        keywords=('app', 'launch', 'program'),
        config_fields=(
            ConfigField('app', 'Application', 'text', required=True,
                        placeholder='notepad'),
        ),
    ),
    ActionSpec(
        id='close_app', label='Close Application', category='web',
        icon=('fas', 'window-close'), action_type='cross_platform',
        default_config=_xp('close_app'),
        description='Close a running application by process name.',
        keywords=('app', 'quit', 'kill'),
        config_fields=(
            ConfigField('app', 'Process name', 'text', required=True,
                        placeholder='notepad.exe'),
        ),
    ),
    ActionSpec(
        id='open_folder', label='Open Folder', category='web',
        icon=('fas', 'folder-open'), action_type='cross_platform',
        default_config=_xp('open_folder'),
        description='Open a folder in the file explorer.',
        keywords=('directory', 'explorer', 'files'),
        config_fields=(
            ConfigField('path', 'Folder path', 'path', required=True,
                        placeholder='C:\\Users\\me\\Projects'),
        ),
    ),
    ActionSpec(
        id='open_file', label='Open File', category='web',
        icon=('fas', 'file'), action_type='cross_platform',
        default_config=_xp('open_file'),
        description='Open a file with its default application.',
        keywords=('document', 'files'),
        config_fields=(
            ConfigField('path', 'File path', 'path', required=True,
                        placeholder='C:\\Users\\me\\notes.txt'),
        ),
    ),
)

# --- Text & clipboard --------------------------------------------------------
# These compose MacroAction steps rather than introducing new action types.

_TEXT: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='type_text', label='Type Text', category='text',
        icon=('fas', 'font'), action_type='macro',
        default_config={'steps': [{'type': 'text', 'text': ''}]},
        description='Type a string into the focused window.',
        keywords=('text', 'write', 'snippet'),
        config_fields=(
            ConfigField('steps', 'Text', 'steps', required=True),
        ),
    ),
    ActionSpec(
        id='clipboard_copy', label='Copy to Clipboard', category='text',
        icon=('fas', 'copy'), action_type='macro',
        default_config={'steps': [{'type': 'clipboard_copy'}]},
        description='Send Ctrl+C to the focused window.',
        keywords=('copy', 'clipboard'),
    ),
    ActionSpec(
        id='clipboard_paste', label='Paste from Clipboard', category='text',
        icon=('fas', 'paste'), action_type='macro',
        default_config={'steps': [{'type': 'clipboard_paste'}]},
        description='Send Ctrl+V to the focused window.',
        keywords=('paste', 'clipboard'),
    ),
    ActionSpec(
        id='clipboard_set', label='Set Clipboard', category='text',
        icon=('fas', 'clipboard'), action_type='macro',
        default_config={'steps': [{'type': 'clipboard_set', 'text': ''}]},
        description='Put a fixed string on the clipboard without pasting.',
        keywords=('clipboard', 'snippet'),
        config_fields=(
            ConfigField('steps', 'Clipboard text', 'steps', required=True),
        ),
    ),
)

# --- Metrics -----------------------------------------------------------------
# Widgets: they render live values and are never dispatched on press.


def _metric(
    entry_id: str, label: str, icon: str, keywords: Tuple[str, ...]
) -> ActionSpec:
    return ActionSpec(
        id=entry_id, label=label, category='metrics', icon=('fas', icon),
        action_type=entry_id, runs_on=RUNS_WIDGET,
        description=f'Live {label.lower()} readout.', keywords=keywords,
        config_fields=(
            ConfigField('refresh_interval', 'Refresh (seconds)', 'number',
                        default=2),
        ),
    )


_METRICS: Tuple[ActionSpec, ...] = (
    _metric('metric_cpu_usage', 'CPU Usage', 'microchip',
            ('cpu', 'processor', 'load')),
    _metric('metric_memory', 'Memory', 'memory', ('ram', 'memory')),
    _metric('metric_harddisk', 'Disk', 'hdd', ('disk', 'storage', 'drive')),
    _metric('metric_internet_speed', 'Network', 'network-wired',
            ('net', 'bandwidth')),
    _metric('metric_cpu_temperature', 'CPU Temperature', 'temperature-high',
            ('cpu', 'temp', 'heat')),
    _metric('metric_cpu_frequency', 'CPU Frequency', 'wave-square',
            ('cpu', 'clock', 'ghz')),
    _metric('metric_cpu_power', 'CPU Power', 'bolt',
            ('cpu', 'watts', 'power')),
    _metric('metric_gpu_usage', 'GPU Usage', 'display', ('gpu', 'graphics')),
    _metric('metric_gpu_temperature', 'GPU Temperature', 'temperature-high',
            ('gpu', 'temp')),
    _metric('metric_gpu_frequency', 'GPU Frequency', 'wave-square',
            ('gpu', 'clock')),
    _metric('metric_gpu_memory_usage', 'GPU Memory', 'memory',
            ('gpu', 'vram')),
    _metric('metric_gpu_memory_freq', 'GPU Memory Clock', 'wave-square',
            ('gpu', 'vram')),
)

# --- Time & weather ----------------------------------------------------------

_TIME: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='time_world_clock', label='World Clock', category='time',
        icon=('fas', 'clock'), action_type='time_world_clock',
        runs_on=RUNS_WIDGET,
        description='Show the time in a chosen timezone.',
        keywords=('clock', 'time', 'timezone'),
        config_fields=(
            ConfigField('timezone', 'Timezone', 'text', default='UTC',
                        placeholder='Europe/London'),
        ),
    ),
    ActionSpec(
        id='time_timer', label='Timer', category='time',
        icon=('fas', 'stopwatch'), action_type='time_timer',
        runs_on=RUNS_WIDGET, description='Count up from zero.',
        keywords=('stopwatch', 'timer', 'elapsed'),
        config_fields=(
            ConfigField('timer_duration', 'Duration (seconds)', 'number',
                        default=300),
        ),
    ),
    ActionSpec(
        id='time_countdown', label='Countdown', category='time',
        icon=('fas', 'hourglass-half'), action_type='time_countdown',
        runs_on=RUNS_WIDGET, description='Count down to a target time.',
        keywords=('countdown', 'timer', 'deadline'),
        config_fields=(
            ConfigField('countdown_target', 'Target', 'text',
                        placeholder='2026-12-31T23:59'),
        ),
    ),
    ActionSpec(
        id='calendar', label='Calendar', category='time',
        icon=('fas', 'calendar'), action_type='calendar',
        runs_on=RUNS_WIDGET, description='Show a small calendar.',
        keywords=('date', 'month', 'calendar'),
    ),
)

_WEATHER: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='weather', label='Weather', category='weather',
        icon=('fas', 'cloud-sun'), action_type='weather',
        runs_on=RUNS_WIDGET,
        description='Current conditions for a location.',
        keywords=('forecast', 'temperature', 'weather'),
        config_fields=(
            ConfigField('weather_location', 'Location', 'text',
                        placeholder='London (blank = auto)'),
        ),
    ),
)

# --- Custom / extensibility --------------------------------------------------

_CUSTOM: Tuple[ActionSpec, ...] = (
    ActionSpec(
        id='multi_action', label='Multi-Action', category='custom',
        icon=('fas', 'layer-group'), action_type='multi_action',
        description='Run several actions one after another.',
        keywords=('chain', 'sequence', 'combo'),
        config_fields=(
            ConfigField('actions', 'Actions', 'steps', required=True),
        ),
    ),
    ActionSpec(
        id='cross_platform', label='Cross-Platform Action', category='custom',
        icon=('fas', 'globe-americas'), action_type='cross_platform',
        description='Any built-in system action, chosen by name.',
        keywords=('system', 'advanced'),
        config_fields=(
            ConfigField('action', 'Action', 'text', required=True,
                        placeholder='volume_up'),
        ),
    ),
)


ACTION_CATALOG: Tuple[ActionSpec, ...] = (
    _SYSTEM + _NAVIGATION + _MEDIA + _WEB + _TEXT
    + _METRICS + _TIME + _WEATHER + _CUSTOM
)

CATALOG_BY_ID: Dict[str, ActionSpec] = {spec.id: spec for spec in ACTION_CATALOG}


def action_types() -> set:
    """Every distinct ``action_type`` the catalog can produce."""
    return {spec.action_type for spec in ACTION_CATALOG}


def dispatched_action_types() -> set:
    """Action types that must have an ActionExecutor handler.

    Frontend- and widget-only entries are excluded: they never reach
    ``POST /api/actions/execute``.
    """
    return {
        spec.action_type for spec in ACTION_CATALOG
        if spec.runs_on == RUNS_BACKEND
    }


def catalog_to_dict(extra: Optional[List[ActionSpec]] = None) -> Dict[str, Any]:
    """Serialise the catalog for ``GET /api/actions/catalog``.

    ``extra`` carries plugin-contributed specs so integration packs appear in
    the picker without the frontend knowing anything about them.
    """
    specs = list(ACTION_CATALOG) + list(extra or ())
    used = {spec.category for spec in specs}
    return {
        'categories': [c.to_dict() for c in CATEGORIES if c.id in used],
        'actions': [spec.to_dict() for spec in specs],
    }
