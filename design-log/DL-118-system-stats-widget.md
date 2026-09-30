# DL-118 — System stats screensaver widget

## Intent

The deck already collects live machine metrics (`/api/metrics/all`, psutil) for
per-button performance monitors, but the screensaver — the surface a 7" panel
shows most of the day — has no glanceable "is the machine healthy" strip. Add a
compact System section that sits beside Markets/Headlines: CPU, MEM, DISK, NET
throughput, and GPU when the payload carries it.

Quick win by design: no backend changes, no new dependencies — just a polling
composable plus a widget that follows `contracts/widget-contract.md`.

## Frictions / constraints

- **Payload is cumulative, not rates.** `network` reports
  `bytes_sent_mb`/`bytes_recv_mb` totals since boot — throughput must be
  derived from deltas between polls, so the composable (not the component)
  owns the previous-sample bookkeeping.
- **`disk` is a partition list, not a number.** `partitions[]` carries one
  `usage_percent` per mountpoint; the row needs a single honest value.
  Rule: prefer the system mount (`C:\` on Windows, `/` elsewhere), else the
  fullest partition — the drive the machine boots from is the one a glance
  cares about.
- **GPU is optional.** `get_all_metrics()` today emits no `gpu` key (GPU
  metric buttons already degrade to `--` for the same reason). The widget
  must accept several plausible shapes — `{usage_percent|load_percent|
  utilization}` or a `[{load_percent}]` array — and simply omit the row when
  nothing numeric arrives, rather than render a dead `0%`.
- **Per-section failures are soft.** A section can come back as `{error}` or
  be missing a key; each row degrades to `—` independently instead of
  failing the whole widget.
- **Server-side cost.** `cpu_percent(interval=1)` blocks ~1 s per request
  (twice, counting the percpu read), so polls must never overlap — an
  in-flight guard keeps a slow backend from stacking requests.
- **Honest states** (hard rule): first-load "Loading…", never-arrived
  "unavailable" (muted icon + reason), and stale-keep-last — a transient
  failure keeps the last reading visible and flags it, exactly like the
  weather chip's `.is-unavailable` precedent.

## Mechanical Translation

- `frontend/src/composables/useSystemStats.ts` — `useSystemStats()` factory
  mirroring `useWeather`/`useMarket`: `refresh()` + `start()`/`stop()` around
  a ~2.5 s `setInterval`, in-flight reentry guard, `apiClient.get('/metrics/all')`.
  Exposes `{ stats, loading, error, stale, lastOkAt, refresh, start, stop }`
  where `stats` is a normalized view-model:
  `{ cpuPercent, memPercent, diskPercent, gpuPercent|null,
     netDownBps|null, netUpBps|null, netPeakBps }`.
  Net rates come from the delta of cumulative MB counters over elapsed
  seconds; `netPeakBps` is a rolling max so the NET meter is self-scaling.
  On failure: `error` set, `stale = stats != null` (kept last reading);
  `lastOkAt` stamps each success.
- `frontend/src/components/screensaver/SystemStatsWidget.vue` — section head
  "System" + rows of `label · thin meter bar · value` for CPU/MEM/DISK/NET
  (GPU only when a number arrives). NET shows `↓ n ↓`-style formatted rates
  (B/s → KB/s → MB/s). Bars are hairline-thin translucent tracks with a fill
  that tints white → warning orange ≥85% → critical red ≥95%. Unavailable
  state: dim server icon + the error reason. Optional `layoutEdit` prop
  accepted and ignored, per the widget contract.
- `frontend/src/tests/system-stats-widget.test.ts` — mocked `@/api/client`
  (the `get` seam other tests use): poll cadence via fake timers, payload →
  view-model mapping (real backend key names), net-rate deltas, GPU
  presence/absence, stale-keep-last on rejection.

## Core Loop

Screensaver mounts the widget → `start()` fetches immediately, then every
2.5 s → each success normalizes into the view-model → bars/values update;
each failure only updates `error`/`stale`. Unmount → `stop()` clears the
interval; nothing polls while the dashboard is up.

## Design Proof

- Backend down at mount → icon + "unavailable" reason, no `--%` lying.
- One poll OK then failures → last numbers stay, dimmed with a stale flag.
- Payload without `gpu` → four rows; payload with `gpu` → five.
- NET first sample has no baseline → rate renders as measuring/`—` until the
  second poll, never a fake 0-throughput claim or a garbage spike.
- 2.5 s cadence verified via fake timers; no overlapping requests while a
  slow `/metrics/all` (~2 s of blocking psutil reads) is in flight.

## Implementation Results

Implemented and verified. No deviations from the design above.

**Built**

- `frontend/src/composables/useSystemStats.ts` — `useSystemStats()` factory
  (`stats`/`loading`/`error`/`stale`/`lastOkAt`/`refresh`/`start`/`stop`),
  polling `/metrics/all` every 2.5 s via `apiClient.get`, in-flight reentry
  guard, start idempotent (a second `start()` while running is a no-op).
  Normalizes the real payload keys (`cpu.usage_percent`,
  `memory.usage_percent`, `disk.partitions[]`, `network.bytes_*_mb`); NET
  rates derived from cumulative-counter deltas (clamped ≥0 so counter resets
  can't render negative rates); `SYSTEM_STATS_POLL_MS` exported for tests.
- `frontend/src/components/screensaver/SystemStatsWidget.vue` — "System"
  section head + hairline mirroring `.ss-section-head`/`.ss-empty`; rows of
  label + hairline meter + value for CPU/MEM/DISK/NET (`↓ x MB/s ↑ y KB/s`),
  GPU row rendered only when the payload carries a number. Fill tints
  orange ≥85% / red ≥95%; `role="meter"` + aria bounds on the tracks.
  Unavailable state = dim `server` icon + reason; transient failure keeps
  the last reading dimmed with a "retrying" flag.
- `frontend/src/tests/system-stats-widget.test.ts` — 15 tests, all green:
  cadence via fake timers, stop(), no-overlap, full payload mapping, NET
  rate math, disk system-mount + fullest-fallback picking, GPU object/array
  forms, per-section nulls, first-load failure, stale-keep-last + recovery,
  `success:false` envelope, and contract assertions on the widget source.

**Verified**

- `npx vitest run src/tests/system-stats-widget.test.ts` — 15/15 pass.
- `npx vue-tsc --noEmit` — clean across the whole frontend.

**Notes for integration:** the widget is self-contained (instantiates and
starts/stops the composable itself); mounting it in a `.ss-pos` wrapper is
all ScreenSaver.vue needs. Today `/metrics/all` emits no `gpu` key, so the
GPU row stays hidden until the backend grows one — no frontend change
required when it does.
