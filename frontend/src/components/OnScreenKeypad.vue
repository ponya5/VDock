<template>
  <div v-if="visible" class="onscreen-keypad-container">
    <div class="onscreen-keypad">
      <!-- Top header bar with close button -->
      <div class="keypad-header">
        <span class="keypad-title">On-screen Keypad</span>
        <button class="btn btn-sm btn-close" @click="emit('close')" title="Close keypad">
          <FontAwesomeIcon :icon="['fas', 'times']" />
        </button>
      </div>

      <!-- Keys Grid layout -->
      <div class="keypad-rows">
        <div v-for="(row, rowIndex) in layout" :key="rowIndex" class="keypad-row">
          <button
            v-for="key in row"
            :key="key.code"
            class="keypad-key touch-target"
            :class="getKeyClass(key)"
            @click="handleKeyPress(key)"
          >
            {{ getKeyLabel(key) }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

interface Props {
  modelValue: string
  visible: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  close: []
}>()

const isShift = ref(false)

interface Key {
  code: string
  label: string
  shiftLabel?: string
  action: 'char' | 'backspace' | 'space' | 'shift' | 'enter'
}

// Simple QWERTY layout matching target touchscreen sizes
const layout = computed<Key[][]>(() => [
  [
    { code: '1', label: '1', shiftLabel: '!', action: 'char' },
    { code: '2', label: '2', shiftLabel: '@', action: 'char' },
    { code: '3', label: '3', shiftLabel: '#', action: 'char' },
    { code: '4', label: '4', shiftLabel: '$', action: 'char' },
    { code: '5', label: '5', shiftLabel: '%', action: 'char' },
    { code: '6', label: '6', shiftLabel: '^', action: 'char' },
    { code: '7', label: '7', shiftLabel: '&', action: 'char' },
    { code: '8', label: '8', shiftLabel: '*', action: 'char' },
    { code: '9', label: '9', shiftLabel: '(', action: 'char' },
    { code: '0', label: '0', shiftLabel: ')', action: 'char' },
    { code: 'Back', label: '⌫', action: 'backspace' }
  ],
  [
    { code: 'q', label: 'q', shiftLabel: 'Q', action: 'char' },
    { code: 'w', label: 'w', shiftLabel: 'W', action: 'char' },
    { code: 'e', label: 'e', shiftLabel: 'E', action: 'char' },
    { code: 'r', label: 'r', shiftLabel: 'R', action: 'char' },
    { code: 't', label: 't', shiftLabel: 'T', action: 'char' },
    { code: 'y', label: 'y', shiftLabel: 'Y', action: 'char' },
    { code: 'u', label: 'u', shiftLabel: 'U', action: 'char' },
    { code: 'i', label: 'i', shiftLabel: 'I', action: 'char' },
    { code: 'o', label: 'o', shiftLabel: 'O', action: 'char' },
    { code: 'p', label: 'p', shiftLabel: 'P', action: 'char' },
    { code: 'minus', label: '-', shiftLabel: '_', action: 'char' }
  ],
  [
    { code: 'a', label: 'a', shiftLabel: 'A', action: 'char' },
    { code: 's', label: 's', shiftLabel: 'S', action: 'char' },
    { code: 'd', label: 'd', shiftLabel: 'D', action: 'char' },
    { code: 'f', label: 'f', shiftLabel: 'F', action: 'char' },
    { code: 'g', label: 'g', shiftLabel: 'G', action: 'char' },
    { code: 'h', label: 'h', shiftLabel: 'H', action: 'char' },
    { code: 'j', label: 'j', shiftLabel: 'J', action: 'char' },
    { code: 'k', label: 'k', shiftLabel: 'K', action: 'char' },
    { code: 'l', label: 'l', shiftLabel: 'L', action: 'char' },
    { code: 'colon', label: ':', shiftLabel: ';', action: 'char' },
    { code: 'Shift', label: '⇧', action: 'shift' }
  ],
  [
    { code: 'z', label: 'z', shiftLabel: 'Z', action: 'char' },
    { code: 'x', label: 'x', shiftLabel: 'X', action: 'char' },
    { code: 'c', label: 'c', shiftLabel: 'C', action: 'char' },
    { code: 'v', label: 'v', shiftLabel: 'V', action: 'char' },
    { code: 'b', label: 'b', shiftLabel: 'B', action: 'char' },
    { code: 'n', label: 'n', shiftLabel: 'N', action: 'char' },
    { code: 'm', label: 'm', shiftLabel: 'M', action: 'char' },
    { code: 'dot', label: '.', shiftLabel: ',', action: 'char' },
    { code: 'slash', label: '/', shiftLabel: '?', action: 'char' },
    { code: 'Space', label: 'Space', action: 'space' },
    { code: 'Enter', label: 'Enter', action: 'enter' }
  ]
])

function getKeyLabel(key: Key): string {
  if (key.action === 'char') {
    return isShift.value ? (key.shiftLabel ?? key.label.toUpperCase()) : key.label
  }
  return key.label
}

function getKeyClass(key: Key) {
  return {
    'key-action': key.action !== 'char',
    'key-shift-active': key.action === 'shift' && isShift.value,
    'key-space': key.action === 'space',
    'key-backspace': key.action === 'backspace',
    'key-enter': key.action === 'enter'
  }
}

function handleKeyPress(key: Key) {
  let val = props.modelValue

  if (key.action === 'char') {
    val += getKeyLabel(key)
  } else if (key.action === 'space') {
    val += ' '
  } else if (key.action === 'backspace') {
    if (val.length > 0) {
      val = val.slice(0, -1)
    }
  } else if (key.action === 'shift') {
    isShift.value = !isShift.value
    return
  } else if (key.action === 'enter') {
    emit('close')
    return
  }

  emit('update:modelValue', val)
}
</script>

<style scoped>
.onscreen-keypad-container {
  background-color: var(--color-surface-dark, #1c1c1e);
  border-top: 1px solid var(--color-border);
  padding: var(--spacing-sm);
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.4);
  width: 100%;
  box-sizing: border-box;
}

.onscreen-keypad {
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.keypad-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xs);
  padding: 0 var(--spacing-xs);
}

.keypad-title {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.keypad-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.keypad-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  width: 100%;
}

.keypad-key {
  flex: 1;
  min-width: 38px;
  height: 44px; /* Touch target min height */
  background-color: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm, 4px);
  color: var(--color-text, #ffffff);
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.1s var(--ease-out);
  padding: 0;
  user-select: none;
}

.keypad-key:active {
  background-color: rgba(255, 255, 255, 0.2);
}

.keypad-key.key-action {
  background-color: rgba(255, 255, 255, 0.15);
  font-size: 0.9rem;
}

.keypad-key.key-shift-active {
  background-color: var(--color-primary, #007aff);
  color: #ffffff;
}

.keypad-key.key-space {
  flex: 3;
}

.keypad-key.key-enter {
  background-color: var(--color-success, #34c759);
  color: #ffffff;
  flex: 1.5;
}

.keypad-key.key-backspace {
  flex: 1.2;
}

.btn-close {
  min-height: 36px;
  min-width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
</style>
