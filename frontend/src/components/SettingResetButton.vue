<template>
  <button
    type="button"
    class="setting-reset"
    :class="{ 'is-default': atDefault }"
    :disabled="atDefault"
    :title="atDefault ? 'Already at default' : `Reset ${label} to default`"
    :aria-label="`Reset ${label} to default`"
    @click="emit('reset')"
  >
    <FontAwesomeIcon :icon="['fas', 'rotate-left']" />
  </button>
</template>

<script setup lang="ts">
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

withDefaults(defineProps<{ atDefault?: boolean; label?: string }>(), {
  atDefault: false,
  label: 'setting'
})
const emit = defineEmits<{ reset: [] }>()
</script>

<style scoped>
.setting-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  touch-action: manipulation;
  transition: color var(--transition-fast), border-color var(--transition-fast),
    background var(--transition-fast), opacity var(--transition-fast);
}

.setting-reset:hover:not(:disabled) {
  color: var(--color-accent, #4aa3ff);
  border-color: var(--color-accent, #4aa3ff);
  background: color-mix(in srgb, var(--color-accent, #4aa3ff) 14%, transparent);
}

.setting-reset:active:not(:disabled) {
  transform: scale(0.94);
}

/* At default = nothing to reset; the dimmed icon still marks the control
   as resettable without shifting layout in and out. */
.setting-reset.is-default {
  opacity: 0.3;
  cursor: default;
}
</style>
