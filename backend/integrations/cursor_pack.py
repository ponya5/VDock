"""Cursor pack.

Covers the AI surface that matters for a dev deck: Composer, chat, inline
edit and accept/reject.

Like the Copilot pack, these are keystrokes sent to a focused editor -- see
``editor_base.py`` for the focus guard.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import CURSOR_COMMANDS, CURSOR_EXES


class Plugin(KeystrokeEditorPlugin):
    """Cursor actions, driven by Cursor keybindings."""

    plugin_id = 'cursor'
    plugin_name = 'Cursor'
    plugin_description = (
        'Composer, AI chat, inline edit and diff controls for the Cursor editor.'
    )
    commands = CURSOR_COMMANDS
    category = 'dev'
    editor_label = 'Cursor'
    editor_exes = CURSOR_EXES
