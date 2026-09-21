<template>
  <footer class="deck-footer" :class="{ 'edit-mode': isEditMode, mobile: isMobileViewport }">
    <!-- Left Side: Page Dots -->
    <div class="footer-left">
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
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useMobileViewport } from '@/utils/mobileViewport'

const { isMobileViewport } = useMobileViewport()

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
</script>

<style scoped>
.deck-footer {
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

/* Mobile: the footer only ever carries page dots (edit controls can't
   activate) — slimmed to the 44px touch-target floor the dots need. */
.deck-footer.mobile {
  min-height: 44px;
}

.footer-left {
  display: flex;
  align-items: center;
  flex: 1;
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
