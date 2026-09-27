# DL-084 — Per-app executable path overrides

**Date:** 2026-09-28
**Status:** Implemented

## Background

User request: "in each template add a setting icon to allow the user to
set/browse that path for the .exe (e.g. cursor.exe, etc.) so when
launching a new session with the app or launching it… it will trigger the
correct path — same in macOS and Linux. When I clicked New Agent in
Cursor I got 'can't find cursor.exe'."

Root cause: `cursor_new_chat` (and every editor keymap action) focuses a
**running** window via `focus_app_window(target_exes)` and nothing ever
launches the app. Cursor's default install —
`%LOCALAPPDATA%\Programs\cursor\Cursor.exe` — is not on PATH and carries
no app registry entry the resolver consulted, so a press on a deck with
no Cursor window simply failed.

## Design

**Storage** — `app_paths` map in `config.json`, `{ appKey: absolutePath }`
via `Config.APP_PATHS`, read/written by the existing `/api/config`
GET/PUT. App keys normalize to lowercase stems (`Cursor.exe`, `cursor`,
`CURSOR` collapse) plus a small bidirectional alias table (`vscode` ↔
`code`, `claude-code` ↔ `claude`) so the friendly UI id and the binary
name find each other.

**Consumers**

1. `subprocess_runner.find_binary` — consults `override_for(name)` before
   PATH, so CLI spawns (claude, codex, ollama…) honor the override. The
   result still goes through `_unwrap_cmd_shim`.
2. `cross_platform_action._open_app` — a configured path launches
   directly; on macOS it switches `open -a <name>` → `open <path>` (the
   former can't take a filesystem path).
3. `editor_base.send` — when `focus_app_window` reports *no window* and
   an override exists for the command's `target_exes`, the app is
   launched, the focus retried once after a 4 s boot grace. Only fires
   on a real miss (`False`), never on `None` (platforms without window
   inspection), and only for commands that already target that app —
   no new launch surface is created for arbitrary keymaps.

**Validation** — PUT requires each value to `exists()` on the deck host
(directories allowed: `.app` bundles). Empty value clears the key; a
stale override (file deleted later) is ignored at read time so PATH
resolution still runs.

**Probe** — `GET /api/app-paths/probe?app=<key>` searches PATH, then the
usual install dirs per OS: Windows `%LOCALAPPDATA%\Programs\<app>` and
`ProgramFiles` variants plus vendor dirs that don't match the exe name
(`Microsoft VS Code\Code.exe`); macOS `/Applications/<Pretty>.app` +
`~/Applications` + `/usr/local/bin`; Linux `/usr/bin` + `/usr/local/bin`
+ `~/.local/bin`. On Windows a `.cmd`/`.bat` PATH hit keeps looking for
the real `.exe` — the shim works but opens a console flash.

**UI**

- A settings (gear) button on every template card toggles an inline
  `AppPathEditor` at the bottom of the card. Key derives from the
  template's first `open_app` program stem, then an alias table, then
  the template id — inert-but-consistent for pure web/keymap packs.
- A new **App launch paths** panel at the top of the Templates tab lists
  curated apps with no gallery card (Cursor, VS Code, VSCodium,
  Windsurf, Zed, Claude CLI, Codex CLI, Ollama) plus any saved keys that
  fall outside the list.
- `AppPathEditor` = input + **Browse** (Electron native picker only),
  **Detect** (backend probe), **Save** / **Reset to auto**, inline
  error text. The set state shows the resolved path in green.

**Electron** — `pick-executable` IPC → `dialog.showOpenDialog` with
platform filters (`.exe/.cmd/.bat/.com` on Windows, `.app` on macOS, all
files on Linux). Exposed via preload `pickExecutable()` and typed in
`useElectron`.

## Implementation Results

**Backend**

- `services/app_paths.py` — `_norm`/`_keys_for`/`override_for`/
  `launch_app`/`probe`/`validate_path`; aliases work both directions so
  UI ids and binary names intersect.
- `config.py` — `APP_PATHS` class attr + `load_saved_settings` restore.
- `routes/config.py` — GET exposes `app_paths`; PUT validates (dict of
  ≤64-char keys → existing paths, 400s otherwise) and persists; new
  `GET /api/app-paths/probe`.
- `utils/subprocess_runner.py` — `find_binary` checks the override map
  first, then PATH; both routes pass through `_unwrap_cmd_shim`.
- `actions/program_action.py` — a bare app name in a "Launch program"
  button resolves through the override, then PATH, before failing.
- `actions/cross_platform_action.py` — `_open_app` prefers the override;
  macOS uses `open <path>` for overrides.
- `integrations/editor_base.py` — on `focus_app_window → False`, launch
  the configured app and retry focus once; failure copy now points at
  the setting ("Templates → gear / App launch paths").

**Frontend**

- `api/appPaths.ts` — reactive `appPaths` map, `loadAppPaths`/
  `saveAppPaths`/`probeAppPath`, `launchApps` curated list,
  `templateAppKey` derivation.
- `components/AppPathEditor.vue` — the shared editor.
- `SettingsView.vue` — gear on all 36 cards; App launch paths panel;
  row shows the saved path in green, button reads "Change".
- `electron/main.js` + `preload.js` + `useElectron.ts` —
  `pick-executable` native dialog end-to-end; browsers fall back to
  Detect + manual entry.

**Verified**

- Live on this Windows box: Detect found
  `…\Programs\cursor\Cursor.exe` (real exe over the `cursor.CMD` PATH
  shim) and `…\Microsoft VS Code\Code.exe` for `vscode`; PUT → GET
  round-trips; missing path → 400 `"Not found on this machine"`; empty
  clears.
- UI: panel + gear rendering confirmed, Detect→Save→row-turns-green flow
  exercised; screenshots `refs/app-launch-paths-panel-*.png`,
  `refs/template-gear-editor-*.png`.
- Tests: `tests/test_app_paths.py` 17/17 (normalization, aliases,
  stale-path ignore, `find_binary` precedence, validation, probe,
  route round-trip); backend regression `test_security_hardening` +
  `test_subprocess_runner` + `test_integrations` + composite/http
  action tests green (157 total run); frontend `vitest` 291/291,
  `vue-tsc` clean, `dist` rebuilt.

**Notes / trade-offs**

- Launch-on-missing-window is Windows-only in practice — it triggers on
  `focus_app_window → False`, and window inspection only returns False
  on Windows. On macOS/Linux the override still drives `open_app` and
  `find_binary`.
- `launch_app` uses `os.startfile`/`open`/detached `Popen` — fire-and-
  forget, no shell strings, no quoting surface.
