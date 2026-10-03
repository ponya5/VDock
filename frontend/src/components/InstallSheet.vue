<template>
  <div class="install-overlay" @click.self="emit('close')">
    <div class="install-sheet" role="dialog" aria-modal="true" aria-label="Add VDock to the Home Screen" data-testid="install-sheet">
      <h3>Add to Home Screen</h3>
      <ol class="install-steps">
        <li v-for="step in steps" :key="step">{{ step }}</li>
      </ol>
      <p v-if="note" class="install-note" data-testid="install-note">{{ note }}</p>
      <button type="button" class="install-done" @click="emit('close')">Got it</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { installNote, installPlatform, installSteps } from '@/utils/installCopy'

const emit = defineEmits<{ close: [] }>()

const platform = installPlatform(navigator.userAgent, navigator.maxTouchPoints)
const steps = installSteps(platform)
const note = installNote(platform, window.isSecureContext)
</script>

<style scoped>
.install-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 16px max(16px, env(safe-area-inset-right)) max(16px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
  background: rgba(0, 0, 0, 0.6);
}
.install-sheet {
  width: min(100%, 420px);
  padding: 20px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(24, 24, 40, 0.97);
  color: rgba(255, 255, 255, 0.88);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
}
.install-sheet h3 { margin: 0 0 10px; color: #fff; font-size: 1.05rem; }
.install-steps { margin: 0 0 12px; padding-left: 20px; display: grid; gap: 6px; font-size: 0.9rem; }
.install-note { margin: 0 0 12px; font-size: 0.8rem; color: #ffd89e; }
.install-done {
  width: 100%;
  min-height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  background: rgba(31, 111, 209, 0.5);
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
</style>
