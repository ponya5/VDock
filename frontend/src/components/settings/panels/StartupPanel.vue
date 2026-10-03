<template>
  <section class="panel" id="startup">
    <div class="panel-head"><h2>Startup &amp; navigation</h2></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Close launcher terminal after startup</span>
          <p>Closes the launcher window once VDock starts. Turn off to keep it open for debugging.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Close launcher terminal</span><input v-model="settings.autoCloseLauncher" type="checkbox" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Open settings in a new browser tab</span>
          <p>Opens Settings separately instead of navigating inside VDock.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Open settings in a new tab</span><input v-model="settings.openSettingsInNewTab" type="checkbox" /><span class="track"></span></label>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'

const settings = useSettingsStore()
</script>
