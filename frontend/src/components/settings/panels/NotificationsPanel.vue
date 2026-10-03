<template>
  <section class="panel" id="notifications">
    <div class="panel-head"><h2>Notifications</h2></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Toast notifications</span>
          <p>Which action results pop up over the dashboard.</p>
        </div>
        <div class="row-control">
          <div class="seg" role="radiogroup" aria-label="Toast level">
            <label v-for="opt in toastLevelOptions" :key="opt.value"><input type="radio" :value="opt.value" v-model="settings.toastLevel" /><span>{{ opt.label }}</span></label>
          </div>
          <SettingResetButton label="Toast notifications" :at-default="settings.toastLevel === SETTINGS_DEFAULTS.toastLevel" @reset="settings.toastLevel = SETTINGS_DEFAULTS.toastLevel" />
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
