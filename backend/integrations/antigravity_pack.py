"""Antigravity pack.

Covers Google's agentic IDE: the agent panel/conversation surface, the
Agent Manager, inline AI commands, and the VS Code-inherited nav chords.

Like the Cursor pack, these are keystrokes sent to a focused editor --
see ``editor_base.py`` for the focus guard.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import ANTIGRAVITY_COMMANDS, ANTIGRAVITY_EXES


class Plugin(KeystrokeEditorPlugin):
    """Antigravity actions, driven by Antigravity keybindings."""

    plugin_id = 'antigravity'
    plugin_name = 'Antigravity'
    plugin_description = (
        'Agent conversations, Agent Manager, inline AI and editor controls '
        'for the Antigravity IDE.'
    )
    commands = ANTIGRAVITY_COMMANDS
    category = 'dev'
    editor_label = 'Antigravity'
    editor_exes = ANTIGRAVITY_EXES
