import { test, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeckOverlay from '../components/DeckOverlay.vue'
import type { Button } from '@/types'

test('Feature: vdock-ui-redesign, Property 13: Ambient overlay per-key offset matches grid geometry', async () => {
  const rows = 3
  const cols = 5
  const buttons: Button[] = [
    {
      id: 'btn-1',
      label: 'Button 1',
      shape: 'rectangle',
      position: { row: 1, col: 2 },
      size: { rows: 1, cols: 1 },
      enabled: true
    }
  ]

  const wrapper = mount(DeckOverlay, {
    props: {
      active: true,
      style: 'aurora',
      mode: 'keys',
      rows,
      cols,
      buttons
    }
  })

  // Set reactive size variables in JSDOM
  const vm = wrapper.vm as any
  vm.gridWidth = 1000
  vm.gridHeight = 600

  await wrapper.vm.$nextTick()

  const cellInner = wrapper.find('.ambient-overlay-inner')
  expect(cellInner.exists()).toBe(true)

  const styleAttr = cellInner.attributes('style')
  expect(styleAttr).toBeDefined()

  // Calculate expected offsets
  const paddingTotal = 32
  const gapSize = 4
  const contentWidth = 1000 - paddingTotal
  const contentHeight = 600 - paddingTotal
  const cellW = (contentWidth - (cols - 1) * gapSize) / cols
  const cellH = (contentHeight - (rows - 1) * gapSize) / rows
  const expectedOffsetX = -2 * (cellW + gapSize) - 16
  const expectedOffsetY = -1 * (cellH + gapSize) - 16

  expect(styleAttr).toContain(`transform: translate(${expectedOffsetX}px, ${expectedOffsetY}px);`)
})
