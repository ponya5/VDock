"""Antigravity keybindings.

Verified against Antigravity's published shortcut list (Google's
Code-OSS-based agentic IDE). The agent-input chords matter most:

- Ctrl+Shift+I opens/focuses the agent panel idempotently, so anything
  that types afterwards starts with it.
- Ctrl+L *toggles* the agent panel (pressed while focused it closes it)
  — it is bound alone, never before typed text.
- Ctrl+Shift+L starts a new conversation thread on the agent surface.
- Enter submits the agent input; Shift+Enter is the line break.
"""
from typing import Tuple

from .base import (
    ANTIGRAVITY_EXES, AppProfile, Command, RISK_INPUT, state_actions_of,
)

FOCUS_AGENT_KEYS = ('ctrl', 'shift', 'i')
NEW_THREAD_KEYS = ('ctrl', 'shift', 'l')
AGENT_NEWLINE_KEYS = ('shift', 'enter')

ANTIGRAVITY_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='antigravity_prompt', label='New Agent Prompt',
        description='Start a new conversation thread and send a prompt '
                    '(Ctrl+Shift+L, type, Enter).',
        keys=NEW_THREAD_KEYS, icon='paper-plane',
        types_text='Explain the current file.', submit=True,
        newline_keys=AGENT_NEWLINE_KEYS,
        keywords=('antigravity', 'prompt', 'agent', 'ask', 'send', 'type'),
        target_exes=ANTIGRAVITY_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='antigravity_followup', label='Send Follow-up',
        description='Send a message to the current conversation '
                    '(Ctrl+Shift+I, type, Enter). Defaults to "continue".',
        keys=FOCUS_AGENT_KEYS, icon='reply',
        types_text='continue', submit=True,
        newline_keys=AGENT_NEWLINE_KEYS,
        keywords=('antigravity', 'followup', 'continue', 'reply', 'send'),
        target_exes=ANTIGRAVITY_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='antigravity_submit', label='Submit',
        description='Send the message typed in the agent input '
                    '(Ctrl+Shift+I, Enter) — focusing the panel first, so '
                    'Enter never lands in a file.',
        keys=FOCUS_AGENT_KEYS, after_keys=(('enter',),),
        icon='paper-plane',
        keywords=('antigravity', 'submit', 'send', 'enter', 'prompt'),
        target_exes=ANTIGRAVITY_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='antigravity_stop', label='Stop Generating',
        description='Halt the running agent stream (Esc).',
        keys=('escape',), icon='hand',
        keywords=('antigravity', 'stop', 'cancel', 'interrupt', 'halt'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_agent', label='Agent Panel',
        description='Show or hide the agent panel (Ctrl+L).',
        keys=('ctrl', 'l'), icon='comments',
        keywords=('antigravity', 'agent', 'chat', 'panel', 'ai'),
        target_exes=ANTIGRAVITY_EXES, priority=10,
    ),
    Command(
        id='antigravity_new_thread', label='New Conversation',
        description='Start a fresh conversation thread, input focused '
                    '(Ctrl+Shift+L).',
        keys=NEW_THREAD_KEYS, icon='plus',
        keywords=('antigravity', 'new', 'chat', 'thread', 'conversation'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_manager', label='Agent Manager',
        description='Toggle between the editor and the Agent Manager '
                    '(Ctrl+E).',
        keys=('ctrl', 'e'), icon='table-columns',
        keywords=('antigravity', 'manager', 'agents', 'switch', 'editor'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_inline', label='Inline Command',
        description='Inline natural-language AI command in the editor or '
                    'terminal (Ctrl+I).',
        keys=('ctrl', 'i'), icon='wand-magic-sparkles',
        keywords=('antigravity', 'inline', 'command', 'ai', 'edit'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_command_palette', label='Command Palette',
        description='Open the command palette.',
        keys=('ctrl', 'shift', 'p'), icon='terminal',
        keywords=('antigravity', 'palette', 'commands'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_quick_open', label='Quick Open',
        description='Jump to a file by name.',
        keys=('ctrl', 'p'), icon='magnifying-glass',
        keywords=('antigravity', 'file', 'open', 'goto'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_toggle_terminal', label='Toggle Terminal',
        description='Show or hide the integrated terminal.',
        keys=('ctrl', '`'), icon='terminal',
        keywords=('antigravity', 'terminal', 'console', 'shell'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_toggle_sidebar', label='Toggle Sidebar',
        description='Show or hide the sidebar.',
        keys=('ctrl', 'b'), icon='bars',
        keywords=('antigravity', 'sidebar', 'explorer'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_find_in_files', label='Find in Files',
        description='Search across the whole project.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('antigravity', 'search', 'find', 'grep'),
        target_exes=ANTIGRAVITY_EXES,
    ),
    Command(
        id='antigravity_settings', label='Settings',
        description='Open Antigravity settings (Ctrl+,).',
        keys=('ctrl', ','), icon='gear',
        keywords=('antigravity', 'settings', 'preferences'),
        target_exes=ANTIGRAVITY_EXES,
    ),
)

ANTIGRAVITY_PROFILE = AppProfile(
    id='antigravity', label='Antigravity', exes=ANTIGRAVITY_EXES,
    commands=ANTIGRAVITY_COMMANDS, kind='editor',
    # Reserved for a future Antigravity hook — 'antigravity' is already
    # in agent_state.ALLOWED_SOURCES, so a hook that posts gets live
    # state rows; until then the 'unknown' row is unreachable.
    status_source='antigravity',
    state_actions=(
        ('ready', state_actions_of(
            'antigravity_submit', ('antigravity_followup', 'Continue'),
            ('antigravity_new_thread', 'New Conversation'),
        )),
        ('working', state_actions_of(
            ('antigravity_stop', 'Stop'),
        )),
        ('unknown', state_actions_of(
            'antigravity_submit', ('antigravity_followup', 'Continue'),
            ('antigravity_stop', 'Stop'),
            ('antigravity_new_thread', 'New Conversation'),
        )),
    ),
    prompt_command='antigravity_followup',
    default_layout=(
        ('antigravity_agent', 'antigravity_new_thread',
         'antigravity_manager', 'antigravity_inline'),
        ('antigravity_submit', 'antigravity_stop',
         'antigravity_toggle_terminal', 'antigravity_quick_open'),
    ),
)
