<template>
  <section class="panel" id="notifications">
    <div class="panel-head"><h2>Toast notifications</h2><span class="hint">The small pop-ups over the dashboard.</span></div>
    <div class="panel-body">
      <div class="row" data-testid="app-toasts">
        <div class="row-text">
          <span class="label">App toasts</span>
          <p>Results of pressing keys, saves and errors. <b>Errors only</b> hides the success messages.</p>
        </div>
        <div class="row-control">
          <div class="seg" role="radiogroup" aria-label="App toast level">
            <label v-for="opt in toastLevelOptions" :key="opt.value"><input type="radio" :value="opt.value" v-model="settings.toastLevel" /><span>{{ opt.label }}</span></label>
          </div>
          <SettingResetButton label="App toasts" :at-default="settings.toastLevel === SETTINGS_DEFAULTS.toastLevel" @reset="settings.toastLevel = SETTINGS_DEFAULTS.toastLevel" />
        </div>
      </div>
    </div>
    <div class="panel-head"><h2>AI agent toasts</h2><span class="hint">Pick the moments you want a toast for. They show even when app toasts are off.</span></div>
    <div class="panel-body" data-testid="agent-toasts">
      <div class="row">
        <div class="row-text">
          <span class="label">Agent goes idle</span>
          <p>Claude Code, Cursor or another agent finished and is waiting for your next prompt.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Toast when an agent goes idle</span><input v-model="settings.agentToastIdle" type="checkbox" data-action="agent-toast-idle" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Agent needs permission</span>
          <p>An agent is blocked on an approval dialog.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Toast when an agent needs permission</span><input v-model="settings.agentToastPermission" type="checkbox" data-action="agent-toast-permission" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Agent starts working</span>
          <p>An idle agent picks up a prompt and starts working.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Toast when an agent starts working</span><input v-model="settings.agentToastWorking" type="checkbox" data-action="agent-toast-working" /><span class="track"></span></label>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import SettingResetButton from '@/components/SettingResetButton.vue'

const settings = useSettingsStore()

const toastLevelOptions = [
  { value: 'all', label: 'All' },
  { value: 'errors-only', label: 'Errors only' },
  { value: 'off', label: 'Off' },
] as const
</script>
