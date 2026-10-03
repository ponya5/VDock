// DL-147 Task 1.5 - one rule decides "stacked deck column" + sidebar shape.
// Before: the dashboard CSS stacked at <=768px while DockedSidebar switched to
// its strip at <768px, so a 768px-wide tablet got a full-height sidebar column
// inside a stacked layout and a 0px-tall deck.
import { describe, it, expect } from 'vitest'
import { dashboardLayout } from '@/utils/dashboardLayout'
import type { DeviceClass, Orientation } from '@/composables/useDeviceClass'

const layout = (
  layoutClass: DeviceClass,
  orientation: Orientation,
  innerWidth: number,
  compactTouch = false,
) => dashboardLayout({ layoutClass, orientation, innerWidth, compactTouch })

describe('dashboardLayout', () => {
  it('phones render no sidebar and never stack', () => {
    expect(layout('phone', 'portrait', 390, true)).toEqual({ stacked: false, sidebar: 'hidden' })
    expect(layout('phone', 'landscape', 844, true)).toEqual({ stacked: false, sidebar: 'hidden' })
  })

  it.each([744, 768, 800, 820, 834, 1024])(
    'tablet portrait %d wide stacks with a strip sidebar',
    (width) => {
      expect(layout('tablet', 'portrait', width)).toEqual({ stacked: true, sidebar: 'strip' })
    },
  )

  it.each([1024, 1133, 1180, 1280, 1366])('tablet landscape %d wide keeps the column', (width) => {
    expect(layout('tablet', 'landscape', width)).toEqual({ stacked: false, sidebar: 'column' })
  })

  it('the stacked flag and the strip sidebar can never disagree', () => {
    const classes: DeviceClass[] = ['phone', 'tablet', 'panel', 'desktop']
    for (const cls of classes) {
      for (const orientation of ['portrait', 'landscape'] as Orientation[]) {
        for (let width = 300; width <= 1500; width += 12) {
          const result = layout(cls, orientation, width)
          if (result.sidebar !== 'hidden') {
            expect(result.stacked).toBe(result.sidebar === 'strip')
          }
        }
      }
    }
  })

  // Desktop / panel oracle: the pre-DL-147 DockedSidebar rule (`innerWidth < 768`
  // is the strip). Exactly 768 was the one disagreeing width: the CSS stacked
  // (<=768) while the sidebar stayed a column. Both now follow the sidebar.
  describe.each<DeviceClass>(['desktop', 'panel'])('%s', (cls) => {
    it.each([480, 600, 767, 769, 1024, 1440])('%d wide matches the old sidebar rule', (width) => {
      const expectStrip = width < 768
      expect(layout(cls, 'landscape', width)).toEqual({
        stacked: expectStrip,
        sidebar: expectStrip ? 'strip' : 'column',
      })
    })

    it('768 wide is a column, not a stacked layout with a column sidebar', () => {
      expect(layout(cls, 'landscape', 768)).toEqual({ stacked: false, sidebar: 'column' })
    })

    it('a compact-touch panel keeps its hidden sidebar', () => {
      expect(layout(cls, 'landscape', 1024, true)).toEqual({ stacked: false, sidebar: 'hidden' })
    })
  })
})
