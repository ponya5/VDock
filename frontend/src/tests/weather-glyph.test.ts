// DL-136 — the animated weather glyph maps WMO code + is_day to the
// right SVG scene: sun with orbiting rays by day, spinning moon at
// night, sun/moon+cloud for partly cloudy, rain/snow/fog/storm scenes,
// a wind overlay, and a dimmed cloud when the reading is unavailable.
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WeatherGlyph from '@/components/screensaver/WeatherGlyph.vue'

describe('WeatherGlyph (DL-136)', () => {
  it('shows the sun with orbiting rays on a clear day', () => {
    const w = mount(WeatherGlyph, { props: { code: 0, isDay: true } })
    expect(w.find('.wg-sun-rays').exists()).toBe(true)
    expect(w.find('.wg-sun-rays').findAll('line')).toHaveLength(8)
    expect(w.find('.wg-moon-spin').exists()).toBe(false)
  })

  it('shows the spinning moon + stars on a clear night', () => {
    const w = mount(WeatherGlyph, { props: { code: 0, isDay: false } })
    expect(w.find('.wg-moon-spin').exists()).toBe(true)
    expect(w.findAll('.wg-star')).toHaveLength(3)
    expect(w.find('.wg-sun-rays').exists()).toBe(false)
  })

  it('draws a real crescent: the inner arc is flatter than the chord allows to collapse', () => {
    // Regression: with an inner radius <= half the chord the two arcs
    // coincide, the moon has zero area and only the stars are visible.
    for (const props of [{ code: 0, isDay: false }, { code: 2, isDay: false }]) {
      const body = mount(WeatherGlyph, { props }).find('.wg-moon-body')
      expect(body.exists()).toBe(true)
      const d = body.attributes('d')!
      const arcs = [...d.matchAll(/a\s*([\d.]+)\s+[\d.]+\s+0\s+(\d)\s+(\d)\s+(-?[\d.]+)\s+(-?[\d.]+)/g)]
      expect(arcs).toHaveLength(2)
      const [outer, inner] = arcs
      const chord = Math.abs(Number(outer[5]))
      expect(Number(inner[1])).toBeGreaterThan(chord / 2 + 0.5) // genuine bulge
      expect(Number(inner[1])).toBeGreaterThan(Number(outer[1])) // flatter than the outer arc
    }
  })

  it('shows sun+cloud when partly cloudy by day, moon+cloud at night', () => {
    const day = mount(WeatherGlyph, { props: { code: 2, isDay: true } })
    expect(day.find('.wg-sun-rays.small').exists()).toBe(true)
    expect(day.find('.wg-cloud-fg').exists()).toBe(true)
    const night = mount(WeatherGlyph, { props: { code: 2, isDay: false } })
    expect(night.find('.wg-moon-spin.small').exists()).toBe(true)
    expect(night.find('.wg-cloud-fg').exists()).toBe(true)
  })

  it('shows falling rain lines for rain codes', () => {
    for (const code of [61, 63, 65, 80, 81, 82]) {
      const w = mount(WeatherGlyph, { props: { code, isDay: true } })
      expect(w.find('.wg-rain').exists(), `code ${code}`).toBe(true)
      expect(w.find('.wg-rain').findAll('line').length).toBeGreaterThanOrEqual(3)
    }
  })

  it('shows sparse drops for drizzle', () => {
    const w = mount(WeatherGlyph, { props: { code: 51, isDay: true } })
    expect(w.find('.wg-rain').findAll('line')).toHaveLength(2)
  })

  it('shows snowflakes for snow codes', () => {
    for (const code of [71, 73, 75, 77, 85, 86]) {
      const w = mount(WeatherGlyph, { props: { code, isDay: true } })
      expect(w.find('.wg-snow').exists(), `code ${code}`).toBe(true)
    }
  })

  it('shows a flashing bolt for thunderstorms', () => {
    const w = mount(WeatherGlyph, { props: { code: 95, isDay: true } })
    expect(w.find('.wg-bolt').exists()).toBe(true)
    expect(w.find('.wg-cloud-storm').exists()).toBe(true)
  })

  it('shows drifting mist lines for fog', () => {
    const w = mount(WeatherGlyph, { props: { code: 45, isDay: true } })
    expect(w.find('.wg-fog-lines').findAll('rect')).toHaveLength(3)
  })

  it('overlays wind streaks on any scene when windy', () => {
    const calm = mount(WeatherGlyph, { props: { code: 0, isDay: true, windy: false } })
    expect(calm.find('.wg-wind').exists()).toBe(false)
    const gusty = mount(WeatherGlyph, { props: { code: 0, isDay: true, windy: true } })
    expect(gusty.find('.wg-wind').exists()).toBe(true)
    expect(gusty.find('.wg-sun-rays').exists()).toBe(true) // wind rides over sun
  })

  it('renders a dimmed plain cloud when unavailable', () => {
    const w = mount(WeatherGlyph, { props: { unavailable: true, code: 0 } })
    expect(w.find('.weather-glyph').classes()).toContain('is-dim')
    expect(w.find('.wg-sun-rays').exists()).toBe(false)
    expect(w.find('.wg-cloud-fg').exists()).toBe(true)
  })
})
