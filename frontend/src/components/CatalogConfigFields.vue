<template>
  <div v-if="visibleFields.length || advancedFields.length" class="ccf">
    <div v-for="field in visibleFields" :key="field.name" class="form-group" data-testid="ccf-field">
      <CatalogField
        :field="field"
        :value="valueOf(field)"
        @update="(v) => setValue(field, v)"
      />
    </div>

    <div v-if="advancedFields.length" class="ccf-advanced">
      <button
        type="button"
        class="ccf-advanced-toggle"
        :aria-expanded="advancedOpen"
        data-testid="ccf-advanced-toggle"
        @click="advancedOpen = !advancedOpen"
      >
        <FontAwesomeIcon :icon="['fas', advancedOpen ? 'chevron-down' : 'chevron-right']" />
        Advanced
      </button>
      <Collapse :open="advancedOpen">
        <div v-for="field in advancedFields" :key="field.name" class="form-group" data-testid="ccf-advanced-field">
          <CatalogField
            :field="field"
            :value="valueOf(field)"
            @update="(v) => setValue(field, v)"
          />
        </div>
      </Collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import Collapse from '@/components/Collapse.vue'
import CatalogField from '@/components/CatalogField.vue'
import type { ActionSpec, ConfigFieldSpec } from '@/stores/actionCatalog'

/**
 * DL-145 - the config form for catalog actions that have no hand-written
 * editor block (every integration-pack action). Fields come from the spec's
 * `config_fields`; `show_when` hides a field until another has a value and
 * `advanced` fields sit behind a collapsed toggle, so an action shows one
 * field by default and the rest only when asked for.
 */

// Types the generic form can render. `keys` and `steps` need dedicated editors.
const RENDERABLE = new Set(['text', 'textarea', 'number', 'select', 'boolean', 'path', 'url'])

const props = defineProps<{
  spec: ActionSpec
  modelValue: Record<string, unknown>
}>()

const emit = defineEmits<{ 'update:modelValue': [value: Record<string, unknown>] }>()

function valueOf(field: ConfigFieldSpec): unknown {
  return props.modelValue[field.name] ?? field.default ?? (field.type === 'boolean' ? false : '')
}

function isShown(field: ConfigFieldSpec): boolean {
  const when = field.show_when
  if (!when) return true
  return Object.entries(when).every(([name, expected]) => {
    const other = props.spec.config_fields.find((f) => f.name === name)
    const current = props.modelValue[name] ?? other?.default
    return current === expected
  })
}

const fields = computed(() =>
  props.spec.config_fields.filter((f) => RENDERABLE.has(f.type) && isShown(f)),
)
const visibleFields = computed(() => fields.value.filter((f) => !f.advanced))
const advancedFields = computed(() => fields.value.filter((f) => f.advanced))

function differsFromDefault(field: ConfigFieldSpec): boolean {
  const current = props.modelValue[field.name]
  if (current === undefined || current === null || current === '') return false
  return current !== field.default
}

const advancedOpen = ref(
  props.spec.config_fields.some((f) => f.advanced && differsFromDefault(f)),
)

function setValue(field: ConfigFieldSpec, value: unknown): void {
  const next = { ...props.modelValue }
  if (value === undefined) delete next[field.name]
  else next[field.name] = value
  emit('update:modelValue', next)
}
</script>

<style scoped>
.ccf-advanced { margin-bottom: var(--spacing-md); }
.ccf-advanced-toggle {
  display: inline-flex; align-items: center; gap: 8px;
  min-height: 36px; padding: 0 4px;
  background: none; border: none; cursor: pointer;
  color: var(--color-text-secondary); font: inherit; font-weight: 500;
  touch-action: manipulation;
}
</style>
