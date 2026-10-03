# DL-146 - Production readiness, repo hygiene, secrets pattern, Settings IA, README refresh

Four phases, one user review stop after each (more inside Phase 3). Plan:
`docs/superpowers/plans/2026-10-03-dl146-production-readiness-readme-settings.md`.
Runs **after DL-145 Phase 1 lands** (that work touches `backend/integrations/*`,
`backend/actions/catalog.py`, `routes/actions.py`, `routes/agent_*`,
`ButtonEditor.vue`); Phase 4 (README + screenshots) runs after every DL-145
phase the user keeps.

## Problem

The user asked to "keep coding best practice, also regarding repo
structure; `.env` and `.env.example` in case the user needs to paste keys;
make sure what needs to be in gitignore; make this repo and app production
ready; update README (not overloaded) + screenshots of the new features;
optimize/evaluate the settings screen so it is easy to navigate". Standing
guidance: intuitive, not overloaded, value for developers.

Audit (2026-10-03, `main` @ `560bbcd`, 304 commits, 1,134 tracked files,
~184 MB working tree / 106 MB pack) found the repo is in better shape than
the request implies (extensive `.gitignore`, green CI on every push, rotating
logs, `services/secrets.py` redaction, `Config.validate()`), but with a
handful of real defects - one of them a security bug on this very machine -
and a Settings screen that has outgrown its 7-tab shell.

## Findings

### A. Repo hygiene & structure

**A0. "Core backend files are untracked" - not true; it is a snapshot artefact.**
`git ls-files backend/app.py backend/actions/catalog.py
backend/integrations/github_pack.py backend/routes/agent_mission.py` lists all
four. The status snapshot showed `M backend/actions/catalog.py` - the leading
space of ` M` (modified in worktree) was trimmed, so it reads like a bare
flag. The `??` lines with **backslash** paths
(`backend\.pytest_cache\v\cache\lastfailed`, `backend\data\vdock.log`,
`backend\tests\test_turn_baseline.py`) come from the IDE's own file-change
list, not `git status`: `git check-ignore -v` confirms `.pytest_cache/`
(`.gitignore:121`) and `backend/data/vdock.log` (`.gitignore:78`) are
ignored. The genuinely untracked files today are DL-145 Phase 1's new files
(`backend/services/agent_prompt.py`, `test_runner.py`, `turn_baseline.py`,
`integrations/live_pack_base.py`, five new tests, the DL-145 doc) - the
concurrent agent's work in progress. **No fix needed**; the hygiene test in
Phase 1 makes "is X tracked" a one-command answer.

**A1. Tracked files that should not be in the repo**

| Path | What | Evidence | Action |
|---|---|---|---|
| `.devin-shots/` (17 PNG) | Agent verification screenshots | Added in `0b77a4e` ("Add .devin-shots screenshots…"); not in `.gitignore`; no references (`rg "\.devin-shots"` = 0); two files byte-identical | `git rm -r --cached`, ignore. Copy any shot a DL cites into `design-log/refs/` first |
| `backend/test-scripts/` (13 files) | One-off DL-131 scripts + **`backend-env.txt`, a full environment dump** | `backend-env.txt` (added `34acf1e`, on `origin/main`) holds Windows username, computer name, OneDrive path, VS Code/Windsurf IPC vars, plus `SECRET_KEY`/`WEATHERAPI_KEY` - **both verified to be the `.env.example` placeholders, not real secrets**. 7 files contain `C:\Users\Daniel…` absolute paths (`capture_guide_shots.py`, `dl131_common.py`, `dumpenv.bat`, `step2_readd_ui.py`, `step3_verify_ui.py`, `step6_final_state.py`) | `git rm` the dir (user confirm). If `capture_guide_shots.py` is still useful, move to `scripts/dev/` with paths parameterised |
| `scripts/vdock_agent_hook.py` | Stale copy of `backend/scripts/vdock_agent_hook.py` | Hashes differ; `integrations/agent_hooks.py:71` installs the **backend** one; nothing references the root copy | `git rm` after a diff review |
| `docs/LICENSE.md` | Duplicate of `LICENSE` | `Compare-Object` = 0 differences | `git rm` |
| `.env.example` (root), `docs/env.example` | Two more env templates | Document dead vars (`JWT_SECRET_KEY`, `DEFAULT_ADMIN_PASSWORD=admin`, `DATABASE_URL`, `SENTRY_DSN`, `LOG_FILE`, `VITE_API_URL`, `WEATHER_API_KEY` misspelt); nothing reads them | Delete; `backend/.env.example` + new `frontend/.env.example` are the only templates |
| `backend/Assets/VdIcon.ico`, `VdockIcon.ico` | Identical to `scripts/vdock-icon.ico` | Same blob hash | Keep one after `rg` for references in `vdock-backend.spec`, NSIS, electron-builder config |
| `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | Container deploy | Mounts non-existent `./backend/Avatars`; container binds 127.0.0.1 because `ALLOW_LAN=False` so port 5000 is unreachable; a container cannot drive the host's keyboard/windows/audio, which is the product | **User decision D4** - recommend delete (or move to `deploy/docker/` labelled unsupported) |
| `frontend/public/assets/animations/gifs/buttons/* (1).gif` etc. | 6 byte-identical duplicate GIFs | blob-hash scan | **Defer**: saved profiles may reference either filename; only remove with an alias or a reference scan of user data |

**A2. Local-only clutter (not tracked, but worth cleaning / ignoring)**
root `NUL` (Windows reserved-name artefact from a `> nul` typo in a POSIX
shell; breaks `rg` with "Incorrect function" and some tools; needs
`Remove-Item -LiteralPath '\\?\C:\…\NUL'`), `backend-restart.log` (2.4 MB),
`backend-run.log`, `vdock-restart.log` (already ignored by `*.log`), root
`/data/` and `/dist/` (ignored), `.benchmarks/` (empty, **not** ignored).

**A3. Missing hygiene files.** No `.gitattributes`, no `.editorconfig`.
Index is clean (750 `i/lf`, 380 `i/-text`, 0 mixed) only because this
machine has `core.autocrlf=true`; 17 files are mixed CRLF/LF in the working
tree, and a macOS/Linux contributor without autocrlf would check `.bat`
files out LF (cmd `goto`/label parsing breaks). LICENSE, SECURITY.md exist at
root; CONTRIBUTING, CHANGELOG, CODE_OF_CONDUCT exist in `docs/` (GitHub finds
`docs/`), so nothing is missing - only the duplicate license.

**A4. Secrets / personal data scan.** `git grep` over tracked files and
`git log --all -G` over history for `ghp_`, `github_pat_`, `sk-…`, `AKIA…`,
`xox[bp]-`, `AIza…`, private-key headers: **no hits**. Historic
`backend/data/config.json` / `data/config.json` versions contain no
key/token/password values. Personal data in tracked files: the author email
(intentional: README/SECURITY/CONTRIBUTING contact, and the server-side
default in `routes/feedback.py:29`), `backend/test-scripts/*` (above),
`design-log/DL-004-ide-agent-control.md` and `design-log/collab/ORCHESTRATION.md`
(absolute user paths, harmless prose). **Conclusion: no history rewrite** -
nothing secret was ever committed; removing the env dump going forward is
enough.

**A5. Repo weight.** `design-log/refs/` 107 files / 34 MB (single PNGs up to
2.7 MB), `frontend/public/assets/animations/` 65 MB, README GIFs 6-7 MB each
plus MP4 twins. Not a defect; set a size budget for new images (≤400 KB,
PNG-quantised or JPEG) and enforce it in the hygiene test for new files.
LFS/history rewrite: out of scope.

### B. Secrets & configuration

**B1. Every env var the backend reads** (`rg "os\.environ|getenv" backend`):

| Var | Read in | In `backend/.env.example`? | Notes |
|---|---|---|---|
| `SECRET_KEY` | `config.py:190` | yes, **placeholder value** | see B2 - security bug |
| `DEBUG` | `config.py:191` | yes | DEBUG+LAN = Werkzeug debugger on the network (B3) |
| `HOST`, `PORT` | `config.py:194-195` | yes | |
| `REQUIRE_AUTH`, `AUTH_PASSWORD`, `TOKEN_EXPIRATION` | `config.py:198-204` | yes | comment "The frontend has no login screen" is **stale** since DL-126 (`AuthGate.vue`); example password `ChangeThisToAStrongPassword123!` is not rejected |
| `RATELIMIT_ENABLED`, `RATELIMIT_DEFAULT` | `config.py:207-209` | yes, **`True` / `200 per day, 50 per hour`** | code default is off / 100k per hour. Copying the example turns on a cap that `agent_mission_bp` (not exempt, `app.py:192-235`) blows through: Mission Control polls every 15 s (`AgentMissionControl.vue:247`) = 240 req/h > 50/h. This machine's `backend/.env` has exactly that |
| `RATELIMIT_STORAGE_URL` | `config.py:208` | **no** | |
| `CORS_ORIGINS`, `ALLOW_LAN` | `config.py:212-213` | yes | |
| `DECK_HOST` | `config.py:217` | **no** | |
| `USE_SSL`, `SSL_CERT_PATH`, `SSL_KEY_PATH` | `config.py:226-228` | yes | missing cert files are not checked at boot |
| `DATA_DIR` | `config.py:233` | yes | Electron sets it in packaged mode (`main.js:91-97`) |
| `ENABLE_PLUGINS`, `REQUIRE_COMMAND_CONFIRMATION`, `ALLOW_COMMAND_EXECUTION` | `config.py`, `actions/command_action.py` | yes | |
| `WEATHERAPI_KEY` | `actions/weather_action.py:23`, `config.py:258` | yes, **`demo-key-replace-with-your-own`** | non-empty junk counts as "configured"; example claims "Default demo key provided" - false since the key was removed |
| `ANTHROPIC_API_KEY`, `GITHUB_TOKEN` | `services/secrets.py:73` | yes | good: `SecretSpec` with help URL + reason |
| `VDOCK_DEFAULT_REPO_PATH` | `integrations/context.py:71,176` | yes | |
| `VDOCK_FEEDBACK_EMAIL` | `routes/feedback.py:29` | **no** | |
| `SPOTIFY_CLIENT_ID/SECRET/REDIRECT_URI/SCOPE` | **nothing** | yes | dead config - remove |
| `APPDATA`, `LOCALAPPDATA`, `ProgramFiles*`, `XDG_DATA_HOME` | OS | n/a | allowlisted |
| Frontend `VITE_PORT`, `VITE_BACKEND_PORT`, `VITE_WS_URL` | `frontend/src` | **no `frontend/.env.example`** | setup writes `frontend/.env` |
| Electron `VDOCK_PRODUCTION`, `VDOCK_DISPLAY_INDEX`, `VDOCK_USE_SMALLEST_DISPLAY`, `VDOCK_FULLSCREEN`, `VDOCK_KIOSK`, `VDOCK_FRONTEND_PORT`, `VDOCK_BACKEND_PORT`, `VDOCK_SKIP_BACKEND_SPAWN`; launcher `VDOCK_DEV_SERVER`, `VDOCK_AUTO_CLOSE_LAUNCHER` | `frontend/electron/main.js`, `scripts/VDock-Launcher.py` | no | process env, not `.env`; document in `docs/development/DEVELOPER_GUIDE.md`, not the user template |

**B2. Security bug - the "secret" key is public.** `setup.sh:101-103` (and
`setup.bat`, re-verify) copy `backend/.env.example` verbatim, so `SECRET_KEY`
becomes the published string `your-secret-key-here-change-this-to-random-string`
(**verified on this machine**: local `backend/.env` holds exactly that).
`routes/config.py:154` only persists a random key "if not already set" - the
placeholder counts as set. JWTs (`auth/auth_manager.py:65,78`, HS256) are
therefore signed with a key anyone can read on GitHub: with `REQUIRE_AUTH`
on, any LAN client can mint a valid token. If `SECRET_KEY` is unset instead,
`os.urandom` each boot means every device re-unlocks after a restart (DL-126
works around that only when a password is set via Settings).

**B3. Insecure combinations at boot.** Today only `REQUIRE_AUTH` without
`AUTH_PASSWORD` is refused (`Config.validate`). Not handled:
- `DEBUG=True` + LAN bind -> `socketio.run(debug=True, allow_unsafe_werkzeug=True)`
  exposes the Werkzeug debugger (remote code execution) to the network.
- `ALLOW_LAN` + `REQUIRE_AUTH` off -> anyone on the Wi-Fi can press keys,
  type into agent sessions, approve agent permission prompts (Mission
  Control), read logs. This is VDock's *main* phone use case, so refusing
  would break it; it must instead be loud: startup warning, a Settings
  "needs attention" item and a password nudge **in the Connect panel**
  (today the password lives under Server, the LAN switch under Connect -
  `SettingsView.vue:1330-1390` vs `1439`). This machine runs exactly this
  combo (`backend/data/config.json`: `allow_lan: true, require_auth: false`).
- `USE_SSL` with missing cert/key files -> crash deep in Werkzeug.
- `REQUIRE_AUTH` with the example password.

**B4. Packaged-app `.env` location is undefined (re-verify).** Electron runs
the PyInstaller onedir backend with `cwd: resources/backend` and
`DATA_DIR=userData/vdock-data` (`main.js:91-97`). `load_dotenv()` (no path,
`app.py:23`) in a frozen exe searches the cwd - the install dir, possibly
read-only Program Files - while `config.backend_dir()` (`config.py:139-144`,
`Path(__file__).parent.parent / 'backend'`) resolves somewhere inside the
bundle. So in the installed app there is no documented, writable place to
paste a `GITHUB_TOKEN`, and the Settings password write (`routes/config.py:157`)
likely lands in the bundle. Fix: one `Config.env_file()` - source runs
`backend/.env`, frozen runs `DATA_DIR/.env` - used by both `load_dotenv` and
`write_env_keys`.

**B5. Where secrets surface today.** Good: `services/secrets.py` (booleans
only to the frontend, `redact()` on CLI output), `PUT /api/config` writes
`AUTH_PASSWORD` to `.env` and never returns it. Gap: there is **no in-app
way to see which keys are configured or to add one** - the only hint is a
greyed action's `unavailable_reason` in the picker (`SecretSpec.reason()`:
"GITHUB_TOKEN is not set in backend/.env…").

### C. Production readiness (local desktop + LAN panel, proportionate)

Already good: rotating logs (`utils/logger.py` `RotatingFileHandler`; this
machine shows `vdock.log` + `.1..3` at ~512 KB), `MAX_CONTENT_LENGTH` 16 MB,
security headers + CSP (`app.py:73-95`), path-traversal guard on dist
serving, localhost-only gates on hook/MCP/webhook routes
(`agent_events.py:89`, `mcp.py:665`, `triggers.py:31`), login throttle
(DL-126), CI on push/PR (`.github/workflows/ci.yml`: pytest on Python 3.9 +
3.12 under xvfb, `vue-tsc`, vitest, build; last 6 runs green), release
workflow building Win/mac/Linux installers, pinned `requirements.txt`.

| # | Item | Evidence | Value | Effort | Verdict |
|---|---|---|---|---|---|
| C1 | Fix public `SECRET_KEY` (B2): treat known placeholders / <32 chars as unset, generate + persist once to `Config.env_file()` | B2 | **High** | S | **P2** |
| C2 | Boot validator: refuse DEBUG+LAN, SSL w/o files, example password; warn LAN w/o auth; log configured integrations by **name only** | B3 | High | S | **P2** |
| C3 | One `.env` location incl. packaged app | B4 | High | S-M | **P2** (re-verify first) |
| C4 | Rate-limit: exempt `agent_mission_bp`; example stops enabling a 200/day cap | B1 | High (Mission Control 429s) | XS | **P2** |
| C5 | Atomic JSON writes (`tmp` + `os.replace`) for `FileManager.save_json`, `Config.save_config`, user settings; daily rolling profile backup (keep 7) in `DATA_DIR/backups/` | only `services/triggers.py` writes atomically; Electron `kill()` on Windows is TerminateProcess - a mid-write kill truncates `profiles/*.json` | High | S | **P2** |
| C6 | Single version source `backend/version.py`; health/MCP import it; test asserts it equals `frontend/package.json` and `frontend/electron/package.json` | `'2.2.0'` hard-coded in `app.py:434`, `routes/mcp.py:41`, two tests, README badge | Med | XS | **P2** |
| C7 | `GET /api/config/integrations` (auth-protected): `secrets.status()` + CLI detection + reason + help URL; health gains `uptime_s` only | feeds Settings Overview (P3) | Med | S | **P2** |
| C8 | Dependency audit: frontend `npm audit` 1 low (transitive `serialize-javascript`); **electron 6 high incl. `electron` itself (direct, `^41.0.2`, fix available)**; pip-audit not run yet | `npm audit --json` 2026-10-03 | Med-High | S + packaged smoke test | **P2** (electron bump = user confirm D6) |
| C9 | CI: `permissions: contents: read`; audit job (npm high+, pip-audit; non-blocking first); a **Windows backend job** (the app is Windows-first; pywin32/comtypes/winrt paths are skipped on Linux) | `ci.yml` | Med | S | **P2** |
| C10 | Node pin: README says Node 18+, but vitest 4 / jsdom 28 / Vite 6 need >=20 (CI uses 20, this machine 22.15); add `engines` + `.nvmrc` = 20 | `package.json`, README:183 | Med | XS | **P2** |
| C11 | `scripts/check.ps1` / `scripts/check.sh`: the CI steps locally in one command | 19 ad-hoc scripts in `scripts/`, none runs the checks | Med | XS | **P2** |
| C12 | `.env.example` rewrite + `frontend/.env.example` + env-documentation test | B1 | High | S | **P1** |
| C13 | SECURITY.md: LAN guidance ("turn on a deck password before Allow LAN") | | Low | XS | **P2** |
| Defer | HTTPS by default / cert generation; dropping CSP `'unsafe-eval'` (needs a bundle audit of three/ogl/vgpu); graceful SIGTERM handler (atomic writes cover the real risk); code signing + auto-update; Sentry/telemetry; gitleaks/LFS/history rewrite; restart-free LAN rebind; Docker | | | | **Deferred** |

Test baselines to re-record at start: backend ~1163 pytest, frontend ~631
vitest (DL-145 Phase 1 will raise both).

### D. README

`README.md` is 308 lines, good tone, image convention
`docs/assets/screens/<kebab>.png|jpg` at `width="820"` (root `/*.png` is
ignored by design). Gaps: nothing about Mission Control / approval inbox /
live CI-PR buttons (DL-144) or DL-145 features; Node 18+ is wrong (C10);
Configuration section is one paragraph with no key table; "Why VDock"
table and six use cases are long; `settings-7inch.png`, `settings-buttons.png`,
`settings-connect-device.png` will be stale after Phase 3. Target: **≤ 300
lines**, "What's new" block near the top, `.env` table pointing at
`backend/.env.example`, refreshed troubleshooting, shots captured last.

### E. Settings screen evaluation

`frontend/src/views/SettingsView.vue` = **5,521 lines** (template 1-1873,
script 1875-3736, style 3738-5521) - the largest file in the frontend
(next: `ButtonEditor.vue` 4,223). Only two panels are extracted
(`components/settings/TriggersPanel.vue` 866, `McpInfoModal.vue` 376).

**E1. Current information architecture** (control counts from the template)

| Top-level (sidebar) | Sub-tabs | Panels (h2) | Rows | Notes |
|---|---|---|---|---|
| Appearance | Buttons · Layout & sidebar · Background · Screen saver | Sizing & touch, Key design, Motion, Labels & feedback / Typography, Docked sidebar, **Notifications** / Dashboard background, Per-scene overrides / General, Spectrum, Screensaver background, Widgets | 46 + 15 + 8 + 42 = **111** | Screen saver alone 405 template lines; "Notifications" (toasts) sits under Layout |
| Templates | - | per-category template cards + app path editor | - | app executable paths edited here *and* probed from Server-ish config |
| Server | - | Startup & navigation, Connection (host, **authentication + deck password**, ports) | 29 | "Open settings in a new browser tab" is a UI preference, not server |
| Integrations | Apps & scenes · Agent alerts · Triggers · MCP server | Auto scene switching, **Running applications**, **Recent actions**, Agent attention alerts + Agent hooks, TriggersPanel, MCP | 33 + Triggers | "Integrations" holds no integrations (no GitHub/Claude/keys); Recent actions is picker history |
| Connect a device | - | Connect a device | 12 | LAN switch here, password two tabs away |
| Logs | - | Session logs, Log files | - | |
| Guide | (opens new window) | - | - | |
| About | - | VDock, What's in it, Build | - | |

7 sidebar entries + Guide link, 8 sub-tabs, max depth 3 (section -> sub-tab ->
panel; plus Advanced collapses inside rows). ~170 interactive rows.

**E2. Where users get lost**
1. *Integrations vs keys.* A developer looking for "GitHub token" opens
   Integrations and finds scene switching and MCP; tokens exist nowhere in
   the UI (B5).
2. *Phone + password split.* Connect (LAN) and Server (password) are
   separate, so the dangerous half of the setup is the one that is skipped.
3. *Automation spread.* Auto scene switching (Integrations/Apps), Triggers
   (Integrations/Triggers), agent alerts (Integrations/Alerts), toasts
   (Appearance/Layout) - four places for "what happens automatically".
4. *Templates* is a top-level peer of Server although it is "add scenes".
5. *No overview.* Nothing says what is configured or broken (hooks
   installed 2 of 4, LAN open without password, GitHub token missing) -
   the only status chip is inside Agent alerts.
6. *Search is a hand-written 25-entry list* (`settingsSearchIndex`,
   `SettingsView.vue:3315-3340`): misses password/auth, LAN, ports,
   deck address, typography, motion, sound, transparency, agent hooks,
   templates paths, recent actions. One entry is **broken**: "Button Display"
   uses `deepTab: 'display'` -> anchor `display` (`deepTabAnchor`, line 3354),
   but no element has `id="display"` (panel ids are `sizing`, `touch`,
   `design`, `motion`, `feedback`), so the jump scrolls nowhere.
7. *Deep links* exist (`?tab=&sub=`, lines 3665-3680) but not to a panel.

**E3. Layout consistency.** The DL-054 row pattern
(`.row > .row-text + .row-control`, `SettingResetButton`, `Collapse` for
Advanced) is applied consistently - keep it. Inconsistent: some panels use
`panel-head` + hint, others bare `h2`; empty states vary (Running apps,
Recent actions, Logs); the topbar "Apply" button shows on tabs where
everything autosaves. 7" behaviour was fixed in DL-140 (short-viewport
collapse, opaque sticky nav); touch targets meet 44 px in rows, but the
sub-tab bar and nav items need a re-measure at 1024x600.

**E4. Maintainability.** 15 test files read `SettingsView.vue` **as text**
(`readFileSync(.../SettingsView.vue)` in `settings-subtabs.test.ts`,
`connect-device.test.ts`, `button-behaviour-subtabs.test.ts`,
`logs-and-weather-move.test.ts`, …). Any extraction breaks them unless a
helper reads the view **plus** its extracted panels - this is the first
step of Phase 3.

**Verdict:** the row-level design is good and should be kept; the shell
(IA + search + file) is the problem. Evolve, do not rewrite.

## Decisions

1. **No history rewrite.** No secret was ever committed (A4). Forward-only
   removal of `backend/test-scripts/` and `.devin-shots/`, both behind user
   confirmation (`git rm` is the only "destructive" git op in this DL; no
   force-push, no filter-repo).
2. **One secrets home:** `Config.env_file()` (`backend/.env` from source,
   `DATA_DIR/.env` when frozen). Secrets never go to `config.json`,
   `user_settings.json`, API responses or logs. `backend/.env.example` is
   the single documented template, grouped *Core / Network & security /
   Integrations (keys) / Advanced*, every key with default, effect and
   where-to-get-it URL; `SECRET_KEY=` ships **empty** and is generated on
   first boot. `frontend/.env.example` documents the three `VITE_*` vars.
3. **A test owns the env contract:** every `os.environ.get('X')` /
   `getenv('X')` in `backend/` (minus an OS allowlist) must appear in
   `backend/.env.example`, and every key in the example must be read
   somewhere. Dead vars cannot creep back.
4. **A test owns repo hygiene:** forbidden tracked paths (`.devin-shots/`,
   `backend/test-scripts/`, `*.log`, `.env`, `NUL`), no absolute user paths in
   tracked code (design-log prose allowlisted), new binaries ≤ 1 MB unless
   allowlisted.
5. **Boot validator, not a framework:** extend `Config.validate()` +
   `Config.report()`; refuse only unambiguous footguns (DEBUG+LAN, SSL
   without files, example password with auth on); warn on LAN without auth.
6. **Settings: six top-level sections max, Overview first.**

   | Before (7 + Guide) | After (6 + Guide) | Contents |
   |---|---|---|
   | - | **Overview** (new, default landing) | "Needs attention" list, quick switches (Auto scene switching, Agent alerts, Allow LAN, Screensaver), "Edit keys on the dashboard" link |
   | Appearance (4 subs) | **Appearance** (Buttons · Layout · Background · Screen saver) | unchanged content; toasts move out |
   | Integrations > Apps / Alerts / Triggers / MCP | **Agents & automation** (Agent alerts · Scene switching · Triggers · MCP) | alerts + hooks status first; Running apps lives inside Scene switching; toast notifications join Agent alerts as "Notifications" |
   | Templates; (keys: nowhere) | **Integrations** (Accounts & keys · App templates) | per-`SecretSpec` status rows, help link, add-key flow (D3); Templates + app paths |
   | Server; Connect a device | **Devices & network** (Connect a device · Security · Ports & host) | LAN switch, QR and the password nudge on one page; ports/host/SSL under Advanced |
   | Logs; About; (Recent actions; Startup) | **System** (Logs · Startup · About) | Recent actions -> "Clear recent actions" row under Startup/Data; About + version |

   Legacy deep links (`?tab=server|connect|integration|templates|logs|about`,
   `?sub=apps|alerts|triggers|mcp|buttons|…`) keep working via a map; new
   `?section=&sub=&anchor=`.
7. **A settings registry** (`frontend/src/settings/registry.ts`) is the one
   source for sections, sub-pages, panel anchors, search entries and legacy
   ids. Search covers every panel and named row; a test asserts every
   registry anchor exists in the rendered panel sources and every `h2`
   has an entry.
8. **Split by panel, mechanically, before moving anything.** One component
   per sub-page under `components/settings/panels/`, state via the existing
   stores plus a small `useServerConfig()` composable; target
   `SettingsView.vue` ≤ 1,200 lines (shell, nav, topbar, search, routing).
9. **README and screenshots last**, from seeded simulated agent sessions
   (fake ids, `POST /api/agent-events`, cleaned with `state: 'ended'`), never
   keystrokes into real windows.

### Mockup-level description (Phase 3)

*Overview, 1024x600:* topbar "Overview - What's set up and what needs you".
Left column "Needs attention" (only when non-empty): amber rows like
"Anyone on your Wi-Fi can press your keys - Set a deck password ->"
(Devices & network › Security), "GitHub token not set - live PR/CI buttons
are off - Add ->" (Integrations › Accounts & keys), "2 of 4 agents hooked -
Install ->" (Agents › Alerts). Right column "Quick switches": four switch
rows. Below: "Edit what a key does -> opens the dashboard in edit mode".
All set: a single green row "Everything is set up". No raw errors.

*Accounts & keys:* one row per `SecretSpec` (GitHub token, Anthropic API key,
WeatherAPI key) + CLI rows (gh login, Claude Code CLI): status chip
(Configured / Not set / CLI found), one-line "what it unlocks", "Get a key"
link, and the add-key control from decision D3. A footnote: "Keys live in
`<env file path>` and are never shown again or sent to other devices."

*Devices & network › Connect:* existing steps + QR; when LAN is on and auth
is off, an inline amber row with the DL-126 set-password flow (component
extracted from Server, reused, not duplicated).

### Click-count acceptance (from the dashboard, settings closed)

| Task | Before | After (target) |
|---|---|---|
| Connect a phone | Settings -> Connect a device -> Allow LAN (3) + relaunch + no password prompt | Settings -> Overview "Connect a phone" -> Allow LAN (3) + relaunch, **password offered on the same page** |
| Add GitHub token | not possible in-app: hover a greyed action, find and edit `backend/.env` by hand, restart | Settings -> "GitHub token not set" -> paste + Save (3, D3=B) or copy line + "Open .env" (3, D3=A) |
| Turn on auto scene switching | Settings -> Integrations -> switch (3) | Settings -> quick switch on Overview (2) |
| Set agent alert behaviour | Settings -> Integrations -> Agent alerts -> control (4) | Settings -> Agents & automation (default sub = Agent alerts) -> control (3) |
| Change a button's action | not in Settings: Back -> Edit mode -> key edit -> pick -> Save (5) | Settings -> "Edit keys" link (lands in edit mode) -> key edit -> pick -> Save (4); from the dashboard unchanged (4) |

No task may get more clicks than before; search must find each task's
control by an obvious word ("phone", "token", "github", "scene", "alert",
"password", "port").

## Risks

- **Concurrent DL-145 work** touches `catalog.py`, `routes/actions.py`,
  `routes/agent_*`, `integrations/*`, `ButtonEditor.vue`. Phase 2's
  `agent_mission_bp` exemption is a one-line `app.py` change; everything in
  `routes/agent_*` waits until DL-145 Phase 1 is merged.
- **Settings split regressions:** 15 source-reading tests, ~170 bindings,
  scroll anchors, `data-tour` attributes (`nav-appearance`, `nav-server`,
  `nav-connect`, `nav-integration`, `nav-templates`, `nav-logs`, `nav-guide`,
  `nav-about`, `subtab-screensaver`; re-grep the tour config before
  renaming) and `GuideView.vue` copy that names settings paths.
- **Default landing change** (Overview) adds one click for appearance
  tweakers; mitigated by remembering the last section in the session.
- **`.env` move for packaged builds** must not lose an existing
  `resources/backend/.env`: migrate it on first boot if found.
- **Electron major-line bump** can break packaging; needs a packaged smoke
  test by the user.
- **Line-ending normalisation** produces a large diff if any index file is
  CRLF (audit says none) - run `git add --renormalize .` and review the
  stat before committing.

## Out of scope

History rewrite / LFS; HTTPS by default; restart-free LAN rebind; code
signing and auto-update; telemetry; Docker support; removing duplicate GIF
assets; a full Settings visual redesign or new design system; moving
ButtonEditor's action editing into Settings; DL-145 feature work itself.

## User decisions

- **D1** `git rm` `.devin-shots/` (cached) and `backend/test-scripts/` (incl.
  the env dump) - confirm; keep anything?
- **D2** No history rewrite (recommended; nothing secret was committed).
- **D3** Adding keys in-app: **A** status + "copy `GITHUB_TOKEN=` line" +
  "Open env file" (no secret ever crosses HTTP) or **B** write-only paste
  field (localhost requests only, written to the env file, applied to
  `os.environ` live, never returned) - **recommend B** (DL-126 precedent).
- **D4** Docker files: delete (recommended) or keep as unsupported.
- **D5** Settings opens on Overview.
- **D6** Bump Electron for the 6 high advisories (needs a packaged smoke test).
- **D7** Release as 2.3.0 with a CHANGELOG entry after Phase 4.

## Implementation Results

### Phase 1 - Repo hygiene, gitignore, env contract
_Implemented 2026-10-03. Not committed (per instruction)._

**User decisions recorded**
- Approved: `git rm -r --cached .devin-shots backend/test-scripts` (files stay on disk, now ignored); no history rewrite, no commit, no push.
- Approved: delete the Docker files (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`) via `git rm`.
- API keys UX (later phases): status + "copy line / open .env" only; no pasting keys in the app. This supersedes D3 = B / Task 2.8.
- Settings will open on Overview (D5); Electron bump + 2.3.0 approved for later phases (not done here).

**Baselines:** backend 1262 -> **1294** passing (+32); frontend 666 passing (664 at brief; 2 added by concurrent DL-145 work; no frontend source touched).

**Assumptions re-verified:** (1) 17 + 13 tracked files in `.devin-shots/` + `backend/test-scripts/` (test-scripts has 14 on disk: one untracked); nothing outside design-log references them; only DL-146 cites `.devin-shots`. (2) `backend-env.txt` `SECRET_KEY`/`WEATHERAPI_KEY` equal the example placeholders (True/True) - no rotation needed. (3) `setup.bat:205-206` / `setup.sh:101-103` copy the example. (4) `python-dotenv` uses `os.getcwd()` when `sys.frozen`. Index has 0 CRLF files (`git ls-files --eol`), so no `--renormalize` was run.

**Pulled forward from Phase 2 (user's security finding)**
- `config.py`: `env_file()` (backend/.env from source, DATA_DIR/.env frozen), `KNOWN_PLACEHOLDER_SECRETS`, `is_weak_secret_key()`, `Config.ensure_strong_secret_key()` - weak/placeholder/missing key -> `secrets.token_hex(32)`, saved with `write_env_keys`; on `OSError` keeps the in-memory key and warns. Logs the file *name* only, never a value.
- `app.py`: `load_dotenv(env_file())` (+ cwd fallback when frozen); guard runs in the `__main__` block (not at import, so tests never write the real `.env`); `limiter.exempt(agent_mission_bp)`.
- `routes/config.py`: password write persists a strong key when the file's is weak, via `env_file()`.
- Not done (Phase 2): frozen `.env` migration, boot validator (DEBUG+LAN etc.), `system.py` ports still read `backend/.env`.

**Files**
- Created: `backend/tests/test_repo_hygiene.py`, `test_env_documented.py`, `test_secret_key.py`, `test_rate_limit_exemptions.py`; `frontend/.env.example`; `.gitattributes`; `.editorconfig`.
- Modified: `backend/.env.example` (rewritten: empty `SECRET_KEY`, `RATELIMIT_ENABLED` commented/off, dead `SPOTIFY_*` removed, `DECK_HOST`/`RATELIMIT_STORAGE_URL`/`VDOCK_FEEDBACK_EMAIL` added), `.gitignore`, `backend/config.py`, `backend/app.py`, `backend/routes/config.py`, `backend/tests/test_security_hardening.py` (fixture patches `env_file`; +1 test), `backend/tests/test_app_main_module_alias.py` (probe redirects `.env` to tmp), `scripts/build-installer.ps1` (dropped `docker-compose.yml` copy entry), `docs/development/DEVELOPER_GUIDE.md`, `docs/CONTRIBUTING.md`.
- Removed from the index only: 30 tracked files (`.devin-shots` 17, `backend/test-scripts` 13). Deleted: the 3 Docker files.

**Deviations / findings**
- `frontend/env.example` (tracked, dead `VITE_*` vars) is a fifth template not named in the plan. With `docs/env.example` and root `.env.example` it sits in `PENDING_REMOVAL` in the hygiene test (needs the user's `git rm`; the test fails if an entry is already gone, so it cannot go stale).
- `scripts/deploy.sh` / `deploy.bat` (and their rows in `scripts/README.md`, plus Docker mentions in `docs/ARCHITECTURE.md`) are Docker-only and now dangling. Not deleted - outside the approved list.
- While verifying, `test_app_main_module_alias.py` (runs `app.py` as `__main__` via `runpy`) hit the new guard and rewrote this machine's real `backend/.env` `SECRET_KEY` (placeholder -> generated 64-char key). Test fixed so it can no longer do that. The outcome equals what the first backend start would have done.
- `RATELIMIT_ENABLED=True` remains in this machine's `backend/.env` (user file untouched); Mission Control is now exempt so it no longer 429s.
- Task 1.4 items needing a separate "yes" were not run: `scripts/vdock_agent_hook.py`, `docs/LICENSE.md`, the three legacy env templates, `backend/Assets` icons, local `NUL` and root log cleanup.

**Not verified:** fresh-clone simulation (nothing committed); `npm run build` (no frontend source changed); packaged/frozen `.env` location (code path covered by unit test only).

### Phase 2 - Production hardening + CI
_Implemented 2026-10-03. Not committed, tagged or pushed (per instruction)._

**User decisions recorded**
- Electron: bump approved for the 6 high advisories. Release **2.3.0** approved (applied only after all verification passed). Docker leftovers (`scripts/deploy.sh|bat`, Docker mentions in `docs/ARCHITECTURE.md`) and the three legacy env templates approved for removal. API-keys UX = status + "copy line / open .env" only, so **Task 2.8 (write-only key endpoint) was NOT built** (superseded, as already recorded in Phase 1).
- Standing guidance: proportionate hardening for a local desktop + LAN panel.

**What changed (user terms)**
- Installed (frozen) builds now have one writable `.env` (`<DATA_DIR>/.env`); an old `.env` next to the exe is copied there once. Ports route also writes through it.
- Startup refuses unsafe combos with an actionable message: `DEBUG` + LAN/non-loopback host, `USE_SSL` with missing cert/key, auth on with an example password (`ChangeThisToAStrongPassword123!`, `your-secure-password-here`, `admin`). LAN on without a deck password logs a WARNING. A names-only startup report is logged (`Bind`, `Auth`, `Integrations: GitHub token ✓ ...`).
- Profiles, `config.json`, `user_settings.json`, triggers and `.env` writes are atomic (tmp + fsync + replace, retries on Windows locks). A daily rolling backup of `profiles/*.json` goes to `<DATA_DIR>/backups/profiles-YYYYMMDD/` (newest 7 kept; backup failure never fails a save).
- One version source `backend/version.py`; `/api/health` (now with `uptime_s`) and the MCP server read it; a test keeps it equal to both `package.json` files.
- `GET /api/config/integrations` (auth-protected): per-secret and per-CLI status, `unlocks`, help URL, display-only env path (no user name), `security.lan_without_password`. WeatherAPI added to the redacted/known secrets. Template placeholder values (e.g. the old `demo-key-replace-with-your-own`) no longer count as "configured".
- CI: `permissions: contents: read`; new `backend-windows` job (Python 3.13); new advisory `audit` job (npm audit frontend + electron, `pip-audit` of the installed env). `scripts/check.ps1` / `check.sh` run the CI steps locally. `engines.node >=20`, `.nvmrc`. `SECURITY.md` "Running on your network" section; `RELEASING.md` version-bump note.
- Release version bumped 2.2.0 -> **2.3.0** in `backend/version.py`, `frontend/package.json`, `frontend/electron/package.json` (+ both lockfile root entries).

**Files**
- Created: `backend/version.py`, `backend/utils/atomic.py`, `backend/services/integration_status.py`, `scripts/check.ps1`, `scripts/check.sh`, `.nvmrc`; tests `test_env_file_location.py`, `test_config_validate.py`, `test_atomic_writes.py`, `test_version_consistency.py`, `test_config_integrations_route.py`, `test_real_env_guard.py`.
- Modified: `backend/config.py` (`migrate_legacy_env`, `EXAMPLE_PASSWORDS`, `validate`, `report`, `lan_without_password`, atomic writes), `app.py`, `routes/{config,system,mcp,profiles,user_settings}.py`, `services/{secrets,triggers}.py`, `utils/{file_manager,logger}.py` (stdout `errors='replace'` so check marks can't break a cp1252 console), `requirements.txt`, `requirements-dev.txt`, tests `conftest.py` (guard), `test_rate_limit_exemptions.py` (9 more polled blueprints), `test_repo_hygiene.py` (pending-removal set dropped), `test_mcp.py`, `test_properties.py`, `test_system_ports.py`; `.github/workflows/ci.yml`, `frontend/package.json`, `frontend/electron/package-lock.json`, `SECURITY.md`, `docs/{RELEASING,CONTRIBUTING,ARCHITECTURE}.md`, `scripts/README.md`.
- Removed with `git rm` (index; nothing committed): `scripts/deploy.sh`, `scripts/deploy.bat`, `.env.example`, `docs/env.example`, `frontend/env.example`. Docker mentions + "Docker Architecture" diagram removed from `docs/ARCHITECTURE.md`; `docs/CONTRIBUTING.md` link fixed to `frontend/.env.example`.

**Already done in Phase 1 (re-verified, not redone):** Task 2.2 SECRET_KEY placeholder fix and `limiter.exempt(agent_mission_bp)`; this phase added the table-driven exemption test and the frozen `.env` migration.

**Counts**
- Backend pytest: 1294 -> **1354** (+60). Frontend vitest: 666 -> **666** (no frontend source changed); `vue-tsc` clean; `npm run build` OK.
- `npm audit` frontend: 1 low -> 1 low (transitive `serialize-javascript`, left per plan). Electron shell: **6 high -> 0** (lockfile refresh within `^41`: electron 41.10.3 -> 41.10.7, @xmldom/xmldom, brace-expansion etc.; `package.json` range unchanged, no `--force`, no major bump).
- `pip-audit` (installed env): 49 vulns in 9 packages -> **8 in 2** (`flask-cors` 4.0.2 -> 6.x and `pytest` 8 -> 9 are major bumps, deferred). Pins bumped: Flask 3.1.3, Werkzeug 3.1.6, PyJWT 2.15.1, python-socketio 5.16.2, python-dotenv 1.2.2 and requests 2.33.0 (both with `python_version >= "3.10"` markers; 3.9 keeps dotenv 1.0.1 / requests 2.32.4 because the newer wheels need 3.10+), urllib3 upgraded in the venv. Full suite verified in a fresh temp venv built from the new pins; `pip check` clean. `pip-audit==2.10.1` added to `requirements-dev.txt`.

**Evidence**
- `scripts/check.ps1`: 4/4 PASS (twice, before and after the version bump). CI YAML parses (jobs: backend, frontend, backend-windows, audit; `permissions` read-only).
- Backend restarted (port 5000, parent + child python.exe replaced). `/api/health` -> `{"status":"ok","version":"2.3.0","uptime_s":...}`; `/api/agent-mission` 200 x120 in a burst with `RATELIMIT_ENABLED=True` still set in this machine's `.env` (no 429); `/api/config/integrations` returns booleans/labels only.
- Startup log shows `Bind: 0.0.0.0:5000 (LAN on)`, `Auth: off`, `Integrations: ... ✓/✗` and the LAN-without-password WARNING; `grep ghp_|sk-ant|github_pat_` over `vdock.log` = 0 hits; `SECRET_KEY` in `backend/.env` is 64 chars (length only printed).
- Insecure combo: `DEBUG=True` + `ALLOW_LAN=True` (temp `DATA_DIR`, env-var overrides, user's `.env` untouched) -> `python app.py` exits 1 with "DEBUG exposes the Werkzeug debugger to your network. Set DEBUG=False in ...".
- Electron: headless smoke on a temp install of the patched electron 41.10.7 -> runtime starts, `preload.js` loads, built `frontend/dist/index.html` loads with 0 renderer console errors; `node --check` on `main.js` / `preload.js`.
- Guard: `conftest.py` now snapshots the real `backend/.env` around every test, restores it and fails if a test changed it (`test_real_env_guard.py` proves it).

**Deviations / notes**
- Electron `node_modules` on this machine was **not** reinstalled: the user's desktop app (4 `electron.exe` processes) holds `node_modules/electron/dist` open (`EBUSY` on rename; npm left the tree intact). The patched lockfile is in place; the fix applies after the app is closed and `cd frontend\electron; npm ci` is run. I did not kill the running desktop app.
- Plan said `pip-audit -r requirements.txt`; that refuses range specifiers (`comtypes>=`, `numpy>=`), so local use and CI audit the installed environment (`pip-audit --skip-editable`).
- Task 2.7 `unlocks` added to `SecretSpec`; `kind: "cli"` rows report "found on PATH" only (no `gh auth status` spawn at request time).
- `scripts/check.sh` has no executable bit (would require staging); run via `bash scripts/check.sh`.
- README badge / `docs/testing/MORNING-TEST-GUIDE.md` still say 2.2.0 (README belongs to Phase 4).
- This machine's `backend/.env` still has `RATELIMIT_ENABLED=True` and dead `SPOTIFY_*` lines (user file, untouched); `WEATHERAPI_KEY` there is the old demo placeholder and now correctly reads as "not set".

**Security note:** this machine runs Allow LAN with **no deck password** (`backend/data/config.json`); startup now warns about it. Recommend setting a password in Settings > Server now.

**Not verified:** the new CI jobs (`backend-windows`, `audit`) have never run on GitHub - only after the user pushes; a packaged installer build (`scripts/build-release.ps1`, needs the PyInstaller backend + closed desktop app) and a frozen-build `.env` run (covered by unit tests only); Python 3.9 behaviour of the new pins (wheels confirmed to exist for 3.9, suite not run on 3.9); 20-minute Mission Control soak (replaced by a 120-request burst).

### Phase 3 - Settings IA (3a split, 3b registry + nav, 3c overview + keys + connect)

#### 3a - split (implemented)
`SettingsView.vue` went from 5,521 to 821 lines. Thirteen panels now live in `components/settings/panels/` (About, AgentAlerts, AppearanceBackground, AppearanceButtons, AppearanceLayout, Connect, Logs, Mcp, RecentActions, SceneSwitching, Screensaver, Server, Templates), with shared state in `composables/useServerConfig.ts`, `useAppShortcutScenes.ts`, `useBackgroundPreview.ts`, `utils/sliderFill.ts` and shared styles in `assets/styles/settings.css`. Source-reading tests were migrated to `tests/helpers/settingsSource.ts`. "Before" screenshots are in `design-log/refs/dl146-before-*`.

The implementing run was cut off by a usage limit after the extraction; it left one test (`background-health.test.ts`) still reading the old file location and wrote no results. Finished by hand: that test now uses `settingsSource()`. Verified: `vue-tsc` clean, vitest 680/680, `npm run build`. A live sweep of every sidebar section at the built bundle produced no console errors and rendered each panel.

**Not done in 3a:** a side-by-side visual diff of every panel against the before set (only the Connect page and a content sweep were checked), and `TemplatesPanel`/`ScreensaverPanel` size review.

#### 3b - registry + nav (PAUSED, partially implemented)
Work stopped at the user's request. Tree is green: `vue-tsc` clean, vitest 691/691 (680 -> 691), `npm run build` OK. **Not verified in a browser at all** (no live check, no tour run, no screenshots).

**Done**
- `frontend/src/settings/registry.ts`: typed `SECTIONS` (Overview, Appearance, Agents & automation, Integrations, Devices & network, System), `SEARCH` (about 35 entries, all anchors real), `NOT_SEARCHABLE`, `LEGACY_TABS`/`LEGACY_SUBS`, `resolveRoute`, `searchSettings`, `NAV_SECTIONS`/`LANDING`. Overview is registered with no pages, so the sidebar lists 5 sections and Settings lands on Appearance until 3c adds the Overview panel.
- `frontend/src/composables/useSettingsNavigation.ts`: section/page state synced to `?section=&page=`; legacy `?tab=&sub=` and `?anchor=` resolved; last section kept in `sessionStorage`; ignores query changes once the route leaves `/settings`.
- `SettingsView.vue` now loops `NAV_SECTIONS` for the sidebar and `activeSection.pages` for the sub-tab bar, uses `searchSettings`, and mounts each page's panels from the registry (`PANELS`, `panelBindings`, `STACKED_PANELS`). Old `activeTab`/`appearanceSubTab`/`integrationSubTab`, `PAGE_META` and the hand-written search index are gone. The topbar Apply button is hidden on pages flagged `autosaves` (Logs, About, Templates, Connect, Security, Ports, Triggers, MCP). `data-tour` values are carried by `tour` on sections/pages (`nav-appearance`, `nav-integration`, `nav-templates`, `nav-server`, `nav-connect`, `nav-logs`, `nav-about`, `subtab-screensaver`).
- `ServerPanel.vue` split into `panels/SecurityPanel.vue` (auth), `panels/PortsPanel.vue` (host and ports), `panels/StartupPanel.vue`; Notifications moved out of `AppearanceLayout.vue` into `panels/NotificationsPanel.vue` (shown under Agent alerts). Shared `.status-msg` rules moved to `assets/styles/settings.css`. The Layout "Reset section" no longer resets the toast level (it has its own reset button).
- Tests: new `tests/settings-registry.test.ts`; updated `settings-subtabs`, `button-behaviour-subtabs`, `logs-and-weather-move`, `session-logs`, `screensaver-layout`, `guide-page`, `dashboard-font` to read the registry or the new wiring.

**Deviations**
- Agents & automation lists Scene switching first (not Agent alerts) so its click count stays at 3. Swap the order in 3c once Overview has the quick switch.
- Registry pages use `panels: string[]` (a page can mount several panels) instead of `component: string`.
- The "every `<h2>` has a search entry" test is implemented as "every `<section class="panel" id>` is a registered anchor, and every anchor is searchable or exempt".
- No search entries for GitHub token, Anthropic key or weather key: there is no Accounts & keys page yet (3c).

**Not done**
- `GuideView.vue` and `AgentMissionControl.vue` copy still names old paths (`Settings -> Integrations -> MCP server`, `Settings -> Server -> Authentication`, `Settings -> Connect a device`, `Settings -> About -> Launch tutorial`); `services/tutorial.ts` text mentions the old rail.
- Live verification at 1024x600 and 1400x900, deep-link checks, search checks, tutorial tour run, click-count table, `design-log/refs/dl146-after-*` screenshots, `scripts/check.ps1`.
- A mounted-component test for nav (6 sections, `?tab=connect`, search "password", `?anchor=touch` scroll) in `settings-subtabs.test.ts`; coverage is registry-level only.
- Not yet checked: `?anchor=` scroll timing after a page switch, that the Appearance Buttons v-model bindings via `panelBindings` still update the draft chip, and that `openStandaloneSettings` links (now `?section=&page=`) open correctly.
- README row note "Phase 3b implemented" deliberately not added (3b is not complete).

#### 3b - finish run (complete)
Supersedes the "PAUSED" status and "Not done" list above. Verified: `vue-tsc` clean, vitest 696/696 (691 -> 696), `npm run build`, `scripts/check.ps1` PASS.

**Live verification** (built bundle on :5000, cursor-ide-browser, CDP viewport emulation at 1024x600, 1400x900, 768x1024, 390x844):
- Sidebar lists 5 sections + Guide at every size. Every page of every section rendered; no horizontal page scroll at any size after the fixes below.
- Deep links: `?tab=server` -> Devices > Ports & host; `?tab=integration&sub=alerts` -> Agents > Agent alerts; `?tab=connect` -> Devices > Connect; `?tab=about` -> System > About; `?section=&page=` and `?anchor=` (scrolled to `#notifications` on phone) all land correctly.
- Search: "phone" -> Connect, "scene" -> Scene switching, "alert" -> Agent alerts, "password" -> Security, "port" -> Ports & host. "token" and "github" return nothing (no Accounts & keys page until 3c).
- Tour (1400x900): launched from About, all 9 steps ran `/profiles` -> `/` -> `/settings` -> `/`; Settings and Find-a-setting steps spotlight `.nav` and `.nav-search`. No tour step uses `data-tour`/`activate`, so nothing broke. Note: the tour (and its auto-start) is skipped when `min(width,height) <= 700` on a touch-capable device, so it cannot run on the 1024x600 panel or a phone (existing DL-061 behaviour, flagged for DL-147).
- Every before-set page still exists: Buttons/Layout/Background/Screen saver, Alerts/Scenes/MCP/Triggers (Agents), Templates, Connect, Security + Ports (old Server), Logs, Startup, About.

**Phone/tablet findings and fixes** (`assets/styles/settings.css`, `ConnectPanel.vue`, `LogsPanel.vue`, `AppearanceButtons.vue`):
- At <=880px the rail stacked above the content as a sticky block 379px tall (45% of a 844px phone) with 40px rows. Now: brand hidden, search row + one swipeable strip of 44px section pills (~110px total). Grid column changed to `minmax(0, 1fr)` so the strip cannot widen the page.
- `--target` is 44px at <=880px; sub-tabs, `.btn.sm` and nav pills are >=44px. Topbar action buttons wrap instead of overflowing.
- Connect: the 380px QR preview overflowed (`max-width: 100%` added on its column). Logs toolbar now wraps. Grid +/- steppers are 44px on coarse pointers / narrow widths.
- Not fixed (panel internals, out of 3b scope; to DL-147): range-slider tracks are 6px tall (thumb is the hit target), and some panels' dense rows were only checked for overflow, not visually.

**Click counts** (from opening Settings; unchanged because section landing = first page):
| Task | Before | After |
|---|---|---|
| Connect a phone | 1 (Connect) | 1 (Devices & network lands on Connect) |
| Add a GitHub token | n/a (no UI) | n/a until 3c |
| Auto scene switching | 1 (Integrations > Apps) | 1 (Agents & automation lands on Scene switching) |
| Agent alert behaviour | 2 | 2 (Agents & automation > Agent alerts) |
| Change a button's action | dashboard edit mode | unchanged (not a Settings task) |

**Screenshots:** `design-log/refs/dl146-after-connect-390x844.png`, `dl146-after-ports-768x1024.png`, `dl146-after-agent-alerts-1024x600.png`, `dl146-after-appearance-buttons-1400x900.png` (all < 400 KB).

**Also done**
- Copy updated to the new paths: `GuideView.vue` (MCP, Security, Connect, tutorial, sidebar blurb), `AgentMissionControl.vue`, `services/tutorial.ts`. `frontend/public/guide/*` is PNG only (no text); `guide-settings.png` still shows the old rail and is refreshed in Phase 4. README/docs paths belong to Phase 4.
- New mounted test `src/tests/settings-nav.test.ts` (5 tests: sections, `?tab=connect`, `?section=&page=`, search "password", `?anchor=` with mocked `scrollIntoView`); wrapper is unmounted after each test.

#### 3c - Overview, Accounts & keys, password in Connect (implemented; live checks below)
_2026-10-03. Not committed._

**What changed**
- **Overview** (new default landing, `panels/OverviewPanel.vue`): "Needs attention" rows (LAN open without password -> Connect; GitHub token not set -> Accounts & keys; "N of 4 agents hooked" -> Agent alerts) or one green "Everything is set up"; Quick switches (Auto scene switching, Agent alerts, Allow LAN, Screen saver); "Edit keys" link to `/?edit=1`, handled in `DashboardView.vue` (enters edit mode once, then drops the flag; hidden on compact-touch devices because the store already refuses edit mode there).
- **Accounts & keys** (`panels/AccountsPanel.vue`, first page of Integrations): one row per secret from `GET /api/config/integrations` with a Configured / Not set chip, what it unlocks, **Copy line** (`GITHUB_TOKEN=`) and **Get a key**; one **Open .env** button (only shown on the PC itself); CLI rows (gh, Claude Code) Found / Not found + Install link. Never accepts or shows a key value.
- **Backend:** `POST /api/config/open-env` (auth-protected, **localhost only**, 403 for LAN) opens the env file in the OS default editor, creating it empty if absent. `services/integration_status.open_env_file` / `_launch`. Test: `test_open_env_route.py` (2).
- **Password beside the LAN switch:** `DeckPasswordForm.vue` extracted from Security (new/confirm, validation, `enable` or `change` mode); `useDeckAuth.setAuthEnabled` holds the require_auth write. Security now uses the form; Connect shows an amber "Protect it with a password" row under the Allow-LAN switch when LAN is on and auth is off.
- **Advanced:** Devices & network's Ports page is now labelled **Advanced** (title still "Ports & host"; legacy `?tab=server` still lands there).
- Agents & automation now opens on **Agent alerts** (swapped with Scene switching, as 3b noted).
- Shared helpers: `useSetupStatus` (integrations + hook counts), `useServerConfig.setAllowLan`, `utils/copyText` (extracted from Connect).
- Search: "token"/"github" -> Accounts & keys; added Overview, Quick switches, Edit keys, Command-line tools entries.

**Tests:** frontend 812 -> **819** (`settings-nav` +3 incl. token/github search + attention row navigation, new `deck-password-form` 4); backend 1516 -> **1518** (`test_open_env_route.py`); `vue-tsc` clean; `npm run build` OK; `scripts/check.ps1` 4/4 PASS.

**Touch targets (shared CSS, `settings.css`):** switch hit area is now the full `--target` (was target - 6 = 38px on phones); a `(pointer: coarse)` block gives `--target: 44px`, `.btn.sm`, sub-tabs and rail items 44px at any width (tablet landscape and the 7" panel were stuck at 28-40px because the 44px rules only applied below 880px).

**Live verification** (built bundle on :5000 after a backend restart for the new route; cursor-ide-browser, CDP emulation incl. touch, reset afterwards; nothing toggled, `backend/.env` untouched):
- 390x844, 768x1024, 744x1133, 834x1194 (portrait), 1133x744 (tablet landscape, touch), 800x480 and 1024x600: no horizontal scroll (`scrollWidth == innerWidth`, no element past the right edge) and no target < 44px on Overview, Accounts & keys and Connect (with the password prompt). 820x1180 not run separately (between 768 and 834, same breakpoint).
- Overview shows this machine's three real problems (LAN without password, GitHub token not set, 3 of 4 agents hooked); each row navigates to the right page. "Edit keys" opened the dashboard in edit mode and cleaned the URL to `/`. The link is absent on compact-touch viewports (800x480), matching the store's edit-mode gate.
- Accounts & keys: Anthropic / GitHub / WeatherAPI "Not set", gh and Claude CLI "Found"; copy-line and Get-a-key present; no input accepts a key. "Open .env" appears only when the page is served from localhost.
- Screenshots: `dl146-after-accounts-390x844.png`, `-accounts-1024x600.png`, `-overview-800x480.png`, `-connect-password-1133x744.png`.

**Click counts from the dashboard (Settings opens on Overview):**
| Task | Before | After |
|---|---|---|
| Connect a phone | Settings -> Connect (3 with the switch), no password prompt | Settings -> Devices & network -> Allow LAN (3); password offered on the same page (+ relaunch); also 2 via Overview quick switch |
| Add GitHub token | impossible in-app | Settings -> "GitHub token not set: Add it" -> Copy line / Open .env (4 incl. opening Settings; 3 after Settings is open) |
| Auto scene switching | 3 | Settings -> Overview switch (2) |
| Agent alert behaviour | 4 | Settings -> Agents & automation (lands on Agent alerts) -> control (3) |
| Change a key's action | 5 | Settings -> Edit keys -> key edit -> pick -> Save (5 incl. opening Settings; 4 once there) |
Search: "token" and "github" -> Accounts & keys; "phone" -> Connect; "password" -> Security; "port" -> Advanced.

**Deviations / not done**
- `DeckPasswordForm` did not exist; it was created by extracting Security's inline form (plan said "reuse").
- "Ports/host/SSL under Advanced": done as a page named **Advanced** in Devices & network (not a collapse inside Connect). SSL fields are not in the Ports panel today and were not added.
- `/api/config/open-env` is new backend surface (needed for "Open .env"); localhost-only.
- Empty-state/consistency pass limited to the new pages (all-set row, "Not found" chips); existing panels' empty states (Running apps, Recent actions, Logs) were not unified.
- Tour is still skipped on touch panels / phones (3b note; DL-147).
- Not verified: "Open .env" actually launching an editor (route tested with a stub; not clicked to avoid opening a window on the user's `.env`); password prompt submit on the real server (would turn auth on); a physical phone/panel.

### Phase 4 - README refresh + screenshots
_Implemented 2026-10-03. Not committed (per instruction)._

**README** (`README.md`, 287 lines, was 308): version badge 2.3.0; "Contents" list and the comparison table/use-case list condensed; new sections "Built for AI coding agents" (Mission Control, branded alert, the DL-145 actions) and "Phone and tablet as the touch screen" (DL-147: phone approval remote, tablet layouts + edit mode, keep-awake, reconnect, QR pairing, install as app) with a LAN-needs-a-deck-password note; Settings section rewritten for Overview / Appearance / Agents & automation / Integrations (Accounts & keys) / Devices & network / System; Configuration now has an env table pointing at `backend/.env.example` and `frontend/.env.example` (names only); Node 20+; stale repo tree removed. Docker and deploy scripts were already gone from the README (verified: no mentions). Project folder name, GitHub URLs and clone commands unchanged.

**Screenshots** (`docs/assets/screens/`, all JPEG, 42-126 KB, captured from the built bundle on :5000 via cursor-ide-browser): `settings-overview.jpg`, `settings-accounts.jpg`, `mission-control.jpg`, `claude-alert.jpg`, `connect-page.jpg`, `phone-portrait.jpg` (390x844 emulated), `tablet-portrait.jpg` (820x1180), `tablet-edit.jpg` (820x1180, entered via `/?edit=1`, nothing saved). The Mission Control / alert / phone shots use fake sessions `readme-demo-1/2` POSTed to `/api/agent-events`; both were ended afterwards. Approve / Deny / Got-it-on-a-real-session were never used (Got it only dismissed the fake alert). On Connect the LAN IP was masked in the DOM to `192.168.x.x` and the QR canvas blurred before capture. Overview and Accounts show no secrets, tokens or paths. Device emulation was cleared afterwards. Screenshots were saved via CDP `Page.captureScreenshot` because the screenshot tool does not write files to disk.

**Other:** `docs/testing/MORNING-TEST-GUIDE.md` updated to 2.3.0 with a banner and a "Phone & tablet checklist" of real-device checks. `.gitignore` already covers `.env`/`backend/.env`/`frontend/.env`, `venv/`, `node_modules/`, `frontend/dist/`, `*.log`, `backend/data` runtime files and backups; no entries added. **Build output policy:** `frontend/dist/` is gitignored (never tracked); Flask serves it, so run `cd frontend && npm run build` after UI changes (CI and releases build it themselves).

**Verification (final):** `vue-tsc` clean; vitest 947/947 (121 files); `npm run build` OK; pytest 1544 passed; `scripts/check.ps1` 4/4 PASS; `GET /api/health` -> `{"status":"ok","version":"2.3.0"}`.

**Not verified:** the phone/tablet shots are Chromium emulation, not real devices (the emulated page showed the "Can't reach VDock" banner, an artefact of this embedded browser's socket, hidden in the DOM before capture - the banner itself is genuine UI); I could not inspect the images pixel-by-pixel, only through descriptions, so crop/layout of `phone-portrait.jpg` and `tablet-portrait.jpg` deserve a glance; new CI jobs have never run on GitHub; packaged installer build; the real-device checklist in the morning guide; README `screens/` files from earlier releases (e.g. `settings-buttons.png`) remain on disk but are no longer referenced.

**DL-146 overall:** Phases 1, 2, 3 (a/b/c) and 4 implemented. Open user actions: `cd frontend\electron; npm ci` after closing the desktop app (patched lockfile), commit/push, set a deck password.

### Follow-up - closure + test pass
_2026-10-03._ Claude usage limit cut a leftover run mid-build; finished in-session.

- **README shots:** live DOM has one `.deck-grid` and `scrollHeight == innerHeight`. The stacked look is a CDP-emulation capture artefact, not a deck bug. Files left as-is (retaking on a throwaway profile was skipped so the owner's live profile stayed untouched). "Volume Slider (Copy)" is a label on the live profile.
- **"Can't reach VDock":** built bundle now dials `location.origin` (`utils/socketUrl.ts`). `socket_origins()` uses `https` when `USE_SSL` is on. Tests: `socket-url.test.ts`, `test_socket_origins_ssl.py`.
- **Tour:** first-run still skipped on phones; Settings → About → Launch tutorial now starts on compact-touch (7" panel / phone).
- **Remaining tablet sizes (remeasured live):** 768x1024 (min key 226), 924x1480 (297), 1180x820 (155), 1194x834 (158), 1366x1024 (186) — one grid, no horizontal scroll, no banner. Five sub-44px chips are slider presets (known leftover).
- **Skipped:** empty-state unification (many panels); guide-settings.png recapture; throwaway-profile screenshot retake; tap-outside edit drawer.
- **Docs:** `docs/FEATURE-SUMMARY-2.3.0.html`, `docs/testing/MANUAL-TEST-CHECKLIST.md`.
- **Verification:** vue-tsc clean; vitest 952; pytest 1546; `scripts/check.ps1` 4/4; `/api/health` ok 2.3.0; `/api/config/integrations` returns status only (no secret values). Secret-pattern scan of source hit CSS `mask-` only. Real `.env` / profiles not modified.
