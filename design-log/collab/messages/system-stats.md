# W3 — system-stats — notes for the orchestrator

## Delivered

- `frontend/src/composables/useSystemStats.ts` — polls `GET /api/metrics/all`
  every 2.5 s (exported `SYSTEM_STATS_POLL_MS`), normalizes into
  `{ cpuPercent, memPercent, diskPercent, gpuPercent|null, netDownBps|null,
  netUpBps|null, netPeakBps, timestamp }`. Exposes
  `{ stats, loading, error, stale, lastOkAt, refresh, start, stop }`.
- `frontend/src/components/screensaver/SystemStatsWidget.vue` — "System"
  section; label + meter + value rows for CPU/MEM/DISK/NET, GPU row only
  when payload carries a number. Accepts optional `layoutEdit` prop.
- `frontend/src/tests/system-stats-widget.test.ts` — 15 tests, all passing.
- `design-log/DL-118-system-stats-widget.md` — with Implementation Results.

## What the orchestrator must wire

- Mount in `ScreenSaver.vue` inside a `.ss-pos` wrapper like the market
  widget: `:style="posStyle('systemstats', widgetScaleNum)"`, drag/resize
  handlers per the existing pattern.
- Register widget id `systemstats` (label "System") in
  `utils/screensaverLayout.ts` (widget id union + default layout position +
  the settings toggle list in `SettingsView.vue`/`stores/settings.ts`).
  Per `widget-contract.md` the suggested ids for the info widgets are in
  view-percent coordinates — a spot beside/under Markets works visually.

## Contract facts the integration should know

- `/api/metrics/all` returns `{success, data}`; `data` keys: `timestamp,
  cpu, memory, disk, network, temperature, battery, processes, system_info`.
  **No `gpu` key today** — the GPU row is simply hidden until the payload
  grows one (object `{usage_percent|load_percent|utilization}` or
  `[{load_percent}]` forms are both handled).
- `network.bytes_*_mb` are cumulative since boot — the composable derives
  B/s rates from deltas; first sample shows `—` for ~2.5 s.
- `disk` is a partition list — the DISK row prefers the system mount
  (`C:\`/`/`), else the fullest partition.
- The widget never stacks polls (in-flight guard); `/all` costs the backend
  ~2 s of blocking psutil reads per call, so the 2.5 s cadence is about as
  fast as it can safely go — don't tighten it.

## No blockers.
