# DL-074: Guided tour realignment + Help guide coverage

## Background

The first-run tour showed dashboard steps as dead floating cards while
the user was still on `/profiles` (screenshot: step "Your Deck" centered
over the Profiles page). Root causes:

- Steps 3–6 (dashboard steps) declared no `route`, so clicking Next past
  the profile step — or wandering off mid-tour — left the tour anchored
  to nothing (targets missing → centered card).
- Two settings steps targeted `.settings-nav-rail` / `.settings-search`,
  classes that don't exist (real: `.nav`, `.nav-search`) — guaranteed
  dead targets.
- Conditional UI (`.agent-action-bar` only renders with agent sessions,
  `.docked-sidebar` only when enabled) produced dead targets when the
  feature was off.

Requested flow: profiles (create or load default) → auto-navigate to
dashboard → dashboard steps → settings overview → finish on dashboard.
Keep it short. Expand the Help guide to cover all features +
troubleshooting.

## Design

### Tour (9 steps, down from 13)

1. `/profiles` centered — Welcome: what a profile is.
2. `/profiles` `.profiles-grid` — load "My VDock" (▶) or New Profile;
   `advanceOnPath: '/'` auto-continues when a profile loads; if the user
   clicks Next instead, step 3's `route: '/'` still pulls them to the
   dashboard.
3. `/` `.enhanced-scene-nav` — scenes & page switching.
4. `/` `.deck-grid` — the deck; `optional` (no profile → skip).
5. `/` `[aria-label="Toggle Edit Mode"]` — edit mode.
6. `/` `.agent-action-bar` — agent session targeting; `optional`.
7. `/settings` `.nav` — settings rail (selector fixed).
8. `/settings` `.nav-search` — search box (selector fixed).
9. `/` centered — Done: screensaver hint + where Help lives.

### Mechanism changes (`tutorial.ts` / `TutorialTour.vue`)

- Every step that needs a specific view declares `route` — `prepareStep`
  navigates there before measuring, so Back/Next and mid-tour wandering
  self-correct.
- New `optional?: boolean` — when `waitForEl` times out the step
  auto-advances instead of showing a dead card. Last step never skips
  (it's centered anyway).
- Fix stale selectors to `.nav` / `.nav-search`.

### Help guide (`UserGuideModal.vue`)

- New **Troubleshooting** tab: backend/port conflicts, buttons not
  firing, empty session picker, mobile can't connect (ALLOW_LAN),
  unsigned-installer SmartScreen note, where logs live.
- New coverage: agent session targeting (picker, Auto vs pinned, flash
  to identify), Quick Deck (Ctrl+Shift+D), screensaver widgets, mobile
  console, key-design "Save & Apply to all keys".
- Corrections: Security toggles live under Settings → Server (the guide
  said Settings → Security); remote URL uses the backend port.

## Implementation Results

Implemented + verified live in Playwright (dev server, 1024×600 viewport
with mobile chrome — the exact conditions from the bug screenshot).

### Changes

- `frontend/src/services/tutorial.ts` — rewritten to the 9-step flow;
  every step declares `route`; `optional?: boolean` added; stale
  `.settings-nav-rail` / `.settings-search` selectors fixed to `.nav` /
  `.nav-search`; scene step targets `.enhanced-scene-nav, .mc-scene-rail`
  (desktop pills OR the mobile rail — on touch/small viewports the app
  renders mobile chrome and the desktop selector doesn't exist).
- `frontend/src/components/TutorialTour.vue` — `prepareStep` navigates to
  `route` before measuring; optional steps with missing **or zero-size**
  targets (a `display:none` element still resolves `querySelector`)
  auto-advance; `firstVisible()` picks the visible match for comma
  selectors; `measure()` treats zero-area rects as no spotlight.
- `frontend/src/components/UserGuideModal.vue` — Troubleshooting tab
  added; agent-session targeting, Quick Deck, screensaver, mobile
  console, and apply-all-keys coverage added; stale "Settings →
  Security" wording corrected to Settings → Server.

### Live verification (both tour paths)

- Path A (Next without loading a profile): 1/9 Welcome → 2/9 Pick a
  Profile (`.profiles-grid` spotlit) → 3/9 auto-routes `/` + spotlit →
  4/9 deck grid spotlit → 5 & 6 auto-skipped (no edit pencil/agent bar
  in mobile chrome — no dead cards) → 7/9 `/settings` `.nav` spotlit →
  8/9 `.nav-search` spotlit → 9/9 "You're all set" back on `/` → Done
  closes, `vdock_tutorial_done=1`, pending flag cleared.
- Path B (real profile click): at step 2 the profile's load button
  fires `advanceOnPath: '/'` → auto-advances to step 3 spotlit on the
  924px scene nav.

### Test results

- `vitest run`: 59 files / 254 tests green (1 pre-existing
  EnvironmentTeardownError from cross-file timer pollution — unrelated).
- `vue-tsc --noEmit` (CI invocation): clean. Note: the root tsconfig is
  a solution file (`files: []` + references), so that check is vacuous;
  `vue-tsc -p tsconfig.app.json` reports ~236 pre-existing errors across
  unrelated files — none in the tour/guide files — flagged as a separate
  CI-coverage gap.
