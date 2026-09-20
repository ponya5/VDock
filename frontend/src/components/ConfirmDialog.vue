<template>
  <!-- Teleport to .theme-dark, not <body>: the theme class (and all themed
       CSS vars) live on App.vue's root, so body-level teleports render with
       unstyled light :root defaults. Same pattern as TouchModeSelector. -->
  <Teleport to=".theme-dark">
    <div v-if="request" class="modal-overlay confirm-overlay" @click.self="cancel">
      <div class="modal confirm-dialog" role="alertdialog" aria-modal="true">
        <div class="confirm-icon" :class="{ danger: request.danger }">
          <FontAwesomeIcon :icon="['fas', request.icon]" />
        </div>
        <h2 class="confirm-title">{{ request.title }}</h2>
        <p class="confirm-message">{{ request.message }}</p>
        <div class="confirm-actions">
          <button class="btn btn-secondary" @click="cancel">
            {{ request.cancelLabel }}
          </button>
          <button
            class="btn"
            :class="request.danger ? 'btn-danger' : 'btn-primary'"
            autofocus
            @click="accept"
          >
            {{ request.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onUnmounted } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useConfirmDialog, settleConfirmDialog } from '@/composables/useConfirm'

const request = useConfirmDialog()

const accept = () => settleConfirmDialog(true)
const cancel = () => settleConfirmDialog(false)

// Esc cancels, Enter accepts — same affordances as a native dialog.
function onKeydown(e: KeyboardEvent) {
  if (!request.value) return
  if (e.key === 'Escape') cancel()
  else if (e.key === 'Enter') accept()
}
if (typeof window !== 'undefined') window.addEventListener('keydown', onKeydown)
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.confirm-overlay {
  z-index: 4000; /* above button editor / settings overlays */
}

.confirm-dialog {
  width: min(420px, 92vw);
  padding: var(--spacing-lg);
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.confirm-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto var(--spacing-md);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  color: #7dbcff;
  background: rgba(74, 163, 255, 0.15);
  border: 1px solid rgba(74, 163, 255, 0.35);
}

.confirm-icon.danger {
  color: #ff6b5e;
  background: rgba(217, 45, 32, 0.15);
  border-color: rgba(217, 45, 32, 0.4);
}

.confirm-title {
  margin: 0 0 var(--spacing-xs);
  font-size: 1.2rem;
  color: var(--color-text);
}

.confirm-message {
  margin: 0 0 var(--spacing-lg);
  font-size: 0.92rem;
  line-height: 1.45;
  color: var(--color-text-secondary);
}

.confirm-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
}

.confirm-actions .btn {
  flex: 1;
  min-height: 46px;
  font-size: 1rem;
  font-weight: 600;
}
</style>
