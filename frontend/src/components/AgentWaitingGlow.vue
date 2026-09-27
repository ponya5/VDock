<template>
  <Teleport to="body">
    <div
      v-if="isWaiting"
      class="agent-waiting-glow"
      :class="{ 'no-anim': !settingsStore.animationsEnabled }"
      role="status"
      :aria-label="`${profile?.label ?? 'Agent'} is waiting for input`"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import type { Scene } from '@/types'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { useAgentSession } from '@/composables/useAgentSession'

/**
 * Waiting-agent edge glow (DL-080): while an IDE scene's agent sits in the
 * `ready` state — idle, waiting for a command — the viewport edges breathe
 * green so the user notices a session wants input. Complements the
 * permission state's AgentAlertOverlay banner; gated by
 * `agentWaitingGlowEnabled` (default on).
 */

const props = defineProps<{ scene: Scene | null }>()

const dashboardStore = useDashboardStore()
const settingsStore = useSettingsStore()
const { profile, currentState, isAgentPossiblyRunning } = useAgentSession(toRef(props, 'scene'))

const isWaiting = computed(() =>
  settingsStore.agentWaitingGlowEnabled !== false &&
  !dashboardStore.isEditMode &&
  isAgentPossiblyRunning.value &&
  currentState.value === 'ready'
)
</script>

<style scoped>
/* Fixed frame painted over the dashboard (1000/2000) but under dialogs and
   the agent-target popover (1500+): the waiting cue must not pretend to be a
   modal. pointer-events none keeps every press landing on the deck. */
.agent-waiting-glow {
  position: fixed;
  inset: 0;
  z-index: 1400;
  pointer-events: none;
  border: 3px solid rgba(34, 197, 94, 0.85);
  box-shadow:
    inset 0 0 clamp(24px, 6vh, 64px) rgba(34, 197, 94, 0.4),
    0 0 clamp(16px, 3vh, 36px) rgba(34, 197, 94, 0.3);
  animation: agent-waiting-breathe 2.4s ease-in-out infinite;
}

.agent-waiting-glow.no-anim {
  animation: none;
}

@keyframes agent-waiting-breathe {
  0%, 100% {
    border-color: rgba(34, 197, 94, 0.85);
    box-shadow:
      inset 0 0 clamp(24px, 6vh, 64px) rgba(34, 197, 94, 0.4),
      0 0 clamp(16px, 3vh, 36px) rgba(34, 197, 94, 0.3);
  }
  50% {
    border-color: rgba(34, 197, 94, 0.4);
    box-shadow:
      inset 0 0 clamp(48px, 10vh, 110px) rgba(34, 197, 94, 0.55),
      0 0 clamp(28px, 5vh, 56px) rgba(34, 197, 94, 0.45);
  }
}

@media (prefers-reduced-motion: reduce) {
  .agent-waiting-glow { animation: none; }
}
</style>
