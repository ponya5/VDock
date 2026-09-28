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
