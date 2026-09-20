<template>
  <Teleport to="body">
    <Transition name="alert-pop">
      <div v-if="alerts.alert.value && enabled" class="agent-alert" role="alert">
        <div class="alert-icon">
          <FontAwesomeIcon :icon="['fas', 'robot']" />
          <span class="alert-pulse"></span>
        </div>
        <div class="alert-body">
          <div class="alert-title">{{ alerts.sourceLabel.value }} needs you</div>
          <div class="alert-message">{{ alerts.alert.value.message }}</div>
          <div v-if="alerts.alert.value.project" class="alert-project">
            <FontAwesomeIcon :icon="['fas', 'folder']" /> {{ alerts.alert.value.project }}
          </div>
        </div>
        <button class="alert-dismiss" @click="alerts.dismiss">
          <FontAwesomeIcon :icon="['fas', 'check']" /> Got it
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useAgentAlerts } from '@/services/agentAlerts'
import { useSettingsStore } from '@/stores/settings'

const alerts = useAgentAlerts()
const settingsStore = useSettingsStore()
const enabled = computed(() => settingsStore.agentAlertsEnabled !== false)
</script>

<style scoped>
/* Sits above everything — dashboard (1000/2000), screensaver (500),
   tutorial (10000) — the whole point is you can't miss it. */
.agent-alert {
  position: fixed;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30000;
  display: flex;
  align-items: center;
  gap: 16px;
  max-width: min(560px, calc(100vw - 24px));
  padding: 14px 18px;
  border-radius: 16px;
  background: rgba(46, 32, 8, 0.96);
  border: 1.5px solid #f5a524;
  box-shadow: 0 0 0 4px rgba(245, 165, 36, 0.18), 0 14px 44px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  color: #ffd89e;
}

.alert-icon {
  position: relative;
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: rgba(245, 165, 36, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  color: #f5a524;
}

.alert-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  border: 2px solid rgba(245, 165, 36, 0.6);
  animation: alert-pulse 1.6s ease-out infinite;
}

@keyframes alert-pulse {
  0% { transform: scale(0.9); opacity: 1; }
  100% { transform: scale(1.35); opacity: 0; }
}

.alert-body {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #ffe4b3;
}

.alert-message {
  font-size: 0.9rem;
  line-height: 1.4;
  color: #f0cf9a;
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.alert-project {
  font-size: 0.78rem;
  color: #c9a061;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-dismiss {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  min-height: 48px;
  border-radius: 12px;
  border: none;
  background: #f5a524;
  color: #2a1c04;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
}

.alert-dismiss:hover { filter: brightness(1.08); }

.alert-pop-enter-active,
.alert-pop-leave-active {
  transition: transform 0.28s ease, opacity 0.28s ease;
}
.alert-pop-enter-from,
.alert-pop-leave-to {
  transform: translateX(-50%) translateY(-16px);
  opacity: 0;
}
</style>
