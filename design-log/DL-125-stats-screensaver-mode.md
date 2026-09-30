# DL-125 — System stats as a third fullscreen screensaver mode

## Context

`screensaverStyle` currently offers `widgets` (the editorial dashboard) and
`spectrum` (DL-123's fullscreen visualizer). The user wants a third style:
a fullscreen **system monitor** — CPU, memory, disk and network meters plus
supporting state — so the idle panel doubles as an at-a-glance machine
dashboard.

The data already exists: `GET /api/metrics/all` returns per-core CPU %,
frequency, memory GB detail, all disk partitions + IO counters, network
counters, temperatures, battery, top processes and system uptime
(`utils/system_metrics.py`). The `useSystemStats` composable flattens only
the five numbers the DL-118 widget strip needs — the stage needs the richer
fields, so the mapping gets extended rather than a second poller.

## Design

- `SystemStats` gains optional fields mapped from the existing payload:
  `cpuPerCore[]`, `cpuFreqMhz`, `memUsedGb/TotalGb`, `diskPartitions[]`
  (system mount first, then fullest), `diskReadBps/diskWriteBps` (counter
  deltas like the net rates), `uptimeHours`, `hostname`, `batteryPercent`,
  `batteryCharging`, `tempC` (hottest sensor), `topProcesses[]` (top 5 by
  CPU) and `processCount`. All nullable/absent-tolerant — same degrade-per-
  row contract as the widget.
- New `StatsStage.vue` — fullscreen editorial board matching the saver's
  JetBrains-Mono/hairline language:
  - header: hostname · uptime · live clock;
  - meter cards: CPU (giant % + per-core bar strip — always moving, good
    for a saver), Memory (% + used/total GB), Disk (system partition bar +
    compact list of the rest), Network (↓/↑ rates + rolling sparkline);
  - footer strip: top processes by CPU + battery/temperature chips when
    those readings exist;
  - honest states: `stale` dims, `error` shows the unavailable message;
  - nothing interactive — every tap bubbles to the root dismiss handler.
- `screensaverStyle` union gains `'stats'`; `ScreenSaver.vue` mounts
  `StatsStage` via the same `spectrumMode`-style computed
  (`statsMode = style === 'stats' && !layoutEdit`).
- SettingsView: third option "System stats" in the When-idle select; the
  existing "not in use while X is picked" notes on the Widgets/Background
  panels fire for *any* non-widget style, and the spectrum panel gets the
  same note when stats is picked — same established pattern, no new
  concepts.
- No new persisted keys; `screensaverStyle` already round-trips (DL-124).

## Implementation Results

- `useSystemStats.ts`: `SystemStats` extended with `cpuPerCore[]`,
  `cpuFreqMhz`, `memUsedGb/memTotalGb`, `diskPartitions[]` (system mount
  first, then fullest, capped at 4), `diskReadBps/diskWriteBps` (counter
  deltas, same pattern as the net rates), `uptimeHours`, `hostname`,
  `batteryPercent/batteryCharging`, `tempC` (hottest sensor),
  `topProcesses[]` (top 5 by CPU) and `processCount`. The single 2.5 s
  poller serves both the widget strip and the stage.
- `StatsStage.vue` (new): fullscreen board — header with hostname, uptime,
  live 1 s clock; 2×2 card grid (CPU hero % + per-core bar strip +
  history sparkline, Memory % + used/total bar, Disk partition bars +
  R/W rates, Network ↓/↑ rates + sparkline); footer with top-5 CPU
  processes and temperature/battery/process-count chips that only render
  when those readings exist. Same warn ≥85 / crit ≥95 thresholds and
  stale-dims-on-flap contract as the widget. No interactive controls —
  taps bubble to the root dismiss handler.
- `ScreenSaver.vue`: `statsMode` computed mounts `StatsStage` via
  `v-else-if` — mutually exclusive with spectrum/widgets, and
  `layoutEdit` still forces the dashboard it edits.
- `stores/settings.ts`: `screensaverStyle` union widened to
  `'widgets' | 'spectrum' | 'stats'`; hydration validator accepts 'stats';
  default stays `'widgets'`. No new keys — the style already round-trips
  through localStorage + `/api/user-settings` (DL-124 allowlist).
- `SettingsView.vue`: "System stats" option in the When-idle select; the
  spectrum panel renamed "Screensaver style" (it hosts the shared picker)
  and its hint now mentions both fullscreen styles; the "not in use" notes
  on Widgets/Background fire for any non-widget style via a
  `screensaverStyleLabel` computed, and the spectrum options get the
  mirror note while stats is picked.
- Tests: `stats-stage.test.ts` — 9 cases covering the extended mapping
  (system-mount ordering, IO-rate deltas, absent-section degradation),
  stage mount/render, honest empty state, stale-keep-last, and the
  ScreenSaver wiring. Full suite: 455 passed; `vue-tsc` +
  `npm run build` clean; `dist` rebuilt.
- Live-verified at 1024×600: saver fires via the existing Test button,
  board renders live metrics (per-core strip, disk IO rates, top
  processes); battery/temp chips correctly absent on the desktop.
