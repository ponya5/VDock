"""Devin CLI keybindings — same terminal-agent shape as Claude Code.

Devin runs as a terminal TUI, so commands are keystrokes or typed slash
commands into whatever terminal hosts it. ``session_marker='devin'`` lets the
resolver find the Devin process's host window no matter which terminal (or
editor terminal panel) owns it.
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

_DEVIN = {
    'target_exes': TERMINAL_EXES,
    'window_title_hint': 'devin',
    'session_marker': 'devin',
    'category': 'general',
}

DEVIN_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='devin_interrupt', label='Interrupt Devin',
        description='Cancel the current input / interrupt (Esc).',
        keys=('escape',), icon='hand',
        keywords=('devin', 'stop', 'interrupt', 'cancel', 'esc'),
        risk=RISK_SAFE, **_DEVIN,
    ),
    Command(
        id='devin_help', label='Devin Help',
        description='List the CLI commands (/help).',
        keys=(), icon='circle-question', types_text='/help', submit=True,
        keywords=('devin', 'help', 'commands'),
        risk=RISK_INPUT, requires_session=True, **_DEVIN,
    ),
    Command(
        id='devin_bug', label='Report Bug',
        description='File a bug against the CLI (/bug).',
        keys=(), icon='bug', types_text='/bug', submit=True,
        keywords=('devin', 'bug', 'report', 'issue'),
        risk=RISK_INPUT, requires_session=True, **_DEVIN,
    ),
    Command(
        id='devin_prompt', label='Send Prompt',
        description='Type a prompt into the live session and send it.',
        keys=(), icon='paper-plane', types_text='continue', submit=True,
        keywords=('devin', 'prompt', 'continue', 'send', 'ask', 'type'),
        risk=RISK_INPUT, requires_session=True, priority=10, **_DEVIN,
    ),
    Command(
        id='devin_exit', label='Quit Devin',
        description='Exit the session (Ctrl+C twice).',
        keys=('ctrl', 'c'), icon='power-off', repeat=2,
        keywords=('devin', 'exit', 'quit', 'close'),
        risk=RISK_DESTRUCTIVE, requires_session=True, **_DEVIN,
    ),
)

DEVIN_PROFILE = AppProfile(
    id='devin', label='Devin CLI', exes=TERMINAL_EXES,
    commands=DEVIN_COMMANDS, kind='terminal_agent',
    default_layout=(
        ('devin_prompt', 'devin_interrupt', 'devin_help', 'devin_exit'),
    ),
)
