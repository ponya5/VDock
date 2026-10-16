"""Codex CLI keybindings — terminal-agent shape like Claude Code / Devin.

Codex runs as a Rust TUI in whatever terminal hosts it, so commands are
keystrokes or typed slash commands. ``session_marker='codex'`` lets the
resolver find the Codex process's host window regardless of terminal.

Approval chords verified against codex-rs v0.145 sources (DL-013
follow-up): ``approval_overlay.rs`` routes single-key option shortcuts
before list navigation — 'y' approve, 'a' approve-for-session, 'n' deny,
Esc cancel — and ``keymap.rs`` built-in defaults bind the composer
newline to Ctrl+J. Typed 'y'/'n' are used (not Enter/Esc) so a decision
never depends on which option happens to be highlighted.
"""
from typing import Tuple

from .base import (
    AppProfile,
    Command,
    RISK_DESTRUCTIVE,
    RISK_INPUT,
    RISK_SAFE,
    TERMINAL_EXES,
    state_actions_of,
)

_CODEX = {
    'target_exes': TERMINAL_EXES,
    'window_title_hint': 'codex',
    'session_marker': 'codex',
    # Ctrl+J is the composer newline: a multi-line prompt stays one prompt.
    'newline_keys': ('ctrl', 'j'),
    'category': 'general',
}

CODEX_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='codex_interrupt', label='Interrupt Codex',
        description='Cancel the current turn (Esc).',
        keys=('escape',), icon='hand',
        keywords=('codex', 'stop', 'interrupt', 'cancel', 'esc'),
        risk=RISK_SAFE, **_CODEX,
    ),
    Command(
        id='codex_prompt', label='Send Prompt',
        description='Type a prompt into the live session and send it. '
                    'Defaults to "continue".',
        keys=(), icon='paper-plane', types_text='continue', submit=True,
        keywords=('codex', 'prompt', 'continue', 'send', 'ask', 'type'),
        risk=RISK_INPUT, requires_session=True, priority=10, **_CODEX,
    ),
    Command(
        id='codex_submit', label='Submit',
        description='Send the prompt you typed in the session (Enter).',
        keys=('enter',), icon='paper-plane',
        keywords=('codex', 'submit', 'send', 'enter', 'prompt'),
        risk=RISK_INPUT, requires_session=True, priority=10, **_CODEX,
    ),
    # Approval dialog: explicit single-key options, verified in keymap.rs /
    # approval_overlay.rs — safer than Enter, which takes whatever option
    # is highlighted.
    Command(
        id='codex_approve', label='Approve',
        description='Approve the waiting action (y).',
        keys=(), icon='circle-check', types_text='y',
        keywords=('codex', 'approve', 'yes', 'accept', 'permission',
                  'allow'),
        risk=RISK_INPUT, requires_session=True, **_CODEX,
    ),
    Command(
        id='codex_deny', label='Deny',
        description='Deny the waiting action (n).',
        keys=(), icon='xmark', types_text='n',
        keywords=('codex', 'deny', 'no', 'reject', 'permission',
                  'decline'),
        risk=RISK_INPUT, requires_session=True, **_CODEX,
    ),
    Command(
        id='codex_approvals', label='Approval Mode',
        description='Open the approval-policy menu (/approvals).',
        keys=(), icon='shield', types_text='/approvals', submit=True,
        keywords=('codex', 'approvals', 'mode', 'policy', 'auto'),
        risk=RISK_INPUT, requires_session=True, **_CODEX,
    ),
    Command(
        id='codex_compact', label='Compact',
        description='Compact the conversation context (/compact).',
        keys=(), icon='compress', types_text='/compact', submit=True,
        keywords=('codex', 'compact', 'context', 'summarize'),
        risk=RISK_INPUT, requires_session=True, **_CODEX,
    ),
    Command(
        id='codex_exit', label='Quit Codex',
        description='Exit the session (/quit).',
        keys=(), icon='power-off', types_text='/quit', submit=True,
        keywords=('codex', 'exit', 'quit', 'close'),
        risk=RISK_DESTRUCTIVE, requires_session=True, **_CODEX,
    ),
)

CODEX_PROFILE = AppProfile(
    id='codex', label='Codex', exes=TERMINAL_EXES,
    commands=CODEX_COMMANDS, kind='terminal_agent',
    status_source='codex',
    default_layout=(
        ('codex_prompt', 'codex_interrupt', 'codex_approve', 'codex_deny'),
    ),
    state_actions=(
        ('ready', state_actions_of(
            'codex_submit', ('codex_prompt', 'Continue'),
            ('codex_approvals', 'Mode'), ('codex_compact', 'Compact'),
        )),
        ('working', state_actions_of(
            ('codex_interrupt', 'Interrupt'),
        )),
        ('permission', state_actions_of(
            ('codex_approve', 'Approve'), ('codex_deny', 'Deny'),
        )),
        ('unknown', state_actions_of(
            'codex_submit', ('codex_prompt', 'Continue'),
            ('codex_interrupt', 'Interrupt'),
        )),
    ),
    prompt_command='codex_prompt',
)
