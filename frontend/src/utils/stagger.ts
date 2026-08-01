export type StaggerOrder = 'by-column' | 'by-row' | 'diagonal' | 'random' | 'none'

/**
 * Computes a stagger order permutation of the grid cells.
 * Returns an array containing every cell index [0, rows*cols) exactly once.
 */
export function computeStaggerOrder(rows: number, cols: number, order: StaggerOrder): number[] {
  const n = rows * cols
  const indices = Array.from({ length: n }, (_, i) => i)

  if (order === 'none') {
    return indices
  }

  const scores = new Map<number, number>()

  if (order === 'random') {
    // Deterministic pseudo-random scores for stability
    for (let i = 0; i < n; i++) {
      const rand = ((1103515245 * i + 12345) % 2147483648) / 2147483648
      scores.set(i, rand)
    }
  } else {
    for (let i = 0; i < n; i++) {
      const r = Math.floor(i / cols)
      const c = i % cols
      let score = 0
      if (order === 'by-row') {
        score = r * 1000 + c
      } else if (order === 'by-column') {
        score = c * 1000 + r
      } else if (order === 'diagonal') {
        score = (r + c) * 1000 + c
      }
      scores.set(i, score)
    }
  }

  return indices.sort((a, b) => (scores.get(a) || 0) - (scores.get(b) || 0))
}
