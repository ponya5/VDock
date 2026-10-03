<template>
<section class="panel" id="recent-actions">
  <div class="panel-head">
    <h2>Recent actions</h2>
    <span class="spacer"></span>
    <button v-if="settings.recentActions.length" type="button" class="btn quiet sm" @click="clearRecentActions">Clear</button>
  </div>
  <div class="panel-body">
    <div v-if="settings.recentActions.length > 0" class="recent-actions">
      <div v-for="(actionId, index) in settings.recentActions" :key="index" class="recent-action-item">{{ actionId }}</div>
    </div>
    <div v-else class="empty-state">No recent actions</div>
  </div>
</section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { confirmDialog } from '@/composables/useConfirm'

const settingsStore = useSettingsStore()
const settings = computed(() => settingsStore)

async function clearRecentActions() {
  const ok = await confirmDialog({
    title: 'Clear recent actions?',
    message: 'The list of recently used actions will be emptied.',
    confirmLabel: 'Clear',
    icon: 'clock-rotate-left',
  })
  if (ok) settingsStore.clearRecentActions()
}
</script>

<style scoped>
.recent-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}
.recent-action-item {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(0,0,0,0.15);
  border-radius: var(--radius-sm);
  font-size: clamp(11px, 0.6vw + 8px, 13px);
  font-family: monospace;
}
</style>
