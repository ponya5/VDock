# DL-075: Cross-platform release pipeline — macOS/Linux artifacts, signing wiring, real icon

## Background

Goal from the release-readiness review: ship on macOS and Linux as
first-class installs (not just Windows), silence SmartScreen as far as
infrastructure allows, and replace the 32px-upscale placeholder icon
with real art.

Constraints: this machine is Windows, so macOS/Linux installers can't
be built or smoke-tested locally — the pipeline must run on GitHub's
native runners per OS. And SmartScreen/Gatekeeper warnings cannot be
configured away; they only lift with a real signing certificate (plus
reputation on Windows), so the fix is: auto-sign the moment cert
secrets exist + document the cheapest cert paths.

## Design

### Release workflow (`.github/workflows/release.yml`)

Matrix build over `windows-latest`/`macos-latest`/`ubuntu-latest`,
triggered by `v*` tags or manual dispatch:

1. `python -m venv backend/venv` + runtime/build deps (mirrors
   `setup.sh`/`setup.bat`, so CI exercises the same layout users get)
2. `scripts/build-backend.{sh,ps1}` — PyInstaller freeze
3. **Smoke-test the frozen binary on the runner OS**: spawn it with a
   temp `DATA_DIR`, curl `/api/health` + `/api/templates/list`. This is
   the real macOS/Linux verification — it catches missing
   hiddenimports and POSIX path bugs the Windows build can't see.
4. `vite build` → `npm ci` (electron) → `electron-builder --publish never`
5. `upload-artifact` always; on tags, `gh release upload/create`
   attaches artifacts with generated notes.

### Platform packaging deltas

- Linux targets: `AppImage` + **`deb`** (apt install is the smooth
  path for Ubuntu/Debian); icon + description + maintainer set.
- `main.js` icon handling: `.ico` doesn't render on Linux/macOS Tray
  or BrowserWindow — `iconFile` picks `.ico` on win32, `.png` else.
- macOS dmg/zip already targeted; electron-builder auto-icns's the
  1024px PNG and auto-notarizes when `APPLE_*` secrets exist.

### Signing (honest scope)

No code change can remove SmartScreen. Wired instead:

- Workflow passes `CSC_LINK`/`CSC_KEY_PASSWORD`, `WIN_CSC_*`, and
  `APPLE_ID`/`APPLE_APP_SPECIFIC_PASSWORD`/`APPLE_TEAM_ID` from
  secrets — electron-builder signs + notarizes automatically when set.
- `docs/RELEASING.md` — cert options (SignPath free-for-OSS, Azure
  Trusted Signing ~$10/mo, Certum ~€25/yr), secret names, and the
  interim "More info → Run anyway" / `xattr -d` user instructions.

### Icon

Master `docs/assets/vdock-icon.svg` adapts the banner's keycap-grid
mark: 3×3 rounded keys on the slate→indigo gradient, accent gradient
on the diagonal, ambient circle glows. Rendered at 1024px (headless
Chromium), Pillow generated: `vdock-icon.png` (1024), `vdock-icon-512.png`,
multi-size `vdock-icon.ico` (16–256), `vdock-tray.png` (64), and the
favicon set (`16/32/apple-touch`) — which `index.html` referenced but
**did not exist** before (silent 404s).

## Implementation Results

- New: `.github/workflows/release.yml` (14 steps, YAML-validated),
  `docs/RELEASING.md`, `docs/assets/vdock-icon.svg` + rendered
  `vdock-icon-1024.png` master, `docs/assets/_icon-render.html`
  (regeneration helper).
- `frontend/electron/package.json`: +`deb` Linux target, icon/
  description/maintainer for linux, `build-mac`/`build-linux` scripts.
- `frontend/electron/main.js`: platform-aware `iconFile` for window +
  tray.
- `frontend/public/`: all icon files replaced with real renders;
  favicons created.
- Verified on Windows: `node --check`, `package.json` parse, YAML
  parse, `bash -n` on both .sh scripts, icon pixel-check at 1024.
- Audited (no changes needed): backend platform guards
  (`platform.system()`/`try-import` everywhere), requirements
  sys_platform markers, `build-backend.sh`/`build-release.sh` POSIX
  correctness, `VDock-Launcher.py` cross-platform, spec's win32-only
  hiddenimports. `python-magic(-bin)` confirmed unused — left in place
  (win32-marked, harmless) rather than churn requirements.

**Not verified here:** the macOS/Linux build legs run for the first
time on the GitHub runners (that's the point of the pipeline).
Electron-builder mac/linux config is standard; first `workflow_dispatch`
will confirm. Signing is inert until secrets are added — by design.

## Follow-up: first pipeline run — 3 real bugs found and fixed

The first `workflow_dispatch` run proved the pipeline's value: all
three legs surfaced real portability bugs that Windows dev hid:

1. **POSIX exec bits** — `build-backend.sh`/`build-release.sh`/
   `deploy.sh` were committed `100644`; freeze died with exit 126 on
   both POSIX runners. Set `100755` in the index (matching
   `setup.sh`/`launch.sh`) and invoke via `bash` in the workflow so a
   lost bit can't recur.

2. **`Key.insert` crashes macOS backend at import** —
   `HotkeyAction.KEY_MAP` was a class-body literal referencing
   `Key.insert`; pynput's Key enum is platform-specific and darwin has
   no Insert key → `AttributeError` killed `app.py` before Flask even
   bound. Map is now getattr-driven via a module-level
   `_KEY_ATTRS`/`_build_key_map()` — platform-missing keys drop out.
   Verified: 45 entries on Windows, simulated darwin-Key drops insert
   cleanly, 281 action tests pass.

3. **Empty `CSC_*` env vars break electron-builder** — passing
   `CSC_LINK: ${{ secrets.CSC_LINK }}` with the secret unset exports
   an *empty* var, which electron-builder resolves as a cert file path
   ("" → cwd → "⨯ ... not a file"). Step now unsets any empty signing
   vars before invoking, so unsigned builds work and signing activates
   automatically once secrets exist.

**Second run: all three legs green** (win 3m24s, mac 2m42s,
ubuntu 4m8s). Each produced real artifacts — `vdock-windows-latest`
479MB (Setup + Portable), `vdock-ubuntu-latest` 466MB (AppImage +
deb), `vdock-macos-latest` 524MB (dmg + zip) — and the frozen backend
passed its live smoke test on all three OSes.
