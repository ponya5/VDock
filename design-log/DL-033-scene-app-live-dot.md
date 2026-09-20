# DL-033 — Live-app indicator dot on scene pills

## Background
User: when a scene is loaded (e.g. Claude Code), show a green dot on the
top-right indicating VDock sees a running session — i.e. the scene's
buttons will actually reach the app. Apply to other apps too.

## Problem
No live "is the app running" signal on the dashboard. Scenes link to apps
via `scene.appId`, `scene.triggeredByApp`, or an enabled AppIntegration,
but nothing checks process state.

## Design

### Backend — `GET /api/app-monitor/detected-profiles`
One `psutil.process_iter` pass collecting lowercased process names +
cmdline haystacks. Per `AppProfile`:
- `kind == 'terminal_agent'` (claude-code, devin): detect via the
  commands' `session_marker` values scanned against process names and
  cmdlines — their `exes` are shared terminal hosts (cmd.exe etc.) and
  would false-positive on any open terminal.
- other kinds: detected iff any `profile.exes` matches a running process
  name.
Response: `{detected_profiles: [...], running_exes: [...]}` — running_exes
covers custom integrations pointing at arbitrary exes (spotify.exe…).

### Frontend
- `services/appDetection.ts`: `detectedProfiles`/`runningExes` Set refs +
  10s poll (idempotent `startAppDetection` on pill mount). Loads
  `/api/app-profiles` once for `exe→profileId` and `commandId→profileId`
  maps.
- `sceneAppIsLive` resolution order (most specific first):
  1. `scene.appId` ∈ detectedProfiles
  2. **command vote** — majority of `button.action.type` ids resolving via
     `commandId→profileId`. This is the decisive path on real profiles:
     saved scenes carry no `appId`/`triggeredByApp`, but their buttons
     always carry command ids (`cc_prompt` → claude-code).
  3. `triggeredByApp`/integration exe → profileId → detected; unknown
     custom exe → raw `runningExes` check.
- `GlassPillSceneSelector`: `.app-live-dot` (green, glowing, pulsing,
  `pointer-events:none`, reduced-motion aware) at the segment's top-right.

## Implementation Results
- Backend endpoint shipped + tested (`test_detected_profiles.py`, 2/2).
- **Reactivity bug found live**: first render hit the `!exe` early return
  before any `detectedProfiles.value` read → render effect never
  subscribed → dot never appeared. Fixed by reading both refs
  unconditionally at the top of `sceneAppIsLive`; regression-locked by a
  source test asserting the read precedes the first branch.
- Live verified at `127.0.0.1:5099`: backend reports
  `[devin, claude-code]` via session markers → Claude Code pill shows the
  green dot (14 `cc_*` command votes), Cursor pill stays dark (cursor.exe
  not running). No false positive on the shared `WindowsTerminal.exe`
  host.
- Tests: 216/216 vitest (9 new), vue-tsc clean, vite build clean.

## Verification
- Live: dot renders top-right of the Claude Code pill when its session is
  detected; absent for apps not running.
- vitest + typecheck + build; backend pytest for the endpoint.
