<template>
        <div class="content has-rail">
<div class="col">
  <section class="panel" id="display">
    <div class="panel-head">
      <h2>Display (this device)</h2>
      <span class="hint">Day mode swaps the dark look for a light one. It applies to this browser only.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Day mode" :at-default="devicePrefs.dayMode === 'off'" @reset="devicePrefs.dayMode = 'off'" />
    </div>
    <div class="panel-body">
      <div class="row" id="day-mode">
        <div class="row-text">
          <span class="label">Day mode</span>
          <p>Auto follows this device's light or dark setting. Day mode turns the animated wallpaper off.</p>
        </div>
        <div class="row-control">
          <div class="seg" role="radiogroup" aria-label="Day mode">
            <label><input type="radio" value="off" v-model="devicePrefs.dayMode" /><span>Dark</span></label>
            <label><input type="radio" value="on" v-model="devicePrefs.dayMode" /><span>Day</span></label>
            <label><input type="radio" value="auto" v-model="devicePrefs.dayMode" /><span>Auto</span></label>
          </div>
        </div>
      </div>
      <div class="row" id="rail-autohide">
        <div class="row-text">
          <span class="label">Hide the scene bar (phone, landscape)</span>
          <p>Folds the scene bar away after a few idle seconds. Fullscreen and the menu button stay put; tap the menu icon to bring it back.</p>
        </div>
        <div class="row-control">
          <div class="seg" role="radiogroup" aria-label="Hide the scene bar">
            <label v-for="s in RAIL_AUTO_HIDE_CHOICES" :key="s"><input type="radio" :value="s" v-model="devicePrefs.railAutoHide" /><span>{{ s ? `${s}s` : 'Never' }}</span></label>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="typography">
    <div class="panel-head">
      <h2>Typography</h2>
      <span class="hint">Button labels, scene pills and the sidebar. The screensaver keeps its own fonts.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Dashboard font" :at-default="settingsStore.dashboardFont === SETTINGS_DEFAULTS.dashboardFont" @reset="settingsStore.dashboardFont = SETTINGS_DEFAULTS.dashboardFont" />
    </div>
    <div class="panel-body">
      <div class="row stack picker-row">
        <div class="picker picker-3 font-style-picker">
          <label v-for="opt in dashboardFontOptions" :key="opt.value" class="pick specimen">
            <input type="radio" :value="opt.value" v-model="settingsStore.dashboardFont" />
            <span class="tick"><FontAwesomeIcon :icon="['fas', 'check']" /></span>
            <span class="aa" :style="{ fontFamily: opt.family }">Aa</span>
            <span class="num" :style="{ fontFamily: opt.family }">12:34</span>
            <span>{{ opt.name }}</span>
          </label>
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="clock-format">
    <div class="panel-head"><h2>Clocks</h2><span class="hint">Time format across the screensaver, session lists and logs.</span></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">24-hour clocks</span>
          <p>Show every clock in 24-hour time. Off follows this device's locale.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">24-hour clocks</span><input v-model="settings.clock24h" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="24-hour clocks" :at-default="settings.clock24h === SETTINGS_DEFAULTS.clock24h" @reset="settings.clock24h = SETTINGS_DEFAULTS.clock24h" />
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="sidebar">
    <div class="panel-head"><h2>Docked sidebar</h2><span class="hint">A permanent column of keys down the left of the dashboard.</span></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Show docked sidebar</span>
          <p>A permanent column of scene and macro keys down the left of the dashboard.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Show docked sidebar</span><input v-model="settings.dockedSidebarEnabled" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Show docked sidebar" :at-default="settings.dockedSidebarEnabled === SETTINGS_DEFAULTS.dockedSidebarEnabled" @reset="settings.dockedSidebarEnabled = SETTINGS_DEFAULTS.dockedSidebarEnabled" />
        </div>
      </div>
      <template v-if="settings.dockedSidebarEnabled">
        <div class="row stack">
          <div class="row-head">
            <div class="row-text">
              <span class="label">Sidebar width</span>
              <p>How much horizontal space the docked column takes.</p>
            </div>
            <SettingResetButton label="Sidebar width" :at-default="settings.dockedSidebarWidth === SETTINGS_DEFAULTS.dockedSidebarWidth" @reset="settings.dockedSidebarWidth = SETTINGS_DEFAULTS.dockedSidebarWidth" />
          </div>
          <div class="row-control">
            <div class="slider">
              <span class="cap">80px</span>
              <input v-model.number="settings.dockedSidebarWidth" type="range" min="80" max="360" step="10" :style="sliderFill(settings.dockedSidebarWidth, 80, 360)" aria-label="Sidebar width" />
              <span class="cap">360px</span>
              <span class="val">{{ settings.dockedSidebarWidth }}px</span>
            </div>
          </div>
        </div>
        <div class="row stack">
          <div class="row-head">
            <div class="row-text">
              <span class="label">Button height</span>
              <p>Height of each docked key. Shrinks automatically if the column runs out of room.</p>
            </div>
            <SettingResetButton label="Button height" :at-default="settings.dockedButtonHeight === SETTINGS_DEFAULTS.dockedButtonHeight" @reset="settings.dockedButtonHeight = SETTINGS_DEFAULTS.dockedButtonHeight" />
          </div>
          <div class="row-control">
            <div class="slider">
              <span class="cap">48px</span>
              <input v-model.number="settings.dockedButtonHeight" type="range" min="48" max="160" step="4" :style="sliderFill(settings.dockedButtonHeight, 48, 160)" aria-label="Docked button height" />
              <span class="cap">160px</span>
              <span class="val">{{ settings.dockedButtonHeight }}px</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </section>

</div>

<div class="rail">
  <div class="preview">
    <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Dashboard preview</div>
    <div class="preview-stage preview-stage-grid" :style="{ fontFamily: dashboardFontFamily }">
      <div class="mock-dash">
        <div v-if="settings.dockedSidebarEnabled" class="mock-dash-side" :style="{ width: `${Math.round(settings.dockedSidebarWidth * 0.3)}px` }">
          <span v-for="i in 3" :key="i" class="mock-key side" :style="{ height: `${Math.round(settings.dockedButtonHeight * 0.4)}px` }"></span>
        </div>
        <div class="mock-dash-grid">
          <span v-for="i in 12" :key="i" class="mock-key"></span>
        </div>
      </div>
    </div>
    <div class="preview-foot">
      {{ settings.dockedSidebarEnabled ? `Sidebar at ${settings.dockedSidebarWidth}px, keys at ${settings.dockedButtonHeight}px` : 'Sidebar hidden' }} — {{ dashboardFontOptions.find(o => o.value === settingsStore.dashboardFont)?.name }}.
    </div>
  </div>
</div>
        </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import SettingResetButton from '@/components/SettingResetButton.vue'
import { sliderFill } from '@/utils/sliderFill'
import { RAIL_AUTO_HIDE_CHOICES, useDevicePrefs } from '@/services/devicePrefs'

const settingsStore = useSettingsStore()
const devicePrefs = useDevicePrefs()
const settings = computed(() => settingsStore)

// Dashboard font picker — samples render in the real font so the card can't
// drift from what the dashboard will show.
const dashboardFontOptions: { value: 'default' | 'editorial' | 'mono'; name: string; sample: string; family: string }[] = [
  { value: 'default', name: 'Modern Sans', sample: 'Aa 12:34', family: "'Heebo', system-ui, sans-serif" },
  { value: 'editorial', name: 'Editorial', sample: 'Aa 12:34', family: "'Instrument Serif', Georgia, serif" },
  { value: 'mono', name: 'Terminal Mono', sample: 'Aa 12:34', family: "'JetBrains Mono', monospace" },
]
const dashboardFontFamily = computed(() =>
  dashboardFontOptions.find(o => o.value === settingsStore.dashboardFont)?.family
)
</script>

<style scoped>
.pick {
  touch-action: manipulation; }
.pick input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
@media (hover: hover) and (pointer: fine) {
  .pick:hover {
    border-color: #2c4368;
    color: var(--text);
  }
}
.pick:active { transform: scale(0.98); }
.pick:has(input:checked) {
  border-color: var(--accent);
  background: var(--accent-ghost);
  color: #fff;
  font-weight: 600;
}
.pick:has(input:focus-visible) {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.pick .tick {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--accent);
  display: none;
  place-items: center;
  color: #fff;
  font-size: var(--fs-xs);
}
.pick:has(input:checked) .tick {
  display: grid;
  animation: tick-pop 0.22s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.pick.specimen {
  padding: 14px 10px;
  gap: 4px;
}
.pick.specimen .aa {
  font-size: var(--fs-xl);
  color: var(--text);
  line-height: 1.15;
}
.pick.specimen .num {
  font-size: var(--fs-lg);
  letter-spacing: 0.04em;
  color: var(--text);
}
.mock-key.side { aspect-ratio: auto; }
.mock-dash-side .mock-key { border-radius: 8px; }
.mock-dash-grid .mock-key { border-radius: 8px; }
@media (max-width: 880px) {
  .picker-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) {
  .pick {
    transition: none; }
  .pick:has(input:checked) .tick {
    animation: none; }
}
</style>
