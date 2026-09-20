"""Claude Code pack — drives a live session running in a terminal.

Unlike ``claude_pack`` (which spawns ``claude -p`` or opens a new terminal),
these actions send keystrokes to the terminal window hosting an already-open
Claude Code session: interrupt, mode cycle, /clear, /resume, /model, the @
file picker and friends. See ``editor_base.py`` for the focus-first delivery
and the session/destructive gating.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import CLAUDE_CODE_COMMANDS, TERMINAL_EXES


class Plugin(KeystrokeEditorPlugin):
    """Claude Code session controls, driven by Claude Code keybindings."""

    plugin_id = 'claude_code'
    plugin_name = 'Claude Code (live session)'
    plugin_description = (
        'Control a Claude Code session already running in a terminal: '
        'interrupt, switch mode, /clear, /resume, /model and more.'
    )
    commands = CLAUDE_CODE_COMMANDS
    category = 'ai'
    editor_label = 'a terminal window'
    editor_exes = TERMINAL_EXES
