import { test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeckOverlay from '../components/DeckOverlay.vue'

test('Feature: vdock-ui-redesign, Property 14: Overlay ripple originates at the tap point', async () => {
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

  // Mock getBoundingClientRect on container element
  wrapper.element.getBoundingClientRect = () => ({
    left: 10,
    top: 20,
    width: 1000,
    height: 600,
    right: 1010,
    bottom: 620,
    x: 10,
    y: 20,
    toJSON: () => {}
  })

  // Trigger tap event
  await wrapper.trigger('mousedown', {
    clientX: 150,
    clientY: 220
  })

  const ripple = wrapper.find('.tap-ripple')
  expect(ripple.exists()).toBe(true)

  const styleAttr = ripple.attributes('style')
  expect(styleAttr).toBeDefined()
  expect(styleAttr).toContain('left: 140px;')
  expect(styleAttr).toContain('top: 200px;')
})
