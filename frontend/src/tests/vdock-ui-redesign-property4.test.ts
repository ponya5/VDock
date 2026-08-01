import { test, expect } from 'vitest'
import fc from 'fast-check'
import type { Button, ButtonLayers, ButtonShape, ButtonSize, ButtonStyle } from '@/types'
import { resolveButtonVisual } from '../utils/buttonVisual'

test('Feature: vdock-ui-redesign, Property 4: Visual resolution is total and respects layer-over-legacy precedence', () => {
  const layersArb = fc.record({
    fill: fc.option(fc.record({
      type: fc.constantFrom('none', 'solid', 'gradient', 'tint', 'image', 'video'),
      value: fc.option(fc.string())
    }), { nil: undefined }),
    effect: fc.option(fc.record({
      type: fc.constantFrom('none', 'glass', 'neumorphism', 'gradient', 'glow', '3d', 'fire', 'plasma', 'particles', 'aurora', 'scanline', 'rain'),
      tint: fc.constantFrom('brand', '#ff0000', 'blue'),
      intensity: fc.option(fc.double({ min: 0, max: 1 }))
    }), { nil: undefined }),
    icon: fc.option(fc.record({
      type: fc.constantFrom('logo', 'fontawesome', 'gif', 'lottie'),
      value: fc.string(),
      loop: fc.option(fc.constantFrom('squash', 'bob', 'spin', 'pulse', 'swing', 'flip', 'jump'), { nil: undefined }),
      size: fc.option(fc.nat())
    }), { nil: undefined }),
    label: fc.option(fc.record({
      text: fc.string(),
      secondary: fc.option(fc.string())
    }), { nil: undefined }),
    behaviour: fc.option(fc.constantFrom('none', 'pulse', 'float', 'breathe', 'tilt'), { nil: undefined })
  }, { requiredKeys: [] })

  const styleArb = fc.record({
    backgroundColor: fc.option(fc.string()),
    gradient: fc.option(fc.string()),
    effect: fc.option(fc.constantFrom('none', 'glass', 'neumorphism', 'gradient', 'glow', '3d')),
    glowColor: fc.option(fc.string()),
    iconSize: fc.option(fc.nat())
  }, { requiredKeys: [] })

  const buttonArb = fc.record({
    id: fc.string(),
    label: fc.option(fc.string()),
    secondary_label: fc.option(fc.string()),
    icon: fc.option(fc.oneof(fc.string(), fc.array(fc.string()))),
    icon_type: fc.option(fc.constantFrom('fontawesome', 'material', 'custom')),
    media_url: fc.option(fc.string()),
    media_type: fc.option(fc.constantFrom('video', 'gif', 'image')),
    shape: fc.constantFrom('rectangle', 'rounded', 'circle') as fc.Arbitrary<ButtonShape>,
    position: fc.record({ row: fc.nat(), col: fc.nat() }),
    size: fc.record({ rows: fc.constant(1), cols: fc.constant(1) }) as fc.Arbitrary<ButtonSize>,
    style: fc.option(styleArb),
    layers: fc.option(layersArb),
    enabled: fc.boolean()
  })

  fc.assert(
    fc.property(buttonArb, (button) => {
      const visual = resolveButtonVisual(button)

      // --- Total resolution checks ---
      expect(visual).toBeDefined()
      expect(visual.fill).toBeDefined()
      expect(visual.fill.type).toBeDefined()
      expect(visual.effect).toBeDefined()
      expect(visual.effect.type).toBeDefined()
      expect(visual.icon).toBeDefined()
      expect(visual.icon.type).toBeDefined()
      expect(visual.label).toBeDefined()
      expect(visual.label.text).toBeDefined()
      expect(visual.label.secondary).toBeDefined()

      // --- Label Precedence ---
      if (button.layers?.label != null) {
        expect(visual.label.text).toBe(button.layers.label.text ?? '')
        expect(visual.label.secondary).toBe(button.layers.label.secondary ?? '')
      } else {
        expect(visual.label.text).toBe(button.label ?? '')
        expect(visual.label.secondary).toBe(button.secondary_label ?? '')
      }

      // --- Icon Precedence ---
      if (button.layers?.icon != null) {
        expect(visual.icon.type).toBe(button.layers.icon.type ?? 'none')
        expect(visual.icon.value).toBe(button.layers.icon.value ?? '')
        expect(visual.icon.loop).toBe(button.layers.icon.loop ?? 'none')
        expect(visual.icon.size).toBe(button.layers.icon.size)
      } else {
        if (button.icon_type) {
          expect(visual.icon.type).toBe(button.icon_type)
        } else if (button.icon) {
          expect(visual.icon.type).toBe('custom')
        } else {
          expect(visual.icon.type).toBe('none')
        }
        
        if (button.icon) {
          expect(visual.icon.value).toEqual(button.icon)
        } else {
          expect(visual.icon.value).toBe('')
        }
        
        if (button.style?.iconSize != null) {
          expect(visual.icon.size).toBe(button.style.iconSize)
        }
        expect(visual.icon.loop).toBe('none')
      }

      // --- Effect Precedence ---
      if (button.layers?.effect != null) {
        expect(visual.effect.type).toBe(button.layers.effect.type ?? 'none')
        expect(visual.effect.intensity).toBe(button.layers.effect.intensity ?? 1.0)
      } else if (button.style?.effect != null) {
        expect(visual.effect.type).toBe(button.style.effect)
        expect(visual.effect.intensity).toBe(1.0)
      } else {
        expect(visual.effect.type).toBe('none')
        expect(visual.effect.intensity).toBe(1.0)
      }

      // --- Fill Precedence ---
      if (button.layers?.fill != null) {
        expect(visual.fill.type).toBe(button.layers.fill.type ?? 'none')
        expect(visual.fill.value).toBe(button.layers.fill.value)
      } else {
        if (button.media_url && button.media_type === 'video') {
          expect(visual.fill.type).toBe('video')
          expect(visual.fill.value).toBe(button.media_url)
        } else if (button.media_url && (button.media_type === 'image' || button.media_type === 'gif')) {
          expect(visual.fill.type).toBe('image')
          expect(visual.fill.value).toBe(button.media_url)
        } else if (button.style?.gradient && button.style?.effect === 'gradient') {
          expect(visual.fill.type).toBe('gradient')
          expect(visual.fill.value).toBe(button.style.gradient)
        } else if (button.style?.backgroundColor) {
          expect(visual.fill.type).toBe('solid')
          expect(visual.fill.value).toBe(button.style.backgroundColor)
        } else {
          expect(visual.fill.type).toBe('none')
          expect(visual.fill.value).toBeUndefined()
        }
      }
    }),
    { numRuns: 100 }
  )
})
