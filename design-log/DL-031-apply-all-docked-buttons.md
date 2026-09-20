# DL-031 — "Save & Apply to All" misses docked sidebar buttons

## Background
User report: Settings → Appearance → Button design → Save & Apply to All
produces no visible change on the dashboard.

## Problem
`dashboardStore.applyGlobalButtonStyle` iterates
`currentProfile.scenes[].pages[].buttons` only. Buttons docked in the
always-visible sidebar live on `profile.dockedButtons` — a separate array
the loop never touches. Grid buttons DO update (verified live: store
`layers.effect` flips to 'deckkey', DOM classes flip to
`deck-button-deckkey`), but the docked sidebar — which is on screen at all
times — keeps its old design, so the apply looks broken.

## Design
Extend `applyGlobalButtonStyle` to run the same mutation over
`currentProfile.dockedButtons` (same `Button` type, same `layers.effect`
precedence). Extract the per-button mutation into a local helper so the
two collections can't drift.

## Verification
- Live: apply 'deckkey' → docked button class flips gem→deckkey, grid
  unchanged-count matches, saveProfile persists.
- vitest suite + typecheck.

## Implementation Results

### Fixed
- `dashboard.ts applyGlobalButtonStyle` — per-button mutation extracted to
  `applyToButton()` helper; now runs over `currentProfile.dockedButtons`
  as well as every scene/page button. Verified live: docked Weather
  flipped gem→statuskey in store AND DOM (`deck-button-statuskey` on the
  sidebar card), all 54 grid buttons flipped, screenshot shows the LED
  design everywhere.

### Adjacent fixes found during verification
- **Rate limiter vs static assets**: `.env` runs `RATELIMIT_ENABLED=True`
  at 50/hour — the static catch-all wasn't exempt, so one page load
  (63 precache files) exhausted the quota and assets 429'd as text/html,
  leaving the app unmounted. `@limiter.exempt` added to `root` +
  `serve_frontend` — file reads aren't API abuse surface.
- **Build failure on vite-plugin-pwa 0.21**: the 2.8MB bundle exceeds
  workbox's 2MiB `maximumFileSizeToCacheInBytes` → build errored.
  Raised to 4MiB in `vite.config.ts` (Electron-local bundle, safe to
  precache).

### Verified
- 201/201 frontend tests (2 new: docked coverage + shared helper).
- `vue-tsc` clean, `vite build` clean with SW precache (63 entries).
- Live: index/css/sw all 200, apply-all hits docked + grid.
