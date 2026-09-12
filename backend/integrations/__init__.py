"""Integration packs that ship with VDock.

Each module here exposes a ``Plugin`` class (a ``BasePlugin`` subclass) and is
discovered by ``PluginManager.load_builtin_packs()``. Packs are plugins, not
core code: they add actions through the catalog and the executor's plugin
fallthrough without touching ``ActionExecutor.ACTION_CLASSES``.

A pack must degrade gracefully. If its CLI is missing or its token is unset it
reports that through ``is_available()``, and the picker greys its actions out
with the reason instead of letting the user press a button that cannot work.
"""
