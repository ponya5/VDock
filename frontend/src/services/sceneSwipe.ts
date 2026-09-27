import { reactive } from 'vue'

/**
 * DL-082 — live state of a horizontal scene-switch swipe, shared between
 * the gesture source (DashboardView's .main-content useSwipe) and the
 * scene rails (GlassPillSceneSelector / MobileDeckChrome), so the active
 * scene's segment can dissolve 1:1 under the finger before the switch
 * commits.
 *
 * `dir` is the scene-order direction the swipe targets: 'next' for a
 * leftward finger (advance), 'prev' for rightward. `progress` is 0..1 of
 * the commit threshold and intentionally stays at its release value after
 * `dragging` clears — the rails read it in their (post-flush) index
 * watcher so the committed sweep can resume from where the finger left
 * off instead of restarting.
 */
export const sceneSwipe = reactive({
  dragging: false,
  dir: 'next' as 'next' | 'prev',
  progress: 0,
  /** Set by the commit path for exactly one index-watcher read. */
  justSwiped: false,
})
