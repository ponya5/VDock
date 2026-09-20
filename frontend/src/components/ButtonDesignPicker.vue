<template>
  <div class="design-picker">
    <div class="design-swatch-grid" role="radiogroup" aria-label="Button design">
      <button
        v-for="d in designs"
        :key="d.value"
        type="button"
        class="design-swatch-wrap"
        :class="{ selected: modelValue === d.value }"
        :title="d.label"
        @click="emit('update:modelValue', d.value)"
      >
        <!-- Mini deck-button stub: the global .deck-button-* classes render
             the real design so the preview never drifts from the grid. -->
        <span
          class="design-swatch deck-button"
          :class="`deck-button-${d.value}`"
          :data-mark="'A'"
        >
          <span class="button-content">
            <span v-if="d.value === 'folder'" class="button-icon">
              <span class="folder-cell"><FontAwesomeIcon :icon="['fas', 'play']" /></span>
              <span class="folder-cell"><FontAwesomeIcon :icon="['fas', 'music']" /></span>
              <span class="folder-cell"></span>
              <span class="folder-cell"></span>
            </span>
            <span v-else class="button-icon">
              <FontAwesomeIcon :icon="d.icon" class="preview-icon" />
            </span>
          </span>
        </span>
        <span class="design-name">{{ d.label }}</span>
      </button>
    </div>

    <!-- Animated / overlay effects stay in a select — they aren't card
         designs and a static swatch would misrepresent them. Picking one
         replaces the design (they share the single effect field). -->
    <div class="overlay-row">
      <label class="overlay-label">Overlay effect</label>
      <select
        class="select overlay-select"
        :value="overlayValue"
        @change="onOverlayChange"
      >
        <option value="">None</option>
        <option v-for="o in overlays" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const props = defineProps<{ modelValue?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const designs = [
  { value: 'none',      label: 'Classic',    icon: ['fas', 'square'] },
  { value: 'glass',     label: 'Glass',      icon: ['fas', 'droplet'] },
  { value: 'glowglass', label: 'Glow Glass', icon: ['fas', 'star'] },
  { value: 'gem',       label: 'Gem',        icon: ['fas', 'gem'] },
  { value: 'neonrim',   label: 'Neon Rim',   icon: ['fas', 'bolt'] },
  { value: 'watermark', label: 'Watermark',  icon: ['fas', 'font'] },
  { value: 'deckkey',   label: 'Deck Key',   icon: ['fas', 'cube'] },
  { value: 'statuskey', label: 'Status Key', icon: ['fas', 'circle-dot'] },
  { value: 'fullart',   label: 'Full Art',   icon: ['fas', 'image'] },
  { value: 'folder',    label: 'Folder',     icon: ['fas', 'folder-open'] },
] as const

const overlays = [
  { value: 'neumorphism', label: 'Neumorphism' },
  { value: 'gradient',    label: 'Gradient' },
  { value: 'glow',        label: 'Glow' },
  { value: '3d',          label: '3D' },
  { value: 'neon',        label: 'Neon' },
  { value: 'metallic',    label: 'Metallic' },
  { value: 'liquid',      label: 'Liquid' },
  { value: 'holographic', label: 'Holographic' },
  { value: 'shadow',      label: 'Deep Shadow' },
  { value: 'emissive',    label: 'Emissive' },
  { value: 'fire',        label: 'Fire' },
  { value: 'plasma',      label: 'Plasma' },
  { value: 'particles',   label: 'Particles' },
  { value: 'aurora',      label: 'Aurora' },
  { value: 'scanline',    label: 'Scanline' },
  { value: 'rain',        label: 'Rain' },
] as const

const overlayValue = computed(() =>
  overlays.some(o => o.value === props.modelValue) ? props.modelValue! : ''
)

function onOverlayChange(e: Event) {
  const value = (e.target as HTMLSelectElement).value
  // Selecting "None" while a card design is active must not wipe the design —
  // the select is only meaningful when an overlay is actually chosen.
  if (value === '' && !overlays.some(o => o.value === props.modelValue)) return
  emit('update:modelValue', value || 'none')
}
</script>

<style scoped>
.design-picker {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.design-swatch-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.design-swatch-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 6px 4px;
  border: 2px solid transparent;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  touch-action: manipulation;
}

.design-swatch-wrap:hover {
  background: rgba(255, 255, 255, 0.09);
}

.design-swatch-wrap.selected {
  border-color: var(--color-accent, #4aa3ff);
  background: color-mix(in srgb, var(--color-accent, #4aa3ff) 14%, transparent);
}

/* Swatch tile — mirrors the real card's box so the global .deck-button-*
   design classes land on a plausible surface. Base look = Classic. */
.design-swatch {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(20, 16, 50, 0.4);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 8px 18px rgba(8, 6, 30, 0.28);
  overflow: hidden;
  color: #eef2fa;
  pointer-events: none;
  --btn-brand: var(--color-accent, #4aa3ff);
}

.design-swatch .button-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  padding: 6px;
  box-sizing: border-box;
}

.design-swatch .button-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40%;
  min-height: 40%;
  padding: 12%;
  border-radius: 22%;
  background: color-mix(in srgb, var(--btn-brand, #4aa3ff) 18%, transparent);
  border: 1px solid color-mix(in srgb, var(--btn-brand, #4aa3ff) 32%, rgba(255, 255, 255, 0.1));
  color: #fff;
  font-size: 1.1rem;
  box-sizing: border-box;
}

/* Full-art swatch: bare giant glyph, capsule stripped (mirrors main.css). */
.design-swatch.deck-button-fullart .button-icon {
  min-width: 0;
  min-height: 0;
  padding: 0;
  background: none;
  border: none;
  box-shadow: none;
}

.design-swatch.deck-button-fullart .preview-icon {
  font-size: 1.9rem;
}

/* Folder swatch: icon capsule becomes the 2×2 peek grid. */
.design-swatch.deck-button-folder .button-icon {
  width: 74%;
  max-width: none;
}

.design-swatch.deck-button-deckkey {
  padding: 5px;
}

.design-name {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text, #eef2fa);
  text-align: center;
  line-height: 1.1;
}

.overlay-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.overlay-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary, #b6c2d9);
  white-space: nowrap;
}

.overlay-select {
  flex: 1;
}

@media (max-width: 640px) {
  .design-swatch-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }
}
</style>
