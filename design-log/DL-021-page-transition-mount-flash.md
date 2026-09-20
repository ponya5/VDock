# DL-021 — Page transition: incoming buttons mounted visible before the wave

## Background

User report: switching pages showed the new page's buttons instantly, and
the left-to-right wave then replayed over already-visible buttons — the
"transition" was an afterthought instead of a reveal.

## Root cause

`useGridTransition.triggerTransition` step 2 ran synchronously right
after `onPageSwap()`:

1. The stagger `forEach` set every cell's class to `''` immediately.
2. Vue flushes the page swap on the next **microtask** — before any of
   the `setTimeout` stagger beats (macrotasks) run.
3. New buttons therefore mounted with **no transition class** — fully
   visible on frame one.
4. `grid-transition-sweep` landed at `seqIdx*50` and
   `grid-transition-in` at `seqIdx*50+180`, each snapping an
   already-visible button back to opacity 0 and re-animating it.

## Fix

- New `.grid-transition-pre` class (`opacity: 0; pointer-events: none`)
  applied to every cell right after the swap. New buttons mount hidden;
  each cell holds `pre` until its own staggered beat.
- The stagger loop now applies the in-class directly on each beat —
  `grid-transition-sweep grid-transition-in` together for `light-bar`
  (the shine passes over the button while it materializes), or the
  style's in-class for flip/iris/cascade/glitch/dissolve. The separate
  +180ms sweep lead is gone — it only ever delayed the reveal.
- Per-cell cleanup waits 900ms (longest animation + buffer); the
  blanket clear at the end is unchanged.
- Reduced-motion path untouched (`grid-transition-dissolve` was already
  applied at mount).

## Implementation results

- Live sampling across a `setPage` transition on a 2-page scene:
  `grid-transition-out` at ~220ms → new page mounted carrying
  `grid-transition-pre` (hidden) → `sweep`/`pre` mix per cell through
  ~1400ms → clean. No instant pop-in; visible counts ramp with the wave.
- `vue-tsc` clean; 49 files / 176 tests pass.
- Applies to page *and* scene switches — both drive the same watcher.
