# DL-061: Mobile = control surface only

User directive: "in mobile view only allow to see the dashboard and switch
between scenes — anything but configurations."

A phone deck is for *pressing buttons*, not configuring them. Every
configuration path is stripped on phone viewports so a small screen can
never strand the user inside an editor.

## Design

Shared detection — `src/utils/mobileViewport.ts` exports a reactive
`isMobileViewport` + `isPortrait` pair: touch-capable (`pointer: coarse`
or `maxTouchPoints > 0`) AND smaller viewport dimension ≤700px. Same
predicate family as DL-060's rotate gate, now the single source of truth
(RotateToLandscape refactored onto it).

Blocked on mobile:

- **Edit mode entirely** — `dashboardStore.toggleEditMode()` refuses to
  turn ON when `isMobileViewport` (toggling OFF still allowed). One choke
  point covers the header pencil, long-press gestures, and every
  edit-mode-gated surface downstream: scene add/edit badge, slider resize
  chips, drag reorder, footer edit controls.
- **Header config buttons** — Profiles, Edit toggle, and Settings are
  `v-if="!isMobileViewport"`; scene selector, page nav, fullscreen,
  refresh, and exit stay (control/app actions, not configuration).
- **Long-press gestures** — `handleDeckButtonLongPress` and
  `handlePlaceholderLongPress` early-return on mobile; they would
  otherwise open the button editor even with edit-mode blocked.

Kept on mobile: button presses, sliders, scene pill, page nav/dots,
swipe navigation, fullscreen, refresh, exit.

Out of scope: the `/profiles` picker (first-connect needs it) and direct
`/settings` deep links — no entry points remain on the dashboard itself.

## Implementation Results

Verified live (touch capability stubbed, 863×360 landscape + 412×839
portrait viewports):

- Header action group on mobile renders exactly three buttons —
  Fullscreen, Refresh, Exit; Profiles / Edit / Settings are absent.
- Scene selector pill intact; scene add/edit badges, footer edit section,
  edit sidebar, and slider resize chips all absent (edit mode can never
  activate — `toggleEditMode` guard).
- `useButtonActions` long-press handlers early-return on mobile, so no
  button editor or new-button modal can appear.
- `RotateToLandscape` refactored onto the shared flag — portrait gate
  still fires correctly.
- `vue-tsc` clean, production build clean, 239/239 frontend tests.
