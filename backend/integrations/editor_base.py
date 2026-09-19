"""Shared machinery for keystroke-driven editor packs (Copilot, Cursor).

Neither GitHub Copilot nor Cursor exposes a CLI or local API, so the only way to
drive them is to send the keystrokes a human would press. That carries a real
hazard: if the wrong window has focus, those keystrokes land somewhere else, and
"type this prompt then press Enter" is destructive in the wrong place.

So every action here checks the foreground process first and refuses to send
anything if the expected editor is not focused. That check is the whole reason
this module exists rather than the packs each calling MacroAction directly.

Note this file is deliberately not named ``*_pack``: PluginManager only scans
modules matching that suffix, so shared helpers are never mistaken for packs.
"""
import logging
import time
from typing import Any, Dict, Optional, Sequence, Tuple

from actions.catalog import ActionSpec, ConfigField, RUNS_BACKEND
from actions.macro_action import MacroAction
from plugins.base_plugin import BasePlugin, PluginInfo
from utils import window_focus

from . import context, sessions
from .keymaps import Command, RISK_DESTRUCTIVE

logger = logging.getLogger('vdock')

# How long to wait after pulling a window forward before typing into it.
FOCUS_SETTLE_SECONDS = 0.25


def foreground_exe() -> Optional[str]:
    """Lowercased process name of the focused window, or None.

    Reads the live foreground window rather than AppMonitor's cache: the
    monitor polls on a multi-second interval, so right after VDock raises a
    window the cache still reports the previous app and the keystroke guard
    would refuse every legitimately-refocused press.
    """
    exe = window_focus.foreground_exe_live()
    if exe is not None:
        return exe
    # Non-Windows or a failed read: fall back to the monitor's view.
    editor = context.current_editor()
    return editor.app_exe


def _resolve_session_host(command: Command) -> Optional[int]:
    """HWND of the window hosting this command's session, or None."""
    if not command.session_marker:
        return None
    return window_focus.find_session_host_window(
        command.session_marker,
        prefer_title=command.window_title_hint,
    )


def send(command: Command, text_override: Optional[str] = None,
         enforce_focus: bool = True, focus_first: bool = True,
         allow_destructive: bool = False) -> Dict[str, Any]:
    """Send ``command`` to the target application.

    Args:
        command: The keymap entry to send.
        text_override: Text to type instead of the command's own.
        enforce_focus: Guard the keystrokes to the expected app. Only turn
            this off deliberately -- it is what stops a prompt being typed
            into whatever happens to be in front.
        focus_first: Bring the target window to the front before sending.
            Required on a touch deck: pressing a button there steals focus,
            so nothing would ever reach the app otherwise.
        allow_destructive: Permit commands classified 'destructive'.
    """
    # Gate on cheap checks first so a refused press never yanks focus around.
    if command.risk == RISK_DESTRUCTIVE and not allow_destructive:
        return {
            'success': False,
            'message': f'{command.label} is a destructive action',
            'details': 'Enable "Allow destructive action" on this button to '
                       'use it.',
        }

    if command.requires_session and command.session_marker:
        if not sessions.session_alive(command.session_marker):
            return {
                'success': False,
                'message': (
                    f'No running {command.session_marker} session detected'
                ),
                'details': (
                    'Start the session first. Without a live session these '
                    'keystrokes could land in a shell prompt instead.'
                ),
            }

    if enforce_focus:
        # Session hosting wins over the exe list when the command carries a
        # session marker: the host window's owner is whatever IDE or terminal
        # spawned the agent (Devin, Cursor, VS Code, Windows Terminal, a
        # classic conhost console...) -- a static exe list can't know it.
        host_hwnd = _resolve_session_host(command)
        if host_hwnd is not None:
            if focus_first:
                if not window_focus.focus_hwnd(host_hwnd):
                    return {
                        'success': False,
                        'message': 'Could not focus the session window',
                        'details': 'The window hosting the session was found '
                                   'but Windows would not bring it forward.',
                    }
                time.sleep(FOCUS_SETTLE_SECONDS)
            fg = window_focus.foreground_hwnd()
            if fg is not None and fg != host_hwnd:
                return {
                    'success': False,
                    'message': 'The session window is not focused',
                    'details': 'Refusing to send keystrokes -- they would '
                               'land in a different window.',
                }
            # fg None means this platform can't verify; fall through.
        elif command.target_exes:
            if focus_first:
                focused = window_focus.focus_app_window(
                    command.target_exes,
                    prefer_title=command.window_title_hint,
                )
                if focused is False:
                    expected = ' or '.join(command.target_exes)
                    return {
                        'success': False,
                        'message': f'No {expected} window found',
                        'details': 'The app is not running, so there is '
                                   'nowhere to send these keystrokes.',
                    }
                if focused:
                    time.sleep(FOCUS_SETTLE_SECONDS)
                # None means this platform can't refocus -- fall through to
                # the foreground check exactly as before.

            current = foreground_exe()
            if current is None:
                return {
                    'success': False,
                    'message': 'Could not determine the focused window',
                    'details': 'Refusing to send keystrokes when the target '
                               'is unknown.',
                }
            if current not in command.target_exes:
                expected = ' or '.join(command.target_exes)
                return {
                    'success': False,
                    'message': f'{expected} is not focused',
                    'details': (
                        f'The focused window is {current}. Focus the editor '
                        f'first -- sending these keystrokes elsewhere could '
                        f'do damage.'
                    ),
                }

    steps = command.to_macro_steps(text_override)
    result = MacroAction({'steps': steps}).execute()

    return {
        'success': result.success,
        'message': result.message if not result.success else command.label,
        'details': result.details,
        'data': result.data,
    }


class KeystrokeEditorPlugin(BasePlugin):
    """Base for packs whose actions are editor keystrokes.

    Subclasses provide the plugin identity and a tuple of Commands.
    """

    #: Overridden by subclasses.
    plugin_id = ''
    plugin_name = ''
    plugin_description = ''
    commands: Tuple[Command, ...] = ()
    category = 'dev'
    #: Human-readable name of the editor, used in unavailability messages.
    editor_label = 'the editor'
    #: Process names that indicate the editor is installed/running.
    editor_exes: Tuple[str, ...] = ()

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id=self.plugin_id,
            name=self.plugin_name,
            version='1.0.0',
            author='VDock',
            description=self.plugin_description,
            actions=[cmd.id for cmd in self.commands],
        )

    def initialize(self) -> bool:
        return True

    def cleanup(self) -> None:
        pass

    def is_available(self) -> tuple:
        # Keystroke packs are always loadable; whether the editor is focused is
        # decided per press, not at load time.
        try:
            from actions.hotkey_action import PYNPUT_AVAILABLE
        except ImportError:
            PYNPUT_AVAILABLE = False

        if not PYNPUT_AVAILABLE:
            return False, (
                'pynput is not installed, so VDock cannot send keystrokes. '
                'Run: pip install pynput'
            )
        return True, ''

    def get_action_specs(self) -> Sequence[ActionSpec]:
        specs = []
        for cmd in self.commands:
            fields = ()
            if cmd.types_text is not None:
                fields += (
                    ConfigField(
                        'text', 'Text to send', 'textarea',
                        default=cmd.types_text,
                        help='Supports {clipboard}, {repo}, {project} and '
                             '{branch}.',
                    ),
                )
            fields += (
                ConfigField(
                    'enforce_focus', f'Only send when {self.editor_label} is focused',
                    'boolean', default=True,
                    help='Strongly recommended. Keystrokes sent to the wrong '
                         'window can be destructive.',
                ),
                ConfigField(
                    'focus_first', 'Bring the app to the front first',
                    'boolean', default=True,
                    help='Finds the app window and raises it before sending. '
                         'Needed on a touch deck, where pressing a button '
                         'takes focus itself.',
                ),
            )
            if cmd.risk == RISK_DESTRUCTIVE:
                fields += (
                    ConfigField(
                        'allow_destructive', 'Allow destructive action',
                        'boolean', default=False,
                        help='Off: the button refuses. On: one tap sends it.',
                    ),
                )

            specs.append(ActionSpec(
                id=cmd.id, label=cmd.label, category=self.category,
                icon=('fas', cmd.icon), action_type=cmd.id,
                runs_on=RUNS_BACKEND, description=cmd.description,
                keywords=cmd.keywords,
                default_config={'enforce_focus': True, 'focus_first': True},
                config_fields=fields,
            ))
        return tuple(specs)

    def get_action_schema(self, action_id: str) -> Dict[str, Any]:
        for spec in self.get_action_specs():
            if spec.id == action_id:
                return {
                    'type': 'object',
                    'properties': {
                        f.name: {'type': 'string', 'title': f.label}
                        for f in spec.config_fields
                    },
                    'required': [],
                }
        return {}

    def execute_action(self, action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        command = next((c for c in self.commands if c.id == action_id), None)
        if command is None:
            return {'success': False, 'message': f'Unknown action: {action_id}'}

        text = config.get('text')
        if text is not None:
            text = context.expand_placeholders(str(text))

        return send(
            command,
            text_override=text,
            enforce_focus=bool(config.get('enforce_focus', True)),
            focus_first=bool(config.get('focus_first', True)),
            allow_destructive=bool(config.get('allow_destructive', False)),
        )
