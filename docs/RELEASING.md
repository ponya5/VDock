# Releasing VDock

`/.github/workflows/release.yml` builds the self-contained installers
on each OS's native runner (`windows-latest`, `macos-latest`,
`ubuntu-latest`). Trigger it two ways:

- **Tag a release:** `git tag v2.0.2 && git push origin v2.0.2` —
  builds all three OSes, smoke-tests each frozen backend, and attaches
  the artifacts to a GitHub Release with generated notes.
- **Manual:** Actions → Release → Run workflow — same build, artifacts
  appear under the run (no Release created).

Artifacts per OS:

| OS | Files | Install UX |
|---|---|---|
| Windows | `VDock Setup x.y.z.exe` (NSIS), `VDock-Portable.exe` | one-click / unzip-and-run |
| macOS | `VDock-x.y.z.dmg`, `.zip` | drag to Applications |
| Linux | `.AppImage`, `.deb` | run directly / `sudo apt install ./vdock*.deb` |

## Signing — silencing SmartScreen and Gatekeeper

**There is no config trick that removes these warnings** — Windows
SmartScreen and macOS Gatekeeper only trust code signed by a real
certificate (plus, for SmartScreen, accumulated reputation on that
cert). The pipeline already signs automatically when the secrets below
exist; until then, artifacts ship unsigned (Windows) or ad-hoc signed
(macOS).

Ad-hoc signing matters on macOS: a completely unsigned app is reported
as **"VDock is damaged and can't be opened"** on Apple Silicon, with no
way past it except the terminal. When no certificate is configured,
`release.yml` and `scripts/build-release.sh` therefore pass
`-c.mac.identity=-` to electron-builder (ad-hoc signature), which turns
the error into the normal "Apple could not verify..." prompt that users
can get past in System Settings. With `CSC_LINK` (or a Developer ID in
the local keychain) the flag is not passed and the real certificate is
used. The "Verify macOS code signature" step in `release.yml` runs
`codesign --verify --deep --strict` on every build.

Both signing modes use the hardened runtime with
`frontend/electron/entitlements.mac.plist` (JIT and unsigned executable
memory for V8 and the frozen Python's ctypes/pyobjc, library validation
off for the PyInstaller bundle, and `automation.apple-events`), and
`Info.plist` carries `NSAppleEventsUsageDescription` — without it macOS
silently denies the Automation requests behind Play/Next/Previous
(Music, Spotify) and the Terminal agent buttons instead of asking.

### Windows (SmartScreen)

Get a code-signing certificate, export as `.p12`/`.pfx`, base64 it into
secrets. Options for an OSS project:

| Option | Cost | Notes |
|---|---|---|
| **SignPath Foundation** | free for OSS | signs via their CI integration; approval takes a few days; cert already has reputation → no SmartScreen at all |
| **Azure Trusted Signing** | ~$10/mo | no hardware token; identity-validated; immediate reputation |
| **Certum open-source cert** | ~€25/yr | cheapest own-cert; OV → reputation builds over first ~hundreds of installs |
| Commercial EV cert | ~$300+/yr | instant reputation; overkill early on |

Secrets to set (repo → Settings → Secrets → Actions):

- `WIN_CSC_LINK` — base64-encoded `.p12`, or HTTPS URL to it
- `WIN_CSC_KEY_PASSWORD` — p12 password

(Generic `CSC_LINK`/`CSC_KEY_PASSWORD` also work and apply to all OSes.)

### macOS (Gatekeeper)

Needs an **Apple Developer Program membership ($99/yr)** — there is no
free path for notarized distribution. Then:

- `CSC_LINK` / `CSC_KEY_PASSWORD` — the Developer ID Application cert
  as base64 `.p12` (or let the runner use a keychain-imported identity)
- `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID` — with
  these set, electron-builder notarizes the `.dmg`/`.zip` automatically.

### Interim UX (unsigned builds)

Until signing is in place, tell users in release notes:

- **Windows:** SmartScreen → "More info" → "Run anyway" (expected for
  unsigned/new-reputation apps). The installer adds a Windows Defender
  Firewall rule for `resources\backend\vdock-backend.exe` (Private
  networks only) so phones can connect; on a per-user install Windows
  asks for approval once. The uninstaller removes the rule (an update
  keeps it). The portable exe adds no rule — Windows asks the first
  time "Allow LAN access" is on.
- **macOS:** drag VDock to Applications and open it. macOS says it
  "could not verify VDock is free of malware" → **Done**, then
  **System Settings → Privacy & Security**, scroll to Security and click
  **Open Anyway** next to the VDock message, and confirm (macOS 15+ no
  longer offers right-click → Open for this). Fallback, in Terminal:
  `xattr -dr com.apple.quarantine /Applications/VDock.app`.
- **Linux:** no gatekeeper — `chmod +x *.AppImage && ./VDock-*.AppImage`.

## What the packaged app does at run time

Support answers for the installed app (DL-010):

- **Data and logs:** `DATA_DIR` = `<Electron userData>/vdock-data`
  (`%APPDATA%\vdock-electron\vdock-data` on Windows,
  `~/Library/Application Support/vdock-electron/vdock-data` on macOS —
  the folder is named after `package.json` `name`, so never rename it).
  The backend's output goes to `vdock-backend-electron.log` there, next
  to `vdock.log`. A source checkout's Electron window uses the same
  `vdock-electron` profile folder (but `backend/data` for its data), so
  `uninstall.sh` / `uninstall.bat` clear that folder *around*
  `vdock-data`, and only one of the two VDock windows runs at a time.
- **Port:** Electron chooses it, not the backend. `PORT` in
  `DATA_DIR/.env` (written by Settings → Ports) wins when it is free;
  an upgraded install keeps the port it used before (5000 on Windows);
  a fresh install takes the first free port from 5001 (5000 is AirPlay
  Receiver on every Mac). The choice is saved to `DATA_DIR/.env`.
- **Crashes:** a backend that dies within 15 s is restarted after 2 s,
  then 4 s; the third quick failure shows a dialog with the log path
  instead of restarting forever. "Address already in use" moves it to
  another port.
- **PATH (macOS/Linux):** the backend gets the user's login-shell PATH,
  so `claude`, `gh`, `cursor` from Homebrew/mise/nvm are found when VDock
  is opened from Finder or the Dock.
- **One instance:** opening VDock again focuses the running window.
- **Not yet:** the Windows uninstaller does not remove agent hooks
  (the frozen backend has no remove-hooks entry point yet), and macOS
  has no uninstaller — remove hooks in Settings before deleting the app.

## Local builds

```bash
./scripts/build-release.sh              # POSIX: freeze → vite → electron-builder
./scripts/build-release.sh --mac dir    # macOS: unpacked VDock.app only (fast)
./scripts/build-release.ps1             # Windows
```

Build with Python 3.10–3.14 (CI uses 3.12); `requirements-build.txt`
pins PyInstaller 6.22.3, which supports up to 3.15 but VDock's runtime
dependencies do not. Check a macOS build with
`codesign --verify --deep --strict --verbose=2 dist-electron/mac-arm64/VDock.app`.

Each OS only builds its own installer — cross-building macOS artifacts
from Windows/Linux isn't supported by electron-builder. That's what the
release workflow is for.

## Version numbers

The version moves **only when a release is cut**, never per commit, and the
level follows what shipped since the previous `v*` tag:

| Level | When | Example |
|---|---|---|
| **major** | a breaking change (`type!:` subject or a `BREAKING CHANGE:` footer) | 2.6.0 → 3.0.0 |
| **minor** | anything user-visible: at least one `feat` commit | 2.6.0 → 2.7.0 |
| **patch** | only fixes, perf, refactor, docs or chore | 2.6.0 → 2.6.1 |

`python scripts/bump_version.py --tag` applies this: it reads the commits since
the last tag, picks the level, updates `backend/version.py`,
`frontend/package.json`, `frontend/electron/package.json` and both lockfiles,
commits `chore: release X.Y.Z` and creates the `vX.Y.Z` tag. Use `--dry-run` to
see the decision first, or pass `major|minor|patch|x.y.z` to override it. It
never pushes: `git push origin HEAD vX.Y.Z` starts the release build.
`backend/tests/test_version_consistency.py` fails when the files drift;
`/api/health` and the MCP server read `backend/version.py`. Use conventional
commit subjects (`feat:`, `fix:`, ...) so the decision is right.