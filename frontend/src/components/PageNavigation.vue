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

/* ── glass pill ── */
.glass-radio-group {
  --bg: rgba(255, 255, 255, 0.08);
  --text: #a9b6cc;
  display: flex;
  position: relative;
  background: var(--bg);
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  overflow: hidden;
  width: fit-content;
  min-height: 48px;
}

.glass-radio-group input {
  display: none;
}

.glass-radio-group label {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  font-size: clamp(15px, 0.7vw + 11px, 20px);
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-weight: 600;
  color: var(--text);
  position: relative;
  z-index: 2;
  transition: color 0.3s ease-in-out;
  white-space: nowrap;
  min-height: 48px;
  border-radius: 14px;
}

.glass-radio-group label:hover {
  color: white;
}

.glass-radio-group input:checked + label {
  color: #fff;
}

/* ── animated glider ── */
.glass-glider {
  position: absolute;
  top: 4px;
  bottom: 4px;
  border-radius: 14px;
  z-index: 1;
  background: #1f6fd1;
  box-shadow: 0 4px 12px rgba(31, 111, 209, 0.45);
  pointer-events: none;
}

@media (max-width: 480px) {
  .glass-radio-group label {
    min-width: 38px;
    padding: 0.7rem 0.8rem;
  }
}
</style>
