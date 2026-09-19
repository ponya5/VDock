"""VS Code pack.

Editor keystrokes for VS Code proper (palette, terminal, panels, debugging)
plus the Copilot AI surface -- the keymap profile merges COPILOT_COMMANDS so a
single plugin covers both.

Focus-first delivery and the focus guard live in ``editor_base.py``.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import VSCODE_PROFILE, VSCODE_EXES


class Plugin(KeystrokeEditorPlugin):
    """VS Code actions, driven by the default Windows keybindings."""

    plugin_id = 'vscode'
    plugin_name = 'VS Code'
    plugin_description = (
        'Navigation, panels, debugging and Copilot actions for VS Code.'
    )
    commands = VSCODE_PROFILE.commands
    category = 'dev'
    editor_label = 'VS Code'
    editor_exes = VSCODE_EXES
