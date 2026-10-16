## Install: pick one file
- **Mac (Apple Silicon):** `VDock-<version>-arm64.dmg`
- **Windows:** `VDock.Setup.<version>.exe` (installer) or `VDock-Portable.exe` (no install)
- **Linux:** the `.AppImage` or the `.deb`
- Ignore the `.zip` (used by the auto-updater) and the "Source code" files.

## Mac: "Apple could not verify VDock" - how to open it
The Mac build is not notarized yet, so macOS blocks the first launch. It is safe to allow:
1. Open the `.dmg` and drag **VDock** to **Applications**.
2. Open VDock. When macOS says it can't verify it, click **Done** (not "Move to Trash").
3. Open **System Settings > Privacy & Security**, scroll to the **Security** section, click **Open Anyway** next to the VDock message, and enter your password.
4. Open VDock again. This is needed only once.

If **Open Anyway** does not appear, run this in Terminal and open VDock again:
`xattr -dr com.apple.quarantine /Applications/VDock.app`

## Windows
If SmartScreen says "Windows protected your PC", click **More info > Run anyway**.
The Windows build has been tested by CI only, not yet by hand on a real PC.

---
