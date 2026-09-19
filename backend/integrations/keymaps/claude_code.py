"""Claude Code keybindings — controls for a live terminal session.

Claude Code is a terminal TUI, so "commands" are keystrokes or typed slash
commands into whatever terminal hosts the session. Every command targets
TERMINAL_EXES and carries ``window_title_hint='claude'`` so window picking
prefers the tab actually running the session.

Slash commands are typed input: ``requires_session`` + ``session_marker``
gate them behind a detected claude process (the interim interlock until the
Phase-3 hook registry lands — see ``integrations/sessions.py``).
"""
from typing import Tuple

from .base import (
    AppProfile,
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    TERMINAL_EXES,
)

_CLAUDE = {
    'target_exes': TERMINAL_EXES,
    'window_title_hint': 'claude',
    'category': 'general',
}

CLAUDE_CODE_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='cc_interrupt', label='Interrupt Claude',
        description='Stop the current response (Esc).',
        keys=('escape',), icon='hand',
        keywords=('claude', 'stop', 'interrupt', 'cancel', 'esc'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_mode', label='Cycle Mode',
        description='Cycle permission mode: normal / auto-accept / plan '
                    '(Shift+Tab).',
        keys=('shift', 'tab'), icon='arrows-rotate',
        keywords=('claude', 'mode', 'plan', 'auto-accept', 'permissions'),
        risk=RISK_SAFE, **_CLAUDE,
    ),
    Command(
        id='cc_clear', label='New Session',
        description='Start a fresh session — clears the context (/clear).',
        keys=(), icon='plus', types_text='/clear', submit=True,
        keywords=('claude', 'new', 'clear', 'reset', 'session'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        priority=10, **_CLAUDE,
    ),
    Command(
        id='cc_resume', label='Resume Session',
        description='Pick up a previous session (/resume).',
        keys=(), icon='rotate-right', types_text='/resume', submit=True,
        keywords=('claude', 'resume', 'continue', 'session'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        **_CLAUDE,
    ),
    Command(
        id='cc_compact', label='Compact Context',
        description='Compact the conversation to free context (/compact).',
        keys=(), icon='compress', types_text='/compact', submit=True,
        keywords=('claude', 'compact', 'context', 'summarize'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        **_CLAUDE,
    ),
    Command(
        id='cc_model', label='Model Picker',
        description='Open the model picker (/model).',
        keys=(), icon='brain', types_text='/model', submit=True,
        keywords=('claude', 'model', 'opus', 'sonnet', 'haiku'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        **_CLAUDE,
    ),
    Command(
        id='cc_add_file', label='Add File',
        description='Open the file-mention picker (@) — the session’s way of '
                    'attaching a file.',
        keys=(), icon='paperclip', types_text='@',
        keywords=('claude', 'file', 'attach', 'mention', 'upload'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        **_CLAUDE,
    ),
    Command(
        id='cc_help', label='Claude Help',
        description='Show available commands (/help).',
        keys=(), icon='circle-question', types_text='/help', submit=True,
        keywords=('claude', 'help', 'commands'),
        risk=RISK_INPUT, requires_session=True, session_marker='claude',
        **_CLAUDE,
    ),
    Command(
        id='cc_exit', label='Quit Claude Code',
        description='Exit the session (Ctrl+C twice).',
        keys=('ctrl', 'c'), icon='power-off', repeat=2,
        keywords=('claude', 'exit', 'quit', 'close'),
        risk=RISK_DESTRUCTIVE, requires_session=True,
        session_marker='claude', **_CLAUDE,
    ),
)

CLAUDE_CODE_PROFILE = AppProfile(
    id='claude-code', label='Claude Code', exes=TERMINAL_EXES,
    commands=CLAUDE_CODE_COMMANDS, kind='terminal_agent',
    # Hooks land in Phase 3; until then sessions are detected by process scan.
    status_source=None,
    default_layout=(
        ('cc_interrupt', 'cc_clear', 'cc_mode', 'cc_model'),
        ('cc_resume', 'cc_compact', 'cc_add_file', 'cc_help'),
    ),
)
