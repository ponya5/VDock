<template>
  <Teleport to="body">
    <div v-if="tour.state.active" class="tour-overlay" @click.self="tour.finish">
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
        <div class="tour-actions">
          <button class="tour-btn ghost" @click="tour.finish">Skip</button>
          <span class="tour-spacer"></span>
          <button v-if="!tour.isFirst.value" class="tour-btn ghost" @click="tour.back">Back</button>
          <button class="tour-btn primary" @click="tour.next">
            {{ tour.isLast.value ? 'Done' : 'Next' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useTutorial, TUTORIAL_STEPS } from '@/services/tutorial'

const tour = useTutorial()
const steps = TUTORIAL_STEPS
const step = computed(() => tour.currentStep.value)
const bubbleEl = ref<HTMLElement | null>(null)
const targetRect = ref<DOMRect | null>(null)
const bubbleSize = ref({ w: 420, h: 240 })
const viewport = ref({ w: window.innerWidth, h: window.innerHeight })

const PAD = 10
const BUBBLE_GAP = 14

function measure() {
  viewport.value = { w: window.innerWidth, h: window.innerHeight }
  const sel = step.value?.target
  const el = sel ? document.querySelector(sel) : null
  targetRect.value = el ? el.getBoundingClientRect() : null
  if (bubbleEl.value) {
    const r = bubbleEl.value.getBoundingClientRect()
    bubbleSize.value = { w: r.width, h: r.height }
  }
}

watch(
  () => tour.state.stepIndex,
  async () => {
    await nextTick()
    measure()
    // Re-measure once more after the bubble settles at its new spot
    requestAnimationFrame(measure)
  }
)

onMounted(() => {
  measure()
  window.addEventListener('resize', measure)
  window.addEventListener('scroll', measure, true)
})
onUnmounted(() => {
  window.removeEventListener('resize', measure)
  window.removeEventListener('scroll', measure, true)
})

const spotlightStyle = computed(() => {
  const r = targetRect.value
  if (!r) return {}
  return {
    top: `${r.top - PAD}px`,
    left: `${r.left - PAD}px`,
    width: `${r.width + PAD * 2}px`,
    height: `${r.height + PAD * 2}px`,
  }
})

/** Where the bubble ends up; also which side the arrow should render on. */
const placement = computed<{ side: 'top' | 'bottom' | 'left' | 'right' | 'none' }>(() => {
  const r = targetRect.value
  if (!r) return { side: 'none' }
  const bw = bubbleSize.value.w
  const bh = bubbleSize.value.h
  const pref = step.value?.placement || 'bottom'
  const fits = {
    top: r.top - PAD - BUBBLE_GAP - bh > 8,
    bottom: r.bottom + PAD + BUBBLE_GAP + bh < viewport.value.h - 8,
    left: r.left - PAD - BUBBLE_GAP - bw > 8,
    right: r.right + PAD + BUBBLE_GAP + bw < viewport.value.w - 8,
  }
  if (fits[pref]) return { side: pref }
  const fallbacks: Array<'top' | 'bottom' | 'left' | 'right'> = ['bottom', 'top', 'right', 'left']
  return { side: fallbacks.find((s) => fits[s]) || 'bottom' }
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
  return { top: `${top}px`, left: `${left}px` }
})
</script>

<style scoped>
.tour-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  /* The dim layer lives on the spotlight's box-shadow so the cutout stays clean */
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
  width: min(420px, calc(100vw - 16px));
  background: rgba(16, 22, 36, 0.97);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border, #2a3444);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55);
  transition: top 0.25s ease, left 0.25s ease;
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
  top: -8px; left: 50%; margin-left: -7px;
  border-right: none; border-bottom: none;
}
.tour-bubble.arrow-top::before {
  bottom: -8px; left: 50%; margin-left: -7px;
  border-left: none; border-top: none;
}
.tour-bubble.arrow-right::before {
  left: -8px; top: 50%; margin-top: -7px;
  border-right: none; border-top: none;
}
.tour-bubble.arrow-left::before {
  right: -8px; top: 50%; margin-top: -7px;
  border-left: none; border-bottom: none;
}
</style>
