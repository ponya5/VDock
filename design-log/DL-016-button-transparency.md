# DL-016 — Global dashboard button transparency

## Background

User request: "add the button transparency level — so if I want to see
somewhat the background animation, I can set % of the dashboard button
transparency level." Dashboard background animations (DL-012 catalog +
custom uploads) are fully hidden behind opaque deck buttons today.

## Problem

- Buttons render at `style?.opacity || 1`; there is no global dial.
- Per-button opacity exists in the Button Editor but must be set per button
  and is meant for emphasis, not for revealing the background.

## Design

- **Setting**: `buttonTransparency: number` (0–100 %, default 0 = solid),
  plumbed through `PersistedUserSettings` / ref / payload / apply / load
  default / watch / export, `user_settings.py` allowlist — same path as
  every other appearance setting so it syncs across windows.
- **Application**: `applyButtonTransparency()` writes
  `--deck-btn-opacity = max(0.05, (100 − transparency)/100)` on
  `document.documentElement`, called next to `applyUIBrightnessFilter()` at
  all four call sites (remote apply, settings watch, server load, init).
  The 5% floor guarantees a stray value can never make every button
  invisible.
- **Consumption**: `DeckButton.vue` `buttonStyle` computes
  `opacity: calc(var(--deck-btn-opacity, 1) * ${style?.opacity || 1})` —
  the global factor multiplies the per-button opacity, so the Button
  Editor's per-button opacity still works on top. Using a CSS variable
  means every window (dashboard, standalone settings preview) inherits it
  with zero prop drilling.
- **UI**: "Button Transparency" slider (0–90%, step 5, Reset button) in
  Appearance → Button Behaviour → Button Display, next to Button Size.
  Capped at 90% in the UI so buttons stay findable; the Live Preview tile
  reflects it immediately since it renders a real `DeckButton`.

## Trade-offs

- Whole-element opacity (icon + label + shadow) rather than background-only
  transparency: buttons have heterogeneous fills (solid/gradient/tint/
  glass/neon…), so compositing a translucent background per fill type would
  be far more invasive; element opacity yields the predictable "glass tile"
  look and keeps labels proportional.
- Stored as transparency percent (user's mental model) but applied as an
  opacity factor — conversion happens in exactly one place.

## Verification Criteria

- Slider at 0% → buttons solid; 50% → background animation visible through
  buttons; per-button opacity still stacks.
- Setting persists locally, syncs to server (`user_settings.py` allowlist)
  and to other windows via the settings broadcast.
- `vue-tsc` clean; vitest suite passes.

## Implementation Results

- `settings.ts`: `buttonTransparency` ref(0) + interface + payload +
  apply + load default + watch + export; `applyButtonTransparency()`
  added and called at all four apply sites.
- `DeckButton.vue`: `opacity` is now
  `calc(var(--deck-btn-opacity, 1) * <per-button>)`.
- `SettingsView.vue`: slider + Reset under Appearance → Button Behaviour
  → Button Display; Live Preview reflects it.
- `user_settings.py`: `'buttonTransparency'` allowlisted.
- Verification: `vue-tsc --noEmit` clean; vitest 175/175 pass.
- Discoverability fix (DL-018 follow-up): the slider sat ~1200px down the
  Button Behaviour tab on a 600px screen — below Touch Mode, Live Preview
  and the apply-all demo — so users reported the feature missing. Button
  Display now opens the tab (slider at ~380px, above the fold), followed
  by Live Preview, then Touch Mode. Re-verified: setting 50% yields
  computed opacity 0.5 on `.deck-button`; vitest 175/175.
