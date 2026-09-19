"""Devin CLI pack.

Terminal-agent actions for a live Devin CLI session -- the same delivery
model as the Claude Code pack: session_marker resolves the hosting terminal's
window through the process tree, so this works inside any terminal or an
editor's integrated terminal panel.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import DEVIN_COMMANDS, TERMINAL_EXES


class Plugin(KeystrokeEditorPlugin):
    """Devin CLI actions, driven by keystrokes into the hosting terminal."""

    plugin_id = 'devin'
    plugin_name = 'Devin CLI'
    plugin_description = (
        'Session controls for a live Devin CLI running in a terminal.'
    )
    commands = DEVIN_COMMANDS
    category = 'dev'
    editor_label = 'Devin CLI'
    editor_exes = TERMINAL_EXES
