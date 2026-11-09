<template>
  <div
    class="agent-view-toggle"
    :class="{ 'always-labels': alwaysLabels }"
    role="radiogroup"
    aria-label="Button view"
    data-testid="agent-view-toggle"
  >
    <button
      v-for="opt in OPTIONS"
      :key="opt.mode"
      type="button"
      role="radio"
      class="avt-seg"
      :class="{ selected: modelValue === opt.mode }"
      :aria-checked="modelValue === opt.mode"
      :aria-label="opt.label"
      :title="opt.title"
      :data-mode="opt.mode"
      @click="emit('update:modelValue', opt.mode)"
    >
      <FontAwesomeIcon :icon="['fas', opt.icon]" aria-hidden="true" />
      <span class="avt-label">{{ opt.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import type { AgentViewMode } from '@/composables/useAgentSceneView'

/**
 * DL-166: Groups / All switch for an AI coding scene. Two segments, each at
 * least 44px tall; the labels drop to icon-only on narrow desktop windows
 * (aria-label and title stay), and always show on the phone console.
 */

defineProps<{ modelValue: AgentViewMode; alwaysLabels?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [mode: AgentViewMode] }>()

const OPTIONS: Array<{ mode: AgentViewMode; label: string; icon: string; title: string }> = [
  { mode: 'groups', label: 'Groups', icon: 'layer-group', title: 'Show buttons grouped by category' },
  { mode: 'all', label: 'All', icon: 'table-cells', title: 'Show every button' },
]
</script>

<style scoped>
.agent-view-toggle {
  display: inline-flex;
  align-items: stretch;
  flex: none;
  padding: 3px;
  gap: 2px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.avt-seg {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 44px;
  min-height: max(44px, calc(36px * var(--touch-multiplier, 1)));
  padding: 0 12px;
  border: 0;
  border-radius: 11px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: clamp(0.8rem, 2vh, 0.95rem);
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
}

.avt-seg.selected {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.avt-seg:focus-visible {
  outline: 2px solid #e5e7eb;
  outline-offset: 1px;
}

@media (max-width: 1100px) {
  .agent-view-toggle:not(.always-labels) .avt-label { display: none; }
  .agent-view-toggle:not(.always-labels) .avt-seg { padding: 0 12px; }
}
</style>
