# DL-020 — Screensaver widgets clamped inside the viewport

## Background

On the 7" panel the screensaver rendered partially out of bounds: the
weather pill clipped off the top edge, the headlines section ran off the
left edge, and the world-time column touched the right edge.

## Root cause

Widget positions are **centers** in viewport percent
(`left: x%; transform: translate(-50%,-50%) scale(k)`). The saved layout
clamps centers to 6..94, but that only bounds the *center point* — a
widget whose half-width exceeds its distance to the edge still
overflows. The 2-column headlines section (~640px = 62% of a 1024px
panel) centered at x=26 puts its left edge ~50px off-screen; even the
default layout overflows at 1024×600.

## Design

Measure the real rendered box and clamp the *effective center* instead:

- Each `.ss-pos` wrapper registers itself via `:ref` → `setWidgetEl`.
- A `ResizeObserver` keeps `widgetSizes[id] = offsetWidth/Height`
  (transform-free layout size); `viewport` tracks window resize.
- `clampCenter(id, x, y, scale)` computes the widget's half-extents in
  viewport percent (`size.w * scale / vw * 50`) and clamps the center to
  `[half + margin, 100 - half - margin]` — margin = 24px converted to
  percent per axis, which also covers the clock's ±20px burn-in drift.
  A widget larger than the viewport centers on that axis.
- `posStyle`/`clockStyle` render the clamped center — saved layout
  values are untouched, so old/saved positions self-heal at render time.
- `onDragMove` uses the same clamp (via `transformScale`, which includes
  the widget-size slider for info widgets), so dragging in the layout
  editor can't push a widget off-screen either.
- Falls back to the old 6..94 center clamp when nothing is measured yet
  (first frame, jsdom tests without ResizeObserver).

## Implementation results

- Live at 1024×600 with deliberately extreme positions (x:4..97, y:6..96):
  every widget reported `overflow: false`, edges landing exactly on the
  24px margins. With defaults: news left edge 24, world-clock right edge
  1000, weather top edge 24.
- `vue-tsc` clean; 49 files / 176 tests pass (added a measured-clamp
  property test to `news-carousel.test.ts`; updated the position test to
  assert `clampCenter` rather than raw `l.x`/`l.y`).
- Narrow (<620px) portrait fallback unchanged — it already switches to a
  relative column flow.
