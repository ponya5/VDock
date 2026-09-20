import { describe, test, expect } from 'vitest'
import { backgroundClassFor, backgroundStyleFor } from '../utils/backgroundStyle'

describe('background precedence: page > scene > global', () => {
  test('a page background wins over scene and global', () => {
    const style = backgroundStyleFor(
      'aurora',
      { image: '/uploads/scene.png' },
      { type: 'solid', color: '#ff0000' },
    )
    expect(style.backgroundColor).toBe('#ff0000')
  })

  test('a scene image wins over global when no page background', () => {
    const style = backgroundStyleFor('aurora', { image: '/uploads/scene.png' })
    expect(style.backgroundImage).toBe('url(/uploads/scene.png)')
  })

  test('a component background contributes no class or style', () => {
    expect(backgroundClassFor('aurora')).toBe('')
    expect(backgroundStyleFor('aurora')).toEqual({})
  })

  test('a css background yields its dashboard-bg class', () => {
    expect(backgroundClassFor('ocean-breeze')).toBe('dashboard-bg-ocean-breeze')
  })

  test('default yields no class', () => {
    expect(backgroundClassFor('default')).toBe('')
  })

  test('an uploaded image yields dashboard-bg-custom and an inline url', () => {
    expect(backgroundClassFor('/api/uploads/bg.png')).toBe('dashboard-bg-custom')
    expect(backgroundStyleFor('/api/uploads/bg.png').backgroundImage)
      .toBe('url(/api/uploads/bg.png)')
  })

  test('a page gradient renders as a linear-gradient', () => {
    const style = backgroundStyleFor('default', undefined, {
      type: 'gradient',
      gradient: { direction: '90deg', from: '#000', to: '#fff' },
    })
    expect(style.background).toBe('linear-gradient(90deg, #000, #fff)')
  })
})
