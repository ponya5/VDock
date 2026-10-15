"""Make a source-checkout Electron window show up as "VDock" on macOS.

Run from a checkout, the window belongs to the stock ``Electron.app`` binary,
and macOS takes the Dock / menu-bar / Cmd-Tab label from that bundle's
``Info.plist`` -- so it reads "Electron". ``app.setName()`` cannot change it.
Packaged builds are already named by electron-builder, and Windows / Linux
take their identity from the AppUserModelId / window title instead, so this is
a macOS-only, source-checkout-only step.
"""
import platform
import plistlib
import subprocess
from pathlib import Path
from typing import Optional

PRODUCT_NAME = "VDock"
BRANDED_KEYS = ("CFBundleName", "CFBundleDisplayName")


def electron_app_bundle(electron_dir: Path) -> Path:
    return electron_dir / "node_modules" / "electron" / "dist" / "Electron.app"


def brand_electron_bundle(electron_dir: Path) -> Optional[bool]:
    """Rename the dev Electron bundle to VDock.

    Returns True when the bundle was rewritten, False when it already carried
    the name, and None when there is nothing to do (not macOS, no bundle).
    """
    if platform.system() != "Darwin":
        return None

    bundle = electron_app_bundle(electron_dir)
    plist_path = bundle / "Contents" / "Info.plist"
    if not plist_path.is_file():
        return None

    with plist_path.open("rb") as plist_file:
        info = plistlib.load(plist_file)

    if all(info.get(key) == PRODUCT_NAME for key in BRANDED_KEYS):
        return False

    for key in BRANDED_KEYS:
        info[key] = PRODUCT_NAME
    with plist_path.open("wb") as plist_file:
        plistlib.dump(info, plist_file)

    resign_bundle(bundle)
    return True


def resign_bundle(bundle: Path) -> None:
    """Re-seal the bundle: editing Info.plist invalidates Electron's signature.

    Ad-hoc signing is enough for a local dev runtime; touching the bundle makes
    LaunchServices drop its cached "Electron" label.
    """
    subprocess.run(
        ["codesign", "--force", "--deep", "--sign", "-", str(bundle)],
        check=True,
        capture_output=True,
    )
    bundle.touch()
