# DL-008 — React Bits background import + scrollable background picker

**Date:** 2026-09-20
**Branch:** `upgrade/upgrade--keypad`
**Status:** Implemented

## Problem

Two asks:

1. Import animated backgrounds from the reactbits.dev gallery into the
   Settings → Appearance → Background selector. Initially six shown in a
   screenshot (Shape Waves, Aero Shards, CRT Warp, Ghost Fibers, Gradient
   Waves, Molten Metal), then expanded to the wider gallery.
2. The background dropdown's scrollbar was so subtle users couldn't tell
   the list scrolled — options below the fold looked absent.

## Design

### Ports

React Bits sources are React + `ogl`/`vgpu`/`three`/canvas components. They
are ported to self-contained Vue SFCs in
`frontend/src/components/backgrounds/` — no React runtime added. Two
approaches:

- **Hand-ported** (first six): renderer internals kept, React shell
  replaced with Vue lifecycle.
- **Batch transform** (`port_batch.py`, temp script): for the 28
  `ogl`/canvas/WebGPU gallery components the upstream component body is
  kept *verbatim* — hooks are shimmed (`useRef` → `{current}` box,
  `useState` → `{value}` + setter, `useEffect` → collected and run once in
  `onMounted`, cleanups run in `onUnmounted`), JSX-bound refs are mapped to
  template `ref`s, and the JSX return is replaced by an effect runner.
  This keeps shader/simulation code identical to upstream.

New deps: `ogl@1.0.11`, `vgpu@0.5.0` (both already in the lockfile tree;
added to `package.json` deps).

### Catalog

`src/data/backgrounds.ts` remains the single source of truth; each import
is a `kind: 'component'` entry with a unique id. Id collisions avoided:
`gradient-waves`/`waves`/`particles` were already taken, so the ports are
`gradient-waves-ogl`, `waves-canvas`, `particles-ogl`. WebGPU entries are
labeled "(WebGPU)".

### Picker

The native `<select>` is replaced by `BackgroundPicker.vue`: grouped
options (Default / Gradients / Animated), ≥40px rows for the 7" touch
panel, and two scroll affordances — a bottom fade edge plus a sticky
"scroll down" chevron hint, both driven by `data-more-below` on the panel
and hidden once scrolled to the end. The panel teleports to `.theme-dark`
so it inherits theme variables.

### Failure fallback

`BackgroundRenderer` now binds `onError`. A component that can't
initialize (WebGPU with no adapter, WebGL context loss) reports via
`onError` → renderer swaps in a quiet gradient div instead of leaving a
silent black screen. Re-picking a different background clears the state;
re-picking the failed one shows the fallback immediately (no flicker
loop). Components that don't declare `onError` ignore it.

## Implementation Results

**Imported (34 total):** Ghost Fibers, Gradient Waves (WebGL), Molten
Metal, CRT Warp, Shape Waves (WebGPU), Aero Shards (WebGPU), Plasma,
Galaxy, Liquid Chrome, Balatro, Orb, Particles, Threads, Faulty Terminal,
Radar, Prism, Plasma Wave, Sliced Waves, Topography, Web Threads, Soft
Aurora, Light Tunnel, Lightfall, Line Waves, Ferrofluid, Acid Squares,
Evil Eye, Grainient, Scanner, Ripple Grid, Gradient Blinds, Waves
(canvas), Shape Grid, Letter Glitch.

**Bugs found and fixed during porting:**

- `GradientWaves.vue`: `fwidth` requires GLSL ES 3.00 — added
  `#version 300 es` + `in`/`out` conversion; ogl's default 1.00 compile
  failed every frame.
- `port_batch.py`: brace/signature detection inserted the shim inside an
  `if` body (`') {'` vs `'})  {'` double-space); `export const X =` was
  matched as plain `const X` leaving a bare `export`; a fetched `.css`
  file was actually a 404 response parsed as CSS; post-component module
  helpers (Orb's `hexToVec3`/`hslToRgb`) were truncated with the JSX
  return — salvaged back into module scope.
- `Orb` spec used `ref='containerRef'` but the source uses `ctnDom` —
  container ref stayed `{current:null}`, effect early-returned, no canvas.
- Picker teleported to `#app` which is *nested* (index.html's mount wraps
  App.vue's `#app.theme-dark`) — panel landed in the unthemed outer div
  and computed white. Retargeted to `.theme-dark`.

**Verification:** `vue-tsc` clean; 138 frontend tests pass. Browser
(Playwright): all 32 non-WebGPU imported backgrounds mount and produce a
1280×720 canvas with no console errors; Orb confirmed after fix. Scroll
hint verified at top/middle (`data-more-below="true"`, hint visible) and
bottom (attribute removed, hint fades).

**WebGPU caveat:** `navigator.gpu` exists but `requestAdapter` returns
null under Playwright's Chromium (headed and headless), so Shape Waves /
Aero Shards could not be verified rendering here. Their `reportFailure`
path is exercised instead — confirmed the fallback gradient appears. On
real Chrome/Edge with a GPU they should render; needs one manual check on
the panel.

## Open items

- Manual check of the two WebGPU backgrounds on real hardware.
- Some ports may benefit from prop exposure in the picker later (colors,
  intensity) — currently all use upstream defaults.

### Follow-up (2026-09-28): cap panel height to real viewport room

Bug: on the screensaver settings panel the open picker ran past the
bottom of the viewport — options below the fold were unreachable.
`positionPanel` capped `maxHeight` at `min(320, innerHeight - 16)` but
never subtracted the space actually left under the trigger. The panel is
`position: fixed`, so page scrolling cannot reveal the overflow, and the
panel's own `clientHeight` included the off-screen region — even its
internal scroll left the last items below the fold.

Fix: `positionPanel` now measures the real room on the side it opens to
(`spaceBelow` / `spaceAbove`, minus the 4 px gap + 8 px viewport margin)
and caps `maxHeight` at `min(320, room)` — floor of 120 px so a cramped
window still shows a usable list. The internal scroll + fades then cover
the rest. Applies to both pickers (dashboard + screensaver background).

#### Implementation results (2026-09-28)

`BackgroundPicker.positionPanel` rewritten: measures `spaceBelow` /
`spaceAbove` (trigger edge → viewport edge, minus the 4 px anchor gap and
8 px margin), opens up when below-room < 180 px and above is roomier, and
caps `maxHeight` at `min(320, room)` with a 120 px floor.

Verified live at 1024×800, screensaver sub-tab, trigger near the fold:
panel top 543 → bottom 771 inside an 800 px viewport
(`clippedBottom: false`), `scrollHeight` 2489 vs `clientHeight` 226 — all
options reachable via the panel's internal scroll + bottom fade/chevron
hint. Screenshot: `design-log/refs/bg-picker-capped-*.png`.

`vue-tsc` clean, `npm run build` rebuilt `dist` for the panel.
