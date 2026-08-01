import { test, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DeckOverlay from '../components/DeckOverlay.vue'
import { useGridTransition } from '../composables/useGridTransition'

test('Feature: vdock-ui-redesign, Property 9: Reduced motion disables every animation layer', async () => {
  // Mock window.matchMedia to simulate prefers-reduced-motion: reduce
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: query.includes('reduce'),
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }))

  // 1. Verify Ambient Overlay is disabled (does not render)
  const wrapper = mount(DeckOverlay, {
    props: {
      active: true,
      style: 'aurora',
      mode: 'keys',
      rows: 3,
      cols: 5,
      buttons: []
    }
  })

  expect(wrapper.find('.ambient-overlay-container').exists()).toBe(false)

  // 2. Verify Grid Transition reduces to plain fade with no staggering
  const { cellClasses, triggerTransition } = useGridTransition()
  const swapPage = vi.fn()

  const promise = triggerTransition(3, 5, 'by-column', 'light-bar', swapPage)

  // Wait a small timeout to let the first step run
  await new Promise(resolve => setTimeout(resolve, 50))
  
  // All cell classes should be 'grid-transition-dissolve' under reduced motion
  expect(cellClasses.value['0-0']).toBe('grid-transition-dissolve')
  expect(cellClasses.value['1-1']).toBe('grid-transition-dissolve')

  await promise
})
