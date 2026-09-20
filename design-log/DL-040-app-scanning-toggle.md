# DL-040: Enable/disable app scanning

## Problem

The Running Applications integration had no master switch — the 10s
`detected-profiles` poll (a full `psutil` process scan each tick) ran
unconditionally to feed the scene live dots, and the settings table
always fetched on tab entry. Users asked for an enable/disable for the
scanning itself.

## Design

A persisted `appScanningEnabled` setting (default on) gates both
consumers:

- **Live dots** — `GlassPillSceneSelector` watches the setting and calls
  `startAppDetection`/`stopAppDetection` instead of unconditionally
  starting on mount. `stopAppDetection` now clears the detected sets so
  the dots vanish immediately rather than lingering stale.
- **Running Applications card** — a new "Enable App Scanning" toggle row
  in the section header area. When off: the refresh button hides, the
  table/search collapse to an "App scanning is disabled" empty state,
  and `refreshRunningApps` short-circuits so the tab-entry fetch is
  skipped too.

Backend endpoints stay functional — disabling is a client decision
about whether to pay the scan cost, not a server lockout.

## Implementation Results

- `stores/settings.ts`: `appScanningEnabled` plumbed through defaults,
  `PersistedUserSettings`, ref, save payload, `applySettingsObject`,
  remote merge, and the store return.
- `services/appDetection.ts`: `stopAppDetection` clears
  `detectedProfiles`/`runningExes`.
- `components/GlassPillSceneSelector.vue`: `immediate` watch on the
  setting replaces `onMounted(startAppDetection)`.
- `views/SettingsView.vue`: toggle row + `toggleAppScanning` (enabling
  refreshes the list, disabling clears it), `v-else` wrapper over the
  toolbar/table, guard in `refreshRunningApps`.
- Verified live at 1024×600: toggle off → "App scanning is disabled"
  empty state, zero `/detected-profiles` requests, dots gone; toggle on
  → list populates, dots return on detected scenes.
