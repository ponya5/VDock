"""Cursor keybindings.

Chat input focus keys, verified against Cursor 3.21's workbench bundle:
Ctrl+L / Ctrl+I *toggle* the agent pane (pressed while it is focused they
close it), so nothing that types afterwards may start with them. Ctrl+Shift+L
("Open New Agent Chat") always opens and focuses a fresh input, and
Ctrl+Shift+Y ("Focus Chat Followup", Windows binding) focuses the current
chat's input. Both chat inputs take Shift+Enter as a line break.
"""
from typing import Tuple

from .base import AppProfile, Command, CURSOR_EXES, RISK_INPUT, state_actions_of

NEW_AGENT_CHAT_KEYS = ('ctrl', 'shift', 'l')
FOCUS_CHAT_FOLLOWUP_KEYS = ('ctrl', 'shift', 'y')
CHAT_NEWLINE_KEYS = ('shift', 'enter')

CURSOR_COMMANDS: Tuple[Command, ...] = (
    Command(
        id='cursor_prompt', label='New Agent Prompt',
        description='Open a new agent chat and send a prompt to it '
                    '(Ctrl+Shift+L, type, Enter).',
        keys=NEW_AGENT_CHAT_KEYS, icon='paper-plane',
        types_text='Explain the current file.', submit=True,
        newline_keys=CHAT_NEWLINE_KEYS,
        keywords=('cursor', 'prompt', 'agent', 'ask', 'send', 'type'),
        target_exes=CURSOR_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='cursor_followup', label='Send Follow-up',
        description='Send a message to the current agent chat '
                    '(Ctrl+Shift+Y, type, Enter). Defaults to "continue".',
        keys=FOCUS_CHAT_FOLLOWUP_KEYS, icon='reply',
        types_text='continue', submit=True,
        newline_keys=CHAT_NEWLINE_KEYS,
        keywords=('cursor', 'followup', 'continue', 'reply', 'send'),
        target_exes=CURSOR_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='cursor_submit', label='Submit',
        description='Send the message typed in the current agent chat '
                    '(Ctrl+Shift+Y, Enter) — focusing the chat first, so '
                    'Enter never lands in a file.',
        keys=FOCUS_CHAT_FOLLOWUP_KEYS, after_keys=(('enter',),),
        icon='paper-plane',
        keywords=('cursor', 'submit', 'send', 'enter', 'prompt'),
        target_exes=CURSOR_EXES, risk=RISK_INPUT, priority=10,
    ),
    Command(
        id='cursor_cancel', label='Stop Generating',
        description='Cancel the running agent / chat generation '
                    '(Ctrl+Shift+Backspace).',
        keys=('ctrl', 'shift', 'backspace'), icon='hand',
        keywords=('cursor', 'stop', 'cancel', 'interrupt', 'generation'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_chat', label='Cursor Chat',
        description='Open the Cursor AI chat pane.',
        keys=('ctrl', 'l'), icon='comments',
        keywords=('cursor', 'chat', 'ai', 'ask'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_composer', label='Cursor Composer',
        description='Open Composer for multi-file edits.',
        keys=('ctrl', 'i'), icon='wand-magic-sparkles',
        keywords=('cursor', 'composer', 'agent', 'multi-file'),
        target_exes=CURSOR_EXES, category='general', priority=10,
    ),
    Command(
        id='cursor_composer_full', label='Composer (Full Screen)',
        description='Open Composer in full screen.',
        keys=('ctrl', 'shift', 'i'), icon='expand',
        keywords=('cursor', 'composer', 'fullscreen'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_inline_edit', label='Cursor Inline Edit',
        description='Edit the selection in place with AI.',
        keys=('ctrl', 'k'), icon='pen',
        keywords=('cursor', 'edit', 'inline', 'k'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_new_chat', label='New Agent Chat',
        description='Open a fresh agent chat, input focused (Ctrl+Shift+L).',
        keys=NEW_AGENT_CHAT_KEYS, icon='plus',
        keywords=('cursor', 'new', 'chat', 'reset'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_accept', label='Accept Diff',
        description='Accept the suggested change.',
        keys=('ctrl', 'enter'), icon='check',
        keywords=('cursor', 'accept', 'apply', 'diff'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_reject', label='Reject Diff',
        description='Reject the suggested change.',
        keys=('ctrl', 'backspace'), icon='xmark',
        keywords=('cursor', 'reject', 'discard', 'diff'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_command_palette', label='Command Palette',
        description='Open the command palette.',
        keys=('ctrl', 'shift', 'p'), icon='terminal',
        keywords=('cursor', 'palette', 'commands'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_quick_open', label='Quick Open',
        description='Jump to a file by name.',
        keys=('ctrl', 'p'), icon='magnifying-glass',
        keywords=('cursor', 'file', 'open', 'goto'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_toggle_terminal', label='Toggle Terminal',
        description='Show or hide the integrated terminal.',
        keys=('ctrl', '`'), icon='terminal',
        keywords=('cursor', 'terminal', 'console', 'shell'),
        target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_toggle_sidebar', label='Toggle Sidebar',
        description='Show or hide the sidebar.',
        keys=('ctrl', 'b'), icon='bars',
        keywords=('cursor', 'sidebar', 'explorer'), target_exes=CURSOR_EXES,
    ),
    Command(
        id='cursor_find_in_files', label='Find in Files',
        description='Search across the whole project.',
        keys=('ctrl', 'shift', 'f'), icon='magnifying-glass',
        keywords=('cursor', 'search', 'find', 'grep'), target_exes=CURSOR_EXES,
    ),
)

CURSOR_PROFILE = AppProfile(
    id='cursor', label='Cursor', exes=CURSOR_EXES,
    commands=CURSOR_COMMANDS, kind='editor',
    status_source='cursor',
    # Cursor's hooks cannot report a pending approval, so there is no
    # 'permission' row: Accept/Reject stay reachable in every state instead.
    state_actions=(
        ('ready', state_actions_of(
            'cursor_submit', ('cursor_followup', 'Continue'),
            ('cursor_new_chat', 'New Chat'),
            ('cursor_accept', 'Accept'), ('cursor_reject', 'Reject'),
        )),
        ('working', state_actions_of(
            ('cursor_cancel', 'Stop'), ('cursor_accept', 'Accept'),
            ('cursor_reject', 'Reject'),
        )),
        ('unknown', state_actions_of(
            'cursor_submit', ('cursor_followup', 'Continue'),
            ('cursor_cancel', 'Stop'), ('cursor_new_chat', 'New Chat'),
        )),
    ),
    prompt_command='cursor_followup',
    default_layout=(
        ('cursor_composer', 'cursor_chat', 'cursor_accept', 'cursor_reject'),
        ('cursor_inline_edit', 'cursor_new_chat', 'cursor_toggle_terminal', 'cursor_quick_open'),
    ),
)
