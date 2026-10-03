<template>
        <div class="content has-rail">
<div class="col">
  <section class="panel" id="sizing">
    <div class="panel-head">
      <h2>Sizing &amp; touch</h2>
      <span class="hint">How big every key is. Touch mode and button size multiply.</span>
    </div>
    <div class="panel-body">
      <div class="row" id="touch">
        <div class="row-text">
          <span class="label">Touch mode</span>
          <p>Scales hit targets for finger input. Presets set the multiplier, minimum target and key height together.</p>
        </div>
        <div class="row-control">
          <div class="seg" role="radiogroup" aria-label="Touch mode">
            <label><input type="radio" value="normal" v-model="settings.touchMode" /><span>Normal</span><span class="sub">1.0×</span></label>
            <label><input type="radio" value="touch-friendly" v-model="settings.touchMode" /><span>Touch-friendly</span><span class="sub">1.5×</span></label>
            <label><input type="radio" value="tablet" v-model="settings.touchMode" /><span>Tablet</span><span class="sub">2.0×</span></label>
          </div>
          <SettingResetButton label="Touch mode" :at-default="settings.touchMode === SETTINGS_DEFAULTS.touchMode" @reset="settings.touchMode = SETTINGS_DEFAULTS.touchMode" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Resolved targets</span>
          <p>Derived from the preset — override the minimum under Advanced.</p>
        </div>
        <div class="row-control">
          <div class="chips">
            <span class="chip">Multiplier <b>{{ settingsStore.touchModeMultiplier }}×</b></span>
            <span class="chip">Min target <b>{{ settingsStore.minimumTouchTargetSize }}px</b></span>
            <span class="chip">Key height <b>{{ resolvedKeyHeight }}px</b></span>
          </div>
          <button type="button" class="btn quiet sm" :aria-expanded="touchAdvancedOpen" @click="touchAdvancedOpen = !touchAdvancedOpen">
            Advanced <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="chev" :class="{ 'chevron-open': touchAdvancedOpen }" />
          </button>
        </div>
      </div>
      <Collapse :open="touchAdvancedOpen">
        <div class="row stack row-inset">
          <div class="row-head">
            <div class="row-text">
              <span class="label">Minimum touch target</span>
              <p>WCAG 2.1 AA asks for at least 44px.</p>
            </div>
          </div>
          <div class="row-control">
            <div class="slider">
              <span class="cap">24px</span>
              <input type="range" min="24" max="64" step="4" v-model.number="settingsStore.minimumTouchTargetSize" :style="sliderFill(settingsStore.minimumTouchTargetSize, 24, 64)" aria-label="Minimum touch target" />
              <span class="cap">64px</span>
              <span class="val">{{ settingsStore.minimumTouchTargetSize }}px</span>
            </div>
          </div>
        </div>
      </Collapse>
      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Button size</span>
            <p>Resizes the key box and its icon inside the grid cell. Below 1× keys shrink; above 1× they grow into the gaps.</p>
          </div>
          <SettingResetButton label="Button size" :at-default="settings.buttonSize === SETTINGS_DEFAULTS.buttonSize" @reset="settings.buttonSize = SETTINGS_DEFAULTS.buttonSize" />
        </div>
        <div class="row-control">
          <div class="slider">
            <span class="cap">0.5×</span>
            <input v-model.number="settings.buttonSize" type="range" min="0.5" max="2" step="0.1" :style="sliderFill(settings.buttonSize, 0.5, 2)" aria-label="Button size" />
            <span class="cap">2×</span>
            <span class="val">{{ settings.buttonSize.toFixed(1) }}×</span>
          </div>
        </div>
      </div>
      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Button transparency</span>
            <p>Lets the dashboard background show through the keys. Capped at 90% so keys stay findable.</p>
          </div>
          <SettingResetButton label="Button transparency" :at-default="settings.buttonTransparency === SETTINGS_DEFAULTS.buttonTransparency" @reset="settings.buttonTransparency = SETTINGS_DEFAULTS.buttonTransparency" />
        </div>
        <div class="row-control">
          <div class="slider">
            <span class="cap">0%</span>
            <input v-model.number="settings.buttonTransparency" type="range" min="0" max="90" step="5" :style="sliderFill(settings.buttonTransparency, 0, 90)" aria-label="Button transparency" />
            <span class="cap">90%</span>
            <span class="val">{{ settings.buttonTransparency }}%</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="design">
    <div class="panel-head">
      <h2>Key design</h2>
      <span class="hint">The default face for every key.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Button design" :at-default="previewEffect === SETTINGS_DEFAULTS.buttonDefaultEffect" @reset="resetButtonDefault('buttonDefaultEffect')" />
    </div>
    <div class="panel-body">
      <div class="row stack design-row">
        <ButtonDesignPicker v-model="previewEffect" class="settings-isolate" />
      </div>
      <div class="note">
        <FontAwesomeIcon :icon="['fas', 'circle-info']" />
        <div>
          Don't see the change on the dashboard? Click the <strong>Refresh</strong> button there
          (the circular arrow icon in the header) to push it through.
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="motion">
    <div class="panel-head"><h2>Motion</h2><span class="hint">Press animation and idle icon motion.</span></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Button animation</span>
          <p>Plays when a key is pressed.</p>
        </div>
        <div class="row-control">
          <select v-model="previewAnimation" class="select w-220" aria-label="Button animation">
            <option value="none">None</option>
            <option value="pulse">Pulse</option>
            <option value="shimmer">Shimmer</option>
            <option value="bounce">Bounce</option>
            <option value="rotate">Rotate</option>
            <option value="wiggle">Wiggle</option>
            <option value="float">Float</option>
            <option value="scale">Scale</option>
            <option value="slide">Slide</option>
            <option value="fade">Fade</option>
            <option value="spin">Spin</option>
          </select>
          <SettingResetButton label="Button animation" :at-default="previewAnimation === SETTINGS_DEFAULTS.buttonDefaultAnimation" @reset="resetButtonDefault('buttonDefaultAnimation')" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Icon animation</span>
          <p>Loops on the icon while the key is idle.</p>
        </div>
        <div class="row-control">
          <select v-model="previewIconLoop" class="select w-220" aria-label="Icon animation">
            <option value="none">None</option>
            <option value="squash">Squash</option>
            <option value="bob">Bob</option>
            <option value="spin">Spin</option>
            <option value="pulse">Pulse</option>
            <option value="swing">Swing</option>
            <option value="flip">Flip</option>
            <option value="jump">Jump</option>
          </select>
          <SettingResetButton label="Icon animation" :at-default="previewIconLoop === SETTINGS_DEFAULTS.buttonDefaultIconLoop" @reset="resetButtonDefault('buttonDefaultIconLoop')" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Enable animations</span>
          <p>Master switch — off disables both of the above without losing them.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Enable animations</span><input v-model="settings.animationsEnabled" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Enable animations" :at-default="settings.animationsEnabled === SETTINGS_DEFAULTS.animationsEnabled" @reset="settings.animationsEnabled = SETTINGS_DEFAULTS.animationsEnabled" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Wiggle buttons in edit mode</span>
          <p>A gentle shake shows keys are draggable while editing.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Wiggle buttons in edit mode</span><input v-model="settings.editModeWiggle" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Wiggle buttons in edit mode" :at-default="settings.editModeWiggle === SETTINGS_DEFAULTS.editModeWiggle" @reset="settings.editModeWiggle = SETTINGS_DEFAULTS.editModeWiggle" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">3D tilt effect</span>
          <p>Keys tilt toward the pointer on hover.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">3D tilt effect</span><input v-model="settings.tiltEffectEnabled" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="3D tilt effect" :at-default="settings.tiltEffectEnabled === SETTINGS_DEFAULTS.tiltEffectEnabled" @reset="settings.tiltEffectEnabled = SETTINGS_DEFAULTS.tiltEffectEnabled" />
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="feedback">
    <div class="panel-head"><h2>Labels &amp; feedback</h2></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Show button labels</span>
          <p>Draws the label under each icon.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Show button labels</span><input v-model="settings.showLabels" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Show button labels" :at-default="settings.showLabels === SETTINGS_DEFAULTS.showLabels" @reset="settings.showLabels = SETTINGS_DEFAULTS.showLabels" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Show tooltips</span>
          <p>Reveals the full action on hover — useful when labels are hidden.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Show tooltips</span><input v-model="settings.showTooltips" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Show tooltips" :at-default="settings.showTooltips === SETTINGS_DEFAULTS.showTooltips" @reset="settings.showTooltips = SETTINGS_DEFAULTS.showTooltips" />
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Press sound</span>
          <p>A short click on every press — makes the panel feel physical.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Press sound</span><input v-model="settings.pressSoundEnabled" type="checkbox" /><span class="track"></span></label>
          <SettingResetButton label="Press sound" :at-default="settings.pressSoundEnabled === SETTINGS_DEFAULTS.pressSoundEnabled" @reset="settings.pressSoundEnabled = SETTINGS_DEFAULTS.pressSoundEnabled" />
        </div>
      </div>
      <div class="row" v-if="settings.pressSoundEnabled">
        <div class="row-text">
          <span class="label">Sound style</span>
          <p>None silences presses without losing the setting.</p>
        </div>
        <div class="row-control">
          <select v-model="settings.pressSoundStyle" class="select w-220" aria-label="Sound style">
            <option value="click">Click</option>
            <option value="blip">Blip</option>
            <option value="pop">Pop</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>
    </div>
  </section>
</div>

<div class="rail">
  <div class="preview">
    <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Live preview</div>
    <div class="preview-stage preview-stage-bg" :class="previewBackgroundClass" :style="previewBackgroundStyle">
      <DeckButton
        :button="previewButton"
        :show-labels="settings.showLabels"
        :show-tooltips="settings.showTooltips"
        :button-size="settings.buttonSize * settingsStore.touchModeMultiplier"
        style="width: 110px; height: 110px;"
      />
    </div>
    <div class="preview-foot">Reflects size, labels, tooltips, touch mode, design and the dashboard background.</div>
  </div>
  <div class="preview">
    <div class="preview-head">In context</div>
    <div class="preview-stage preview-stage-grid">
      <div class="mock-grid" :style="{ gridTemplateColumns: `repeat(${previewGridCols}, 1fr)` }">
        <span v-for="i in previewGridCols * previewGridRows" :key="i" class="mock-key" :style="{ transform: `scale(${Math.min(settings.buttonSize * settingsStore.touchModeMultiplier, 1)})`, opacity: String(1 - settings.buttonTransparency / 130) }"></span>
      </div>
    </div>
    <div class="preview-foot grid-foot">
      <div class="grid-steppers">
        <span class="grid-ctl">
          Cols
          <button type="button" :disabled="!canStepGrid || previewGridCols <= GRID_COLS_MIN" @click="stepPreviewGrid('cols', -1)">−</button>
          <b>{{ previewGridCols }}</b>
          <button type="button" :disabled="!canStepGrid || previewGridCols >= GRID_COLS_MAX" @click="stepPreviewGrid('cols', 1)">+</button>
        </span>
        ×
        <span class="grid-ctl">
          Rows
          <button type="button" :disabled="!canStepGrid || previewGridRows <= GRID_ROWS_MIN" @click="stepPreviewGrid('rows', -1)">−</button>
          <b>{{ previewGridRows }}</b>
          <button type="button" :disabled="!canStepGrid || previewGridRows >= GRID_ROWS_MAX" @click="stepPreviewGrid('rows', 1)">+</button>
        </span>
      </div>
      <span>{{ canStepGrid ? 'Resizes the current page — saved to your profile.' : 'Open the dashboard once to load a profile, then resize the grid here.' }}</span>
    </div>
  </div>
</div>
        </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import DeckButton from '@/components/DeckButton.vue'
import ButtonDesignPicker from '@/components/ButtonDesignPicker.vue'
import SettingResetButton from '@/components/SettingResetButton.vue'
import Collapse from '@/components/Collapse.vue'
import type { Button } from '@/types'
import { requestVdockRefresh } from '@/composables/useVdockRefresh'
import { sliderFill } from '@/utils/sliderFill'
import { useBackgroundPreview } from '@/composables/useBackgroundPreview'

const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const settings = computed(() => settingsStore)
const { previewBackgroundClass, previewBackgroundStyle } = useBackgroundPreview()

// The draft lives in SettingsView (the topbar save bar reads it); the page edits it via v-model.
const previewAnimation = defineModel<string>('animation', { required: true })
const previewIconLoop = defineModel<string>('iconLoop', { required: true })
const previewEffect = defineModel<string>('effect', { required: true })

// DL-028: resetting a demo control restores the factory default AND the
// persisted new-button default; applying to existing buttons stays behind
// the explicit "Save & Apply to All Buttons" action.
const previewDefaults = {
  buttonDefaultAnimation: previewAnimation,
  buttonDefaultIconLoop: previewIconLoop,
  buttonDefaultEffect: previewEffect
} as const
function resetButtonDefault(key: keyof typeof previewDefaults) {
  previewDefaults[key].value = SETTINGS_DEFAULTS[key]
  settingsStore[key] = SETTINGS_DEFAULTS[key]
}

const previewButton = computed<Button>(() => ({
  id: 'preview-button',
  label: 'Preview',
  tooltip: 'Sample tooltip',
  icon_type: 'fontawesome',
  icon: ['fas', 'star'],
  shape: 'rounded',
  position: { row: 0, col: 0 },
  size: { rows: 1, cols: 1 },
  style: {
    backgroundColor: '#3498db',
    textColor: '#ffffff',
    animation: previewAnimation.value === 'none' ? undefined : (previewAnimation.value as any)
  },
  layers: {
    // `layers.icon`, when present, is treated by resolveButtonVisual() as the
    // authoritative icon definition — it must always carry `type`/`value`
    // (not just `loop`), or the icon renders empty and the loop animation
    // has nothing left to animate.
    icon: previewIconLoop.value === 'none'
      ? undefined
      : { type: 'fontawesome', value: ['fas', 'star'], loop: previewIconLoop.value as any },
    effect: previewEffect.value === 'none' ? undefined : { type: previewEffect.value as any, tint: 'brand' }
  },
  enabled: true
}))

const touchAdvancedOpen = ref(false)
// Matches the store's --button-min-height formula so the chip reads the same
// number the deck actually enforces.
const resolvedKeyHeight = computed(() =>
  Math.round(Math.max(36 * settingsStore.touchModeMultiplier, settingsStore.minimumTouchTargetSize))
)

// In-context grid control — resizes the CURRENT page's grid_config (the same
// field the deck footer edits), persisted via a debounced profile save so
// rapid +/- clicks coalesce into one PUT.
const GRID_COLS_MIN = 2, GRID_COLS_MAX = 10, GRID_ROWS_MIN = 1, GRID_ROWS_MAX = 6
const previewGridCols = computed(() => dashboardStore.currentPage?.grid_config?.cols ?? 4)
const previewGridRows = computed(() => dashboardStore.currentPage?.grid_config?.rows ?? 3)
const canStepGrid = computed(() => !!dashboardStore.currentPage)

let previewGridSaveTimer: ReturnType<typeof setTimeout> | null = null
function stepPreviewGrid(axis: 'cols' | 'rows', delta: number) {
  const page = dashboardStore.currentPage
  if (!page) return
  const [min, max] = axis === 'cols' ? [GRID_COLS_MIN, GRID_COLS_MAX] : [GRID_ROWS_MIN, GRID_ROWS_MAX]
  const next = Math.min(max, Math.max(min, page.grid_config[axis] + delta))
  if (next === page.grid_config[axis]) return
  page.grid_config[axis] = next
  if (previewGridSaveTimer) clearTimeout(previewGridSaveTimer)
  previewGridSaveTimer = setTimeout(() => {
    previewGridSaveTimer = null
    void dashboardStore.saveProfile().then(ok => { if (ok) requestVdockRefresh() })
  }, 500)
}
</script>

<style scoped>
.grid-ctl button {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.06);
  color: inherit;
  font-size: 0.9rem;
  line-height: 1;
  cursor: pointer;
  touch-action: manipulation;
}
@media (pointer: coarse), (max-width: 880px) {
  .grid-ctl button { width: 44px; height: 44px; }
}
.grid-ctl button:hover:not(:disabled) { background: rgba(255, 255, 255, 0.12); }
.grid-ctl button:disabled {
  opacity: 0.35;
  cursor: default;
}
.grid-ctl b {
  min-width: 1.4ch;
  text-align: center;
}
.sub {
  color: var(--text-3);
  font-size: var(--fs-xs);
}
</style>
