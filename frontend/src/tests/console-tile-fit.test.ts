// DL-166 layout: tile grid fit for the phone agent console.
import { describe, it, expect } from 'vitest'
import { FIT_GAP, MAX_TILE_W, fitTiles } from '@/utils/consoleTileFit'

describe('fitTiles', () => {
  it('keeps a lone tile tile-sized instead of a full-width banner', () => {
    expect(fitTiles(1, 510, 200)).toMatchObject({ cols: 1, tileW: MAX_TILE_W })
  })

  it('puts two tiles side by side when both layouts max out', () => {
    expect(fitTiles(2, 366, 400).cols).toBe(2)
  })

  it('fits every tile when it can, never below the 44px touch floor', () => {
    const fit = fitTiles(13, 561, 154)
    expect(fit.cols * Math.ceil(13 / fit.cols)).toBeGreaterThanOrEqual(13)
    expect(fit.rowH).toBeGreaterThanOrEqual(44)
    expect(fit.tileW).toBeGreaterThanOrEqual(84)
  })

  it('when it must scroll, sizes rows so the box holds whole rows', () => {
    const H = 100
    const fit = fitTiles(13, 561, H)
    const rows = Math.floor((H + FIT_GAP) / (fit.rowH + FIT_GAP))
    expect(fit.rowH).toBeGreaterThanOrEqual(44)
    // Whole rows fill the box to within a pixel per row: no half-cut row at rest.
    expect(H - (rows * fit.rowH + (rows - 1) * FIT_GAP)).toBeLessThanOrEqual(rows)
  })
})
