# DL-083 — Safari / iPhone compatibility pass

**Date:** 2026-09-28
**Status:** Implemented

## Background

User request: "make sure all this interface also works in safari and
iphone — just to be sure." Audit of this week's surfaces (mobile console,
scene swipe dissolve, screensaver bloom, background picker, connect-a-
device, waiting glow) against WebKit quirks.

## Findings and fixes

1. **`viewport-fit=cover` missing** from the viewport meta — without it
   `env(safe-area-inset-*)` always reads 0, so every safe-area padding in
   the app is dead code on notched iPhones. Added.
2. **`-webkit-mask-size` in the screensaver keyframes** — the scene wipes
   already carry full `-webkit-mask-*` pairs, but the saver bloom
   keyframes animated `mask-size` unprefixed; Safari < 18.4 ignores it →
   the bloom would have been a plain fade. Added the prefixed longhand
   inside both keyframes.
3. **`touch-action` on the swipe host** — `.main-content` (the scene
   swipe surface) had none; `pan-y` declares "vertical pans are native
   scroll, horizontal is ours" and `overscroll-behavior-y: contain`
   stops Chrome-Android pull-to-refresh from stealing the gesture.
4. **`100dvh` fallbacks** — iOS Safari's 100 vh includes the area under
   the collapsing URL bar; bottom-anchored chrome (console, chips) can
   hide behind it. `height/min-height: 100dvh` paired after each 100vh
   on the app-root containers (older Safari ignores it and keeps 100vh).
5. **`-webkit-user-select: none`** on touch surfaces (console chips /
   actions / shortcuts / links, scene segments, picker options, saver
   root, header trigger) — without it a long-press on iOS pops the text
   selection callout over the button.
6. **`-webkit-backdrop-filter` pairs** added where missing on today's
   surfaces (snooze chip) and the global/main.css translucent chrome —
   Safari < 18 only honors the prefixed property.
7. **`.input` font ≥16px on coarse pointers** — iOS auto-zooms the page
   when focusing an input under 16 px.
8. **Copy fallback for insecure LAN origins** — `navigator.clipboard` is
   undefined on `http://192.168.x` (not a secure context), which is
   exactly what an iPhone loading the deck sees. `copyLanUrl` falls back
   to a hidden textarea + `execCommand('copy')`.

## Out of scope / accepted

- `ResizeObserver`, `BroadcastChannel`, `navigator.vibrate` are all
  already guarded (`typeof` checks) — iOS degrades gracefully.
- `overscroll-behavior`, `scrollbar-color`, `color-mix` need modernish
  iOS (15.4+/16+/16.2) — graceful degradation on older.
- iOS edge-swipe (Safari back gesture) only triggers within ~20 pt of
  the bezel — center-screen scene swipes don't collide.

## Implementation Results

All eight fixes applied, verified in Playwright **WebKit** (AppleWebKit
605, Safari 26 engine — closest automated stand-in for Safari) plus a
real iPhone 13 device context.

**WebKit, desktop (1280×800):**

- Screensaver enter: `saver-bloom` fired, `-webkit-mask-size` interpolated
  20%→~300% with opacity 0.25→1; leave fired `saver-evaporate`, element
  removed after — full lifecycle intact.
- Scene click: `scene-wipe-next` enter/leave classes with proper
  from→to handoff (~430 ms), `seg-sweep-out`/`seg-sweep-in` on the rail.
- Synthetic pointer swipe on `.main-content`: committed scene advance;
  computed `touch-action: pan-y`.

**WebKit, iPhone 13 context (844×390 landscape, coarse pointer):**

- Mobile chrome active (4 `.mc-seg`), `maxTouchPoints` is 0 on headless
  WebKit but the `pointer: coarse` gate is what selects mobile — works.
- Real `page.tap()` on a rail segment switched scenes; console showed
  merged status row, 5 action tiles, `claude.ai` in the dashed links
  strip.
- Pointer swipe on `.main-content` switched scenes over the console.
- Posted `ready` state → waiting frame overlay + `.mc-seg.agent-waiting`
  + snooze chip all rendered. No elements clipped past the viewport.
- Portrait → rotate gate shown (by design).
- `reducedMotion: 'reduce'` → saver used `saver-fade-in` with
  `mask-image: none` — the reduced path, not the bloom.

Zero page errors in any run. `vue-tsc` clean, **287/287** vitest green,
`dist` rebuilt.

**Remaining caveat:** Playwright WebKit approximates but is not physical
iPhone Safari — real-device quirks (dynamic toolbar collapse behavior,
GPU-composited masks under memory pressure, haptic timing) should get a
spot-check on hardware when convenient.
