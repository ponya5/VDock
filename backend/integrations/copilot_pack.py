"""GitHub Copilot pack.

Copilot has no external control surface, so these actions focus VS Code and
send the keystrokes a human would press. Bindings live in ``keymaps.py``;
the focus guard and dispatch live in ``editor_base.py``.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import COPILOT_COMMANDS, VSCODE_EXES


class Plugin(KeystrokeEditorPlugin):
    """GitHub Copilot actions, driven by VS Code keybindings."""

    plugin_id = 'copilot'
    plugin_name = 'GitHub Copilot'
    plugin_description = (
        'Drive Copilot Chat, inline suggestions and slash commands in VS Code.'
    )
    commands = COPILOT_COMMANDS
    category = 'ai'
    editor_label = 'VS Code'
    editor_exes = VSCODE_EXES
