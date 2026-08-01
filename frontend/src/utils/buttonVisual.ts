import type { Button, ButtonLayers, IconType, IconLoop, BehaviourType, EffectType } from '@/types'
import { presetRegistry } from '@/data/presets'
import { resolveBrandTint } from './brandTint'

export interface ResolvedVisual {
  fill: {
    type: 'none' | 'solid' | 'gradient' | 'tint' | 'image' | 'video'
    value?: string
  }
  effect: {
    type: EffectType | 'none'
    tint: string | undefined
    intensity: number
  }
  icon: {
    type: IconType | 'none'
    value: string | string[]
    loop: IconLoop | 'none'
    size?: number
  }
  label: {
    text: string
    secondary: string
  }
}

/**
 * Resolves the brand tint colour for a button.
 * Resolves with the following precedence:
 * 1. layers.effect.tint (if set to a valid colour, i.e. not 'brand')
 * 2. The owning preset's brand.primary (if the button action id matches a preset)
 * 3. The legacy style.glowColor
 * 4. undefined (signalling to fall back to the CSS-defined default)
 */
export function resolveButtonBrandTint(button: Button): string | undefined {
  if (button.layers?.effect?.tint && button.layers.effect.tint !== 'brand') {
    return resolveBrandTint(button.layers.effect.tint)
  }

  // Fallback to preset brand if layers.effect.tint is 'brand' or unset
  const presetId = button.action?.id
  if (presetId) {
    const preset = presetRegistry.find((p) => p.id === presetId)
    if (preset?.brand?.primary) {
      return resolveBrandTint(preset.brand.primary)
    }
  }

  if (button.style?.glowColor) {
    return resolveBrandTint(button.style.glowColor)
  }

  return undefined
}

/**
 * Resolves a button record (which may or may not have layers) into a complete ResolvedVisual structure.
 * Guaranteed to never return undefined for any of the four slots.
 */
export function resolveButtonVisual(button: Button): ResolvedVisual {
  // --- Fill Layer ---
  let fillType: 'none' | 'solid' | 'gradient' | 'tint' | 'image' | 'video' = 'none'
  let fillValue: string | undefined = undefined

  if (button.layers?.fill) {
    fillType = button.layers.fill.type ?? 'none'
    fillValue = button.layers.fill.value
  } else {
    // Legacy fallbacks
    if (button.media_url && button.media_type === 'video') {
      fillType = 'video'
      fillValue = button.media_url
    } else if (button.media_url && (button.media_type === 'image' || button.media_type === 'gif')) {
      fillType = 'image'
      fillValue = button.media_url
    } else if (button.style?.gradient && button.style?.effect === 'gradient') {
      fillType = 'gradient'
      fillValue = button.style.gradient
    } else if (button.style?.backgroundColor) {
      fillType = 'solid'
      fillValue = button.style.backgroundColor
    }
  }

  // --- Effect Layer ---
  let effectType: EffectType | 'none' = 'none'
  let effectTint: string | undefined = undefined
  let effectIntensity = 1.0

  if (button.layers?.effect) {
    effectType = button.layers.effect.type ?? 'none'
    effectTint = button.layers.effect.tint === 'brand' ? resolveButtonBrandTint(button) : resolveBrandTint(button.layers.effect.tint)
    effectIntensity = button.layers.effect.intensity ?? 1.0
  } else if (button.style?.effect) {
    effectType = button.style.effect
    effectTint = resolveButtonBrandTint(button)
  }

  // --- Icon Layer ---
  let iconType: IconType | 'none' = 'none'
  let iconValue: string | string[] = ''
  let iconLoop: IconLoop | 'none' = 'none'
  let iconSize: number | undefined = undefined

  if (button.layers?.icon) {
    iconType = button.layers.icon.type ?? 'none'
    iconValue = button.layers.icon.value ?? ''
    iconLoop = button.layers.icon.loop ?? 'none'
    iconSize = button.layers.icon.size
  } else {
    // Legacy fallbacks
    if (button.icon_type) {
      iconType = button.icon_type
    } else if (button.icon) {
      iconType = 'custom'
    }

    if (button.icon) {
      iconValue = button.icon
    }
    iconSize = button.style?.iconSize
  }

  // --- Label Layer ---
  let labelText = ''
  let labelSecondary = ''

  if (button.layers?.label) {
    labelText = button.layers.label.text ?? ''
    labelSecondary = button.layers.label.secondary ?? ''
  } else {
    // Legacy fallbacks
    labelText = button.label ?? ''
    labelSecondary = button.secondary_label ?? ''
  }

  return {
    fill: {
      type: fillType,
      value: fillValue
    },
    effect: {
      type: effectType,
      tint: effectTint,
      intensity: effectIntensity
    },
    icon: {
      type: iconType,
      value: iconValue,
      loop: iconLoop,
      size: iconSize
    },
    label: {
      text: labelText,
      secondary: labelSecondary
    }
  }
}
