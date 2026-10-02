<template>
  <label v-if="field.type === 'boolean'" class="cf-switch">
    <input
      type="checkbox"
      :checked="Boolean(value)"
      @change="emit('update', ($event.target as HTMLInputElement).checked)"
    />
    <span>{{ field.label }}</span>
  </label>

  <template v-else>
    <label class="cf-label">{{ field.label }}</label>

    <select
      v-if="field.type === 'select'"
      class="select"
      :value="String(value)"
      @change="emit('update', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="opt in field.options ?? []" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>

    <textarea
      v-else-if="field.type === 'textarea'"
      class="textarea"
      :value="String(value)"
      :placeholder="field.placeholder"
      @input="emit('update', ($event.target as HTMLTextAreaElement).value)"
    ></textarea>

    <input
      v-else-if="field.type === 'number'"
      class="input"
      type="number"
      :value="value === '' ? '' : Number(value)"
      :placeholder="field.placeholder"
      @input="onNumber"
    />

    <input
      v-else
      class="input"
      type="text"
      :value="String(value)"
      :placeholder="field.placeholder"
      @input="emit('update', ($event.target as HTMLInputElement).value)"
    />
  </template>

  <p v-if="field.help" class="cf-help">{{ field.help }}</p>
</template>

<script setup lang="ts">
import type { ConfigFieldSpec } from '@/stores/actionCatalog'

/** One catalog config field (DL-145); see CatalogConfigFields.vue. */

defineProps<{ field: ConfigFieldSpec; value: unknown }>()
const emit = defineEmits<{ update: [value: unknown] }>()

function onNumber(event: Event): void {
  const raw = (event.target as HTMLInputElement).value
  emit('update', raw === '' ? undefined : Number(raw))
}
</script>

<style scoped>
.cf-label { display: block; margin-bottom: var(--spacing-xs); font-weight: 500; color: var(--color-text); }
.cf-switch { display: flex; align-items: center; gap: 10px; min-height: 40px; cursor: pointer; color: var(--color-text); }
.cf-switch input { width: 20px; height: 20px; }
.cf-help { margin: var(--spacing-xs) 0 0; font-size: 0.85rem; color: var(--color-text-secondary); line-height: 1.4; }
</style>
