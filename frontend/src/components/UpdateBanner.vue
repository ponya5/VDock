<template>
  <div v-if="update.visible && update.status" class="update-banner" role="status" data-testid="update-banner">
    <template v-if="update.busy">
      <span class="ub-text" data-testid="update-progress">{{ progressText }}</span>
    </template>
    <template v-else-if="update.state === 'error'">
      <span class="ub-text ub-error" data-testid="update-error">{{ update.status.stateMessage || update.status.error || 'Update failed' }}</span>
      <button type="button" class="ub-btn" @click="update.dismiss()">Dismiss</button>
    </template>
    <template v-else>
      <span class="ub-text">VDock {{ update.status.latest }} is available</span>
      <button v-if="update.status.canAutoInstall && !isPhone && !update.forbidden" type="button" class="ub-btn ub-primary" data-testid="update-now" @click="update.install()">Update now</button>
      <span v-else-if="update.status.canAutoInstall" class="ub-hint" data-testid="update-pc-hint">Update from your PC</span>
      <button v-else type="button" class="ub-btn ub-primary" data-testid="update-download" @click="openLink(update.status.downloadUrl)">Download</button>
      <button v-if="update.status.releaseUrl" type="button" class="ub-btn" data-testid="update-notes" @click="openLink(update.status.releaseUrl)">What's new</button>
      <button type="button" class="ub-btn" data-testid="update-later" @click="update.dismiss()">Later</button>
      <span v-if="update.installError" class="ub-text ub-error">{{ update.installError }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useUpdateStore } from '@/stores/update'
import { useDeviceClass } from '@/composables/useDeviceClass'
import { openLink } from '@/utils/openLink'

const update = useUpdateStore()
const { deviceClass } = useDeviceClass()
const isPhone = computed(() => deviceClass.value === 'phone')

const progressText = computed(() => {
  const msg = update.status?.stateMessage
  if (msg) return msg
  switch (update.state) {
    case 'downloading': return 'Downloading update…'
    case 'installing': return 'Installing update…'
    default: return 'Restarting VDock…'
  }
})

onMounted(() => update.start())
</script>

<style scoped>
/* Overlay: floats above the deck so it never moves a key. */
.update-banner {
  position: fixed;
  bottom: max(10px, env(safe-area-inset-bottom));
  left: 50%;
  transform: translateX(-50%);
  z-index: 8900;
  max-width: min(94vw, 640px);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 8px 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--line-soft, rgba(255, 255, 255, 0.18));
  background: rgba(16, 22, 36, 0.94);
  color: var(--text, #e8eefc);
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
}
.ub-text { padding-right: 4px; }
.ub-error { color: #ffb4a8; }
.ub-hint { color: var(--text-2, #aab4cc); font-weight: 500; }
.ub-btn {
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.ub-primary {
  background: var(--accent, #4f8cff);
  border-color: transparent;
  color: #fff;
}
.ub-btn:active { transform: scale(0.96); }
</style>
