import { describe, it, expect } from 'vitest'
import { firstFreeSlot } from '@/composables/useAppShortcutScenes'
import { starterPresetIds } from '@/data/appStarterActions'
import { presetRegistry } from '@/data/presets'
import type { Page } from '@/types'

const page = (buttons: Array<{ row: number; col: number; rows?: number; cols?: number }>): Page => ({
  id: 'p', name: 'p', grid_config: { rows: 2, cols: 3 },
  buttons: buttons.map((b, i) => ({
    id: `b${i}`, position: { row: b.row, col: b.col }, size: { rows: b.rows ?? 1, cols: b.cols ?? 1 },
  })),
} as unknown as Page)

describe('app scene placement', () => {
  it('skips cells covered by wide buttons and fits wide ones', () => {
    const p = page([{ row: 0, col: 0, cols: 2 }])
    expect(firstFreeSlot(p)).toEqual({ row: 0, col: 2 })
    expect(firstFreeSlot(p, { rows: 1, cols: 2 })).toEqual({ row: 1, col: 0 })
  })
  it('returns null when the page is full', () => {
    expect(firstFreeSlot(page([{ row: 0, col: 0, rows: 2, cols: 3 }]))).toBeNull()
  })
  it('starter presets exist, matched on Windows and macOS process names', () => {
    for (const exe of ['Spotify.exe', 'spotify']) {
      const ids = starterPresetIds(exe)
      expect(ids.length).toBeGreaterThan(0)
      for (const id of ids) expect(presetRegistry.some(p => p.id === id), id).toBe(true)
    }
    expect(starterPresetIds('unknown.exe')).toEqual([])
  })
})
