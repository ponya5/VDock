"""Cursor keybindings."""
from typing import Tuple

from .base import AppProfile, Command, CURSOR_EXES

CURSOR_COMMANDS: Tuple[Command, ...] = (
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
        id='cursor_new_chat', label='New Cursor Chat',
        description='Start a fresh chat session.',
        keys=('ctrl', 'shift', 'l'), icon='plus',
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
    default_layout=(
        ('cursor_composer', 'cursor_chat', 'cursor_accept', 'cursor_reject'),
        ('cursor_inline_edit', 'cursor_new_chat', 'cursor_toggle_terminal', 'cursor_quick_open'),
    ),
)
