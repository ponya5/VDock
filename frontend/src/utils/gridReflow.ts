import type { Button, Page } from '@/types'

/**
 * DL-147 - runtime portrait reflow of a landscape-authored page.
 *
 * A 3x6 deck folded into a portrait phone would be 56px slivers, and per-class
 * saved layouts were rejected (data-model change). Instead the pane re-packs
 * the enabled buttons into fewer columns for display only: reading order is
 * kept, nothing is saved, edit mode keeps showing the authored grid.
 */
export interface ReflowOptions {
  /** Size of the pane the grid fills, in CSS px. */
  width: number
  height: number
  /** Smallest comfortable cell edge; below it the pane scrolls vertically. */
  minCell: number
  /** False in edit mode or when the device prefers the authored layout. */
  enabled: boolean
}

export interface ReflowResult {
  page: Page
  reflowed: boolean
  /** Reflow only ever scrolls vertically, never sideways. */
  scroll: 'none' | 'y'
  /** Cell edge used for icon scaling (and the fixed row height when scrolling). */
  cellPx: number
}

const MIN_REFLOW_COLS = 2

function unchanged(page: Page): ReflowResult {
  return { page, reflowed: false, scroll: 'none', cellPx: 0 }
}

/** First-fit packing in reading order; every placement is at or after the previous one. */
function pack(buttons: Button[], cols: number): { placed: Button[]; rows: number } {
  const taken = new Set<number>()
  const fits = (row: number, col: number, rowSpan: number, colSpan: number) => {
    if (col + colSpan > cols) return false
    for (let r = row; r < row + rowSpan; r++) {
      for (let c = col; c < col + colSpan; c++) if (taken.has(r * cols + c)) return false
    }
    return true
  }

  const ordered = [...buttons].sort(
    (a, b) => a.position.row - b.position.row || a.position.col - b.position.col,
  )
  let cursor = 0
  let rows = 1
  const placed = ordered.map((button) => {
    const colSpan = Math.min(button.size.cols, cols)
    const rowSpan = button.size.rows
    while (!fits(Math.floor(cursor / cols), cursor % cols, rowSpan, colSpan)) cursor++
    const row = Math.floor(cursor / cols)
    const col = cursor % cols
    for (let r = row; r < row + rowSpan; r++) {
      for (let c = col; c < col + colSpan; c++) taken.add(r * cols + c)
    }
    rows = Math.max(rows, row + rowSpan)
    return { ...button, position: { row, col }, size: { rows: rowSpan, cols: colSpan } }
  })
  return { placed, rows }
}

export function reflowPage(page: Page, options: ReflowOptions): ReflowResult {
  const { rows: authoredRows, cols: authoredCols } = page.grid_config
  const { width, height, minCell } = options
  const portrait = width > 0 && height > width
  if (!options.enabled || !portrait || authoredCols <= authoredRows) return unchanged(page)

  const cols = Math.min(authoredCols, Math.max(MIN_REFLOW_COLS, authoredRows))
  const { placed, rows } = pack(page.buttons.filter((b) => b.enabled), cols)

  const fitCell = Math.min(width / cols, height / rows)
  const scrolls = height / rows < minCell
  return {
    page: { ...page, grid_config: { rows, cols }, buttons: placed },
    reflowed: true,
    scroll: scrolls ? 'y' : 'none',
    cellPx: scrolls ? minCell : Math.floor(fitCell),
  }
}
