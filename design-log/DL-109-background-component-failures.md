# DL-109: Fix hard-failing component backgrounds + honest preview failure state

**Date:** 2026-10-02

## Problem

User report: not all dashboard backgrounds work, and some previews in
Settings → Appearance render broken. A live sweep of all 58 catalog ids
(driven through the real `BroadcastChannel` settings path in the running
app, inspecting the mounted DOM + console) found two hard failures —
both fall back to the default gradient on the dashboard and to the bare
checkerboard in the Settings preview, which reads as a "broken" tile:

1. **`molten-metal`** — fragment shader line 62:
   `'*' : wrong operand types — mediump int * const float`. Line 130:
   `noise(q * uFold + ... + i * 1.7)` multiplies the `int` loop counter
   by a float. GLSL ES 1.0 has no implicit int→float conversion, so the
   shader never compiles. OGL's own error path then throws a secondary
   `TypeError: ... 'forEach'` — collateral, removed by the same fix.
   Sibling shaders avoid this by declaring `float` loop vars
   (Galaxy, LineWaves) — MoltenMetal is the only `int` counter used in
   float arithmetic.
2. **`shape-waves`** — `ValidationError: Texture kind must be explicit`.
   `createMaskTexture()` calls `gpu.device.createTexture({...})`, and
   `gpu.device` is the **vgpu Device wrapper** (not the raw GPUDevice);
   vgpu's contract requires an explicit `opts.kind` (`"2d"` etc.) — no
   inference. It's the only raw `createTexture` call in the codebase;
   every other texture goes through vgpu's `target()`/`texture()`
   factories which carry kind.

CSS-kind coverage audited too: all 12 non-sentinel css-kind ids have a
matching `dashboard-bg-*` rule in `main.css` (`default` intentionally
has none — it's the base-gradient sentinel). Preview reuses the same
classes (`backgroundStyleFor` returns `{}` for css kinds), so css
backgrounds render identically in preview and dashboard — no divergence.

## Fix

- `MoltenMetal.vue`: `i * 1.7` → `float(i) * 1.7`.
- `ShapeWaves.vue`: `kind: '2d'` in the mask-texture descriptor (also
  fixes the resize-recreated texture at the second call site, which
  reuses the same factory).
- `SettingsView.vue`: when a component preview reports an init failure
  (`bgPreviewFailed`), overlay a small "Preview unavailable" caption on
  the checkerboard stage instead of leaving a bare checkerboard that
  looks like a corrupted render.

## Implementation Results

- `MoltenMetal.vue`: `float(i) * 1.7` — fragment shader compiles.
- `ShapeWaves.vue`: `kind: '2d'` added to the mask-texture descriptor
  (covers both the init-time `createMaskTexture(1,1)` and the
  mask-upload recreation path).
- `SettingsView.vue`: `previewBgUnavailable` computed +
  `.preview-bg-note` overlay — a failed component now shows
  "Preview unavailable on this device" on the checkerboard instead of
  an unexplained garbled tile.
- New `src/tests/background-health.test.ts` (6 pins): css-kind catalog
  ids all have `dashboard-bg-*` rules, component catalog entries all
  resolve to real `.vue` imports, `float(i)` + `kind: '2d'` pinned, no
  raw `createTexture` without `kind` anywhere in backgrounds/, preview
  failure-state wiring.
- **Live verification** (Chrome DevTools protocol against the running
  dev server, driving `vdock-settings-sync` BroadcastChannel — the same
  path the picker uses):
  - `molten-metal` — canvas 1920×968 mounted on the dashboard, zero
    console errors (previously: shader compile error + `forEach`
    TypeError → fallback).
  - `shape-waves` — canvas 1920×968 mounted, zero errors (previously:
    `ValidationError: Texture kind must be explicit` → fallback).
  - Settings → Appearance → Background preview rail: both components
    mount real canvases inside `.preview-bg-clip` (scaled viewport),
    no warnings.
  - Note: `BackgroundRenderer` latches `failedId` per session — a
    background that failed once won't remount until reload. That's why
    a page reload was needed to verify the fix live; worth remembering
    for future background debugging.
- Full sweep context: 58 catalog ids exercised — these were the only
  two hard failures; all css-kind rules present; remaining components
  mounted clean.
- Frontend suite: **340 passed / 68 files**; `vue-tsc --noEmit` clean;
  `npm run build` clean, `dist/` rebuilt (75 precached entries).

## Follow-up (2026-09-28): mount-time error boundary for component backgrounds

**Context:** user report — dashboard + screensaver backgrounds show plain on
their phone. Live verification (Chromium + WebKit mobile emulation, dev +
prod builds) shows both backgrounds already apply on mobile — the likely
device-side cause is a stale precached bundle: `balatro`/`prismatic-burst`
both entered the catalog in `2d99146` (2026-09-20), and a bundle older than
that resolves both ids to `'default'` = plain on both surfaces. The hourly
SW self-update heals any phone whose bundle has it; older bundles need one
manual reload (DL-060 documented this gap).

**Real defect found in the audit:** every ported component background
declares an `onError` prop but never calls it — `mount*()` runs the
renderer effects loop bare, so an init throw (`new Renderer()` when WebGL
is refused or the context is lost) escapes as an uncaught Vue error and the
`BackgroundRenderer` fallback never engages. The screensaver's
`ssBgComponent` mount and the Settings preview have the same hole — a
mount-time throw propagates past their failure states entirely.

**Design:** one shared boundary — `backgrounds/BackgroundHost.vue` —
renders `<component :is>`, wires the inner `onError` prop AND captures
uncaught lifecycle errors via `onErrorCaptured`; on any failure it unmounts
the child and emits `error`. Used by `BackgroundRenderer` (→ designed
quiet-gradient fallback), `ScreenSaver` (component bg drops to the dark
base), and the Settings preview (→ "Preview unavailable").

### Implementation Results (2026-09-28 follow-up)

- New `frontend/src/components/backgrounds/BackgroundHost.vue`: forwards
  `onError` into the child AND `onErrorCaptured`-captures init throws;
  `failed` unmounts the child and emits `error` once. `inheritAttrs:false`
  + `v-bind="$attrs"` keeps `class`/style fallthrough landing on the real
  component (and silent once it's unmounted).
- `BackgroundRenderer`, `ScreenSaver` (`ssBgComponent`), and the Settings
  preview all mount component backgrounds through the host — every
  component-kind catalog entry now fails soft on every surface.
- New test in `background-renderer.test.ts`: a stubbed Balatro throwing in
  `setup()` produces `.background-renderer__fallback` + the
  `[background] fell back to gradient` warn, no uncaught error.
- **Live failure simulation (prod build :5000, Pixel-7-landscape
  emulation):** nulled `canvas.getContext('webgl*')`, broadcast a
  background flip over `vdock-settings-sync` to force a remount under the
  broken context — console shows `unable to create webgl context` then
  `[background] fell back to gradient: galaxy TypeError: Cannot set
  properties of null`; `.background-renderer__fallback` rendered and the
  deck stayed usable. Same for `balatro`. Store/localStorage restored to
  `balatro`; settings PUTs were stubbed during the flip.
- **Stale-bundle note:** the user's phone symptom (plain on both surfaces,
  landscape included) matches a precached bundle older than `2d99146`
  (2026-09-20), which lacks the `balatro`/`prismatic-burst` catalog ids —
  both resolve to `'default'`. `dist/` rebuilt; one manual reload on the
  phone pulls the new bundle and the hourly/visibility SW update takes over
  from there (the DL-060 poll).
- Frontend suite: **365 passed / 70 files** (1 known vitest-worker teardown
  flake in `property6_settings.test.ts`); `vue-tsc --noEmit` clean;
  `npm run build` clean, `dist/` rebuilt (75 precached entries).
