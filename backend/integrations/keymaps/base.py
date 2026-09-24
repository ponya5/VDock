"""The Command dataclass shared by every app keymap.

Editor keybindings live as data rather than code because they change between
versions, differ per platform, and users remap them. When a shortcut changes,
one module changes and nothing else does.

`risk` and `requires_session` are declared here in phase 1 but not yet enforced
-- editor_base starts honouring them in phase 2. Declaring them up front means
each app's keymap is written once, with its blast radius already recorded,
rather than being revisited later.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: Process names for the editors these keymaps target.
VSCODE_EXES = ('code.exe', 'codium.exe')
CURSOR_EXES = ('cursor.exe',)
JETBRAINS_EXES = (
    'idea64.exe', 'pycharm64.exe', 'webstorm64.exe', 'phpstorm64.exe',
    'rider64.exe', 'clion64.exe', 'goland64.exe', 'datagrip64.exe',
    'rubymine64.exe',
)
VISUAL_STUDIO_EXES = ('devenv.exe',)
DEVIN_EXES = ('devin.exe',)

#: Processes that can own a terminal window hosting a CLI agent.
#: VS Code / Cursor are deliberately absent -- a keystroke meant for an
#: integrated terminal would otherwise be typed into the editor itself.
TERMINAL_EXES = (
    'windowsterminal.exe', 'wt.exe', 'cmd.exe', 'powershell.exe', 'pwsh.exe',
    'conhost.exe', 'mintty.exe', 'wezterm-gui.exe', 'alacritty.exe',
    'tabby.exe',
)

#: How much damage a mistargeted keystroke could do.
#: 'safe'        -- toggles a view; harmless anywhere.
#: 'input'       -- types or submits; needs a confirmed live session.
#: 'destructive' -- exits, kills agents, answers a permission prompt.
RISK_SAFE = 'safe'
RISK_INPUT = 'input'
RISK_DESTRUCTIVE = 'destructive'


@dataclass(frozen=True)
class Command:
    """One editor command, expressed as macro steps."""
    id: str
    label: str
    description: str
    keys: Tuple[str, ...]
    icon: str = 'keyboard'
    keywords: Tuple[str, ...] = ()
    #: Process names this command expects to be focused. Empty means any.
    target_exes: Tuple[str, ...] = ()
    #: Text typed after the keystroke, e.g. a chat slash command.
    types_text: Optional[str] = None
    #: Press Enter after typing.
    submit: bool = False
    #: See RISK_* above. Enforced by editor_base.
    risk: str = RISK_SAFE
    #: Requires a detected agent session. Enforced by editor_base via
    #: `session_marker`.
    requires_session: bool = False
    #: Process marker scanned for when requires_session is set ('claude'
    #: matches claude.exe, node .../claude, claude.cmd, ...).
    session_marker: Optional[str] = None
    #: Prefer target windows whose title contains this substring when several
    #: windows share the same process (e.g. the terminal tab running claude).
    window_title_hint: Optional[str] = None
    #: Press the chord this many times (Ctrl+D twice exits Claude Code).
    repeat: int = 1
    #: Follow-up keystrokes pressed after ``keys``, one tuple per stroke.
    #: Expresses two-stroke chords like Ctrl+X Ctrl+K (kill agents) or
    #: Ctrl+X Enter (queue submit): ``keys=('ctrl','x')`` plus
    #: ``after_keys=(('ctrl','k'),)``.
    after_keys: Tuple[Tuple[str, ...], ...] = ()
    #: Chord that inserts a line break without submitting. When set, typed
    #: text is split on newlines and each break sent as this chord -- in a
    #: TUI a raw newline is Enter and would submit the first line alone.
    newline_keys: Tuple[str, ...] = ()
    #: Mirrors the categories the frontend shortcut list used.
    category: str = 'general'
    #: Higher sorts earlier when auto-populating a deck.
    priority: int = 5

    def to_macro_steps(self, text_override: Optional[str] = None) -> List[Dict[str, Any]]:
        """Build the macro step list MacroAction executes."""
        steps: List[Dict[str, Any]] = []

        if self.keys:
            # MacroAction treats an empty key list as a failure, so typed-only
            # commands must not emit a hotkey step at all.
            for press in range(max(1, self.repeat)):
                if press:
                    steps.append({'type': 'delay', 'delay': 150})
                steps.append({'type': 'hotkey', 'keys': list(self.keys)})
            for stroke in self.after_keys:
                steps.append({'type': 'delay', 'delay': 150})
                steps.append({'type': 'hotkey', 'keys': list(stroke)})

        text = text_override if text_override is not None else self.types_text
        if text:
            # The editor needs a moment to focus its input before typing.
            steps.append({'type': 'delay', 'delay': 350})
            steps.extend(self._text_steps(text))

        if self.submit and text:
            steps.append({'type': 'delay', 'delay': 120})
            steps.append({'type': 'hotkey', 'keys': ['enter']})

        return steps

    def _text_steps(self, text: str) -> List[Dict[str, Any]]:
        if not self.newline_keys:
            return [{'type': 'text', 'text': text}]
        steps: List[Dict[str, Any]] = []
        lines = text.replace('\r\n', '\n').split('\n')
        for line_index, line in enumerate(lines):
            if line_index:
                steps.append({'type': 'hotkey', 'keys': list(self.newline_keys)})
            if line:
                steps.append({'type': 'text', 'text': line})
        return steps


@dataclass(frozen=True)
class StateAction:
    """One agent action-bar entry: a command, optionally relabelled for the
    state it appears in (Enter reads "Approve" in a permission prompt)."""
    command_id: str
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {'id': self.command_id, 'label': self.label}


def state_actions_of(*entries: Any) -> Tuple[StateAction, ...]:
    """Build StateActions from command ids or (command_id, label) pairs."""
    return tuple(
        StateAction(*entry) if isinstance(entry, tuple) else StateAction(entry)
        for entry in entries
    )


@dataclass(frozen=True)
class AppProfile:
    """One application: how to recognise it, what it can do, how it lays out.

    `default_layout` is rows of command ids. Phase 4 builds the context scene
    from it, and keeping the same grid positions across apps is deliberate --
    muscle memory should survive an alt-tab.
    """
    id: str
    label: str
    exes: Tuple[str, ...]
    commands: Tuple[Command, ...]
    #: 'editor' focuses the app itself; 'terminal_agent' runs inside a terminal.
    kind: str = 'editor'
    default_layout: Tuple[Tuple[str, ...], ...] = ()
    #: Agent-state source key reported by this app's hooks ('claude',
    #: 'cursor', see integrations/agent_state). None means no live status.
    status_source: Optional[str] = None
    #: Action-type ids owned by this profile that are NOT keymap commands --
    #: plugin actions like claude_pack's `claude_prompt`. The frontend's
    #: scene→app vote maps these to the profile so a scene built purely of
    #: plugin buttons still resolves (DL-033 follow-up).
    action_types: Tuple[str, ...] = ()
    #: Agent state ('ready' | 'working' | 'permission' | 'unknown') -> the
    #: actions that fit it, in display order. Drives the dashboard's agent
    #: action bar (DL-064). 'unknown' is used when the agent runs but
    #: reports no state (no hook installed).
    state_actions: Tuple[Tuple[str, Tuple[StateAction, ...]], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Serialise for GET /api/app-profiles."""
        return {
            'id': self.id,
            'label': self.label,
            'exes': list(self.exes),
            'kind': self.kind,
            'status_source': self.status_source,
            'action_types': list(self.action_types),
            'default_layout': [list(row) for row in self.default_layout],
            'state_actions': {
                state: [action.to_dict() for action in actions]
                for state, actions in self.state_actions
            },
            'commands': [
                {
                    'id': cmd.id,
                    'label': cmd.label,
                    'description': cmd.description,
                    'keys': list(cmd.keys),
                    'icon': cmd.icon,
                    'keywords': list(cmd.keywords),
                    'category': cmd.category,
                    'priority': cmd.priority,
                    'risk': cmd.risk,
                    'requires_session': cmd.requires_session,
                    'session_marker': cmd.session_marker,
                    'window_title_hint': cmd.window_title_hint,
                    'repeat': cmd.repeat,
                    'after_keys': [list(stroke) for stroke in cmd.after_keys],
                }
                for cmd in self.commands
            ],
        }
