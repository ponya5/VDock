<template>
  <footer class="deck-footer" :class="{ 'edit-mode': isEditMode }">
    <!-- Left Side: docked header-reveal pill (while the header is hidden),
         then Page Dots. The pill lives in-flow in the chrome strip — as a
         floating element it overlapped grid tiles and would have sat on
         top of the dots (DL-014 follow-up). Tap or swipe-down reveals. -->
    <div class="footer-left">
      <Transition name="hdr-pill">
        <div
          v-if="!settingsStore.showHeader"
          ref="revealTriggerRef"
          class="header-reveal-trigger"
          @click="revealHeader"
          title="Swipe down or tap to show header"
        >
          <div class="reveal-pill">
            <span class="reveal-ripple" aria-hidden="true"></span>
            <span class="reveal-pill-label">
              <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
              <span>Show Header</span>
            </span>
            <span class="reveal-ripple" aria-hidden="true"></span>
          </div>
        </div>
      </Transition>
      <div v-if="totalPages > 1" class="page-dots">
        <button
          v-for="p in totalPages"
          :key="p"
          class="page-dot touch-target"
          :class="{ active: currentPageIndex === p - 1 }"
          @click="emit('setPage', p - 1)"
          :aria-label="`Go to page ${p}`"
        />
      </div>
    </div>

    <!-- Edit Mode controls (displayed in center during edit mode) -->
    <div v-if="isEditMode" class="footer-edit-section">
      <!-- Grid size controls -->
      <div class="grid-size-controls">
        <label>Grid:</label>
        <input
          :value="gridRows"
          @input="emit('updateRows', parseInt(($event.target as HTMLInputElement).value))"
          type="number"
          min="1"
          max="10"
          class="grid-input"
          title="Rows"
        />
        <span>×</span>
        <input
          :value="gridCols"
          @input="emit('updateCols', parseInt(($event.target as HTMLInputElement).value))"
          type="number"
          min="1"
          max="10"
          class="grid-input"
          title="Columns"
        />
      </div>

      <!-- Page actions -->
      <button class="btn btn-primary btn-sm touch-target" @click="emit('addPage')">
        <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Page
      </button>
      <button
        class="btn btn-danger btn-sm touch-target"
        @click="emit('deletePage')"
        :disabled="totalPages <= 1"
      >
        <FontAwesomeIcon :icon="['fas', 'trash']" /> Delete Page
      </button>
      <button class="btn btn-success btn-sm touch-target" @click="emit('saveProfile')">
        <FontAwesomeIcon :icon="['fas', 'save']" /> Save Profile
      </button>
    </div>

  </footer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useSettingsStore } from '@/stores/settings'
import { useSwipe } from '@/composables/useGestures'

interface Props {
  isEditMode: boolean
  totalPages: number
  currentPageIndex: number
  gridRows: number
  gridCols: number
}

defineProps<Props>()
const emit = defineEmits<{
  setPage: [index: number]
  addPage: []
  deletePage: []
  saveProfile: []
  updateRows: [rows: number]
  updateCols: [cols: number]
}>()

const settingsStore = useSettingsStore()
const revealTriggerRef = ref<HTMLElement | null>(null)

function revealHeader() {
  settingsStore.showHeader = true
}

// Swipe down on the pill reveals too — the same gesture the header
// dismisses with (swipe up) in reverse.
useSwipe(revealTriggerRef, {
  onSwipeEnd: (direction) => {
    if (direction === 'DOWN') {
      revealHeader()
    }
  }
})
</script>

<style scoped>
/* DL-097: the whole footer mounts/unmounts depending on whether it has
   content, wrapped in `footer-slide` by DashboardView — slides up from
   below the viewport edge on enter and back down off it on leave.
   leave-active goes absolute (anchored to the relative .dashboard-view)
   so the grid reclaims the strip at the start of the slide, inside the
   motion, rather than snapping after it. */
.deck-footer.footer-slide-enter-active,
.deck-footer.footer-slide-leave-active {
  transition: transform 0.3s var(--ease-io);
}

.deck-footer.footer-slide-enter-from,
.deck-footer.footer-slide-leave-to {
  transform: translateY(100%);
}

.deck-footer.footer-slide-leave-active {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
}

.deck-footer {
  /* Anchors the reveal pill while it slides out (hdr-pill-leave-active
     takes it out of flow so the footer reclaims its height inside the
     header's slide, not after it). */
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 44px;
  /* Grows with touch mode so the edit controls keep finger room on small
     panels. The plain 44px above stays as the baseline/fallback. */
  min-height: max(44px, calc(56px * var(--touch-multiplier, 1)));
  background: rgba(10, 8, 32, 0.66);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  padding: 0 var(--spacing-touch-md, var(--spacing-md));
  box-sizing: border-box;
  z-index: 90;
}

.footer-left {
  display: flex;
  align-items: center;
  flex: 1;
}

/* Header-reveal trigger docked in the footer strip (DL-014 follow-up
   2026-09-28): an in-flow flex item — the old position:fixed corner pill
   covered the footer's left end (where page dots live on multi-page
   scenes) and grazed the grid's bottom-left tile. In-flow it can overlap
   nothing; if it is taller than the footer's minimum the footer simply
   grows to fit. */
.header-reveal-trigger {
  -webkit-user-select: none;
  user-select: none;
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-right: var(--spacing-touch-sm, var(--spacing-sm));
  cursor: pointer;
  touch-action: none;
}

/* Visible tap affordance — a labelled pill reads as a button on
   touchscreens, where the bare handle bar did not. Styled on the Uiverse
   "ripple button" (DL-014 follow-up, 2026-09-27): solid teal, square-ish
   corners, uppercase tracked label flanked by two ripple dots. */
.reveal-pill {
  -webkit-user-select: none;
  user-select: none;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(14px * min(var(--touch-multiplier, 1), 1.6));
  min-width: calc(200px * min(var(--touch-multiplier, 1), 1.6));
  min-height: 44px;
  min-height: max(var(--min-touch-target, 48px), calc(52px * min(var(--touch-multiplier, 1), 1.6)));
  padding:
    calc(16px * min(var(--touch-multiplier, 1), 1.6))
    calc(20px * min(var(--touch-multiplier, 1), 1.6));
  background: #40B3A2;
  border: 0;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35), 0 2px 6px rgba(0, 0, 0, 0.3);
  color: #fff;
  font-size: calc(0.75rem * min(var(--touch-multiplier, 1), 1.6));
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.reveal-pill-label {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
}

/* Ripple dots — expanding box-shadow rings, clipped inside the button. */
.reveal-ripple {
  width: 10px;
  height: 10px;
  border-radius: 100%;
  background: rgba(255, 255, 255, 0.85);
  flex-shrink: 0;
  animation: reveal-ripple 0.6s linear infinite;
}

@keyframes reveal-ripple {
  0% {
    box-shadow:
      0 0 0 0 rgba(255, 255, 255, 0.1),
      0 0 0 20px rgba(255, 255, 255, 0.1),
      0 0 0 40px rgba(255, 255, 255, 0.1),
      0 0 0 60px rgba(255, 255, 255, 0.1);
  }
  100% {
    box-shadow:
      0 0 0 20px rgba(255, 255, 255, 0.1),
      0 0 0 40px rgba(255, 255, 255, 0.1),
      0 0 0 60px rgba(255, 255, 255, 0.1),
      0 0 0 80px rgba(255, 255, 255, 0);
  }
}

.header-reveal-trigger:hover .reveal-pill,
.header-reveal-trigger:active .reveal-pill {
  opacity: 0.92;
  transform: scale(1.04);
}

@media (prefers-reduced-motion: reduce) {
  .reveal-ripple { animation: none; }
}

/* Same-direction choreography, docked edition: on hide the pill rises up
   into its footer slot while the header slides up away; on reveal it
   slides down off the bottom edge while the header slides down in. The
   entering pill stays in-flow (footer grows into place inside the
   header's collapse motion); the leaving pill goes absolute on the
   relative footer — same left offset, vertically centred — so the footer
   height snaps at the *start* of the leave, masked by the header slide,
   rather than jumping after the transition ends. */
.hdr-pill-enter-active,
.hdr-pill-leave-active {
  transition: transform 0.55s var(--ease-io, cubic-bezier(0.4, 0, 0.2, 1));
  will-change: transform;
}

.hdr-pill-leave-active {
  position: absolute;
  left: var(--spacing-touch-md, var(--spacing-md));
  top: 50%;
}

.header-reveal-trigger.hdr-pill-enter-from {
  transform: translateY(140%);
}

.header-reveal-trigger.hdr-pill-leave-from {
  transform: translateY(-50%);
}

.header-reveal-trigger.hdr-pill-leave-to {
  transform: translateY(90%);
}

@media (prefers-reduced-motion: reduce) {
  .hdr-pill-enter-active,
  .hdr-pill-leave-active {
    transition: none;
  }
}

.page-dots {
  display: flex;
  align-items: center;
  gap: var(--spacing-touch-sm, var(--spacing-sm));
}

.page-dot {
  width: 10px;
  height: 10px;
  width: calc(10px * var(--touch-multiplier, 1));
  height: calc(10px * var(--touch-multiplier, 1));
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.3);
  border: none;
  cursor: pointer;
  padding: 17px; /* Makes it 44x44px touch target */
  padding: calc(17px * var(--touch-multiplier, 1));
  background-clip: content-box;
  box-sizing: content-box;
  transition: all 0.2s var(--ease-out);
}


.page-dot.active {
  background-color: #4aa3ff;
  transform: scale(1.2);
}

.footer-edit-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-touch-md, var(--spacing-md));
  flex: 2;
  justify-content: center;
  flex-wrap: wrap;
}

.grid-size-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-touch-xs, var(--spacing-xs));
  color: var(--color-text-secondary);
  font-size: calc(0.9rem * var(--touch-multiplier, 1));
}

.grid-input {
  width: 44px;
  width: calc(56px * var(--touch-multiplier, 1));
  height: 32px;
  height: calc(44px * var(--touch-multiplier, 1));
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  background-color: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 12px;
  color: var(--color-text);
  text-align: center;
  font-family: inherit;
  font-size: calc(0.9rem * var(--touch-multiplier, 1));
}

.btn-sm {
  min-height: 44px;
  min-height: max(var(--min-touch-target, 44px), calc(44px * var(--touch-multiplier, 1)));
  padding: var(--spacing-touch-xs, var(--spacing-xs)) var(--spacing-touch-md, var(--spacing-md));
  gap: var(--spacing-touch-xs, var(--spacing-xs));
  font-size: calc(0.9rem * var(--touch-multiplier, 1));
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
