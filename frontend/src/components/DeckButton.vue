<template>
  <div
    class="deck-button"
    :class="buttonClasses"
    :style="buttonStyle"
    @click="handleClick"
    @contextmenu.prevent="handleRightClick"
  >
    <div v-if="isEditMode" class="edit-overlay">
      <button class="edit-btn" @click.stop="emit('edit', button)" title="Edit">
        <FontAwesomeIcon :icon="['fas', 'edit']" />
      </button>
      <button class="delete-btn" @click.stop="emit('delete', button.id)" title="Delete">
        <FontAwesomeIcon :icon="['fas', 'trash']" />
      </button>
    </div>

    <div class="button-content">
      <div v-if="button.icon" class="button-icon">
        <FontAwesomeIcon 
          v-if="button.icon_type === 'fontawesome'" 
          :icon="parseIcon(button.icon)" 
          :style="iconStyle"
        />
        <img 
          v-else-if="button.icon_type === 'custom'" 
          :src="button.icon" 
          :style="iconStyle"
          alt="Button icon"
        />
      </div>

      <div v-if="button.label" class="button-label">
        {{ button.label }}
      </div>

      <div v-if="button.secondary_label" class="button-secondary-label">
        {{ button.secondary_label }}
      </div>
    </div>

    <div v-if="button.tooltip && !isEditMode" class="button-tooltip">
      {{ button.tooltip }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Button } from '@/types'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  button: Button
  isEditMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isEditMode: false
})

const emit = defineEmits<{
  click: [button: Button]
  edit: [button: Button]
  delete: [buttonId: string]
}>()

const buttonClasses = computed(() => ({
  'shape-rectangle': props.button.shape === 'rectangle',
  'shape-rounded': props.button.shape === 'rounded',
  'shape-circle': props.button.shape === 'circle',
  'edit-mode': props.isEditMode,
  'has-action': !!props.button.action
}))

const buttonStyle = computed(() => {
  const { position, size, style } = props.button
  
  return {
    gridRow: `${position.row + 1} / span ${size.rows}`,
    gridColumn: `${position.col + 1} / span ${size.cols}`,
    backgroundColor: style?.backgroundColor || 'var(--color-surface)',
    color: style?.textColor || 'var(--color-text)',
    borderColor: style?.borderColor || 'var(--color-border)',
    borderWidth: style?.borderWidth ? `${style.borderWidth}px` : '2px',
    opacity: style?.opacity || 1,
    fontSize: style?.fontSize ? `${style.fontSize}px` : '0.875rem'
  }
})

const iconStyle = computed(() => {
  const size = props.button.style?.iconSize || 32
  return {
    width: `${size}px`,
    height: `${size}px`,
    fontSize: `${size}px`
  }
})

function parseIcon(iconString: string) {
  // Format: "fas fa-home" or "fab fa-twitter"
  const parts = iconString.split(' ')
  if (parts.length === 2) {
    return [parts[0], parts[1].replace('fa-', '')]
  }
  return ['fas', 'question']
}

function handleClick() {
  if (!props.isEditMode) {
    emit('click', props.button)
  }
}

function handleRightClick() {
  if (!props.isEditMode) {
    emit('edit', props.button)
  }
}
</script>

<style scoped>
.deck-button {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-md);
  border: 2px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
  user-select: none;
}

.deck-button.shape-rectangle {
  border-radius: var(--radius-sm);
}

.deck-button.shape-rounded {
  border-radius: var(--radius-lg);
}

.deck-button.shape-circle {
  border-radius: var(--radius-full);
}

.deck-button.has-action:hover:not(.edit-mode) {
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.deck-button:active:not(.edit-mode) {
  transform: scale(0.95);
}

.edit-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  opacity: 0;
  transition: opacity var(--transition-fast);
  z-index: 10;
}

.deck-button.edit-mode:hover .edit-overlay {
  opacity: 1;
}

.edit-btn,
.delete-btn {
  padding: var(--spacing-sm);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1.25rem;
  transition: all var(--transition-fast);
}

.edit-btn {
  background-color: var(--color-primary);
  color: white;
}

.delete-btn {
  background-color: var(--color-error);
  color: white;
}

.edit-btn:hover,
.delete-btn:hover {
  transform: scale(1.1);
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  text-align: center;
  width: 100%;
}

.button-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.button-icon img {
  object-fit: contain;
}

.button-label {
  font-weight: 600;
  word-wrap: break-word;
  max-width: 100%;
}

.button-secondary-label {
  font-size: 0.75em;
  opacity: 0.8;
  word-wrap: break-word;
  max-width: 100%;
}

.button-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  background-color: rgba(0, 0, 0, 0.9);
  color: white;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  z-index: 100;
}

.deck-button:hover .button-tooltip {
  opacity: 1;
}

/* Ripple animation */
.deck-button::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  transform: translate(-50%, -50%);
  transition: width var(--transition-normal), height var(--transition-normal), opacity var(--transition-normal);
  opacity: 0;
}

.deck-button:active::after:not(.edit-mode) {
  width: 100%;
  height: 100%;
  opacity: 0.3;
}
</style>

