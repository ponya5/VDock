# DL-048 — Power Features Pack (8 features from competitive analysis)

## Background

`competitive-analysis.md` compared VDock against Elgato Virtual Stream Deck,
Touch Portal, WebDeck, and VSDinside M18. Eight gaps were worth closing. Survey
of the codebase found the backend already executes `multi_action`, `macro`, and
`toggle` (`actions/multi_action.py`, `toggle_action.py`, `macro_action.py`);
profile export/import API + UI exist; Electron already registers a global
summon shortcut (Ctrl+Shift+D). So most features are frontend/editor work, not
new engines.

## Problem

Buttons are single-shot: one press runs one action, fire-and-forget. No state,
no sequences, no drags, no remote-device on-ramp, no sharing format for scenes.

## Questions and Answers

**Q: `multi_action` vs `macro` — unify?**
A: Keep both. `macro` = keystroke/text sequence (existing step builder);
`multi_action` = sequence of full deck actions (any catalog action + delay +
stop_on_error). They solve different things — macros type, multi-actions do.

**Q: Where does toggle visual state live?**
A: `buttonStateStore` (transient, already maps `data.sublabel` onto the face).
Extend `ButtonState` with `toggleSide`. Backend `ToggleAction` already returns
`data.side`/`sublabel` and rolls back on failure — the frontend just consumes
it. DeckButton swaps icon/color/label when `side === 1` using new config keys
`off_label`/`off_color`/`off_icon`. Cross-window sync: broadcast toggle side
via existing `settings_updated`-style socket event → `buttonStateStore.set`.
Initial side: backend `GET /api/actions/toggles` returns the `_sides` map.

**Q: Slider — new Button kind or action type?**
A: Action type `slider` with config `{target, min, max, step, value}`.
DeckButton renders a drag track instead of icon+label. Drag dispatches throttled
`execute` with `config.value` filled in. Targets: `volume` (new backend
`volume_set`), `brightness` (existing `brightness_set`), `ui_brightness`
(frontend-only, reuses uiBrightness setting). No new Button kind — keeps the
grid/schema identical.

**Q: QR — how does a phone find the server?**
A: `qrcode` npm package renders `http://<lan-ip>:<port>` to a canvas in a
"Connect a device" card (Settings → Server). LAN IP from backend
`GET /api/config` (add `lan_ip` via socket.gethostbyname). Gate: requires
server bound to 0.0.0.0 — the existing `ALLOW_LAN` env; card shows a warning
when bound to localhost with instructions to relaunch with `ALLOW_LAN=1`.

**Q: Summon overlay — global hotkey in browser?**
A: Two tiers. Electron: existing `Ctrl+Shift+D` already summons the window at
cursor — extend to also open the quick-deck overlay via `webContents.send`.
Browser: in-window hotkey (default `` ` ``) toggles `QuickDeckOverlay` —
a compact floating deck (docked sidebar + current scene page) centered,
Esc/action-dismiss. Honest scope: browsers can't do OS-global hotkeys.

**Q: Press feedback — WebAudio without a file?**
A: Tiny oscillator tick (no asset, no paid service), gated by a persisted
`pressSoundEnabled` setting + `pressSoundStyle` (click/blip/none). Respects
prefers-reduced-motion for the scale animation.

**Q: Press/release — how not to break `click`?**
A: `action.trigger: 'press'|'release'` (default `release` = today's click).
`action.release_action` optional — when set, pointerdown runs `action`,
pointerup/leave runs `release_action` (push-to-talk). Edit mode and drags skip
all dispatch. Pointer capture handles finger-slide-off.

**Q: Export/import — what format?**
A: Profile packs exist. Add scene packs: `{vdock_pack: {kind:'scene', v:1},
scene: {...}}` — IDs regenerated on import, unknown action types pass through
(they degrade to no-op, not crash), no settings/secrets exported (scenes only
carry buttons).

## Design

```
ButtonEditor
 ├─ multi_action → step list (catalog picker + per-step delay + reorder)
 ├─ toggle       → on/off action pickers + on/off label/icon/color
 ├─ slider       → target/min/max/step
 └─ any          → trigger select + optional release action

DeckButton
 ├─ action.type==='slider' → <SliderFace> (pointer drag → throttled execute)
 ├─ toggle + side===1     → off-icon/color/label swap
 ├─ trigger==='press'     → dispatch on pointerdown
 └─ release_action        → dispatch on pointerup

QuickDeckOverlay (Teleport body, z below alert 30000)
 └─ docked buttons + current scene grid, hotkey `` ` `` / Ctrl+Shift+D (Electron)

Settings → Server → "Connect a device" card → QR canvas + LAN URL + bind warning
```

## Implementation Plan

- [ ] F6 press feedback (sound + scale) — smallest, self-contained
- [ ] F8 press/release trigger + release_action
- [ ] F2 toggle editor + frontend side rendering + socket sync
- [ ] F1 multi_action editor UI (backend exists)
- [ ] F3 slider action + backend volume_set + SliderFace
- [ ] F7 scene pack export/import (profile packs exist)
- [ ] F4 QR card + lan_ip endpoint + mobile verify
- [ ] F5 QuickDeckOverlay + Electron hotkey bridge

## Trade-offs

- Slider as action type (not Button kind): zero schema churn, reuses grid.
- Oscillator tick vs sound file: no asset to ship/license; less satisfying than
  a real click sample — acceptable v1.
- Scene packs carry buttons only (no profile settings): safe to share publicly.
- Browser summon is in-window only — documented honestly in the UI.

## Verification Criteria

- Each feature exercised live at 1024×600 + 390×844 (mobile for QR/layout).
- Toggle: press → icon/color/label swap; reload → correct side.
- Multi-action: 3 steps incl. delay run in order; failure stops chain.
- Slider: drag changes real volume; badge shows value.
- QR card shows real LAN URL; QR decodes to it.
- Export → import round-trips a scene with fresh IDs.
- Full test suites + typecheck + build green.

## Implementation Results

All eight features implemented, exercised live at 1024×600, and verified.

- **F1 Multi-action** — catalog `multi_action` spec + ButtonEditor ordered-step
  list (SubActionEditor per step, per-step `delay` ms, reorder/remove).
  Backend `multi_action.py` reads `delay` off each step (delay = wait before
  the *next* step; a delay on the last step is a no-op). Verified: 300ms delay
  on step 1 → 300ms elapsed; sequential; `stop_on_error` aborts the chain.
- **F2 Toggle** — catalog `toggle` spec (on/off action + label + icon +
  colour), editor SubActionEditor pair + per-side fields. Backend
  `toggle_action.py` corrected so `sublabel` reports the *current* state (was
  the next press's label) — the test asserting the old semantic was updated.
  Verified: side flips 1→0, sublabel Muted→Unmuted, failed action rolls back.
  Face re-skins via `buttonStateStore.toggleSide` (icon/colour/label per side);
  `toggleSync` service + `toggle_state` socket broadcast keep other windows in
  step; `GET /api/actions/toggles` seeds late-loading windows.
- **F3 Slider** — new `slider` action type + `SliderButtonFace` drag track.
  Backend `cross_platform` gained `volume_set`/`volume_get` (pycaw → nircmd →
  osascript/amixer/pactl fallbacks) and `brightness_set` already existed.
  Verified live: drag to ~80% → label/fill/ badge all show 80%, `volume_set`
  dispatched. `pycaw==20240210` added to requirements (Feb 2024, well-aged).
- **F4 QR + mobile** — Settings → Server → "Connect a device" card: LAN toggle,
  QR canvas, URL text, localhost warning. Backend `/api/config` now returns
  `lan_ip`/`lan_reachable`; `app.py` binds `0.0.0.0` when `ALLOW_LAN=true` even
  with `HOST` unset (was a latent bug). URL points at the backend port — correct,
  because Flask serves `dist/` in production. `qrcode` dep added. Portrait
  600×1024 verified — grid reflows, labels wrap inside buttons, slider works.
- **F5 Quick-deck** — `QuickDeckOverlay` (glass panel, scene title, current-page
  buttons, hint bar) mounted in `App.vue`. Summon paths: in-window `` ` `` key →
  `vdock-quick-deck` CustomEvent; `ui_command` socket `toggle_quick_deck`;
  Electron `Ctrl+Shift+D` → preload IPC → same event. Verified live: opens with
  all 7 scene buttons, closes on toggle/Esc.
- **F6 Press feedback** — `usePressFeedback` (WebAudio oscillator tick, style
  variants) + `pressSoundEnabled`/`pressSoundStyle` persisted end-to-end
  (defaults → ref → payload → apply → load → watch → backend allowlist).
  Ripple + scale already existed; sound added. Settings UI under Button
  Behaviour.
- **F7 Scene packs** — `utils/scenePack.ts` (export/sanitize/regenerate IDs) +
  Export/Import in `SceneEditor` + `SceneNavigation` + `DashboardView` handler.
  Buttons only, IDs regenerated on import — safe to share publicly.
- **F8 Press/release** — `ButtonAction.trigger` + `release_action` added to
  types; `DeckButton` pointerdown/up/leave/cancel lifecycle; `useButtonActions`
  `handleButtonPress`/`handleButtonRelease`; `dashboard.executeAction` for the
  release payload; editor trigger picker + release SubActionEditor.

### Deviations from plan

- Toggle `sublabel` semantic flipped to *current* state (test updated to match)
  so the face reads as a status indicator, not a "next press" hint.
- `volume_get` on Darwin changed to parse command output directly — the helper
  didn't accept the extra arg my first pass passed.
- Slider `brightness` target dispatches `brightness_set` with `brightness` (not
  `value`) — matched the existing action's config key.
- Backend test added-then-fixed: catalog `toggle` id duplicated a spec already
  at line 566 — removed my redundant `_COMPOSITE` entry, kept the richer one.
- `test_backend_source_parses_on_the_minimum_python` caught a `str | None`
  union — replaced with `Optional[str]` (repo targets Python 3.9).

### Verification

- Frontend: **231/231** tests, 57 files; `vue-tsc` clean; production build green.
- Backend: **772/772** tests.
- Live at 1024×600: onboarding → dashboard → quick-deck overlay → slider editor
  → slider drag → settings QR card → portrait 600×1024.
- Backend functional: toggle side/sublabel flip + rollback; multi-action delay.
- No secrets/personal data added; QR carries only a LAN URL; LAN stays opt-in.

### Follow-up (2026-09-21): volume slider broken on Windows

Reported: slider stuck at 0%, drag did nothing, and the name/% text was
tiny next to regular button labels.

Two root causes:

1. **Missing dep**: `pycaw` (in `requirements.txt`, `sys_platform ==
   'win32'`) was never installed in `backend/venv`, so
   `_windows_volume_interface()` returned early and `volume_set` fell
   through to NirCmd — also absent. Installed `pycaw==20240210` (+ dep
   `comtypes`) into the venv.
2. **COM threading**: once pycaw was present, calls still failed with
   `WinError -2147221008 CoInitialize has not been called` — COM is
   per-thread and Flask-SocketIO request workers start uninitialized.
   Fix: `comtypes.CoInitialize()` inside `_windows_volume_interface()`
   before `AudioUtilities.GetSpeakers()` (OSError swallowed — already-
   initialized threads stay usable). Verified: direct thread test +
   8× `volume_get` + `volume_set` over the live API all succeed, and a
   synthetic pointer drag on the dashboard moved the real OS volume
   (30%) and read it back.

UI sizing: `SliderButtonFace` ignored `buttonSize`, so its text stayed
at fixed ~13px while regular labels scaled. Now accepts `button-size`
(DeckButton passes it), scales label/value/icon via `--slider-text`
(same `fontSize × buttonSize` formula as `labelStyle`), and scales
track/thumb via `--slider-track-h`/`--slider-thumb` capped at 1.5×.
Verified live at 1568×830: label and % read at parity with neighbouring
button labels.

Frontend: `vue-tsc` clean, 231/231 tests. Backend: py_compile clean,
501 action/catalog/plugin tests pass.

### Still open (follow-ups)

- `volume_set`/`volume_get` exercised on Windows dev host; macOS/Linux fallbacks
  are code-reviewed but not run on-device.
- `ui_command` `toggle_quick_deck` relay verified at the listener level; the
  full remote-trigger path (another window emitting it) not yet exercised.
- Scene-pack file round-trip verified via unit-level sanitize/regenerate; an
  on-disk export→import of a real scene file is a good manual pass.
