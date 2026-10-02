<template>
  <Teleport to="body">
    <Transition name="dock-pop">
      <div
        v-if="enabled && alerts.alerts.value.length"
        class="agent-waiting-dock"
        role="status"
        :aria-label="dockAriaLabel"
      >
        <button
          type="button"
          class="dock-inbox"
          title="Open Mission Control - every agent session and pending approval"
          data-testid="dock-inbox"
          @click="openMissionControl"
        >
          <FontAwesomeIcon :icon="['fas', 'satellite-dish']" />
          Mission Control
        </button>
        <div
          v-for="alert in alerts.alerts.value"
          :key="alert.source"
          class="dock-chip"
          role="button"
          tabindex="0"
          :title="`${alerts.sourceLabelFor(alert.source)} needs you${alert.project ? ` — ${alert.project}` : ''}`"
          @click="navigate(alert.source)"
          @keydown.enter="navigate(alert.source)"
        >
          <span class="dock-dot" aria-hidden="true"><span class="dock-pulse"></span></span>
          <span class="dock-label">{{ alerts.sourceLabelFor(alert.source) }}</span>
          <span v-if="alert.project" class="dock-project">{{ alert.project }}</span>
          <button
            class="dock-dismiss"
            :title="`Dismiss ${alerts.sourceLabelFor(alert.source)}`"
            @click.stop="alerts.dismiss(alert.source)"
          >
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useAgentAlerts } from '@/services/agentAlerts'
import { useSettingsStore } from '@/stores/settings'
import { openMissionControl } from '@/services/missionControl'

/**
 * DL-119: persistent "who needs you" dock. One chip per pending per-source
 * alert, pinned to the bottom-right corner just under the alert overlay's
 * z-index — after the banner is dismissed the chips stay until each alert
 * actually clears backend-side (per-source dismiss, state change, or TTL).
 *
 * A chip tap asks the shell to navigate to that agent's scene via the
 * `vdock:navigate-scene` window event (the listener is wired by the
 * orchestrator — this component deliberately does not touch the dashboard
 * store). The × on a chip dismisses just that source's alert.
 */

const alerts = useAgentAlerts()
const settingsStore = useSettingsStore()

const enabled = computed(() =>
  settingsStore.agentAlertsEnabled !== false &&
  settingsStore.agentWaitingDockEnabled !== false)

const dockAriaLabel = computed(() => {
  const count = alerts.alerts.value.length
  return count === 1
    ? `${alerts.sourceLabelFor(alerts.alerts.value[0].source)} is waiting for input`
    : `${count} agents are waiting for input`
})

function navigate(source: string) {
  window.dispatchEvent(new CustomEvent('vdock:navigate-scene', { detail: { source } }))
}
</script>

<style scoped>
/* Bottom-right corner, under the overlay (30000) but above everything else —
   the chips must survive the banner being dismissed. */
.agent-waiting-dock {
  position: fixed;
  right: clamp(10px, 2vw, 22px);
  bottom: clamp(10px, 2.4vh, 22px);
  z-index: 29000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: clamp(8px, 1.6vh, 14px);
}

.dock-chip {
  display: flex;
  align-items: center;
  gap: clamp(8px, 1.4vw, 14px);
  padding: clamp(8px, 1.8vh, 14px) clamp(12px, 2vw, 18px);
  border-radius: 999px;
  background: rgba(46, 32, 8, 0.95);
  border: 2px solid #f5a524;
  box-shadow: 0 0 0 3px rgba(245, 165, 36, 0.18), 0 10px 30px rgba(0, 0, 0, 0.55);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
  color: #ffd89e;
  font-size: clamp(0.9rem, 2.6vh, 1.2rem);
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
  white-space: nowrap;
  max-width: min(70vw, 420px);
}

.dock-inbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: clamp(6px, 1.4vh, 10px) clamp(12px, 1.8vw, 16px);
  border-radius: 999px;
  border: 1px solid #3b5a8c;
  background: rgba(15, 24, 41, 0.95);
  color: #9cc2ff;
  font: inherit;
  font-size: clamp(0.8rem, 2.2vh, 1rem);
  font-weight: 600;
  cursor: pointer;
  touch-action: manipulation;
}
.dock-inbox:active { transform: scale(0.97); }

.dock-chip:hover { filter: brightness(1.1); }
.dock-chip:active { transform: scale(0.97); }

.dock-dot {
  position: relative;
  flex-shrink: 0;
  width: clamp(10px, 2.4vh, 16px);
  height: clamp(10px, 2.4vh, 16px);
  border-radius: 50%;
  background: #f5a524;
}

.dock-pulse {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid rgba(245, 165, 36, 0.6);
  animation: dock-pulse 1.6s ease-out infinite;
}

@keyframes dock-pulse {
  0% { transform: scale(0.85); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

.dock-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.dock-project {
  color: #c9a061;
  font-weight: 500;
  font-size: 0.85em;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 12em;
}

.dock-dismiss {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: clamp(24px, 5vh, 34px);
  height: clamp(24px, 5vh, 34px);
  border-radius: 50%;
  border: none;
  background: rgba(245, 165, 36, 0.18);
  color: #ffd89e;
  font-size: clamp(0.7rem, 2vh, 0.95rem);
  cursor: pointer;
  touch-action: manipulation;
}

.dock-dismiss:hover { background: rgba(245, 165, 36, 0.4); }

.dock-pop-enter-active,
.dock-pop-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.dock-pop-enter-from,
.dock-pop-leave-to {
  transform: translateY(14px);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .dock-pulse { animation: none; opacity: 0; }
}
</style>
