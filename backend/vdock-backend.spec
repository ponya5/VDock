# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the VDock backend — one-dir bundle consumed by
# electron-builder's extraResources (see frontend/electron/package.json).
# Run from backend/:  pyinstaller vdock-backend.spec --distpath ../dist
# Output: <distpath>/vdock-backend/vdock-backend(.exe) + _internal/
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Read-only product content the routes resolve via __file__-relative
# paths — bundled into _internal so the packaged app finds them where
# backend/<module>.py used to look:
#   routes/templates.py -> <backend>/data/templates -> _internal/data/templates
#   routes/assets.py    -> <backend>/Assets         -> _internal/Assets
datas = [
    ('data/templates', 'data/templates'),
    ('Assets', 'Assets'),
]

binaries = []
hiddenimports = (
    # Integration packs are discovered at runtime via
    # pkgutil.iter_modules(integrations.__path__) + importlib — static
    # analysis never sees them, so they must be named explicitly.
    collect_submodules('integrations')
    # flask-limiter resolves its storage backend lazily.
    + collect_submodules('limits')
    + [
        # Socket.IO picks its async driver dynamically; app.py pins
        # async_mode='threading'. The driver lives in engineio —
        # python-socketio has no async_drivers package of its own.
        'engineio.async_drivers.threading',
    ]
)

if sys.platform == 'win32':
    # Volume (pycaw) and window-control stack — only installed on
    # Windows. comtypes itself is covered by PyInstaller's bundled
    # comtypes hooks + pycaw's own imports; a full collect_submodules
    # would drag in the 90-module comtypes.test suite.
    hiddenimports += collect_submodules('pycaw')
    # python-magic-bin ships libmagic DLLs as package data.
    m_datas, m_binaries, m_hidden = collect_all('magic')
    datas += m_datas
    binaries += m_binaries
    hiddenimports += m_hidden

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vdock-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Console build on purpose: Electron hides the window (windowsHide)
    # and drains stdout/stderr for diagnostics — a windowed binary would
    # swallow them.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='vdock-backend',
)
