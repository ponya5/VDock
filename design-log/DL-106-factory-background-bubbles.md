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

## Follow-up (2026-05-21): factory look → Balatro

**Request:** the out-of-box desktop background should be `balatro`
instead of `bubble-float`. Same semantics as before — strictly
first-install; `migrateBackground` is still untouched so existing stored
files keep their saved choice (this install keeps `galaxy`, etc.).

**Design delta:** one-line — `FACTORY_BACKGROUND_ID = 'balatro'`.
`SETTINGS_DEFAULTS.background`, the `background` ref seed and the
Appearance "Reset to default" all follow the constant automatically.
Unlike `bubble-float`, `balatro` is `kind: 'component'` (ogl/WebGL
renderer): the dashboard contributes no `dashboard-bg-*` class and
`BackgroundRenderer` mounts it. If the renderer can't initialize on a
device (e.g. no WebGL), its `onError` fallback shows the quiet gradient —
out-of-box still never lands on a blank screen.

**Plan:**

- [x] `FACTORY_BACKGROUND_ID = 'balatro'` + comment
- [x] Test pin: fresh store → `balatro` (rename describe to match)
- [x] vitest, vue-tsc, build
- [x] Point this install's `user_settings.json` at `balatro` too so the
      change is visible here — separate from the factory seed, noted in
      the reply.

### Follow-up results

- `backgrounds.ts` — `FACTORY_BACKGROUND_ID = 'balatro'`; comment updated.
  `SETTINGS_DEFAULTS.background`, the `background` ref seed and Appearance
  → Reset all follow the constant — nothing else to touch.
- `background-migration.test.ts` — pin updated (fresh store → `balatro`);
  the `'default'` sentinel and `migrateBackground` stay as-is, so existing
  installs keep their saved background. 8/8 green; `vue-tsc` clean;
  `npm run build` + `dist/` rebuilt.
- This install: switched via the real client path (Settings → Appearance →
  Background → Balatro) rather than a file edit — important because
  `PUT /api/user-settings` **replaces** the whole settings blob: an early
  `{"background":"balatro"}`-only PUT wiped the file momentarily until a
  connected client's next save re-wrote it with `bubble-float`. A client-side
  pick instead PUTs the full payload **and** broadcasts `settings_changed`,
  healing every connected device's localStorage in one shot.
- Verified live at 1024×600: `.balatro-container` + canvas mounted in
  `BackgroundRenderer`, picker shows Balatro, server file persisted
  `background: balatro` (45 keys), preview renders the red/blue swirl.
