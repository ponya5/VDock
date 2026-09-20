<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="quick-deck-backdrop"
      @click.self="close"
      @keydown.esc="close"
    >
      <div ref="panelRef" class="quick-deck-panel" role="dialog" aria-label="Quick deck">
        <div class="quick-deck-head">
          <span class="quick-deck-title">
            <FontAwesomeIcon :icon="['fas', 'bolt']" />
            {{ dashboardStore.currentScene?.name || 'Quick Deck' }}
          </span>
          <button class="qd-close" title="Close (Esc)" @click="close">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>

        <div
          v-if="buttons.length"
          class="quick-deck-grid"
          :style="gridStyle"
        >
          <DeckButton
            v-for="b in buttons"
            :key="b.id"
            :button="b"
            :show-labels="settingsStore.showLabels"
            :show-tooltips="false"
            compact
            @click="runButton"
            @press="runButton"
            @release="runRelease"
          />
        </div>
        <div v-else class="quick-deck-empty">
          <p>No buttons on this page yet.</p>
        </div>

        <p class="quick-deck-hint">
          <kbd>`</kbd> or <kbd>Esc</kbd> to close · Electron: <kbd>Ctrl+Shift+D</kbd> summons at cursor
        </p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
/**
 * Summon overlay — Elgato's "deck at cursor" idea. A hotkey pops a compact
 * copy of the current scene's buttons; pressing one runs it and closes.
 *
 * Trigger paths:
 *  - In-window: backtick (`) keydown in App.vue → CustomEvent.
 *  - Electron: Ctrl+Shift+D (main.js globalShortcut) → IPC → CustomEvent.
 *  - Remote: ui_command socket relay ('toggle_quick_deck', allowlisted) — a
 *    LAN panel or second window can summon this deck's overlay.
 *
 * Browsers cannot register OS-global hotkeys — the in-window shortcut is the
 * honest scope for a plain web client; the global one lives in Electron.
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import DeckButton from './DeckButton.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { useButtonStateStore } from '@/stores/buttonState'
import { useNotificationsStore } from '@/stores/notifications'
import { listenForUiCommands } from '@/composables/useUiCommands'
import type { Button } from '@/types'

const QUICK_DECK_EVENT = 'vdock-quick-deck'

const open = ref(false)
const panelRef = ref<HTMLElement | null>(null)
const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()
const buttonStateStore = useButtonStateStore()
const notificationsStore = useNotificationsStore()

const buttons = computed<Button[]>(() =>
  dashboardStore.currentPage?.buttons?.filter((b) => b.enabled !== false) ?? []
)

const gridStyle = computed(() => {
  const cols = dashboardStore.currentPage?.grid_config?.cols ?? 4
  return { gridTemplateColumns: `repeat(${Math.max(cols, 1)}, minmax(0, 1fr))` }
})

function close() {
  open.value = false
}

function toggle() {
  open.value = !open.value
}

function runButton(button: Button) {
  const action = button.action
  if (!action) return
  buttonStateStore.markRunning(button.id)
  dashboardStore.executeButtonAction(button).then((result) => {
    buttonStateStore.markFinished(button.id, result)
    // Toggles and sliders keep the overlay open — flipping twice or nudging a
    // level several times is the whole point of the mini deck.
    if (action.type !== 'toggle' && action.type !== 'slider') close()
  }).catch(() => close())
}

function runRelease(button: Button) {
  const release = button.action?.release_action
  if (!release?.type) return
  dashboardStore.executeAction(release, button.id).catch(() => {})
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value) return
  if (e.key === 'Escape' || e.key === '`') {
    e.stopPropagation()
    close()
  }
}

let stopListening: (() => void) | undefined
function onCustomEvent() { toggle() }

onMounted(() => {
  stopListening = listenForUiCommands((cmd) => {
    if (cmd === 'toggle_quick_deck') toggle()
  })
  window.addEventListener(QUICK_DECK_EVENT, onCustomEvent)
  window.addEventListener('keydown', onKeydown)
  // Electron's global Ctrl+Shift+D lands here via preload's IPC bridge.
  ;(window as any).electron?.onQuickDeckToggle?.(() => toggle())
})

onUnmounted(() => {
  stopListening?.()
  window.removeEventListener(QUICK_DECK_EVENT, onCustomEvent)
  window.removeEventListener('keydown', onKeydown)
})

// Unused but keeps TS honest about the import being a store, not a composable.
void notificationsStore
void panelRef
</script>

<style scoped>
.quick-deck-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000; /* above screensaver (500), below agent alert (30000) */
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 12vh;
  background: rgba(8, 6, 30, 0.55);
  backdrop-filter: blur(4px);
}
.quick-deck-panel {
  width: min(560px, 92vw);
  max-height: 70vh;
  overflow: auto;
  background: var(--color-surface, rgba(24, 20, 56, 0.96));
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.14));
  border-radius: 20px;
  padding: 14px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.55);
}
.quick-deck-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.quick-deck-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 0.95rem;
}
.qd-close {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--color-text-muted, #9aa0b4);
  cursor: pointer;
  border-radius: 10px;
}
.qd-close:hover { color: var(--color-text, #fff); }
.quick-deck-grid {
  display: grid;
  gap: 10px;
}
.quick-deck-grid :deep(.deck-button) {
  min-height: 84px;
}
.quick-deck-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted, #9aa0b4);
}
.quick-deck-hint {
  margin: 12px 0 0;
  font-size: 0.7rem;
  color: var(--color-text-muted, #9aa0b4);
  text-align: center;
}
.quick-deck-hint kbd {
  padding: 1px 6px;
  border: 1px solid var(--color-border, rgba(255, 255, 255, 0.2));
  border-radius: 4px;
  font-size: 0.65rem;
}
</style>
