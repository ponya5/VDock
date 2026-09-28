# DL-106: Out-of-box dashboard background = Floating Bubbles

## Problem

New installs greet with the plain `default` gradient. User wants the
first-run dashboard to ship with motion: the catalog's
`bubble-float` ("Floating Bubbles", a pure-CSS animated option).

## Design

`'default'` is a **sentinel**, not just a preference: `resolveBackground`
falls back to it for unknown ids, `backgroundClassFor('default')`
returns `''`, `App.vue` keys `bg-animated` off it, and the screensaver's
`hasCustomBg` compares against it. So the sentinel stays — only the
**seed** changes:

- `backgrounds.ts` gains `FACTORY_BACKGROUND_ID = 'bubble-float'`
  (mirroring `DEFAULT_SCREENSAVER_BACKGROUND_ID`).
- `settings.ts`: `SETTINGS_DEFAULTS.background` and the `background` ref
  seed from it — so "Reset to default" in Appearance also restores
  bubbles, consistently.
- `migrateBackground` is untouched: it still falls back to
  `DEFAULT_BACKGROUND_ID` when no background key is stored, so existing
  installs that never picked a background keep the gradient — the change
  is strictly out-of-box. A user who explicitly chose "Default
  (Gradient)" keeps it either way.

`bubble-float` is `kind:'css'` → `dashboard-bg-bubble-float` class +
`bg-animated`; no component runtime, no asset to ship.

## Implementation Plan

- [ ] `FACTORY_BACKGROUND_ID` in `backgrounds.ts`; seed settings from it
- [ ] Test pin: fresh store → `bubble-float`; existing migration tests
      unchanged
- [ ] vitest, vue-tsc, build

## Implementation Results

Landed as designed:

- `backgrounds.ts` — `FACTORY_BACKGROUND_ID = 'bubble-float'` beside the
  sentinel `DEFAULT_BACKGROUND_ID` (unchanged — still the
  `resolveBackground` fallback and the "plain gradient" picker entry).
- `settings.ts` — `SETTINGS_DEFAULTS.background` and the `background`
  ref seed from `FACTORY_BACKGROUND_ID`, so both a fresh install and
  Appearance → "Reset to default" land on Floating Bubbles.
- `migrateBackground` deliberately untouched — a stored file with no
  background key still resolves `'default'`, keeping existing users on
  the gradient. Out-of-box only, per the request.

**Tests:** +1 pin (fresh store → `bubble-float`; `migrateBackground({})`
→ `'default'`). `vitest` 328/328, `vue-tsc` clean, `npm run build`
clean, `dist/` rebuilt.
