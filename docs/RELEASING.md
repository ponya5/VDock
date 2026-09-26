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
  unsigned/new-reputation apps).
- **macOS:** right-click → Open, or `xattr -d com.apple.quarantine
  /Applications/VDock.app` after install.
- **Linux:** no gatekeeper — `chmod +x *.AppImage && ./VDock-*.AppImage`.

## Local builds

```bash
./scripts/build-release.sh    # POSIX: freeze → vite → electron-builder
./scripts/build-release.ps1   # Windows
```

Each OS only builds its own installer — cross-building macOS artifacts
from Windows/Linux isn't supported by electron-builder. That's what the
release workflow is for.
