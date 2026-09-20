import { describe, test, expect } from 'vitest'
import {
  BACKGROUNDS,
  resolveBackground,
  isImageBackground,
} from '../data/backgrounds'

describe('background catalog', () => {
  test('ids are unique', () => {
    const ids = BACKGROUNDS.map(b => b.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  test('every component-kind entry carries a component', () => {
    for (const bg of BACKGROUNDS.filter(b => b.kind === 'component')) {
      expect(bg.component, `${bg.id} has no component`).toBeTruthy()
    }
  })

  test('every css-kind entry carries no component', () => {
    for (const bg of BACKGROUNDS.filter(b => b.kind === 'css')) {
      expect(bg.component).toBeUndefined()
    }
  })

  test('resolveBackground returns the matching entry', () => {
    expect(resolveBackground('aurora').id).toBe('aurora')
    expect(resolveBackground('ocean-breeze').kind).toBe('css')
  })

  test('an unknown id falls back to default rather than rendering nothing', () => {
    expect(resolveBackground('does-not-exist').id).toBe('default')
  })

  test('image URLs resolve to kind image', () => {
    expect(isImageBackground('/api/uploads/bg.png')).toBe(true)
    expect(isImageBackground('/uploads/bg.png')).toBe(true)
    expect(isImageBackground('https://example.com/bg.png')).toBe(true)
    expect(isImageBackground('aurora')).toBe(false)
    expect(resolveBackground('/api/uploads/bg.png').kind).toBe('image')
  })

  test('catalog contains both duplicate pairs, distinctly labelled', () => {
    const ids = BACKGROUNDS.map(b => b.id)
    expect(ids).toContain('particles')
    expect(ids).toContain('floating-particles')
    expect(ids).toContain('aurora')
    expect(ids).toContain('aurora-borealis')
    const labels = BACKGROUNDS.map(b => b.label)
    expect(new Set(labels).size).toBe(labels.length)
  })
})
