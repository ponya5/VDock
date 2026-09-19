<template>
  <div ref="rootRef" class="bg-picker">
    <button
      ref="triggerRef"
      type="button"
      class="select bg-picker__trigger"
      :aria-expanded="open"
      aria-haspopup="listbox"
      @click="toggle"
      @keydown.down.prevent="openAndFocus(0)"
      @keydown.up.prevent="openAndFocus(-1)"
    >
      <span class="bg-picker__value">{{ selectedLabel }}</span>
      <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="bg-picker__chevron" :class="{ open }" />
    </button>

    <Teleport to=".theme-dark">
      <div
        v-if="open"
        ref="panelRef"
        class="bg-picker__panel"
        :style="panelStyle"
        role="listbox"
        :aria-activedescendant="activeId"
        tabindex="-1"
        @scroll="updateScrollState"
        @keydown="onPanelKeydown"
      >
        <template v-for="group in groups" :key="group.label">
          <div v-if="group.options.length" class="bg-picker__group" role="presentation">
            {{ group.label }}
          </div>
          <button
            v-for="option in group.options"
            :key="option.id"
            :id="optionDomId(option.id)"
            type="button"
            class="bg-picker__option"
            :class="{ selected: option.id === modelValue, highlighted: option.id === highlightedId }"
            role="option"
            :aria-selected="option.id === modelValue"
            @click="choose(option.id)"
            @mousemove="highlightedId = option.id"
          >
            <FontAwesomeIcon
              :icon="['fas', 'check']"
              class="bg-picker__check"
              :style="{ visibility: option.id === modelValue ? 'visible' : 'hidden' }"
            />
            <span>{{ option.label }}</span>
          </button>
        </template>
        <div class="bg-picker__scrollhint" aria-hidden="true">
          <FontAwesomeIcon :icon="['fas', 'chevron-down']" />
        </div>
      </div>
    </Teleport>
    <Teleport to=".theme-dark">
      <div v-if="open" class="bg-picker__backdrop" @pointerdown="close" />
    </Teleport>
  </div>
</template>

<script setup lang="ts">
// Custom grouped listbox for the background catalog.
//
// A native <select> popup paints its own OS-level scrollbar that CSS cannot
// reach -- on the dark theme it renders nearly invisible, so users could not
// tell the list scrolled (the "no more options" confusion). This picker owns
// its scroll area, so the scrollbar is styled for contrast and a bottom fade
// signals more options below. Rows are also >=40px for the 7" touchscreen.
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

export interface BackgroundPickerOption {
  id: string
  label: string
}

export interface BackgroundPickerGroup {
  label: string
  options: BackgroundPickerOption[]
}

const props = defineProps<{
  modelValue: string
  groups: BackgroundPickerGroup[]
}>()

const emit = defineEmits<{
  'update:modelValue': [id: string]
  change: [id: string]
}>()

const rootRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLButtonElement | null>(null)
const panelRef = ref<HTMLElement | null>(null)
const open = ref(false)
const highlightedId = ref<string | null>(null)
const panelStyle = ref<Record<string, string>>({})

const allOptions = computed(() => props.groups.flatMap(g => g.options))
const selectedLabel = computed(
  () => allOptions.value.find(o => o.id === props.modelValue)?.label ?? props.modelValue
)
const activeId = computed(() =>
  highlightedId.value ? optionDomId(highlightedId.value) : undefined
)

const optionDomId = (id: string) => `bg-picker-opt-${id.replace(/[^a-zA-Z0-9_-]/g, '-')}`

const positionPanel = () => {
  const trigger = triggerRef.value
  if (!trigger) return
  const rect = trigger.getBoundingClientRect()
  const maxHeight = Math.min(320, window.innerHeight - 16)
  const spaceBelow = window.innerHeight - rect.bottom - 8
  const openUp = spaceBelow < 180 && rect.top > spaceBelow
  panelStyle.value = {
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    maxHeight: `${maxHeight}px`,
    ...(openUp
      ? { bottom: `${window.innerHeight - rect.top + 4}px` }
      : { top: `${rect.bottom + 4}px` })
  }
}

const updateScrollState = () => {
  // Scroll state lives on the element via CSS-only fades; also toggles a
  // data attribute so the fade knows when more content exists below.
  const panel = panelRef.value
  if (!panel) return
  const below = panel.scrollHeight - panel.scrollTop - panel.clientHeight
  panel.dataset.moreBelow = below > 4 ? 'true' : undefined
  panel.dataset.moreAbove = panel.scrollTop > 4 ? 'true' : undefined
}

const scrollToSelected = () => {
  const panel = panelRef.value
  if (!panel) return
  const el = panel.querySelector(`#${optionDomId(props.modelValue)}`)
  el?.scrollIntoView({ block: 'center' })
  updateScrollState()
}

const openPanel = async (focusIndex?: number) => {
  open.value = true
  positionPanel()
  await nextTick()
  highlightedId.value =
    focusIndex === undefined
      ? props.modelValue
      : (allOptions.value[focusIndex === -1 ? allOptions.value.length - 1 : focusIndex]?.id ??
        props.modelValue)
  if (focusIndex === undefined) scrollToSelected()
  else {
    panelRef.value
      ?.querySelector(`#${optionDomId(highlightedId.value ?? '')}`)
      ?.scrollIntoView({ block: 'nearest' })
    updateScrollState()
  }
}

const openAndFocus = (index: number) => {
  if (open.value) return
  void openPanel(index)
}

const toggle = () => {
  if (open.value) close()
  else void openPanel()
}

const close = () => {
  open.value = false
}

const choose = (id: string) => {
  emit('update:modelValue', id)
  emit('change', id)
  close()
  triggerRef.value?.focus()
}

const moveHighlight = (delta: number) => {
  const options = allOptions.value
  if (!options.length) return
  const index = options.findIndex(o => o.id === highlightedId.value)
  const next = options[(index + delta + options.length) % options.length]
  highlightedId.value = next.id
  panelRef.value
    ?.querySelector(`#${optionDomId(next.id)}`)
    ?.scrollIntoView({ block: 'nearest' })
  updateScrollState()
}

const onPanelKeydown = (event: KeyboardEvent) => {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    moveHighlight(1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    moveHighlight(-1)
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    if (highlightedId.value) choose(highlightedId.value)
  } else if (event.key === 'Escape') {
    event.preventDefault()
    close()
    triggerRef.value?.focus()
  } else if (event.key === 'Home') {
    event.preventDefault()
    highlightedId.value = allOptions.value[0]?.id ?? null
  } else if (event.key === 'End') {
    event.preventDefault()
    highlightedId.value = allOptions.value[allOptions.value.length - 1]?.id ?? null
  }
}

const onGlobalKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && open.value) {
    close()
    triggerRef.value?.focus()
  }
}

const onWindowChange = () => {
  if (open.value) positionPanel()
}

watch(open, value => {
  if (value) {
    window.addEventListener('keydown', onGlobalKeydown, true)
    window.addEventListener('resize', onWindowChange)
    window.addEventListener('scroll', onWindowChange, true)
    nextTick(updateScrollState)
  } else {
    window.removeEventListener('keydown', onGlobalKeydown, true)
    window.removeEventListener('resize', onWindowChange)
    window.removeEventListener('scroll', onWindowChange, true)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKeydown, true)
  window.removeEventListener('resize', onWindowChange)
  window.removeEventListener('scroll', onWindowChange, true)
})
</script>

<style scoped>
.bg-picker {
  position: relative;
}

.bg-picker__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  cursor: pointer;
  text-align: left;
}

.bg-picker__value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bg-picker__chevron {
  flex-shrink: 0;
  font-size: 0.75em;
  color: var(--color-text-secondary);
  transition: transform var(--transition-fast);
}

.bg-picker__chevron.open {
  transform: rotate(180deg);
}
</style>

<style>
/* Not scoped: the panel is teleported to <body>. */
.bg-picker__backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

.bg-picker__panel {
  position: fixed;
  z-index: 9999;
  overflow-y: auto;
  overscroll-behavior: contain;
  background: var(--color-surface-solid, #1a1d24);
  border: 1px solid var(--color-border, #2a2e3a);
  border-radius: var(--radius-md, 8px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
  padding: 4px;
  outline: none;
  /* Firefox: always-visible thin scrollbar with a contrasting thumb. */
  scrollbar-width: thin;
  scrollbar-color: var(--color-primary, #4f7cff) rgba(255, 255, 255, 0.07);
}

/* Chromium/WebKit: a real, always-on scrollbar the OS can't fade away. */
.bg-picker__panel::-webkit-scrollbar {
  width: 10px;
}

.bg-picker__panel::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.07);
  border-radius: 5px;
}

.bg-picker__panel::-webkit-scrollbar-thumb {
  background: var(--color-primary, #4f7cff);
  border-radius: 5px;
  border: 2px solid transparent;
  background-clip: padding-box;
  min-height: 28px;
}

.bg-picker__panel::-webkit-scrollbar-thumb:hover {
  background: var(--color-primary-light, #7b9dff);
  border: 2px solid transparent;
  background-clip: padding-box;
}

/* Scroll affordance: fades + edge hints that appear only when there is more
   content in that direction. */
.bg-picker__panel::before,
.bg-picker__panel::after {
  content: '';
  position: sticky;
  display: block;
  height: 18px;
  pointer-events: none;
  z-index: 1;
}

.bg-picker__panel::before {
  top: 0;
  margin-bottom: -18px;
  background: linear-gradient(to bottom, var(--color-surface-solid, #1a1d24), transparent);
  opacity: 0;
}

.bg-picker__panel[data-more-above]::before {
  opacity: 1;
}

.bg-picker__panel::after {
  bottom: 0;
  margin-top: -18px;
  background: linear-gradient(to top, var(--color-surface-solid, #1a1d24), transparent);
  opacity: 0;
}

.bg-picker__panel[data-more-below]::after {
  opacity: 1;
}

/* Sticky "scroll down" hint: pinned to the visible bottom edge while more
   options exist, hidden once the user reaches the end. Overlay scrollbars
   (touch devices) auto-hide, so this is the persistent affordance. */
.bg-picker__scrollhint {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: flex-end;
  height: 26px;
  padding-bottom: 5px;
  margin-top: -26px;
  color: var(--color-primary, #4f7cff);
  font-size: clamp(11px, 0.8vw + 9px, 14px);
  background: linear-gradient(to top, var(--color-surface-solid, #1a1d24) 30%, transparent);
  pointer-events: none;
  opacity: 0;
  transition: opacity var(--transition-fast, 150ms);
}

.bg-picker__panel[data-more-below] .bg-picker__scrollhint {
  opacity: 1;
}

.bg-picker__group {
  padding: 6px 10px 2px;
  font-size: clamp(10px, 0.6vw + 8px, 13px);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-secondary, #9aa0b0);
  user-select: none;
}

.bg-picker__option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 40px;
  padding: 8px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text, #e8eaf0);
  font-size: clamp(12px, 0.9vw + 10px, 16px);
  text-align: left;
  cursor: pointer;
  touch-action: manipulation;
}

.bg-picker__option:hover,
.bg-picker__option.highlighted {
  background: rgba(255, 255, 255, 0.08);
}

.bg-picker__option.selected {
  color: var(--color-primary, #4f7cff);
  font-weight: 600;
}

.bg-picker__check {
  width: 12px;
  flex-shrink: 0;
  font-size: clamp(10px, 0.6vw + 8px, 13px);
}
</style>
