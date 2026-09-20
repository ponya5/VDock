# DL-018 — Settings sync: stale-load revert & rebroadcast (background flicker)

## Background

User report: "the background style get crazy and changing by it self in a
flickering way" — the Background Style picker on Settings visibly flipped
between values on its own.

## Root cause

Two compounding defects in `frontend/src/stores/settings.ts`, both on the
`loadSettingsFromServer()` path (runs at every app mount and on every
`refreshVdock()` — i.e. every Settings→Dashboard navigation, plus every
`vdock_refresh` request; with `openSettingsInNewTab` the user runs two
windows, so broadcasts actually have an audience):

1. **Stale-GET regression.** Saves are debounced 400 ms
   (`SERVER_SYNC_DELAY_MS`). If a reload/refresh landed inside that window,
   the GET returned the pre-change value and `applySettingsObject()`
   force-applied it — the just-picked background reverted.
2. **Unguarded rebroadcast.** The server apply ran outside
   `isApplyingRemoteSettings`, so the deep settings watcher called
   `saveSettings()` → `broadcastSettingsToOtherWindows()` and pushed the
   stale value to every other open window — which then flipped their
   pickers too. Each refresh re-asserted the stale value: visible flicker.

Contributing factor: the backend allowlist dropped four payload keys
(`dockedButtonHeight`, `buttonDefaultAnimation`, `buttonDefaultIconLoop`,
`buttonDefaultEffect`), so server payloads never matched the local shape.

## Design

- `loadSettingsFromServer()` now `await nextTick()` (lets a just-queued
  watcher schedule its PUT), then drains pending writes — pending debounce
  → `flushSettingsToServer()`; in-flight PUT → awaits it — **before** the
  GET, so the response can't be older than local state.
- The server payload is applied through `applySettingsFromRemote()` (the
  guarded path) — the watcher sees `isApplyingRemoteSettings` and never
  rebroadcasts server state.
- `persistSettingsToServer()` rewritten with trailing-write semantics:
  `serverSyncInFlight` is now a `Promise`; a call during flight queues one
  follow-up PUT (latest payload) and returns the shared promise, so
  callers can await a fully-drained server.
- New `remoteSettingsDiffer()` replaces the strict whole-payload
  `JSON.stringify` equality check: compares only keys the remote actually
  sent (`background` resolves through `migrateBackground` so legacy fields
  compare correctly). Subset/legacy payloads that change nothing are now
  skipped entirely instead of re-applying every ref.
- `user_settings.py` allowlist gains the four missing keys so server
  payloads stop diverging in shape from client payloads.

## Implementation results

- Live reproduction at `localhost:4445/settings`: assign `background` and
  call `loadSettingsFromServer()` in the same task (tightest possible
  race). Before: value reverted to the stale server value and an
  unguarded broadcast pushed it to other windows. After: the drain flushes
  the pending PUT first, the GET returns the fresh value, nothing
  reverts, no rebroadcast. Server file confirmed updated.
- Remote-apply semantics unchanged for genuine diffs: a payload with a
  different `background` still applies (remote wins, guarded, no echo).
- `vue-tsc --noEmit` clean; 49 files / 175 tests pass.
