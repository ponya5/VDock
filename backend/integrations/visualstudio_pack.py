"""Visual Studio pack.

Default Windows keybindings for devenv.exe. Only single-chord commands are
exposed -- VS's two-stroke chords cannot be sent as one hotkey.

Focus-first delivery and the focus guard live in ``editor_base.py``.
"""
from .editor_base import KeystrokeEditorPlugin
from .keymaps import VISUAL_STUDIO_COMMANDS, VISUAL_STUDIO_EXES


class Plugin(KeystrokeEditorPlugin):
    """Visual Studio actions, driven by the default Windows keybindings."""

    plugin_id = 'visualstudio'
    plugin_name = 'Visual Studio'
    plugin_description = (
        'Navigation, build and debugging actions for Visual Studio.'
    )
    commands = VISUAL_STUDIO_COMMANDS
    category = 'dev'
    editor_label = 'Visual Studio'
    editor_exes = VISUAL_STUDIO_EXES
