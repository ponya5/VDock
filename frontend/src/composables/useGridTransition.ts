import { ref } from 'vue'
import { computeStaggerOrder } from '../utils/stagger'
import type { StaggerOrder } from '../utils/stagger'

export type TransitionStyle = 'light-bar' | 'flip' | 'iris' | 'cascade' | 'glitch' | 'dissolve'

type PendingTransition = {
  rows: number
  cols: number
  order: StaggerOrder
  style: TransitionStyle
  onPageSwap: () => Promise<void> | void
}

export function useGridTransition() {
  const cellClasses = ref<Record<string, string>>({})
  const isTransitioning = ref(false)

  // When a switch request comes in while one is already playing (e.g. tapping
  // through scene tabs quickly), it used to be dropped outright — onPageSwap
  // never ran, so the grid stayed stuck showing whichever scene the in-flight
  // transition was for even though the store had already moved on. Queue the
  // latest request instead and replay it in full once the current one ends.
  let pending: PendingTransition | null = null

  const triggerTransition = async (
    rows: number,
    cols: number,
    order: StaggerOrder,
    style: TransitionStyle,
    onPageSwap: () => Promise<void> | void
  ) => {
    if (isTransitioning.value) {
      pending = { rows, cols, order, style, onPageSwap }
      return
    }
    isTransitioning.value = true

    const isReduced = typeof window !== 'undefined' && 
      window.matchMedia && 
      window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Step 1: Out transition
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        cellClasses.value[`${r}-${c}`] = isReduced ? 'grid-transition-dissolve' : 'grid-transition-out'
      }
    }

    // Wait for out transition (220ms)
    await new Promise(resolve => setTimeout(resolve, 220))

    // Swap the page content
    await onPageSwap()

    // If reduced motion, just fade in immediately
    if (isReduced) {
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          cellClasses.value[`${r}-${c}`] = 'grid-transition-dissolve'
        }
      }
      await new Promise(resolve => setTimeout(resolve, 340))
      cellClasses.value = {}
      finishAndRunPending()
      return
    }

    // Step 2: Staggered sweep & in transitions
    const staggerOrder = computeStaggerOrder(rows, cols, order)
    const staggerDelay = 50 // ms delay between cells

    const promises: Promise<void>[] = []

    staggerOrder.forEach((cellIdx, seqIdx) => {
      const r = Math.floor(cellIdx / cols)
      const c = cellIdx % cols
      const key = `${r}-${c}`

      cellClasses.value[key] = ''

      // Sweep effect
      const sweepPromise = new Promise<void>(resolve => {
        setTimeout(() => {
          if (style === 'light-bar') {
            cellClasses.value[key] = 'grid-transition-sweep'
          }
          resolve()
        }, seqIdx * staggerDelay)
      })
      promises.push(sweepPromise)

      // In transition (180ms after sweep)
      const inPromise = new Promise<void>(resolve => {
        setTimeout(() => {
          let inClass = 'grid-transition-in'
          if (style === 'flip') inClass = 'grid-transition-flip'
          else if (style === 'iris') inClass = 'grid-transition-iris'
          else if (style === 'cascade') inClass = 'grid-transition-cascade'
          else if (style === 'glitch') inClass = 'grid-transition-glitch'
          else if (style === 'dissolve') inClass = 'grid-transition-dissolve'

          cellClasses.value[key] = inClass

          setTimeout(() => {
            if (cellClasses.value[key] === inClass) {
              delete cellClasses.value[key]
            }
          }, 650)

          resolve()
        }, seqIdx * staggerDelay + 180)
      })
      promises.push(inPromise)
    })

    await Promise.all(promises)
    await new Promise(resolve => setTimeout(resolve, 650))
    cellClasses.value = {}
    finishAndRunPending()
  }

  const finishAndRunPending = () => {
    isTransitioning.value = false
    if (pending) {
      const next = pending
      pending = null
      void triggerTransition(next.rows, next.cols, next.order, next.style, next.onPageSwap)
    }
  }

  return {
    cellClasses,
    isTransitioning,
    triggerTransition
  }
}
