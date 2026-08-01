// Preset registry — combined registry, category lookup, and keyword/name match.
// See design.md, section "1. Preset registry".
//
// API design (read this before extending in tasks 3.2 / 3.3 / 3.6):
//
// - `presetRegistry: ButtonPreset[]` is the single combined registry array. It starts
//   empty in this file. `apps.ts` (task 3.3) and `system.ts` (task 3.2) each export
//   their own `ButtonPreset[]` array (e.g. `export const appPresets: ButtonPreset[]`,
//   `export const systemPresets: ButtonPreset[]`). Once those files exist, import them
//   here and concatenate into `presetRegistry`, e.g.:
//
//     import { appPresets } from './apps'
//     import { systemPresets } from './system'
//     export const presetRegistry: ButtonPreset[] = [...appPresets, ...systemPresets]
//
//   This keeps each category's data in its own file while giving every consumer
//   (QuickAddPicker, useButtonActions, presetToButton, tests) one array to work with.
//
// - `getPresetsByCategory` and `findPresetsByKeyword` are pure functions that take a
//   registry as an explicit parameter. This keeps them trivially testable (Property 1,
//   Property 2) without depending on module-level mutable state, and lets callers pass
//   a filtered/derived registry if ever needed. Call them as
//   `getPresetsByCategory(presetRegistry, 'ai')` using the exported `presetRegistry`
//   for normal app usage.
//
// - `presetToButton(preset, position)` (task 3.6) will be added to this file, deriving
//   a `Button` from a `ButtonPreset`. Not implemented yet — out of scope for task 3.1.

import type { Button, ButtonAction, ButtonEffect, ButtonPosition } from '@/types'
import type { ButtonPreset, PresetCategory } from './types'
import { appPresets } from './apps'
import { systemPresets } from './system'

/**
 * The combined preset registry. Populated by concatenating the per-category arrays
 * exported from `./apps` (task 3.3) and `./system` (task 3.2).
 */
export const presetRegistry: ButtonPreset[] = [...appPresets, ...systemPresets]

/**
 * Returns every preset in `registry` whose `category` matches `category`.
 */
export function getPresetsByCategory(
  registry: ButtonPreset[],
  category: PresetCategory
): ButtonPreset[] {
  return registry.filter((preset) => preset.category === category)
}

/**
 * Returns every preset in `registry` matching `query` (case-insensitive), matching
 * against `preset.name` (substring match) or any element of `preset.keywords`
 * (substring match). An empty/whitespace-only query matches nothing.
 */
export function findPresetsByKeyword(registry: ButtonPreset[], query: string): ButtonPreset[] {
  const normalized = query.trim().toLowerCase()
  if (!normalized) {
    return []
  }

  return registry.filter((preset) => {
    if (preset.name.toLowerCase().includes(normalized)) {
      return true
    }
    return (preset.keywords ?? []).some((keyword) => keyword.toLowerCase().includes(normalized))
  })
}

export type { ButtonPreset, PresetCategory, EffectType, IconLoop } from './types'

/**
 * Derives a fully-configured `Button` from a registered `ButtonPreset`, placed at
 * `position`. See design.md, section "1. Preset registry", function contract for
 * `presetToButton(preset, position)`.
 *
 * SCOPE NOTE (task 3.6 / Requirements 1.7): the design document's function contract
 * describes the result in terms of `layers.icon` / `layers.effect.tint` — the
 * `ButtonLayers` model that lands in task 5.1 (Phase 3). That type does not exist on
 * `Button` yet, so this function currently returns a `Button` built from the
 * EXISTING fields (`icon` / `icon_type`, `style.effect` / `style.glowColor`), using
 * the same brand-tint convention introduced in task 1.3 (`--btn-brand` /
 * `resolveBrandTint`). This achieves the same visual outcome — a brand-tinted
 * effect with the correct icon — without inventing a throwaway `layers` shape. Once
 * task 5.1 lands `ButtonLayers`, this function should be upgraded to populate
 * `layers.icon` / `layers.effect.tint` directly (task 9.3 depends on this function
 * for `QuickAddPicker`, and must work correctly before task 5.1 exists).
 *
 * Preconditions: `preset` is a registered entry from the preset index; `position`
 * is a valid, currently-empty grid cell.
 *
 * Postconditions: returns a `Button` with a freshly generated `id`, an icon derived
 * from `preset.icon`, a brand-tinted effect derived from `preset.brand` (unless the
 * preset defines its own tint via `brand.glow`), and `action` copied from
 * `preset.action`. Does not mutate `preset` or any registry entry.
 */
export function presetToButton(preset: ButtonPreset, position: ButtonPosition): Button {
  // --- Icon resolution -------------------------------------------------------
  // Mirrors the `icon` / `icon_type` fields DeckButton.vue already knows how to
  // render (see DeckButton.vue's `button.icon_type` branches). `logo` presets are
  // rendered as an <img> (`icon_type: 'custom'`); `fontawesome` presets decode the
  // `'prefix:iconName'` string convention (documented in system.ts/apps.ts) back
  // into the `[prefix, iconName]` tuple DeckButton.vue's FontAwesome branch expects.
  let icon: string | string[]
  let iconType: 'fontawesome' | 'material' | 'custom'

  if (preset.icon.type === 'logo') {
    iconType = 'custom'
    icon = preset.icon.value
  } else if (preset.icon.type === 'fontawesome') {
    iconType = 'fontawesome'
    // 'fas:power-off' -> ['fas', 'power-off']; construct a new array so the preset's
    // string is never referenced (and can't be mutated) by the returned Button.
    icon = preset.icon.value.split(':')
  } else {
    // 'gif' | 'lottie' — not yet supported by DeckButton.vue's rendering. Best-effort
    // fallback: treat the value as a custom icon path. This is a placeholder until a
    // later phase adds a dedicated GIF/Lottie icon layer (see design.md "Button layer
    // model", IconType).
    iconType = 'custom'
    icon = preset.icon.value
  }

  // --- Brand tint resolution --------------------------------------------------
  // `ButtonPreset` has no separate tint-override field beyond `brand.primary` /
  // `brand.glow`; per the design doc's "unless the preset defines its own tint"
  // clause, `brand.glow` (when present) is treated as that override, falling back
  // to `brand.primary` otherwise. This matches the `--btn-brand` / glowColor
  // convention from task 1.3/1.4.
  const glowColor = preset.brand.glow ?? preset.brand.primary

  const layers = {
    fill: { type: 'solid' as const, value: 'var(--color-surface)' },
    effect: preset.effect ? { type: preset.effect, tint: glowColor } : undefined,
    icon: {
      type: preset.icon.type,
      value: icon,
      loop: preset.icon.loop ?? 'none'
    },
    label: { text: preset.name }
  }

  return {
    id: `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    label: preset.name,
    icon,
    icon_type: iconType,
    shape: 'rounded',
    position: { row: position.row, col: position.col },
    size: { rows: 1, cols: 1 },
    style: {
      // preset.effect uses the broader Phase-3 EffectType (adds fire/plasma/etc, not
      // yet implemented as CSS classes per task 5.5); only forward it when it maps
      // onto the currently-supported ButtonEffect union, else leave style.effect
      // unset so DeckButton.vue falls back to its existing default rendering.
      ...(preset.effect && isKnownButtonEffect(preset.effect)
        ? { effect: preset.effect as ButtonEffect }
        : {}),
      glowColor
    },
    layers,
    // Shallow-copy action and its config so later edits to the returned Button (or
    // its action.config) can never mutate the registry entry's `preset.action`.
    action: { ...preset.action, config: { ...preset.action.config } } as ButtonAction,
    enabled: true
  }
}

/**
 * Narrows the broader preset `EffectType` down to the subset already implemented
 * as `ButtonEffect` CSS classes. Presets referencing not-yet-implemented Phase 3
 * effects (fire, plasma, particles, aurora, scanline, rain) fall back to no effect
 * rather than producing an invalid `style.effect` value.
 */
function isKnownButtonEffect(effect: string): effect is ButtonEffect {
  return (
    effect === 'none' ||
    effect === 'glass' ||
    effect === 'neumorphism' ||
    effect === 'gradient' ||
    effect === 'glow' ||
    effect === '3d'
  )
}
