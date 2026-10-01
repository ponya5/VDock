# DL-134 — Spectrum: skin crossfade, restored skin catalogue, RGB bars, bar-skin ambience

## Background

The spectrum screensaver (DL-123) shipped with 7 skins and a dip-to-black
skin swap. A later dynamics expansion on the `research_upgrade1` branch
(commit `b0dfb58`, tagged DL-136 there) grew the catalogue to 13 skins and
gave every skin ambient/beat-reactive polish, but that work never merged
to `main` — the expanded file lives only on that branch, so the skins read
as "removed" from the user's point of view.

User asks for this pass:

1. **Soft transition** on skin shuffle — the current swap fades the canvas
   to black, swaps the renderer, fades back in. On a fullscreen saver that
   reads as a blink, not a transition.
2. **Restore the removed spectrum templates** — the `research_upgrade1`
   skin set: rotor, swarm, wave, ring, mirror, psyche, plus the shared
   dynamics helpers (beat pulse, spark pool, gravity peak caps).
3. **New bars skin** — RGB bars whose colors drift through soft hues with
   smooth transitions.
4. **WOW backgrounds** on the three classic bar skins (winamp / mono / uv)
   — the flat black stage should gain atmosphere, not a static wash.

## Problem

- `SpectrumStage.vue` owns one canvas; a true crossfade (old skin fading
  out *while* the new skin fades in) needs two stacked layers.
- `createBars(palette)` only accepts a static `BarPalette` — the RGB skin
  needs per-bar, per-frame colours that move.
- Restoring `b0dfb58`'s skins file verbatim is safe: `spectrumSkins.ts` is
  self-contained and its public API is unchanged. The accompanying
  SpectrumStage changes on that branch are *not* all safe — they reference
  `nowPlayingIcon`/`nowPlayingSourceLabel`/the `backdrop` prop, which are
  DL-135/136 features absent on main. Only the renderer-independent parts
  (envelope smoothing, fps governor) come across.

## Design

### Crossfade (`SpectrumStage.vue`)

Two stacked `<canvas>` elements, each with its own 2D context and its own
`SpectrumRenderer`. `frontLayer` marks which canvas is on top and opaque.

- `swapSkin(id)` builds the new renderer into the *back* layer, updates
  `activeSkinId` (tag follows immediately), then flips `frontLayer`. A CSS
  `opacity` transition (~850 ms `ease`) fades the incoming canvas in and
  the outgoing one out simultaneously — a real cross-dissolve, no black
  dip. Retire timer clears the outgoing renderer after the fade so the
  rAF loop stops paying for it.
- Rapid re-swaps are safe: the free layer is always the one not in front;
  whichever mid-fade renderer it still holds is simply replaced.
- Duration lives on `--xfade-ms`; `prefers-reduced-motion` drops it to a
  short ~350 ms fade (opacity fades stay — no transform motion involved).
- Mount also rides the crossfade: front layer starts transparent and
  fades in on the first frame.

Also ported from `b0dfb58` (renderer-independent smoothness):

- Asymmetric band envelope — fast attack lerp (~50 ms constant) bridges
  the backend's ~22 Hz emit cadence; slower release keeps decays graceful;
  jumps > `SPIKE_SNAP` skip the lerp so real transients land full height.
- `levelSm` — smoothed overall level passed to skins for glow/pulse.
- Frame governor — 60 fps target, EMA of draw cost; if draws consistently
  miss the 16 ms budget the loop settles to ~30 fps; reduced-motion ~22 fps.

### Skin catalogue (`spectrumSkins.ts`)

- Restored verbatim from `b0dfb58`: `hexRgb`, `createPulse`, `Spark` /
  `drawSparks` helpers; upgraded `createBars` (floor glow + sweeping beam +
  spark emission + gravity peak caps); upgraded iso (hue drift, ripple,
  under-glow, fixed painter order), scope (level-driven spin, pulsing core,
  comet orbiters), aurora (breathing rings, comet shimmer), ember (swell,
  crest hot spots, ember lift-off); new skins `createRotor`, `createSwarm`,
  `createWave`, `createRing`, `createMirror`, `createPsyche`.

### WOW bar background (winamp / mono / uv)

On top of the restored floor-glow + beam:

- **Ambient nebula** — two large palette-tinted radial washes (base colour
  pooling low-left, tip colour drifting high-right) that wander slowly and
  breathe with level; the stage never reads flat black even at silence.
- **Beat core glow** — the existing floor wash stays, still pulse-driven.
- **Vignette** — a soft edge-darkening radial drawn last, focusing the
  bars; also lifts perceived contrast for the additive spark layer.

### RGB bars skin (`rgb` / "RGB Bars")

`createBars` gains an optional `BarsFx` param:

```ts
interface BarsFx {
  /** Per-bar colour at height fraction 0 (base) … 1 (tip). Overrides the
   *  shared palette gradient when present. */
  colorAt?: (bar: number, y01: number, t: number, lvl: number) => string
  /** "r, g, b" strings feeding the ambient layers — may drift over time. */
  ambient?: (t: number) => { base: string; top: string }
}
```

Chroma skin: `hue = t*14 + i*9 + lvl*24` — a slow full-wheel drift
(~26 s/cycle) with a 9°/bar offset so neighbouring bars are always adjacent
hues (a flowing rainbow, not confetti), plus a gentle beat twist. Colour
depth varies along the bar (deep base → pastel tip) — soft by construction,
smooth because hue is continuous in `t`. Ambient layers take the current
lead hue so the whole scene shifts together.

### Registry order

`winamp, mono, uv, rgb` (bars block), then `iso, scope, aurora, ember,
rotor, swarm, wave, ring, mirror, psyche` — 14 skins total.

## Implementation Plan

- [ ] Restore expanded `spectrumSkins.ts` + add `BarsFx`/`rgb` skin +
      nebula/vignette ambience
- [ ] `SpectrumStage.vue`: two-layer crossfade, envelope + governor port
- [ ] Update `spectrum-stage.test.ts` registry expectation; run frontend
      tests; `npm run build` (panel serves the bundle)

## Trade-offs

- Two canvases double draw cost only during the ~0.9 s crossfade — cheap
  insurance vs. an offscreen-bitmap compositor, and each renderer keeps a
  clean `clearRect` owner.
- The `rgb` skin reuses the bars renderer via `colorAt` rather than a
  fourth copy of the bars loop — one code path, per-bar gradients only
  when the resolver is present.
- `nowPlayingIcon`/`backdrop` stage changes deliberately not ported —
  they belong to reverted/out-of-scope features.

## Verification Criteria

- `npm test` green incl. updated 14-skin registry expectation.
- Manual: settings picker shows all 14 live previews; skin clicks
  crossfade; `spectrumShuffle` rotation crossfades without a black blink;
  bars show ambient clouds + beam + sparks over a vignette; RGB bars cycle
  hues smoothly.

## Implementation Results

- `spectrumSkins.ts`: restored the six-skin catalogue from
  `research_upgrade1` (`rotor`, `swarm`, `wave`, `ring`, `mirror`,
  `psyche`) with their dynamics (beat pulse, sparks, gravity peak caps,
  comet trails); added `rgb` — RGB Bars — via a `BarsFx` `colorAt`
  resolver so per-bar hues drift smoothly; bar skins gained the ambient
  nebula/floor-glow/beam/vignette stack. 14 skins total.
- `SpectrumStage.vue`: single canvas + dip replaced by a two-layer
  canvas crossfade (`XFADE_MS` 850 ms, 350 ms under reduced motion) —
  each layer owns one renderer, swap promotes the back layer, retire
  timer frees the old one. Audio envelope: fast attack / slow release /
  spike snap + frame-cost governor.
- `spectrum-stage.test.ts`: registry now asserts the 14-skin list and
  two canvas layers. 545/545 frontend tests green; `vue-tsc` clean;
  `dist` rebuilt (panel bundle).
- Verified live: all 14 previews render in the skin grid; the saver
  showed Winamp with nebula ambience + media card.

### Follow-up: interactive ambience for every skin

The WOW backdrop was bar-skin-only; the nine non-bar skins still sat on
near-black. Added a shared `createAmbient({ h1, h2, orbit })` helper —
tinted base (never pure black), two roaming hue clouds on counter-phase
Lissajous paths, a center aura whose radius/alpha ride `level` and flare
on the beat pulse, and a vignette — painted right after each skin's
`clearRect`, tinted from the skin's own palette (`iso` 205/285,
`scope` 150/185, `aurora` 170/300, `ember` 18/335, `rotor` 190/270,
`wave` 172/200, `ring` 190/315, `mirror` 280/195; `swarm` orbits the
whole wheel at 10°/s). `psyche` is trail-based — an opaque backdrop
would erase the smear — so instead its trail-fade fill is tinted by the
drifting `hueBase`, decaying into ambience. Each ambient owns its own
`createPulse`, so per-renderer state still resets cleanly on skin swaps.
Verified live on the built bundle: Wave Ring shows violet/teal clouds +
breathing center aura (`refs/saver-ring-ambient-2026-10-01T22-12-10-
460Z.png`); Psychedelia's trails decay into tinted ambience
(`refs/saver-psyche-ambient-2026-10-01T22-12-34-728Z.png`).

### Follow-up: 60 fps render-cost pass + occluded-background suspend

Target: every skin pinned at 60 fps, not just under the governor's 30 fps
fallback. The ambient stack had added ~5 fullscreen gradient rasterizations
per frame; measurement then showed the real killer was elsewhere.

Render-side cuts in `spectrumSkins.ts`:

- `createAmbient` now paints its five layers into a ~1/8-scale offscreen
  canvas (clamped 96×60) and blits it up once — the upscale filter is free
  bloom. Static per-size pieces (vignette) are rasterized once and re-blitted.
- `createBars` ambience uses the same mini-canvas painter; its base palette
  gradient and vignette are cached per canvas size instead of being
  re-created/re-rasterized every frame.
- `createSwarm` was ~460 cubes × 3 path fills (~1400 fills/frame). Cubes
  are now 30 pre-rendered hue-bucket sprites drawn via `drawImage`
  (~460 blits/frame); level/beat still drive brightness via `globalAlpha`.
  Falls back to the path cube where no offscreen 2D context exists.
- `createIso` ripple distance per cell precomputed once (was `Math.hypot`
  per cell per frame).
- `SpectrumStage.vue`: 2D contexts cached per layer (was `getContext`
  per layer per frame).

App-side fix: `BackgroundRenderer` (App.vue) kept animating a 1400×900
shader canvas *under* the opaque saver — rAF doesn't stop on occlusion.
New `services/screensaverState.ts` exports `screensaverCovered`, lagging
saver visibility by the 450 ms dissolve enter; DashboardView reports via
`setScreensaverVisible` in its watcher + unmount reset; App.vue gates the
renderer on `!screensaverCovered`. Restores instantly on dismiss so the
background is back for the exit fade.

Measured live on the built bundle (800×480, balatro bg active,
90 rAF deltas per skin): before the suspend, deltas were bimodal
16.7/33.4 ms with `iso`/`aurora` locked at 33 ms; after, all 14 skins pin
at 16.7 ms p50/p95/max, and a crossfade into Swarm mid-measurement shows
0 frames over 20 ms. Swarm sprite look verified visually
(`refs/saver-swarm-sprites-60fps-2026-10-01T22-27-17-271Z.png`).
545/545 tests, `vue-tsc`, build all green.
