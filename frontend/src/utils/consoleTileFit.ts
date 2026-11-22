/**
 * DL-166 layout: column count and row height for the phone agent console's tile grid.
 * Picks the layout that fits every tile with the biggest readable tile; when nothing
 * fits, it scrolls with rows sized to fill the box exactly (the grid snaps per row).
 */
export interface TileFit { cols: number; rowH: number; tileW: number }

export const FIT_GAP = 8
/** Tiles stop growing at this width: a lone tile is a tile, not a full-width banner. */
export const MAX_TILE_W = 200
const MIN_W = 84
const MIN_H = 44 // the touch-target floor
const MAX_H = 92

export function fitTiles(n: number, W: number, H: number): TileFit {
  let best: { cols: number; rowH: number; score: number } | null = null
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols)
    const tw = (W - FIT_GAP * (cols - 1)) / cols
    const th = (H - FIT_GAP * (rows - 1)) / rows
    if (tw < MIN_W || th < MIN_H) continue
    const score = Math.min(tw, 170) * Math.min(th, MAX_H)
    // Ties (both sizes capped) go to more columns: two tiles side by side, not two stacked bars.
    if (!best || score >= best.score) best = { cols, rowH: Math.min(th, MAX_H), score }
  }
  if (!best) {
    // Cannot fit: most columns that keep the minimum width; rows sized so the box holds whole
    // rows, so with the per-row scroll snap a resting scroll never shows a half-cut row.
    const cols = Math.max(1, Math.min(n, Math.floor((W + FIT_GAP) / (MIN_W + FIT_GAP))))
    const rows = Math.max(1, Math.floor((H + FIT_GAP) / (MIN_H + FIT_GAP)))
    best = { cols, rowH: Math.max(MIN_H, (H - FIT_GAP * (rows - 1)) / rows), score: 0 }
  }
  const tileW = Math.min(MAX_TILE_W, (W - FIT_GAP * (best.cols - 1)) / best.cols)
  return { cols: best.cols, rowH: Math.floor(best.rowH), tileW: Math.floor(tileW) }
}
