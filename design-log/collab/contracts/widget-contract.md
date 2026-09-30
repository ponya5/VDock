# Contract — Screensaver widget components

Applies to W1 (NowPlayingWidget), W2 (SpectrumWidget), W3 (SystemStatsWidget).

Each widget is a self-contained Vue SFC at
`frontend/src/components/screensaver/<Name>Widget.vue`. The orchestrator
mounts it inside `ScreenSaver.vue` wrapped in the standard `.ss-pos`
positioning div (drag/resize/measure are the parent's job). Do NOT edit
`ScreenSaver.vue`, `utils/screensaverLayout.ts`, `SettingsView.vue`, or
`stores/settings.ts`.

## Component requirements

- `<script setup lang="ts">`, scoped styles. Props: none required (accept an
  optional `layoutEdit?: boolean` — the parent may pass it; you may ignore
  it). No emits required.
- Own its own data: instantiate your service/composable inside the component,
  clean up in `onUnmounted` (stop polling, unsubscribe socket, cancel rAF).
- Natural size: render at a sensible default (~180–260 px wide, content
  height) — the parent's transform scale handles resizing. Don't pin yourself
  to viewport units; use px/rem and let the scale wrapper do its job.
- Visual language: match the existing widgets (read `ScreenSaver.vue` styles:
  `.ss-section`, `.ss-section-head` (small-caps h2 + hairline), `.ss-empty`).
  Reproduce that pattern in your scoped styles — small caps section title,
  hairline, dim secondary text, generous tap-friendly spacing. Dark-glass
  friendly: content sits over `rgba` surfaces on a dark background.
- **Honest states** (hard rule from the codebase): three states — live data,
  first-load ("Loading…"/skeleton), never-arrived ("unavailable" + reason,
  muted styling, e.g. `.ss-empty`-like with a dim icon). A widget that got
  data once keeps showing the last reading on transient failures.
- Touch: no hover-only affordances; anything interactive needs ≥44 px
  targets.
- Fonts/icons: FontAwesomeIcon (`@fortawesome/vue-fontawesome`) is available;
  use the `['fas','…']` tuple form as elsewhere.

## Widget ids (orchestrator registers)

- W1 → `nowplaying` — "Now Playing"
- W2 → `spectrum` — "Spectrum"
- W3 → `systemstats` — "System"
