# DL-044: Onboarding & release prep — default profile, tour, help screens

## Problem

Preparing VDock for public release needs: (1) test profiles cleared,
(2) repo publish-ready, (3) a richer out-of-box default profile,
(4) a first-run bubble tutorial re-launchable from Settings,
(5) a help screen with sub-screens showing annotated UI screenshots.

## Design

### Default profile
`createDefaultProfile()` gains two scenes beyond the existing `Home`
media scene (single source of truth stays `createDefaultScene()` for
reset parity): **AI Assistant** (Claude/ChatGPT/Gemini `url` buttons +
copy/paste/screenshot helpers) and **Tools** (lock, screenshot,
fullscreen, terminal, undo/redo) — all generic actions, no API keys.

### Tutorial
`services/tutorial.ts` holds reactive state + step list; `TutorialTour.vue`
renders a spotlight overlay (dimmed mask with transparent cutout via
CSS `box-shadow` spread trick) and a positioned bubble with an arrow.
Steps target stable selectors (`aria-label`s, `.enhanced-scene-nav`,
`.docked-sidebar`, `.deck-footer`). Missing targets skip gracefully.
`vdock_tutorial_done` gates auto-start; `vdock_tutorial_pending` lets
Settings → "Launch Tutorial" start the tour after navigating home.

### Help screens
Real captures at 1024×600 saved to `public/assets/help/`; a data file
records marker coordinates as % of image size so arrows stay accurate
at any render scale. `UserGuideModal` gains a "Screens" tab with
sub-screen pills; `AnnotatedFigure.vue` renders shot + numbered
arrow markers + caption list.

## Implementation Results

- **Test profiles cleared**: `QA Dev Deck` + a stale duplicate `My VDock`
  moved to `backend/data/backups/profiles-2026-09-20/` (untracked; the
  app's non-recursive profile glob never sees them).
- **Publish-ready**: no tracked secrets, `.env` never committed, MIT
  LICENSE + SECURITY.md present, issues enabled, repo already public.
  README-referenced images were untracked (would 404 on GitHub) —
  `docs/assets/screens/*`, `vdock2-tour.{gif,mp4}` now committed;
  `backend/data/backups/` added to `.gitignore`.
- **Default profile**: `createDefaultProfile()` now seeds Home +
  AI Assistant + Tools scenes (14 buttons, all `url`/`hotkey`/
  `cross_platform` — no API keys). `createDefaultScene()` untouched so
  "Reset to Default" parity holds.
- **Tutorial**: `services/tutorial.ts` + `components/TutorialTour.vue`;
  7 steps, spotlight cutout + arrow bubble, skips missing targets,
  auto-starts on first run, re-launches via Settings → About →
  "Launch Tutorial". Verified live: all spotlights resolve, Skip/Done
  work, launch-from-settings navigates home and starts the tour.
- **Help screens**: real 1024×600 captures (dashboard, edit mode,
  settings) in `public/assets/help/`; `helpScreens.ts` marker coords in
  % so arrows scale; `AnnotatedFigure.vue` + new "Screens" tab in
  `UserGuideModal` with sub-pills. Verified live: images load, markers
  sit on the right elements.
- 231/231 frontend tests (5 new in `default-profile.test.ts`),
  typecheck clean, production build green.

### Follow-up: tour ↔ screensaver mutex + 7" readability

Device testing showed the tour running *under* the screensaver and the
bubble too small on the 7" panel. Fixes:

- `resetIdleTimer` never raises the screensaver while the tour is
  active; starting the tour dismisses a visible screensaver; the
  screensaver appearing mid-tour ends it (two watchers in
  DashboardView).
- Bubble widened to `min(420px, 100vw-16px)`, near-opaque background
  (`rgba(16,22,36,.97)` + blur), 1rem body / 1.3rem title, 48px
  buttons — readable and tappable at 1024×600.
