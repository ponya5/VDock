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

## Follow-up: first-connect no longer needs the profiles picker (2026-09-27)

### Problem

This entry's own "out of scope" note assumed a phone's first connection
genuinely needed the `/profiles` picker — there was no other way for it to
know which profile to load. In practice that assumption produced exactly
the two things DL-061 exists to prevent: a phone landing on the dashboard
for the first time fell through `DashboardView`'s "no last-used profile in
*this browser's* localStorage" branch, which (a) picked whichever profile
happened to be first in the backend's list — not necessarily the one the
desktop was actually showing — and (b) let the first-run tutorial
auto-start, whose very first step force-navigates to `/profiles` to walk
through profile selection. Both are configuration surfaces mobile should
never reach.

### Root cause

"Which profile is active" was tracked purely in `localStorage` (`
vdock_last_profile`, dashboard store) — per-browser, per-device state with
no server component. A phone's browser has always been a blank slate here,
so it could never actually know what the desktop had already set up; it
was only ever coincidence when a single-profile setup made `profiles[0]`
happen to match.

### Fix

- Added `activeProfileId` to the server-persisted settings (`
  frontend/src/stores/settings.ts`, `backend/routes/user_settings.py`
  allow-list) — same mechanism as `tutorialCompleted`: a real value shared
  by every window/device on this backend, not a per-browser cache.
- `dashboardStore.setProfile()` now writes it alongside the existing
  `localStorage` mirror, so the very next profile load on ANY device
  (including the desktop's own next launch) publishes which profile is
  active.
- `DashboardView`'s mounted hook now checks `settingsStore.activeProfileId`
  first, before its own `localStorage` cache — so a phone's first-ever
  visit loads the same profile the desktop already has open, with no
  `/profiles` visit required. (`localStorage` stays as a fallback for the
  rare case settings failed to load.)
- The first-run tutorial no longer auto-starts on mobile viewports at all
  (`tour.consumePendingOrFirstRun()` gated on `!isMobileViewport`) — its
  first step's forced `/profiles` navigation was the other path into a
  configuration screen mobile shouldn't reach, and a phone connecting to an
  already-set-up desktop has no reason to be walked through profile
  selection regardless.
- The dashboard's "no profile loaded" fallback (only reachable now if the
  desktop itself has never set one up) drops its "Select Profile" button on
  mobile, replacing it with a hint to configure a profile on the desktop
  app first — the button doesn't get replaced with anything that opens
  `/profiles` from a phone, since that's exactly the surface this entry
  blocks.

### Verification

- Backend: 867/867 tests green (added `activeProfileId` to the
  `ALLOWED_USER_SETTING_KEYS` allow-list in `user_settings.py` — without it
  the new field would have been silently dropped on every save).
- Frontend: 59 files / 254 tests green; `vue-tsc --noEmit` clean.
- Not yet verified live with two real devices (desktop + phone) from this
  session — flagged for the user to confirm a phone's first connection now
  lands directly on the desktop's active profile with no tutorial.
