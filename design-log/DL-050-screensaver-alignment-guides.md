# DL-050 — Snap/alignment guides in the screensaver layout editor

**Date**: 2026-09-21
**Status**: Implemented

## Background

The screensaver layout editor (Settings → Screen Saver → Customize
Layout) lets users drag widgets freely, but gives no spatial feedback:
you can't tell when two widgets share a center line or edge, so
arranging them neatly is pure guesswork. Requested: alignment
indicators while moving a widget — the classic "smart guides" pattern
(PowerPoint/Figma).

## Design

All geometry already exists: positions are widget centers in viewport
percent, `widgetBox(id)` computes each mounted widget's center +
half-extents, and `onDragMove` runs on every pointer move.

### Snap model

While dragging, compare the dragged widget's anchors — left edge,
center, right edge (and top/center/bottom on Y) — against:

- every other mounted widget's edges and center (visual box; the
  clock's ±20px drift padding is excluded — guides must align with
  what you see, not the invisible excursion reserve), and
- the viewport center lines (50%).

If the nearest anchor↔target distance is within ~8px, snap the dragged
center so the two coincide and show the guide. One snap per axis; the
smallest delta wins.

### Hysteresis

A bare threshold flickers at the boundary (position jumps between
snapped and raw on alternating pointer events). Once a snap engages it
holds until the *raw* pointer-derived position clears a ~14px release
band — the widget feels magnetically stuck, then releases cleanly.

### Clamping interaction

Snap is computed on the clamped drag position, then re-clamped. If
edge clamping shifts the snapped position, the alignment isn't real —
the guide is dropped rather than shown at a position the widget isn't
actually at.

### Rendering

Guide lines are full-span 1px dashed rules (`--accent` color) in an
overlay layer at z-index 3 — above the widgets (z 2), below the edit
toolbar (z 4). They're only mounted in `layoutEdit` mode and only
while a snap is engaged; `endInteraction` clears them.

TypeSafe considered and not used: snap alignment is deterministic
geometry — no semantic judgment involved.

## Implementation Results (2026-09-21)

- `widgetBox(id, padClock)` — optional flag; guides use the visual box
  (`padClock=false`) so lines align with the rendered edge, not the
  clock's invisible ±20px drift reserve.
- `dragState` carries `snapX`/`snapY` holds; `snapAxis()` picks the
  nearest anchor↔target within 8px (per axis: edges + center of each
  mounted widget, plus the viewport 50% line), then holds through a
  14px release band for magnetic-stick hysteresis.
- `onDragMove` snaps each axis independently, re-clamps, and drops a
  guide if edge clamping moved the widget off its snap.
- Guides render as full-span 2px dashed `--accent` rules at z-index 3
  (above widgets, under the toolbar), cleared on pointerup/cancel.

Verified live (Settings → Screen Saver → Customize Layout, 1024×600):
- Center-to-center snap: weather → news center-x, guide at 24.66%.
- Edge-to-edge snap: weather right edge → sports left edge at 45.45%.
- Top-edge snap + viewport-center snap (y=50%) both engage and hold.
- Hysteresis holds position past the 8px band; releasing at 14px+
  clears the guide; pointerup removes all guides.

`vue-tsc` clean, 231/231 frontend tests pass.
