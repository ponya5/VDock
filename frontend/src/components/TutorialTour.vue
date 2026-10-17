<template>
  <Teleport to="body">
    <div v-if="tour.state.active" class="tour-overlay">
      <!-- Plain dim when the step has no target element -->
      <div v-if="!targetRect" class="tour-dim" aria-hidden="true"></div>
      <!-- Spotlight ring over the current target -->
      <div
        v-if="targetRect"
        class="tour-spotlight"
        :style="spotlightStyle"
        aria-hidden="true"
      ></div>

      <!-- Bubble -->
      <div
        ref="bubbleEl"
        class="tour-bubble"
        :class="`arrow-${arrowSide}`"
        :style="bubbleStyle"
        role="dialog"
        aria-live="polite"
      >
        <div class="tour-bubble-head">
          <span class="tour-step-count">{{ tour.state.stepIndex + 1 }} / {{ steps.length }}</span>
          <button class="tour-close" @click="tour.finish" aria-label="Close tutorial">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>
        <h3 class="tour-title">{{ step.title }}</h3>
        <p class="tour-text">{{ step.text }}</p>
        <div v-if="step.kind === 'apps'" class="tour-apps" role="group" aria-label="Apps you use">
          <span class="tour-app included"><FontAwesomeIcon :icon="['fas', 'circle-check']" /> Media <small>included</small></span>
          <button
            v-for="app in TUTORIAL_APPS"
            :key="app.id"
            type="button"
            class="tour-app"
            :class="{ on: tour.state.picked.includes(app.id) }"
            :aria-pressed="tour.state.picked.includes(app.id)"
            @click="tour.togglePicked(app.id)"
          >
            <FontAwesomeIcon :icon="app.icon" /> {{ app.label }}
          </button>
        </div>
        <div class="tour-actions">
          <button class="tour-btn ghost" data-testid="tour-skip" @click="tour.finish">Skip tour</button>
          <span class="tour-spacer"></span>
          <button v-if="!tour.isFirst.value" class="tour-btn ghost" @click="tour.back">Back</button>
          <button class="tour-btn primary" @click="tour.next">{{ nextLabel }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useTutorial, TUTORIAL_STEPS } from '@/services/tutorial'
import { TUTORIAL_APPS } from '@/data/tutorialApps'
import { useSettingsStore } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import { useMobileViewport } from '@/utils/mobileViewport'
import { loadProfileMaps, sceneAppProfile } from '@/services/appDetection'
import { useAppIntegrations } from '@/composables/useAppIntegrations'

const tour = useTutorial()
const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const appIntegrations = useAppIntegrations()
const { isMobileViewport } = useMobileViewport()
const router = useRouter()
const route = useRoute()
const steps = TUTORIAL_STEPS
const step = computed(() => tour.currentStep.value)
const nextLabel = computed(() => {
  if (tour.isLast.value) return 'Done'
  if (step.value?.kind === 'apps') {
    const n = tour.state.picked.length
    return n ? `Add ${n} & continue` : 'Continue'
  }
  return tour.isFirst.value ? 'Start' : 'Next'
})
const bubbleEl = ref<HTMLElement | null>(null)
const targetRect = ref<DOMRect | null>(null)
const bubbleSize = ref({ w: 420, h: 240 })
const viewport = ref({ w: window.innerWidth, h: window.innerHeight })

const PAD = 10
const BUBBLE_GAP = 14

/** First visible match for the selector — comma fallbacks can resolve a
    hidden variant before the real one (e.g. desktop nav vs mobile rail). */
function firstVisible(sel: string): Element | null {
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect()
    if (r.width > 0 || r.height > 0) return el
  }
  return document.querySelector(sel)
}

function measure() {
  viewport.value = { w: window.innerWidth, h: window.innerHeight }
  const sel = step.value?.target
  const el = sel ? firstVisible(sel) : null
  const r = el?.getBoundingClientRect()
  targetRect.value = r && (r.width > 0 || r.height > 0) ? r : null
  if (bubbleEl.value) {
    const b = bubbleEl.value.getBoundingClientRect()
    bubbleSize.value = { w: b.width, h: b.height }
  }
}

/** Poll for a selector to appear (view mounts async after a route push).
    Uses firstVisible so comma fallbacks resolve the rendered variant. */
function waitForEl(sel: string, timeout = 2500): Promise<Element | null> {
  return new Promise((resolve) => {
    const t0 = performance.now()
    const tick = () => {
      const el = firstVisible(sel)
      if (el || performance.now() - t0 > timeout) resolve(el)
      else setTimeout(tick, 60)
    }
    tick()
  })
}

let prepareToken = 0
/* DL-131 F/U2: steps whose targets live in DeckHeader need the header
   revealed first — it's unmounted by default and would re-hide after the
   5 s autohide otherwise. We reveal via the store (the reveal FAB hides
   in edit mode) and pin the countdown pill so the target can't vanish
   mid-step. Only a reveal *we* did gets restored — when the tour leaves
   '/' or ends, a user-hidden header goes back to hidden. */
let headerRevealedByTour = false
let headerPinnedByTour = false
/* The agent bar mounts only on agent-backed scenes — step 6 switches to
   one so it has something real to spotlight. Restored like the header,
   but only while the user hasn't moved off that scene themselves
   (clicks pass through the tour overlay). */
let sceneSwitchFrom: number | null = null
let sceneSwitchTo: number | null = null

function restoreDashboardState() {
  if (headerRevealedByTour) {
    settingsStore.showHeader = false
    headerRevealedByTour = false
  } else if (headerPinnedByTour) {
    // The header was already visible — resume the countdown we paused.
    // Unmounted already (route left '/')? The query no-ops and the next
    // mount starts with a fresh unpinned countdown.
    document.querySelector('.autohide-pill.pinned')
      ?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  }
  headerPinnedByTour = false
  if (sceneSwitchTo !== null) {
    if (sceneSwitchFrom !== null && dashboardStore.currentSceneIndex === sceneSwitchTo) {
      dashboardStore.setScene(sceneSwitchFrom)
    }
    sceneSwitchFrom = null
    sceneSwitchTo = null
  }
}

/** Get the view into the state the step needs, then measure the target. */
async function prepareStep() {
  const token = ++prepareToken
  const s = step.value
  if (!tour.state.active || !s) return
  if (s.route && route.path !== s.route) {
    await router.push(s.route)
    await nextTick()
  }
  if (token !== prepareToken) return
  // Put the header back as soon as a step no longer needs it, not only when leaving '/'.
  if (s.route !== '/' || !s.needsHeader) restoreDashboardState()
  // On mobile the header would *replace* the mobile chrome we're meant
  // to spotlight (.mc-scene-rail) — skip the reveal, the rail is already
  // mounted and the edit button genuinely doesn't exist there.
  if (s.needsHeader && !isMobileViewport.value) {
    if (!settingsStore.showHeader) {
      settingsStore.showHeader = true
      headerRevealedByTour = true
    }
    // Pause the autohide countdown — :not(.pinned) makes the click a no-op
    // when the user already keeps the header pinned open.
    const pin = await waitForEl('.autohide-pill:not(.pinned)', 1500)
    if (pin) {
      pin.dispatchEvent(new MouseEvent('click', { bubbles: true }))
      headerPinnedByTour = true
    }
  }
  if (token !== prepareToken) return
  if (s.needsAgentScene) {
    // The bar renders only while the active scene maps to an agent
    // profile — same state_actions gate DashboardView uses. Already on
    // one? Leave it; otherwise hop to the first agent scene and mark it
    // for restore (only if the user hasn't moved scenes themselves).
    await loadProfileMaps()
    const scenes = dashboardStore.currentProfile?.scenes ?? []
    const agentIdx = scenes.findIndex(
      (sc) => sceneAppProfile(sc, appIntegrations.value)?.state_actions
    )
    if (agentIdx >= 0 && agentIdx !== dashboardStore.currentSceneIndex) {
      sceneSwitchFrom = dashboardStore.currentSceneIndex
      sceneSwitchTo = agentIdx
      dashboardStore.setScene(agentIdx)
      await nextTick()
    }
  }
  if (token !== prepareToken) return
  if (s.activate) {
    const el = await waitForEl(s.activate)
    if (el) el.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await nextTick()
  }
  if (token !== prepareToken) return
  if (s.target) {
    const el = await waitForEl(s.target)
    // Conditional UI (agent bar, hidden header, mobile chrome swaps) may
    // be absent or zero-sized — a missing target renders as a centered
    // card. The tour NEVER advances on its own: only Next/Back/Skip.
    const box = el?.getBoundingClientRect()
    if (!el || !box || (box.width === 0 && box.height === 0)) targetRect.value = null
  }
  if (token !== prepareToken) return
  measure()
  // Re-measure once more after the bubble settles at its new spot
  requestAnimationFrame(measure)
}

watch(() => tour.state.stepIndex, prepareStep)
watch(() => tour.state.active, (active) => {
  if (active) {
    prepareStep()
    // Keep the ring honest while a step is open: the target can slide
    // away (header auto-hide), unmount (chrome swaps), or arrive late —
    // none of those fire resize/scroll. ~3×/s re-measure follows the box
    // (including transform-driven moves) and drops to a centered card if
    // the target vanishes, instead of leaving a stale ring floating over
    // whatever slid underneath.
    startReanchor()
  } else {
    stopReanchor()
    restoreDashboardState()
  }
})
// The user (or a Back step) may change routes mid-tour — re-anchor onto
// whatever the step's target resolves to on the new screen.
watch(() => route.path, () => {
  if (!tour.state.active) return
  prepareStep()
})

let reanchorTimer: ReturnType<typeof setInterval> | null = null
function startReanchor() {
  stopReanchor()
  reanchorTimer = setInterval(() => {
    if (!tour.state.active) return
    if (bubbleEl.value) {
      const b = bubbleEl.value.getBoundingClientRect()
      if (b.width !== bubbleSize.value.w || b.height !== bubbleSize.value.h) bubbleSize.value = { w: b.width, h: b.height }
    }
    viewport.value = { w: window.innerWidth, h: window.innerHeight }
    const sel = step.value?.target
    if (!sel) { targetRect.value = null; return }
    const el = firstVisible(sel)
    const r = el?.getBoundingClientRect()
    targetRect.value = r && (r.width > 0 || r.height > 0) ? r : null
  }, 350)
}
function stopReanchor() {
  if (reanchorTimer) { clearInterval(reanchorTimer); reanchorTimer = null }
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && tour.state.active) tour.finish()
}

onMounted(() => {
  measure()
  window.addEventListener('keydown', onKey)
  window.addEventListener('resize', measure)
  window.addEventListener('scroll', measure, true)
})
onUnmounted(() => {
  stopReanchor()
  window.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', measure)
  window.removeEventListener('scroll', measure, true)
})

const spotlightStyle = computed(() => {
  const r = targetRect.value
  if (!r) return {}
  // Clamp to the screen so a target taller or wider than the viewport still
  // shows a ring (and the dim cut-out) instead of one that runs off-screen.
  const { w: vw, h: vh } = viewport.value
  const top = Math.max(4, r.top - PAD)
  const left = Math.max(4, r.left - PAD)
  const bottom = Math.min(vh - 4, r.bottom + PAD)
  const right = Math.min(vw - 4, r.right + PAD)
  return {
    top: `${top}px`,
    left: `${left}px`,
    width: `${Math.max(0, right - left)}px`,
    height: `${Math.max(0, bottom - top)}px`,
  }
})

/** Where the bubble ends up; also which side the arrow should render on. */
const placement = computed<{ side: 'top' | 'bottom' | 'left' | 'right' | 'none' }>(() => {
  const r = targetRect.value
  if (!r) return { side: 'none' }
  const bw = bubbleSize.value.w
  const bh = bubbleSize.value.h
  const pref = step.value?.placement || 'bottom'
  const narrow = viewport.value.w < 600
  const room = {
    top: r.top - PAD - BUBBLE_GAP,
    bottom: viewport.value.h - r.bottom - PAD - BUBBLE_GAP,
    left: r.left - PAD - BUBBLE_GAP,
    right: viewport.value.w - r.right - PAD - BUBBLE_GAP,
  }
  const fits = {
    top: room.top - bh > 8,
    bottom: room.bottom - bh > 8,
    left: room.left - bw > 8,
    right: room.right - bw > 8,
  }
  const order: Array<'top' | 'bottom' | 'left' | 'right'> =
    narrow ? ['bottom', 'top'] : [pref, 'bottom', 'top', 'right', 'left']
  const preferred = narrow && (pref === 'left' || pref === 'right') ? 'bottom' : pref
  if (fits[preferred]) return { side: preferred }
  const found = order.find((sd) => fits[sd])
  if (found) return { side: found }
  // Nothing fits (tall target, small screen): take the side with the most room;
  // the bubble is clamped on-screen and scrolls if it must.
  const sides = (narrow ? ['bottom', 'top'] : ['bottom', 'top', 'right', 'left']) as Array<'top' | 'bottom' | 'left' | 'right'>
  return { side: sides.sort((x, y) => room[y] - room[x])[0] }
})

const arrowSide = computed(() => placement.value.side)

const bubbleStyle = computed(() => {
  const r = targetRect.value
  const bw = bubbleSize.value.w
  const bh = bubbleSize.value.h
  const { w: vw, h: vh } = viewport.value

  // Centered card when there is no target
  if (!r) {
    return {
      top: `${Math.max(8, (vh - bh) / 2)}px`,
      left: `${Math.max(8, (vw - bw) / 2)}px`,
    }
  }

  const cx = r.left + r.width / 2
  const cy = r.top + r.height / 2
  let top = 0
  let left = 0
  switch (placement.value.side) {
    case 'bottom':
      top = r.bottom + PAD + BUBBLE_GAP
      left = cx - bw / 2
      break
    case 'top':
      top = r.top - PAD - BUBBLE_GAP - bh
      left = cx - bw / 2
      break
    case 'right':
      left = r.right + PAD + BUBBLE_GAP
      top = cy - bh / 2
      break
    case 'left':
      left = r.left - PAD - BUBBLE_GAP - bw
      top = cy - bh / 2
      break
  }
  // Clamp inside the viewport
  left = Math.min(Math.max(8, left), vw - bw - 8)
  top = Math.min(Math.max(8, top), vh - bh - 8)
  // Keep the arrow on the target even when the bubble was clamped to a screen edge.
  const arrowX = Math.min(Math.max(20, cx - left), Math.max(20, bw - 20))
  const arrowY = Math.min(Math.max(20, cy - top), Math.max(20, bh - 20))
  return { top: `${top}px`, left: `${left}px`, '--arrow-x': `${arrowX}px`, '--arrow-y': `${arrowY}px` }
})
</script>

<style scoped>
.tour-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  /* Pass clicks through to the page — interactive steps (e.g. "tap ▶ to
     load a profile") require it; only the bubble takes pointer events. */
  pointer-events: none;
}

.tour-dim {
  position: fixed;
  inset: 0;
  background: rgba(4, 8, 16, 0.72);
}

.tour-spotlight {
  position: fixed;
  border-radius: 14px;
  box-shadow: 0 0 0 9999px rgba(4, 8, 16, 0.72);
  border: 2px solid var(--color-primary, #4f8ef7);
  pointer-events: none;
  transition: top 0.25s ease, left 0.25s ease, width 0.25s ease, height 0.25s ease;
}

.tour-bubble {
  position: fixed;
  pointer-events: auto;
  width: min(420px, calc(100vw - 16px));
  background: rgba(16, 22, 36, 0.97);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border, #2a3444);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55);
  transition: top 0.25s ease, left 0.25s ease;
  max-height: calc(100vh - 16px);
  max-height: calc(100dvh - 16px);
  overflow-y: auto;
}

.tour-bubble-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tour-step-count {
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  color: var(--color-text-secondary, #8b96a8);
  font-weight: 600;
}

.tour-close {
  background: none;
  border: none;
  color: var(--color-text-secondary, #8b96a8);
  cursor: pointer;
  font-size: 1.1rem;
  padding: 6px;
  min-width: 36px;
  min-height: 36px;
}

.tour-close:hover { color: var(--color-text, #fff); }

.tour-title {
  margin: 0 0 8px;
  font-size: 1.3rem;
  color: var(--color-text, #fff);
}

.tour-text {
  margin: 0 0 16px;
  font-size: 1rem;
  line-height: 1.55;
  color: var(--color-text-secondary, #b9c2d0);
}

.tour-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tour-spacer { flex: 1; }

.tour-btn {
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid transparent;
  min-height: 48px;
}

.tour-btn.primary {
  background: var(--color-primary, #4f8ef7);
  color: #fff;
}

.tour-btn.primary:hover { filter: brightness(1.1); }

.tour-btn.ghost {
  background: transparent;
  color: var(--color-text-secondary, #a8b3c4);
  border-color: var(--color-border, #2a3444);
}

.tour-btn.ghost:hover { color: var(--color-text, #fff); }

/* App picker */
.tour-apps { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
.tour-app {
  display: inline-flex; align-items: center; gap: 8px;
  min-height: 44px; padding: 8px 14px; border-radius: 999px;
  font: inherit; font-size: 0.95rem; font-weight: 600; cursor: pointer;
  color: var(--color-text-secondary, #b9c2d0);
  background: transparent; border: 1px solid var(--color-border, #2a3444);
}
.tour-app:hover { color: var(--color-text, #fff); }
.tour-app.on { color: #fff; background: var(--color-primary, #4f8ef7); border-color: var(--color-primary, #4f8ef7); }
.tour-app.included { cursor: default; opacity: 0.7; }
.tour-app small { font-weight: 400; opacity: 0.8; }
@media (max-width: 480px) {
  .tour-bubble { padding: 14px 14px; }
  .tour-title { font-size: 1.15rem; }
  .tour-btn { padding: 10px 14px; }
}

/* Arrow pointing back toward the spotlight */
.tour-bubble::before {
  content: '';
  position: absolute;
  width: 14px;
  height: 14px;
  background: inherit;
  border: inherit;
  transform: rotate(45deg);
}

.tour-bubble.arrow-none::before { display: none; }
.tour-bubble.arrow-bottom::before {
  top: -8px; left: var(--arrow-x, 50%); margin-left: -7px;
  border-right: none; border-bottom: none;
}
.tour-bubble.arrow-top::before {
  bottom: -8px; left: var(--arrow-x, 50%); margin-left: -7px;
  border-left: none; border-top: none;
}
.tour-bubble.arrow-right::before {
  left: -8px; top: var(--arrow-y, 50%); margin-top: -7px;
  border-right: none; border-top: none;
}
.tour-bubble.arrow-left::before {
  right: -8px; top: var(--arrow-y, 50%); margin-top: -7px;
  border-left: none; border-bottom: none;
}
</style>
