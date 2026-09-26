# DL-073: Self-contained installer — PyInstaller backend + electron-builder bundle

## Background

DL-072 found the electron-builder packaging structurally incomplete: it
bundled backend *source* and spawned a Python interpreter the user's
machine may not have. This entry wires a true one-click install: the
Flask backend is frozen with PyInstaller and shipped inside the Electron
app via `extraResources`.

## Design

### Freeze layout

PyInstaller builds `backend/app.py` into a **onedir** bundle
(`dist/vdock-backend/` containing `vdock-backend.exe` + `_internal/`).
Onedir over onefile: faster startup, no per-launch temp extraction, and
`_MEIPASS` data dirs stay stable paths.

Frozen path math: `__file__` for a bundled module is
`resources/backend/_internal/<module>.py`, so every existing
`Path(__file__).parent.parent` ("backend dir" → "project root") resolution
keeps working if the electron resources layout mirrors the repo:

```
resources/backend/
  vdock-backend.exe      # spawned by main.js
  _internal/             # PyInstaller runtime + bundled datas
  frontend/dist/         # built SPA, copied by extraResources
```

`app.py`'s `project_root / 'frontend' / 'dist'` resolves to
`resources/backend/frontend/dist` unchanged — no serving code changes.

### Bundled data (spec `datas`)

- `backend/data/templates` → `data/templates` (scene templates are
  read-only product content; `routes/templates.py` resolves them
  `_internal`-relative).
- `backend/Assets` → `Assets`; `frontend/public/assets` →
  `frontend/public/assets` (`routes/assets.py` catalog dirs).

### Hidden imports (spec)

- `collect_submodules('integrations')` — packs load via
  `pkgutil.iter_modules` + `importlib.import_module`; without this no
  `*_pack` is in the bundle.
- `collect_submodules('limits')` — flask-limiter resolves storage
  backends lazily.
- `engineio.async_drivers.threading` — Socket.IO picks its async driver
  dynamically; the backend runs `async_mode='threading'`.
- Windows-only extras guarded by `sys.platform`: `collect_submodules`
  for `pycaw`/`comtypes`, `collect_all('magic')` (python-magic-bin ships
  libmagic DLLs as package data).

### Writable data dir

A Program Files install makes `BASE_DIR/data` unwritable. `config.py`
gains a frozen-aware default for `DATA_DIR` (`%APPDATA%/VDock`,
`~/Library/Application Support/VDock`, `~/.local/share/vdock`), still
overridable by the `DATA_DIR` env var — which `main.js` sets explicitly
to `app.getPath('userData')/backend-data` anyway.

### Electron changes

- `main.js` prod branch spawns `resources/backend/vdock-backend(.exe)`
  with `windowsHide: true`, cwd = its dir, env `DATA_DIR` + `PORT`.
- `package.json` build config: drop `../../backend/**/*` source from
  `files` (no more source shipping) and `../dist` from files (Flask
  serves it); `extraResources` carries `dist/vdock-backend` → `backend`
  and `frontend/dist` → `backend/frontend/dist`. Add `mac`/`linux`
  targets for the cross-platform story.

### Orchestration

- `backend/requirements-build.txt` — pinned `pyinstaller` (opt-in dep,
  keeps runtime requirements clean).
- `backend/vdock-backend.spec` — the bundle recipe (source-tracked).
- `scripts/build-backend.ps1` / `.sh` — install build dep + run spec.
- `scripts/build-release.ps1` / `.sh` — end-to-end: freeze backend →
  `vite build` → `electron-builder` for the host OS.

## Implementation Results

Built and verified end-to-end on Windows:

- `backend/config.py` — `_default_data_dir()` returns per-user app-data
  paths when `sys.frozen` (`%APPDATA%/VDock`, `~/Library/Application
  Support/VDock`, `$XDG_DATA_HOME/vdock`); `DATA_DIR` env still wins.
- `backend/routes/assets.py` — fixed a pre-existing bug where
  `parent.parent` resolved to `backend/`, making `FRONTEND_ASSETS_DIR`
  point at nonexistent `backend/frontend/...` (the `/api/assets/*`
  endpoints were 500ing in dev). Now resolves three levels up — repo
  root in dev, `resources/backend` frozen — and prefers `frontend/dist`
  assets so the 69MB catalog ships once.
- `backend/app.py` — CSP widened for packaged mode: Google Fonts
  (`fonts.googleapis.com` styles / `fonts.gstatic.com` fonts) and the
  widget APIs (`open-meteo` ×2, `coingecko`, `bigdatacloud`). In dev the
  page is vite-served without this header, so the block only ever
  applied to packaged/prod serving — silent until now.
- `backend/vdock-backend.spec` — onedir, console build (Electron hides
  the window and reads stdout), datas: `data/templates`, `Assets`;
  hidden imports: `collect_submodules('integrations')`,
  `collect_submodules('limits')`, `engineio.async_drivers.threading`,
  win32-only `collect_submodules('pycaw')` + `collect_all('magic')`.
  (comtypes is covered by PyInstaller's bundled hooks — a full
  collect_submodules dragged in the 90-module comtypes.test suite.)
- `backend/requirements-build.txt` — `pyinstaller==6.11.1`.
- `frontend/electron/main.js` — prod spawns
  `resources/backend/vdock-backend(.exe)`, `windowsHide`, `DATA_DIR`
  env → `app.getPath('userData')/vdock-data`.
- `frontend/electron/package.json` — `files` slimmed to
  main/preload; `extraResources`: `dist/vdock-backend` → `backend`,
  `frontend/dist` → `backend/frontend/dist`, `frontend/public` →
  `public` (tray icon). Added mac (dmg/zip) and linux (AppImage)
  targets; win icon switched to a new `vdock-icon.png` (electron-builder
  rejects <256px ico — the source ico only had a 32px frame, so a
  multi-size ico + 512px png were generated; the png is an upscale —
  soft; replace with real art before a public release).
- `scripts/build-backend.{ps1,sh}` — freeze step;
  `scripts/build-release.{ps1,sh}` — freeze → vite build →
  electron-builder for the host OS.

**Verified**: `vdock-backend.exe` standalone — boots, 9 packs load,
health/templates/assets endpoints 200, `DATA_DIR` lands correctly.
`electron-builder --dir` → `win-unpacked/` layout confirmed; launched —
window + tray + backend + SPA serving + profile PUT round-trip all work.
Full `electron-builder --win` produced `VDock Setup 2.0.1.exe` (250MB
NSIS) and `VDock-Portable.exe` (250MB); portable exe smoke-tested — runs
self-contained. 867 backend tests pass.

Notes: installer is unsigned (SmartScreen will warn); macOS/Linux builds
must run on those OSes and remain untested here; the `.ico`/`.png` icon
is a 32px-source upscale — ship real art later.
