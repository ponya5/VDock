# DL-130 — Bigger header reveal FAB + auto-hide countdown pill

## Problem

Two pieces of header chrome under-communicated:

1. The floating "Header ⌄" reveal button was 68×46 px — small against a
   1024×600 panel and the only path back to the header once hidden.
2. The header's auto-hide "timer" was a bare 4px progress line: it showed
   *that* time was passing but never *how much* remained, and offered no
   way to keep the header open besides touching it again.

The user supplied a Uiverse "space button" recipe (animated gradient
border, starfield, blurred glow) as the target aesthetic for the timer.

## Design

**Reveal FAB** — same window-glyph + label, enlarged 68×46 → 92×58 with
proportionally larger type (0.72 → 0.86 rem label). Still bottom-right,
still lifts above the footer strip when it mounts.

**Countdown pill** — replaces the "mystery bar" with a glass chip at the
header's bottom-right (mirrors the FAB's corner — the chrome's home):

- Face: clock icon + live seconds (`4s`), tabular-nums so it doesn't
  wobble per tick.
- Border: the Uiverse `background-clip: padding-box, border-box` trick —
  solid dark fill over a 300%-size conic-ish gradient sweeping on a 5 s
  loop (the motion says "this is actively counting down").
- Behind the face: a star layer (1px dots on a 22 px grid, drifting up
  exactly one period per 3.6 s loop — seamless, transform-composited)
  and two blurred glow blobs (magenta/violet, 4 s scale pulse).
- **Tap pins the header open** — face flips to a pin icon + "Pinned",
  gradient freezes mid-sweep, glow dims. Tap again resumes the countdown
  from where it paused (no free 5 s reset). Pin state clears on hide so
  the next reveal re-arms. Swipe-up/collapse still work while pinned.

The 4px progress line stays — proportional fill (ambient) and pill
(readout) answer different questions.

## Trade-offs

- The full Uiverse recipe (two rotating 200rem star canvases, `double`
  border, 1.1 hover scale) was scaled down to chip size: one drift layer,
  one border sweep, 1.06 hover scale on fine pointers only. At 100 px
  the extra canvases are invisible cost.
- Pin-on-tap adds the only new behavior; it's the obvious affordance for
  a countdown you can't otherwise stop.
- Seconds are reactive refs updated on the existing 50 ms tick — no new
  timer source.

## Implementation Results

- `DeckHeader.vue`: `.autohide-pill` button + `toggleAutohidePin`
  (stop → resume-from-remainder), `secondsLeft`/`autohidePaused` refs on
  the existing tick, pin cleared on collapse/hide.
- `DashboardView.vue`: FAB 92×58, label/caret/gap bumped, radius 14.
- Reduced-motion: all three pill animations off; static border + number
  remain.
- Tests: 8 new (`header-timer-pill.test.ts`) — mounted pin/fire
  behavior plus source assertions for layers, resume, reset, FAB size,
  reduced-motion. The unpaused test had to poll with real timers —
  jsdom throttles `setInterval`, so 100 ticks land past 5 s wall time.
- Verified live via Playwright: FAB at the larger size, pill counting
  `5s→…` with gradient border visible on the open header.

## Follow-up (DL-134 session): slicker, larger FAB redesign

Feedback: the 92×58 mini-window read plain — "a bit bigger… more slick
professional look (animated)". New recipe keeps the glyph language
(band on top = the header being summoned) but restyles it:

- **Bigger**: 120×68 px (was 92×58), radius 18.
- **Orbiting rim**: `::before` spins a conic teal→cyan gradient under
  `overflow: hidden`; a `::after` inner glass plate masks it to a
  ~1.5 px living edge — the same trick family as the pill's border
  sweep, at FAB scale.
- **Band sheen**: the accent head band is a 260%-wide gradient whose
  background-position ping-pongs — the teal band glints on a loop.
- **Caret dip**: the chevron sinks 3 px and back every 1.9 s — the
  pull-down affordance, legible on touchscreens with no hover.
- **Face sheen**: a skewed white highlight (`fab-sheen`) sweeps the
  glass every ~5.4 s — the "premium card" glint.
- Breathe ring removed — the orbit rim is the discoverability cue now.
- Reduced-motion: orbit, band sheen, caret dip and face sheen all off;
  static layered rim + band remain.

### Implementation Results

- `DashboardView.vue`: one new `fab-sheen` span; base rule + four new
  animation blocks (`fab-orbit`, `fab-head-sheen`, `fab-caret-dip`,
  `fab-sheen-sweep`); content layers get `z-index` above the plate.
- `header-timer-pill.test.ts` size pin updated 92×58 → 120×68;
  `header-reveal-dock`/`edit-mode-touch-drag` contracts still hold
  (fixed position, `overflow: hidden`, `top: 0` band, label present,
  no ≥150 px fixed width, edit-mode suppression intact).
- 39/39 frontend tests green; `npm run build` clean, `dist` rebuilt.
