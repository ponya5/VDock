import type { Button, Page, Profile } from '@/types'

/**
 * DL-167 - hand-authored portrait layout.
 *
 * A page keeps its landscape placement in `grid_config` / `button.position` /
 * `button.size` and its portrait placement in `portrait_grid` / `button.portrait`.
 * Edit mode in portrait swaps the two in memory (`swapOrientation`), so every
 * existing edit path works unchanged; saving swaps back first (see the dashboard store).
 */

/**
 * Make `page` fully placed in its "other" orientation: seed the grid and any unplaced enabled button
 * (reading order, first fit). `fold` is true when the other grid is portrait and unseeded (same fold as the
 * auto reflow); false in the portrait edit view, where the other grid is landscape and mirrors the current one.
 */
export function ensurePortrait(page: Page, fold = true): void {
  const { rows: lRows, cols: lCols } = page.grid_config
  // Same fold as the DL-147 auto reflow, so the first portrait edit starts from what the phone shows today.
  const cols = page.portrait_grid?.cols ?? (fold && lCols > lRows ? Math.min(lCols, Math.max(2, lRows)) : lCols)
  // An empty page keeps the landscape capacity so there is room to build; a populated one starts tight.
  const empty = !page.buttons.some((b) => b.enabled)
  let rows = page.portrait_grid?.rows ?? (empty ? Math.ceil((lRows * lCols) / cols) : 1)

  const taken = new Set<number>()
  const mark = (b: Button) => {
    const p = b.portrait!
    for (let r = p.position.row; r < p.position.row + p.size.rows; r++) {
      for (let c = p.position.col; c < p.position.col + p.size.cols; c++) taken.add(r * cols + c)
    }
    rows = Math.max(rows, p.position.row + p.size.rows)
  }
  page.buttons.forEach((b) => { if (b.enabled && b.portrait) mark(b) })

  const fits = (row: number, col: number, rs: number, cs: number) => {
    if (col + cs > cols) return false
    for (let r = row; r < row + rs; r++) for (let c = col; c < col + cs; c++) if (taken.has(r * cols + c)) return false
    return true
  }
  const unplaced = page.buttons
    .filter((b) => !b.portrait)
    .sort((a, b) => a.position.row - b.position.row || a.position.col - b.position.col)
  for (const b of unplaced) {
    if (!b.enabled) { // disabled keys occupy no cell; keep a copy so the swap stays symmetric
      b.portrait = { position: { ...b.position }, size: { ...b.size } }
      continue
    }
    const size = { rows: b.size.rows, cols: Math.min(b.size.cols, cols) }
    let i = 0
    while (!fits(Math.floor(i / cols), i % cols, size.rows, size.cols)) i++
    b.portrait = { position: { row: Math.floor(i / cols), col: i % cols }, size }
    mark(b)
  }
  page.portrait_grid = { rows, cols }
}

/** Exchange landscape and portrait placement of one page in place (self-inverse). Needs `ensurePortrait` first. */
function swapPage(page: Page): void {
  if (!page.portrait_grid) return
  ;[page.grid_config, page.portrait_grid] = [page.portrait_grid, page.grid_config]
  for (const b of page.buttons) {
    if (!b.portrait) continue
    ;[b.position, b.portrait.position] = [b.portrait.position, b.position]
    ;[b.size, b.portrait.size] = [b.portrait.size, b.size]
  }
}

/** Swap every page of every scene (the whole profile is shown in one orientation at a time). */
export function swapOrientation(profile: Profile, toPortrait: boolean): void {
  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      ensurePortrait(page, toPortrait)
      swapPage(page)
    }
  }
}

/** Remove portrait data from the given pages (undoes an unmodified "peek" so it is never persisted). */
export function stripPortrait(profile: Profile, pageIds: Set<string>): void {
  for (const scene of profile.scenes) {
    for (const page of scene.pages) {
      if (!pageIds.has(page.id)) continue
      delete page.portrait_grid
      for (const b of page.buttons) delete b.portrait
    }
  }
}

/** Read-only portrait view of a page for rendering; the page itself when it has no authored portrait layout. */
export function projectPortrait(page: Page): Page {
  if (!page.portrait_grid) return page
  const copy: Page = JSON.parse(JSON.stringify(page))
  ensurePortrait(copy)
  swapPage(copy)
  return copy
}
