# DL-060: Landscape-only mobile gate

User directive: "the vdock on mobile should be on landscape view only."

Portrait phones get a crushed 5-6-column deck no matter how cells are
sized — the Stream Deck form factor is inherently wide. Rather than
presenting a degraded portrait layout, gate it: a full-screen overlay asks
the user to rotate, and clears itself the moment they do.

## Design

New `RotateToLandscape.vue`, mounted once in `DashboardView` (deck only —
Settings/Profiles remain usable in portrait; they're plain scrolling
pages).

Gate predicate (all required):

- viewport is portrait (`innerHeight > innerWidth`),
- device is touch-capable (`pointer: coarse` media query OR
  `navigator.maxTouchPoints > 0`) — desktop windows resized narrow never
  match,
- viewport width ≤ 700px — tablets in portrait (iPad ≈ 744–834px) keep the
  normal layout since the deck already fits there.

`screen.orientation.lock()` is intentionally not used: browsers reject it
outside fullscreen/installed-PWA contexts, so a prompt is the universal
mechanism.

Overlay: fixed inset-0, z-index above the header reveal pill (10000),
dark themed card with an animated rotating phone icon (paused under
`prefers-reduced-motion`), "Rotate your device" copy, and a rotation-lock
hint. Listens to `resize` + `orientationchange`; clears automatically on
rotation.

Escape hatch: a low-emphasis "Continue anyway" button dismisses the gate
for the session — otherwise a phone with rotation lock enabled would be
permanently blocked.

## Implementation Results

- `RotateToLandscape.vue` created and mounted in `DashboardView`; gate
  predicate, listeners, overlay card, animated `mobile-screen` icon, and
  rotation-lock hint all as designed.
- Verified live (touch capability stubbed via `maxTouchPoints` + coarse
  pointer matchMedia): portrait 412×839 → gate shown; resize to 863×360 →
  gate clears and the compact landscape deck (72px buttons, auto-hidden
  header) is interactive; back to portrait → gate returns; "Continue
  anyway" dismisses for the session (survives subsequent resizes, clears
  on route remount).
- Fluid-type fix during verification: `property8` test enforces `clamp()`
  on all literal font sizes — initial px values replaced with the
  project's clamp convention.
- `vue-tsc` clean, production build clean, 239/239 frontend tests.
