"""Single source of truth for the VDock version.

Bump this together with ``frontend/package.json`` and
``frontend/electron/package.json`` -- ``tests/test_version_consistency.py``
fails when they drift. See ``docs/RELEASING.md``.
"""
__version__ = '2.3.3'
