"""JetBrains pack.

Default keybindings shared by IntelliJ, PyCharm, WebStorm, Rider, CLion,
GoLand, DataGrip and RubyMine.

Focus-first delivery and the focus guard live in ``editor_base.py``.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import JETBRAINS_COMMANDS, JETBRAINS_EXES


class Plugin(KeystrokeEditorPlugin):
    """JetBrains IDE actions, driven by the default Windows keymap."""

    plugin_id = 'jetbrains'
    plugin_name = 'JetBrains IDE'
    plugin_description = (
        'Navigation, tool windows, run/debug and refactoring actions for '
        'IntelliJ-family IDEs.'
    )
    commands = JETBRAINS_COMMANDS
    category = 'dev'
    editor_label = 'JetBrains IDE'
    editor_exes = JETBRAINS_EXES
