<template>
  <!-- Teleport to <body> — NOT .theme-dark: a component whose root vnode is a
       Teleport into its own ancestor breaks Vue's host-anchor tracking on
       update (getNextHostNode crash → the dialog silently never renders and
       the confirm promise never resolves). Since .theme-dark only defines CSS
       variables, carrying the class on the overlay itself gives the dialog
       the same themed vars without the ancestor-teleport bug. -->
  <Teleport to="body">
    <div v-if="request" class="modal-overlay confirm-overlay theme-dark" @click.self="cancel">
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
