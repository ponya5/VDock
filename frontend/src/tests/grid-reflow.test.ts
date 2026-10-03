// DL-147 Task 2.1 - portrait reflow of a landscape-authored page: a pure
// function, pinned by examples and fast-check properties.
import { describe, it, expect } from 'vitest'
import fc from 'fast-check'
import { reflowPage } from '@/utils/gridReflow'
import type { Button, Page } from '@/types'

function btn(id: string, row: number, col: number, rows = 1, cols = 1, enabled = true): Button {
  return {
    id,
    label: id,
    shape: 'rounded',
    position: { row, col },
    size: { rows, cols },
    enabled,
  } as Button
}

function page(rows: number, cols: number, buttons: Button[]): Page {
  return { id: 'p', name: 'p', grid_config: { rows, cols }, buttons }
}

const PORTRAIT = { width: 390, height: 780, minCell: 72, enabled: true }

function layout(result: ReturnType<typeof reflowPage>) {
  return result.page.buttons.map((b) => `${b.id}@${b.position.row},${b.position.col}:${b.size.rows}x${b.size.cols}`)
}

describe('reflowPage examples', () => {
  it('folds a 3x6 media page into 3 columns, keeping reading order and spans', () => {
    const buttons = [
      btn('a', 0, 0), btn('b', 0, 1), btn('c', 0, 2, 1, 2),
      btn('d', 1, 0), btn('e', 1, 1, 1, 2), btn('f', 1, 3),
      btn('g', 2, 0), btn('h', 2, 5),
    ]
    const result = reflowPage(page(3, 6, buttons), PORTRAIT)
    expect(result.reflowed).toBe(true)
    expect(result.page.grid_config.cols).toBe(3)
    expect(layout(result)).toEqual([
      'a@0,0:1x1', 'b@0,1:1x1',
      'c@1,0:1x2', 'd@1,2:1x1',
      'e@2,0:1x2', 'f@2,2:1x1',
      'g@3,0:1x1', 'h@3,1:1x1',
    ])
    expect(result.page.grid_config.rows).toBe(4)
  })

  it('folds a 2x4 page into 2 columns', () => {
    const result = reflowPage(page(2, 4, [btn('a', 0, 0), btn('b', 0, 3), btn('c', 1, 1), btn('d', 1, 2)]), PORTRAIT)
    expect(result.page.grid_config).toEqual({ rows: 2, cols: 2 })
    expect(layout(result)).toEqual(['a@0,0:1x1', 'b@0,1:1x1', 'c@1,0:1x1', 'd@1,1:1x1'])
  })

  it('keeps a full-width slider full-width', () => {
    const result = reflowPage(page(3, 6, [btn('s', 0, 0, 1, 3), btn('a', 0, 3)]), PORTRAIT)
    expect(layout(result)).toEqual(['s@0,0:1x3', 'a@1,0:1x1'])
  })

  it('clamps a span wider than the new column count', () => {
    const result = reflowPage(page(3, 6, [btn('w', 0, 0, 1, 6)]), PORTRAIT)
    expect(result.page.buttons[0].size).toEqual({ rows: 1, cols: 3 })
  })

  it('keeps a tall key tall and packs later keys around it', () => {
    const result = reflowPage(page(3, 6, [btn('t', 0, 0, 2, 1), btn('a', 0, 1), btn('b', 0, 2), btn('c', 0, 3)]), PORTRAIT)
    expect(layout(result)).toEqual(['t@0,0:2x1', 'a@0,1:1x1', 'b@0,2:1x1', 'c@1,1:1x1'])
  })

  it('drops disabled buttons and compacts empty authored cells', () => {
    const result = reflowPage(page(3, 6, [btn('a', 0, 0), btn('x', 0, 1, 1, 1, false), btn('b', 2, 5)]), PORTRAIT)
    expect(layout(result)).toEqual(['a@0,0:1x1', 'b@0,1:1x1'])
  })

  it('never mutates the input page', () => {
    const input = page(3, 6, [btn('a', 0, 5), btn('b', 2, 0)])
    const snapshot = JSON.stringify(input)
    reflowPage(input, PORTRAIT)
    expect(JSON.stringify(input)).toBe(snapshot)
  })

  it('stretch-fills the pane when the cells stay above the minimum', () => {
    const result = reflowPage(page(3, 6, [btn('a', 0, 0), btn('b', 0, 1), btn('c', 0, 2), btn('d', 1, 0)]), PORTRAIT)
    expect(result.scroll).toBe('none')
    expect(result.cellPx).toBeGreaterThanOrEqual(72)
  })

  it('scrolls vertically when the rows would fall below the minimum cell', () => {
    const buttons = Array.from({ length: 30 }, (_, i) => btn(`k${i}`, Math.floor(i / 6) % 3, i % 6))
    const result = reflowPage(page(3, 6, buttons), { ...PORTRAIT, height: 500 })
    expect(result.scroll).toBe('y')
    expect(result.cellPx).toBe(72)
  })
})

describe('reflowPage is not applicable', () => {
  const landscapeAuthored = page(3, 6, [btn('a', 0, 5)])

  it('returns the same object in a landscape viewport', () => {
    const result = reflowPage(landscapeAuthored, { ...PORTRAIT, width: 844, height: 390 })
    expect(result.page).toBe(landscapeAuthored)
    expect(result.reflowed).toBe(false)
    expect(result.scroll).toBe('none')
  })

  it('returns the same object when the grid is not wider than tall', () => {
    const tall = page(4, 3, [btn('a', 0, 2)])
    expect(reflowPage(tall, PORTRAIT).page).toBe(tall)
    const square = page(3, 3, [btn('a', 0, 2)])
    expect(reflowPage(square, PORTRAIT).page).toBe(square)
  })

  it('returns the same object when reflow is disabled (edit mode / designed layout)', () => {
    expect(reflowPage(landscapeAuthored, { ...PORTRAIT, enabled: false }).page).toBe(landscapeAuthored)
  })

  it('returns the same object before the pane has a size', () => {
    expect(reflowPage(landscapeAuthored, { ...PORTRAIT, width: 0, height: 0 }).page).toBe(landscapeAuthored)
  })
})

describe('reflowPage properties', () => {
  const buttonArb = (rows: number, cols: number) =>
    fc.record({
      row: fc.integer({ min: 0, max: rows - 1 }),
      col: fc.integer({ min: 0, max: cols - 1 }),
      r: fc.integer({ min: 1, max: 2 }),
      c: fc.integer({ min: 1, max: cols }),
      enabled: fc.boolean(),
    })

  const pageArb = fc
    .record({ rows: fc.integer({ min: 2, max: 5 }), extra: fc.integer({ min: 1, max: 5 }) })
    .chain(({ rows, extra }) => {
      const cols = rows + extra
      return fc.record({
        rows: fc.constant(rows),
        cols: fc.constant(cols),
        items: fc.array(buttonArb(rows, cols), { minLength: 0, maxLength: 30 }),
      })
    })
    .map(({ rows, cols, items }) =>
      page(rows, cols, items.map((b, i) => btn(`b${i}`, b.row, b.col, b.r, b.c, b.enabled))),
    )

  const sizeArb = fc.record({
    width: fc.integer({ min: 280, max: 500 }),
    height: fc.integer({ min: 501, max: 1000 }),
    minCell: fc.constantFrom(72, 96),
  })

  it('places every enabled button exactly once, without overlap, in reading order', () => {
    fc.assert(
      fc.property(pageArb, sizeArb, (input, size) => {
        const { page: out, reflowed } = reflowPage(input, { ...size, enabled: true })
        expect(reflowed).toBe(true)
        const enabled = input.buttons.filter((b) => b.enabled)
        expect(out.buttons.map((b) => b.id).sort()).toEqual(enabled.map((b) => b.id).sort())

        const authoredOrder = [...enabled]
          .sort((a, b) => a.position.row - b.position.row || a.position.col - b.position.col)
          .map((b) => b.id)
        const cols = out.grid_config.cols
        const placedOrder = [...out.buttons]
          .sort((a, b) => a.position.row * cols + a.position.col - (b.position.row * cols + b.position.col))
          .map((b) => b.id)
        expect(placedOrder).toEqual(authoredOrder)

        const taken = new Set<string>()
        for (const b of out.buttons) {
          for (let r = b.position.row; r < b.position.row + b.size.rows; r++) {
            for (let c = b.position.col; c < b.position.col + b.size.cols; c++) {
              const key = `${r}-${c}`
              expect(taken.has(key)).toBe(false)
              taken.add(key)
            }
          }
        }
      }),
      { numRuns: 200 },
    )
  })

  it('keeps columns in [2, cols], spans inside the grid and never scrolls sideways', () => {
    fc.assert(
      fc.property(pageArb, sizeArb, (input, size) => {
        const { page: out, scroll, cellPx } = reflowPage(input, { ...size, enabled: true })
        expect(out.grid_config.cols).toBeGreaterThanOrEqual(2)
        expect(out.grid_config.cols).toBeLessThanOrEqual(input.grid_config.cols)
        for (const b of out.buttons) {
          expect(b.position.col + b.size.cols).toBeLessThanOrEqual(out.grid_config.cols)
          expect(b.position.row + b.size.rows).toBeLessThanOrEqual(out.grid_config.rows)
        }
        expect(scroll === 'none' || scroll === 'y').toBe(true)
        if (scroll === 'none') expect(out.grid_config.rows * cellPx).toBeLessThanOrEqual(size.height)
        else expect(cellPx).toBe(size.minCell)
      }),
      { numRuns: 200 },
    )
  })
})
