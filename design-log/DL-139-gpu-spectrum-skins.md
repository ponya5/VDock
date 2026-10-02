# DL-139 — GPU spectrum skins: radial pulse, smoke plume, wave grid, neon flight, liquid chrome

## Problem

The spectrum saver's 14 skins are all Canvas2D. A set of five new skins was
requested that go beyond what 2D paths can deliver convincingly:

1. **Radial spectrum** — 64 log-spaced FFT bins around a pulsing bass
   counter, plus a waveform line, with a beat-synced fallback when silent.
2. **Smoke plume** — WebGL fragment shader: fractal noise advected upward,
   widening envelope, lit by its own density gradient, warm at the source,
   cool at the top, ember glow at the base.
3. **Wave grid** — lit 3D scene: 16×16 instanced columns in a travelling
   height wave, coloured by height, one shadow-casting key light + soft sky
   fill, orbiting camera.
4. **Neon flight** — camera fly-through on a closed Catmull-Rom spline
   through 60 neon rings and floating blocks, banking into turns,
   exponential fog, grid floor.
5. **Liquid chrome** — WebGL fragment shader: eight orbiting metaball
   charges, surface normal from the field gradient, painted studio
   reflection, iridescent fresnel rim.

## Design

### Architecture — GPU behind the existing 2D stage

`SpectrumStage` owns two stacked 2D canvases and cross-dissolves renderers
(`SpectrumRenderer.draw(ctx2d, frame)`). A canvas element's context type is
fixed, so GL content can't draw into the stage canvas — instead each GPU
skin owns an **offscreen canvas** (its own WebGL context / Three.js
renderer) and blits into the stage ctx with one `drawImage` per frame.
That preserves crossfades, the frame governor, idle handling, and the
widget overlay pipeline unchanged.

Fragment-shader skins (smoke, chrome) render at reduced internal
resolution (~0.5×, capped ~640×360) — fluid/smoke shading wants softness
anyway, so the upscale is free bloom, matching the ambient mini-canvas
pattern from DL-134.

### Fallbacks

jsdom and GL-less panels return null from `getContext('webgl')` and
`WebGLRenderer` throws — every GPU skin guards creation and falls back to
a 2D renderer (`createAmbient` + simple lit shapes) so tests pass and
devices without WebGL still get a themed saver.

### Audio driving

Shared uniforms per frame: `u_level` (0-1), `u_bass` (bands 0-3 mean),
`u_beat` (transient pulse via `createPulse`), `u_time`, `u_res`, and
`u_bands[20]` where a scene indexes the spectrum. When `frame.live` is
false, skins drive a synthetic beat clock (~120 BPM) and `demoBands`
swatch so the saver still breathes — the "beat-synced fallback".

### New module

`frontend/src/services/spectrumSkins3d.ts` holds the four GPU skins; the
pure-2D `radial` skin lives in `spectrumSkins.ts` beside the helpers it
reuses. Shared helpers (`createAmbient`, `createPulse`, `hslRgb`,
`sampleBandsCircular`) become exported. Registry grows 14 → 19 skins:

| id | label | tech |
|---|---|---|
| `radial` | Radial Pulse | Canvas2D |
| `smoke` | Smoke Plume | WebGL fragment shader |
| `wavegrid` | Wave Grid | Three.js instanced mesh |
| `flight` | Neon Flight | Three.js spline camera |
| `chrome` | Liquid Chrome | WebGL fragment shader |

Dependency: `three@0.186.1` (published 2026-09-24) + `@types/three` dev.

## Implementation Results

Implemented as designed. Notes:

- **`spectrumSkins3d.ts`** is a new module holding the four GPU skins plus
  shared plumbing: `makeDrive()` (level/bass/beat/bands per frame with the
  122 BPM synthetic fallback), `makeShaderCanvas()` (WebGL1 boilerplate —
  compile/link a fullscreen triangle, uniform map), `createShaderSkin()`
  (~55% internal res, capped 560×400, upscaled blit), `createThreeSkin()`
  (offscreen `WebGLRenderer`, resize tracking, try/catch → 2D fallback),
  and `fallback2d()` (ambient + drifting orbs) for GL-less clients.
- **`spectrumSkins.ts`** exports the shared helpers (`createAmbient`,
  `createPulse`, `hslRgb`, `sampleBandsCircular`, `hexRgb`) and gains the
  pure-2D `radial` skin; the circular import between the two modules is
  safe — every cross-reference is inside function bodies evaluated lazily.
- **Radial Pulse**: `bandPos` maps 64 bins log-spaced onto the 20-band
  array (`pow(20, k/63)`), bass counter is an arc gauge + numeric readout,
  waveform strip reuses the harmonic-sum trace from Wave.
- **Smoke**: `density()` evaluates fbm twice per pixel (main + gradient
  offset for self-lighting); rise speed rides `u_level`, beat kicks
  buoyancy, ember scales with bass.
- **Wave Grid**: 256 instances, height = travelling wave + per-column band
  (x = frequency axis) + bass lift; `setColorAt` per frame maps height to
  teal→magenta; `DirectionalLight` casts shadows into a 26-unit ortho
  frustum over a hemisphere-lit ground plane.
- **Neon Flight**: 8-point closed centripetal Catmull-Rom; 60 torus rings
  offset on a slalom (`sin(u·9π)` lateral, `cos(u·7π)` vertical); camera
  banks via signed tangent cross-product clamped to ±0.5 rad; cruise speed
  integrates `dt` so it's frame-rate independent.
- **Chrome**: 8 charges with analytic gradient accumulation (no derivative
  builtins — WebGL1), painted env() studio (room gradient + window stripes
  + overhead strip), cosine-palette iridescence on the fresnel rim.

### Verified

- `vue-tsc` clean, 19/19 spectrum tests green (catalogue assertion updated
  to the full 19-skin list), `npm run build` clean — `dist` rebuilt
  (three.js adds ~530 KB precache; local-served so acceptable)
- **Live on the built bundle** (1280×800): all five skins render —
  `refs/saver-radial-*.png`, `refs/saver-smoke-*.png`,
  `refs/saver-wavegrid-*.png`, `refs/saver-flight-*.png`,
  `refs/saver-chrome-*.png`
- **Frame budget**: rAF sampling per skin — p50 = 16.7 ms on all five
  (chrome 16.8 max; smoke 33 ms max and wavegrid/flight spikes only during
  the crossfade frame when the GL context first initializes)
- GL-less path exercised implicitly by vitest — `create()` runs under
  jsdom (no WebGL) and the catalogue test passes via the 2D fallbacks

## Follow-up — Psychedelia, Smoke Plume and Liquid Chrome removed

The user cut three skins on taste grounds: `psyche` (Psychedelia),
`smoke` (Smoke Plume) and `chrome` (Liquid Chrome). Registry is now
16 skins: the 13 legacy 2D skins plus `radial`, `wavegrid`, `flight`.

- `createPsyche` deleted from `spectrumSkins.ts`; `createSmoke`,
  `createChrome`, both fragment shaders (`SMOKE_FRAG`, `CHROME_FRAG`) and
  the now-unused shader plumbing (`makeShaderCanvas`, `createShaderSkin`,
  `ShaderCanvas`, `VERT`) deleted from `spectrumSkins3d.ts`. The module
  now holds only the two Three.js skins; `makeDrive`/`fallback2d` remain
  (shared by `createThreeSkin`).
- Persisted `spectrumSkin` values of removed ids resolve to `winamp` via
  `getSpectrumSkin` fallback — unchanged, no migration needed.
- Shuffle iterates the registry, so removed skins drop out automatically.
- Catalogue test updated to the 16-skin list; README/CHANGELOG skin
  counts updated (19 → 16).

Verified: `vue-tsc` clean, spectrum tests green, build clean, `dist`
rebuilt.

## Follow-up 2 — Neon Flight flies through the rings, beat-driven

Reworked `flight` per user request ("flying inside the circles, beat
affects speed and colors"):

- **Rings centered on the spline** — was a slalom offset ±7 units off the
  path (camera flew *past* rings); now each ring is centered on the curve
  with a small wander (≤ ~3.4 units — well inside the 6-radius bore), so
  the camera passes through every ring. Radius bumped 5.2 → 6 for a more
  tunnel-like read.
- **Beat → speed**: `uCruise` gain gains `+ beat * 2.2` (was level-only),
  plus a subtle FOV kick (68 + beat·9°) so each kick reads as a surge.
- **Beat → color**: the hue wheel now integrates `dt * (0.05 + beat·0.45)`
  instead of a flat `t * 0.03` — kicks accelerate the color cycle; rings
  also brighten (+0.15) and swell (scale ×1.07) with the beat envelope.
- Floating blocks pushed ≥9 units off the spline so the camera can't
  clip through one.

Verified live on the built bundle (Spotify playing): camera rides inside
the ring tunnel — `refs/flight-through-rings-*.png`. `vue-tsc` clean,
19/19 spectrum tests, `dist` rebuilt.
