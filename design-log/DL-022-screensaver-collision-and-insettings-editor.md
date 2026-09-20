# DL-022 — Screensaver widget collisions + in-settings layout editor

## Problem

Two reported issues on the 7" (1024×600) panel:

1. **Customize Layout "doesn't work at all"** — the button sent a
   `screensaver_layout_edit` ui_command to the *deck* window. When no deck
   window is mounted/reachable (settings opened standalone on the panel, deck
   window closed, socket/broadcast not connected), the command went nowhere
   and nothing visibly happened.
2. **Widgets overlap** — the saved layout had the Markets widget sitting on
   top of Headlines. DL-020's measured viewport clamp keeps widgets on-screen
   but says nothing about widget-vs-widget collisions, and the widget-size
   slider could scale a widget past half the screen, making any non-overlap
   impossible.

## Changes

### In-settings editor (`SettingsView.vue`)

- `ScreenSaver` is self-contained (settings store + data composables only), so
  the layout editor now mounts directly inside the settings window:
  `screensaverLayoutEditOpen` → `<ScreenSaver :visible :layout-edit>`.
- `handleCustomizeScreensaverLayout` just opens it — no routing, no command
  relay, works in every window configuration.
- `onSaveScreensaverLayout` assigns `settingsStore.screensaverLayout`, which
  persists through the existing settings watch → local + server + broadcast
  sync, so a connected deck window picks the new arrangement up live.
- The deck-window `screensaver_layout_edit` ui_command path is kept (backend
  allowlist, DashboardView wiring) for externally-triggered editing.

### Collision-aware layout (`ScreenSaver.vue`)

- `displayCenters` computed: after the DL-020 edge clamp, a pairwise
  separation pass pushes overlapping widget boxes apart along the axis of
  least correction. Correction is distributed by how much room each widget
  can yield before its own clamp bound (a widget pinned at the edge yields
  nothing; the free one takes the whole push). Up to 8 relaxation passes.
- Recomputed fresh from the *saved* centers every render — deterministic,
  self-healing, never mutates the stored layout. Skipped in edit mode so the
  editor always shows true saved positions.
- `transformScale` now caps each widget's effective scale by measured
  viewport: rendered box ≤ 62% wide / 46% tall — a widget bigger than that can
  never be laid out next to others on a 7" display.
- The clock's box reserves its ±20px drift excursion so neighbors never clip
  it mid-drift.

## Verification

- Live @1024×600, user's colliding saved layout (market 52,76 over news
  26,78), 5-widget set: **zero overlaps**, all boxes inside the 24px margins.
- 6-widget set (sports enabled): converges to at most a transient ~9px sliver
  against the clock's drift reserve — the center column is exactly full.
- Edit mode shows true saved positions (collision visible as overlapping
  outlines); Done dismisses back to settings without navigation.
- `vue-tsc` clean, 176/176 tests (updated `screensaver-layout.test.ts` wiring
  assertions for the in-window editor).
