# DL-138 — Field-level settings sync (fix the boot stomp)

## Problem

A phone that scans the connect QR shows the widget-dashboard screensaver
even though `screensaverStyle` is `spectrum` server-side. Root cause is a
full-payload sync protocol: every client PUT/broadcast carries its
**entire** settings blob, so any client holding stale or default values
overwrites the shared state:

- `detectSmallScreenDefaults()` runs at store setup on every
  compact/touch device and calls `saveSettings()` → a PUT of ~60 factory
  defaults (`screensaverStyle: 'widgets'`, `screensaverSpectrumWidgets:
  false`, …) is scheduled before the boot GET lands.
- `loadSettingsFromServer()` deliberately **drains that pending PUT
  before the GET** (it was protecting fresh local edits from being
  regressed by a stale read) — so the phone writes defaults to the server
  *and then reads them back*. Spectrum never stands a chance.
- The same path explains earlier "ghost" flips: a freshly booted compact
  client (browser devtools device mode, the panel, a phone) stomped
  `screensaverSpectrumWidgets`/style for every peer mid-session.
- `user_settings_changed` socket relays rebroadcast a sender's whole
  blob, so a stale long-lived tab can keep re-poisoning peers.

## Design

Make propagation **per-field last-write-wins** — a client may only push
keys it actually changed since its own last persist:

1. **Backend merge.** `PUT /api/user-settings` merges the sanitized
   incoming keys into the stored file instead of replacing it. Clients
   now send partial payloads; merge is required so unsent keys survive.
2. **Baseline diff.** The store keeps `persistedBaseline` — the last
   agreed state — seeded from the localStorage blob at boot, merged with
   every server GET and remote apply, and advanced by each save's diff.
   `diffPayload()` emits only keys whose JSON differs from baseline.
3. **Sync gate.** `serverSyncEnabled` starts false; PUTs and broadcasts
   are suppressed until the first successful `loadSettingsFromServer()`.
   Pre-sync saves still write localStorage and queue their keys in
   `pendingSyncKeys`, which flush after the first sync — with
   *post-sync* values, so nothing stale travels. The pre-GET drain is
   skipped on the first sync only (the drain still protects in-session
   edits afterwards).
4. **Changed-only broadcast.** `BroadcastChannel` + the socket relay send
   `changed` subsets. The localStorage blob becomes
   `{ at, changed, settings }`: `settings` is the full cache for next
   boot; `changed` is what the storage-event listener applies in other
   tabs. Legacy flat blobs still parse (`.settings ?? blob` /
   `.changed ?? blob`).
5. **Reconnect resync.** `socketClient.on('connect')` runs
   `ensureSettingsLoaded()` — a stale long-lived client (the panel)
   self-heals on reconnect without a page reload.

`detectSmallScreenDefaults()` keeps its behaviour (tablet mode on compact
devices) but its save now lands pre-sync: localStorage only, queued keys
flush post-GET — by which time server truth has already resolved them.

## Test plan

- Backend: partial PUT merges with existing keys; unsent keys survive;
  sanitized keys still stored.
- Frontend: store-level — seed baseline, change one ref, assert the PUT
  body contains only that key; remote apply produces no broadcast echo;
  pre-sync saves queue without PUT until first load.

## Implementation Results

**Backend** (`routes/user_settings.py`): PUT merges the sanitized
incoming keys into the stored file (`existing.update(sanitized)`) and
returns the merged file. Partial writes can't drop unsent keys.

**Frontend** (`stores/settings.ts`):

- `persistedBaseline` — the last agreed state: seeded from the
  localStorage blob in `loadSettings()`, adopted wholesale after the
  first `loadSettingsFromServer()` (post-apply payload), merged with
  every remote apply, advanced by each save's diff.
- `factoryDefaults` — a full-payload snapshot taken before
  `loadSettings()` runs; `diffPersistedPayload()` counts a
  baseline-absent key as changed only when it differs from factory, so
  hydrating an old blob doesn't queue ~60 phantom edits.
- `saveSettings()` → `saveSettingsLocalOnly()` diffs vs baseline, writes
  the flat blob (`vdock_settings`, byte-compatible) plus a delta signal
  (`vdock_settings_delta` = `{at, changed}`), queues keys in
  `pendingSyncKeys`, and — only when `serverSyncEnabled` — schedules the
  PUT and broadcasts the changed subset (BroadcastChannel + socket).
- `persistSettingsToServer()` no-ops before the first sync, PUTs
  `pick(payload, pendingSyncKeys)`, keeps unsent keys on failure for
  retry, and drains trailing saves in-flight.
- `loadSettingsFromServer()` drains pending PUTs only *after* sync is
  established (the pre-GET drain was the stomp's ignition), merges server
  keys into baseline, applies via the guarded remote path, then flushes
  queued keys with post-sync values. Empty-server case seeds the file
  with a one-off full PUT.
- `initLiveSync()` — the storage-event listener moved to the delta key
  (sibling tabs apply `changed`, never our untouched keys), and a socket
  `connect` re-pulls settings once sync is established — stale
  long-lived clients self-heal on reconnect.

**Verified live:** wiped the client (localStorage + SW + IDB), mobile
393×852 → store boots to `spectrum`/`rgb`, server file still
`spectrum`/`rgb` (previously the compact-device defaults PUT would have
overwritten it to `widgets`), and `show_screensaver` renders the RGB
Bars spectrum — `refs/mobile-fresh-spectrum-not-stomped-2026-10-01T23-40-27-311Z.png`.

**Suites:** 5 new `settings-sync.test.ts` cases (pre-sync suppression,
changed-only PUT, stale-key non-propagation, no remote echo, subset
broadcast); backend `test_partial_put_merges_into_existing_settings`.
560/560 vitest, 1119/1119 pytest, `vue-tsc` + `npm run build` clean.

**Semantics change worth noting:** cross-device settings are now
per-field last-write-wins. A device whose local blob disagrees with the
server on a key it never touched stops resurrecting the stale value —
the server value wins on next sync/reconnect.
