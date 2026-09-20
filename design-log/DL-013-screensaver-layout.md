# DL-013 — Screensaver Layout, Background & Layout Editor

**Date:** 2026-09-20
**Status:** In progress

## Background

User request: the stacked single column is wasteful — "not one on top of
each other.. keep the main clock in the center (a bit up).. place the news
box, crypto, and world clock side by side." Plus two feature asks: a
screensaver background, and the ability to "modify the layout (drag and drop,
and resize) in screensaver settings."

## Problem

1. Widgets stack in one centered column; on a landscape panel the sides sit
   empty.
2. The screensaver paints a fixed `#050510` — no background choice.
3. Positions are hardcoded CSS; users cannot rearrange.

## Questions and Answers

**Q: Flex row or free positioning?**
A: **Free positioning, driven by a `screensaverLayout` setting.** A flex row
fixes this complaint but is another hardcoded layout; absolute positions from
a stored `{x, y, scale}` per widget give the side-by-side default AND power
the drag/resize editor through one code path.

**Q: Edit real widgets or mock boxes?**
A: **Real widgets** — a `layoutEdit` prop on `ScreenSaver` itself. A separate
mock-box editor duplicates the widget rendering and lies about sizes. In edit
mode the root dismiss handlers are disabled and widget children get
`pointer-events: none` so drags can't trigger row clicks.

**Q: Which backgrounds work?**
A: All catalog kinds — `resolveBackground(id).component` mounts inside the
screensaver for component-kind (WebGL/CSS) entries, CSS classes paint a
`.ss-bg` layer, images use the existing `backgroundStyleFor` cover style. A
dim scrim keeps text readable over any of them.

## Design

- `utils/screensaverLayout.ts` — `ScreensaverLayout = Record<id, {x,y,scale}>`
  (viewport %, center-anchored), `DEFAULT_SCREENSAVER_LAYOUT`, and
  `normalizeScreensaverLayout` (clamps, fills missing ids from defaults).
- `screensaverLayout` + `screensaverBackground` added to the settings store,
  `PersistedUserSettings`, and `ALLOWED_USER_SETTING_KEYS`.
- `ScreenSaver.vue` — every widget in an absolutely-positioned wrapper at
  `left/top%` + `translate(-50%,-50%) scale(...)`. The global widget/weather
  size sliders still multiply in. Clock drift folds into the same transform.
- Edit mode: `layoutEdit` prop → dashed outlines, pointer-drag moves
  (clamped 6–94%), corner handle resizes scale (0.5–2.5), toolbar with
  Save / Reset / Done. Triggered by new ui_command `screensaver_layout_edit`
  (added to `ALLOWED_UI_COMMANDS` + `UiCommand` type) from a "Customize
  Layout" button next to Test Screensaver.
- `DashboardView` — `screensaverLayoutEdit` flag; `save-layout` writes the
  store (the settings watch persists it).

## Implementation Plan

- [x] Task 1: `screensaverLayout` util + store plumbing + backend allowlist
- [x] Task 2: ScreenSaver absolute positioning (side-by-side default)
- [x] Task 3: `screensaverBackground` + picker + upload in Settings
- [x] Task 4: layout edit mode + ui_command + Customize Layout button
- [x] Task 5: tests, type-check, log results

## Trade-offs

- **Chose** absolute % positioning over keeping flex as the normal path: one
  code path, and the default IS the requested layout. Cost: narrow portrait
  panels can overlap; mitigated with a `max-width: 620px` fallback that
  reverts widgets to a static column.
- **Chose** scale-resize over width-drag: one handle, no reflow surprises.

## Verification Criteria

1. Default layout: clock centered slightly up; news/market/worldclock side by
   side; weather top-right.
2. Choosing a screensaver background paints it behind a readable scrim;
   component backgrounds animate.
3. Customize Layout opens the live screensaver in edit mode; drag moves,
   corner handle resizes, Save persists across reload; Reset restores.
4. Tapping a news row still opens the article without dismissing.

## Implementation Results

**Files created**
- `frontend/src/utils/screensaverLayout.ts` — `ScreensaverLayout`
  (`Record<widgetId, {x,y,scale}>`, viewport-% centers), defaults, and
  `normalizeScreensaverLayout` (fills missing ids, clamps x/y to 0–100 and
  scale to 0.4–3, drops unknown ids).
- `frontend/src/tests/screensaver-layout.test.ts` — normalize unit tests +
  wiring assertions (store payload/apply, backend allowlist, ui_command
  routing, settings UI, bg layer).

**Files changed**
- `components/ScreenSaver.vue` — flex column replaced by per-widget
  absolutely-positioned `.ss-pos` wrappers driven by the layout
  (`translate(-50%,-50%) scale(s)`, scale composes around the anchor point).
  Clock drift folded into the same transform and paused in edit mode.
  `.ss-bg` layer + `.ss-dim` scrim + `<component :is>` mount for
  component-kind backgrounds. `layoutEdit` prop: root dismiss gated, children
  `pointer-events: none`, dashed outlines, pointer-event drag (clamped
  6–94%), corner-dot resize (0.5–2.5), toolbar with Reset/Save/Done. Weather
  scale capped at 2×, widget scale at 1.35 (double-scaling pushed the card
  past a 480px panel). Short-screen compaction (`max-height:560px`) shrinks
  the clock and drops headlines to one line; narrow fallback
  (`max-width:620px`) reverts to a static column.
- `views/DashboardView.vue` — `screensaverLayoutEdit` flag,
  `screensaver_layout_edit` command handling, `saveScreensaverLayout` writes
  the store (watch → localStorage + server sync).
- `views/SettingsView.vue` — "Customize Layout" button next to Test
  Screensaver; new "Screensaver Background" section (picker with
  'Default (Dark)', custom upload, remove, preview).
- `stores/settings.ts` — `screensaverBackground` ('default' = classic dark)
  + `screensaverLayout` refs plumbed through payload/apply/load/watch/return.
- `composables/useUiCommands.ts` — `screensaver_layout_edit` added to
  `UiCommand`.
- `backend/app.py` — command added to `ALLOWED_UI_COMMANDS`.
- `backend/routes/user_settings.py` — `screensaverBackground` +
  `screensaverLayout` added to `ALLOWED_USER_SETTING_KEYS`.
- `tests/news-carousel.test.ts` — layout assertions updated to the new
  structure (`.ss-pos` wrappers, side-by-side defaults, edit mode).

**Deviations from plan**
- Weather/widget effective scales capped (2×/1.35) — verified on-device that
  uncapped values clipped off-screen; the layout editor's per-widget scale
  (0.5–2.5) remains the escape hatch.
- Narrow-viewport fallback uses `position: relative` (not `static`) so the
  resize handle still anchors to its widget in edit mode.

**Verification**
- 175/175 frontend tests, `vue-tsc` clean, backend settings tests pass.
- Live-verified at 800×480 via Playwright: side-by-side layout renders with
  clock centered slightly up; drag moves widgets (clock → 19%/72%), the
  corner dot resizes (scale 1.32), Reset+Save persists the new defaults to
  `vdock_settings`; background layer + scrim verified with a gradient.

**Known limitation**
- `screensaverBackground`/`screensaverLayout` persist to localStorage
  immediately but server-side sync needs the backend restarted once — the
  running `app.py` process predates the new allowlist keys and drops them.
