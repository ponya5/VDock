# DL-019 — Rich button card styles (Buttons-Rich mockup)

## Background

User supplied a second Claude-generated mockup (`Buttons-Rich.dc.html`,
saved under `design-log/refs/`) with four richer deck-button card styles,
each shown across four brand tints plus a pressed state:

- **Glow glass** — dark glass card, brand glow pooling at the bottom edge,
  brand blob behind the icon tile.
- **Gem** — saturated brand-gradient jewel card, domed gloss cap, giant
  ghost watermark glyph bleeding off the bottom-right corner.
- **Neon rim** — dark scanline card, glowing brand outline, brand wash
  rising from the bottom edge, neon-ringed icon tile.
- **Watermark card** — dark glass, brand light source low-left, giant
  ghost glyph top-right, left-aligned editorial layout.

## Design

Implemented as four new `EffectType` values — `glowglass`, `gem`,
`neonrim`, `watermark` — reusing the existing effect pipeline end-to-end:

- `types/index.ts`: `EffectType` widened; `ButtonStyle.effect` retyped
  `ButtonEffect` → `EffectType` so the per-button editor can store them.
- `DeckButton.vue`: four class bindings; new `buttonStyle` branch returns
  `baseStyle + color` only (classes own background/border/shadow); root
  gets `:data-mark="watermarkGlyph"` (label initial, `•` fallback) feeding
  `content: attr(data-mark)` on `::before` — `::after` stays the ripple.
- `assets/styles/main.css`: the four `.deck-button-*` classes appended
  after `.deck-button-rain`, brand-parametric via `color-mix()` +
  `var(--btn-brand)` (same convention as property 7; `!important` to beat
  scoped base styles, matching every other effect class). Pressed state
  reuses the base `:active` scale(0.96) plus stronger inset shadow.
- Selects: `SettingsView` preview picker and `ButtonEditor` Visual
  Effects picker both gained the four options; the editor also gained the
  six previously-implemented-but-unselectable effects
  (fire/plasma/particles/aurora/scanline/rain).

## Implementation results

- `vue-tsc --noEmit` clean; vitest 49 files / 175 tests pass.
- Live on `localhost:4445`: all four classes render on real buttons —
  Gem shows the saturated brand gradient + ghost glyph, Neon Rim the
  glowing outline + ringed icon tile, Watermark the left-aligned layout +
  ghost glyph, Glow Glass the pooled bottom glow.
- Pick per-button in the Button Editor (Visual Effects) or apply to all
  buttons via Settings → Appearance → Button Behaviour → Visual effect.
