<template>
  <div class="page-nav-wrapper">
    <div
      class="glass-radio-group"
      role="radiogroup"
      aria-label="Page selector"
    >
      <!-- Glider must come BEFORE labels so CSS sibling selector works if needed,
           but we drive it via inline style for dynamic page count -->
      <div class="glass-glider" :style="gliderStyle" aria-hidden="true"></div>

      <template v-for="(page, index) in pages" :key="page.id">
        <input
          type="radio"
          :id="`page-radio-${groupId}-${index}`"
          :name="`page-group-${groupId}`"
          :value="index"
          :checked="index === currentPage"
          @change="emit('goTo', index)"
        />
        <label
          :for="`page-radio-${groupId}-${index}`"
          :title="page.name"
        >
          {{ index + 1 }}
        </label>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Page } from '@/types'

interface Props {
  pages: Page[]
  currentPage: number
  showPageName?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showPageName: true
})

const emit = defineEmits<{
  previous: []
  next: []
  goTo: [index: number]
}>()

const groupId = Math.random().toString(36).slice(2, 8)

const disableAnimation = ref(false)
watch(
  () => props.pages.length,
  () => {
    disableAnimation.value = true
    setTimeout(() => { disableAnimation.value = false }, 50)
  }
)

const gliderStyle = computed(() => {
  const n = props.pages.length || 1
  return {
    width: `calc(100% / ${n})`,
    transform: `translateX(${props.currentPage * 100}%)`,
    transition: disableAnimation.value
      ? 'none'
      : 'transform 0.5s cubic-bezier(0.37, 1.95, 0.66, 0.56), background 0.4s ease-in-out, box-shadow 0.4s ease-in-out',
  }
})
</script>

<style scoped>
.page-nav-wrapper {
  display: flex;
  align-items: center;
}

/* ── chase2k25 glass pill ── */
.glass-radio-group {
  --bg: rgba(255, 255, 255, 0.06);
  --text: #e5e5e5;
  display: flex;
  position: relative;
  background: var(--bg);
  border-radius: 1rem;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow:
    inset 1px 1px 4px rgba(255, 255, 255, 0.2),
    inset -1px -1px 6px rgba(0, 0, 0, 0.3),
    0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  width: fit-content;
  min-height: 44px;
}

.glass-radio-group input {
  display: none;
}

.glass-radio-group label {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  font-size: clamp(0.65rem, 0.7vw + 0.45rem, 0.85rem);
  padding: 0.8rem 1.2rem;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--text);
  position: relative;
  z-index: 2;
  transition: color 0.3s ease-in-out;
  white-space: nowrap;
  min-height: 44px;
}

.glass-radio-group label:hover {
  color: white;
}

.glass-radio-group input:checked + label {
  color: #fff;
}

/* ── animated glider — VDock blue ── */
.glass-glider {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 1rem;
  z-index: 1;
  background: linear-gradient(135deg, rgba(52, 152, 219, 0.45), rgba(52, 152, 219, 0.85));
  box-shadow:
    0 0 18px rgba(52, 152, 219, 0.5),
    inset 0 0 10px rgba(255, 255, 255, 0.15);
  pointer-events: none;
}

@media (max-width: 480px) {
  .glass-radio-group label {
    min-width: 38px;
    padding: 0.7rem 0.8rem;
  }
}
</style>
