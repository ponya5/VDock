<template>
        <div class="content has-rail">
<div class="col">
  <!-- DL-133: the type pick is the first thing on the tab —
       'shuffle' rotates the saver view on an interval.
       DL-137 follow-up: type, activation and the try-it controls
       merged into one generic "General" panel — three panels for
       six rows read as clutter on the panel. -->
  <section class="panel" id="ss-general">
    <div class="panel-head"><h2>General</h2></div>
    <div class="panel-body">
      <div class="row">
        <div class="row-text">
          <span class="label">Screensaver Type</span>
          <p>What fills the screen when the saver kicks in. Shuffle rotates between the other types while it's up.</p>
        </div>
        <div class="row-control">
          <select v-model="settingsStore.screensaverStyle" class="select" aria-label="Screensaver type">
            <option value="widgets">Widget dashboard</option>
            <option value="spectrum">Spectrum visualizer</option>
            <option value="stats">System stats</option>
            <option value="shuffle">Shuffle</option>
          </select>
        </div>
      </div>
      <!-- DL-135: the enabled info widgets can overlay the
           spectrum — same toggles and positions as the Widget
           dashboard; only offered when the style can show it. -->
      <div class="row" v-if="settingsStore.screensaverStyle === 'spectrum' || settingsStore.screensaverStyle === 'shuffle'">
        <div class="row-text">
          <span class="label">Widgets on the visualizer</span>
          <p>Show the widgets enabled below over the spectrum — same positions as Customise layout.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Widgets on the visualizer</span><input type="checkbox" :checked="settingsStore.screensaverSpectrumWidgets" @change="settingsStore.screensaverSpectrumWidgets = !settingsStore.screensaverSpectrumWidgets" /><span class="track"></span></label>
        </div>
      </div>
      <div class="row" v-if="settingsStore.screensaverStyle === 'shuffle'">
        <div class="row-text">
          <span class="label">Rotate every</span>
          <p>How often Shuffle swaps the saver view.</p>
        </div>
        <div class="row-control">
          <select v-model.number="settingsStore.screensaverShuffleMinutes" class="select" aria-label="Shuffle rotation interval">
            <option :value="1">1 min</option>
            <option :value="5">5 min</option>
            <option :value="10">10 min</option>
            <option :value="30">30 min</option>
          </select>
        </div>
      </div>
      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Idle delay</span>
            <p>Time before the screensaver appears. 0 disables it entirely.</p>
          </div>
          <SettingResetButton label="Idle delay" :at-default="settingsStore.screensaverTimeout === SETTINGS_DEFAULTS.screensaverTimeout" @reset="settingsStore.screensaverTimeout = SETTINGS_DEFAULTS.screensaverTimeout" />
        </div>
        <div class="row-control">
          <div class="slider">
            <span class="cap">Off</span>
            <input type="range" min="0" max="600" step="30" :value="settingsStore.screensaverTimeout" @input="settingsStore.screensaverTimeout = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverTimeout, 0, 600)" aria-label="Idle delay" />
            <span class="cap">10m</span>
            <span class="val">{{ settingsStore.screensaverTimeout === 0 ? 'Off' : formatScreensaverTimeout(settingsStore.screensaverTimeout) }}</span>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="row-text">
          <span class="label">Try it</span>
          <p>Test shows the screensaver even when the delay is off. Customise opens a live editor — drag widgets to move them, drag a corner to resize.</p>
        </div>
        <div class="row-control">
          <button type="button" class="btn sm" @click="handleTestScreensaver"><FontAwesomeIcon :icon="['fas', 'display']" /> Test</button>
          <button type="button" class="btn sm" @click="$emit('customize-layout')"><FontAwesomeIcon :icon="['fas', 'up-down-left-right']" /> Customise layout</button>
        </div>
      </div>
    </div>
  </section>

  <!-- DL-123/125: fullscreen saver styles — the shared style
       picker, then spectrum skin/shuffle/media-bar prefs. Widget-
       mode controls below still apply when 'Widget dashboard' is
       selected. -->
  <section class="panel" id="ss-spectrum">
    <div class="panel-head">
      <h2>Spectrum visualizer</h2>
      <span class="spacer"></span>
      <SettingResetButton label="Spectrum screensaver" :at-default="spectrumAtDefault" @reset="resetSpectrumSettings" />
    </div>
    <div class="panel-body">
      <div class="note" v-if="settingsStore.screensaverStyle === 'widgets' || settingsStore.screensaverStyle === 'stats'">
        <FontAwesomeIcon :icon="['fas', 'circle-info']" />
        <div>Not in use while <strong>{{ screensaverStyleLabel }}</strong> is picked — the options below belong to the <strong>Spectrum visualizer</strong> type.</div>
      </div>

      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Skin</span>
            <p>Live previews. Applies while the spectrum saver is showing.</p>
          </div>
        </div>
        <div class="row-control">
          <div class="skin-grid" role="radiogroup" aria-label="Spectrum skin">
            <button
              v-for="skin in spectrumSkins"
              :key="skin.id"
              type="button"
              class="skin-card"
              :class="{ 'skin-active': settingsStore.spectrumSkin === skin.id }"
              :aria-checked="settingsStore.spectrumSkin === skin.id"
              role="radio"
              @click="settingsStore.spectrumSkin = skin.id"
            >
              <span class="skin-thumb"><SkinPreview :skin-id="skin.id" class="settings-isolate" /></span>
              <span class="skin-name">{{ skin.label }}</span>
            </button>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="row-text">
          <span class="label">Shuffle skins</span>
          <p>Rotate to a random skin on an interval while the saver is up.</p>
        </div>
        <div class="row-control">
          <select
            v-model.number="settingsStore.spectrumShuffleMinutes"
            class="select"
            :disabled="!settingsStore.spectrumShuffle"
            aria-label="Shuffle interval"
          >
            <option :value="1">1 min</option>
            <option :value="5">5 min</option>
            <option :value="10">10 min</option>
            <option :value="30">30 min</option>
          </select>
          <label class="switch">
            <span class="sr-only">Shuffle skins</span>
            <input type="checkbox" :checked="settingsStore.spectrumShuffle" @change="settingsStore.spectrumShuffle = !settingsStore.spectrumShuffle" />
            <span class="track"></span>
          </label>
        </div>
      </div>

      <div class="row">
        <div class="row-text">
          <span class="label">Media controls</span>
          <p>Now-playing card with transport controls pinned to the bottom of the visualizer — taps inside it don't exit the saver; a tap anywhere else does.</p>
        </div>
        <div class="row-control">
          <label class="switch">
            <span class="sr-only">Media controls</span>
            <input type="checkbox" :checked="settingsStore.spectrumMediaBar" @change="settingsStore.spectrumMediaBar = !settingsStore.spectrumMediaBar" />
            <span class="track"></span>
          </label>
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="ss-background">
    <div class="panel-head">
      <h2>Screensaver background</h2>
      <span class="hint">Shown only while the screensaver is on — the dashboard keeps its own.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Screensaver background" :at-default="settings.screensaverBackground === SETTINGS_DEFAULTS.screensaverBackground" @reset="settings.screensaverBackground = SETTINGS_DEFAULTS.screensaverBackground" />
    </div>
    <div class="panel-body">
      <div class="note" v-if="settingsStore.screensaverStyle === 'spectrum' || settingsStore.screensaverStyle === 'stats'">
        <FontAwesomeIcon :icon="['fas', 'circle-info']" />
        <div>Not in use while <strong>{{ screensaverStyleLabel }}</strong> is picked above — this background belongs to the <strong>Widget dashboard</strong> type.</div>
      </div>
      <div class="row stack picker-row">
        <BackgroundPicker
          class="settings-isolate"
          v-model="settings.screensaverBackground"
          :groups="screensaverPickerGroups"
        />
      </div>
      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Custom image or GIF</span>
            <p>Replaces the style above while the screensaver is on.</p>
          </div>
        </div>
        <div class="row-control">
          <div class="drop">
            <FontAwesomeIcon :icon="['fas', 'upload']" />
            <span>{{ isCustomScreensaverBackground ? 'A custom image is active.' : 'Drop a file here, or browse.' }}</span>
            <input ref="screensaverBgFileInput" type="file" accept="image/*,.gif" @change="handleScreensaverBackgroundUpload" style="display:none" />
            <button type="button" class="btn sm" :disabled="uploadingScreensaverBackground" @click="($refs.screensaverBgFileInput as HTMLInputElement).click()">
              <FontAwesomeIcon :icon="uploadingScreensaverBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingScreensaverBackground" />
              {{ uploadingScreensaverBackground ? 'Uploading…' : 'Choose file…' }}
            </button>
            <button v-if="isCustomScreensaverBackground" type="button" class="btn danger sm" @click="removeScreensaverBackground">
              <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
            </button>
          </div>
        </div>
        <div v-if="isCustomScreensaverBackground" class="bg-thumb">
          <img :src="settings.screensaverBackground" alt="Screensaver background" />
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="ss-widgets" data-tour="screensaver-picker">
    <div class="panel-head">
      <h2>Widgets</h2>
      <span class="hint">What shows besides the clock. Each row opens its own settings.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Screensaver widgets" :at-default="screensaverWidgetsAtDefault" @reset="resetScreensaverWidgets" />
    </div>
    <div class="panel-body">
      <div class="note" v-if="settingsStore.screensaverStyle === 'spectrum'">
        <FontAwesomeIcon :icon="['fas', 'circle-info']" />
        <div>The enabled widgets also overlay the <strong>Spectrum visualizer</strong> when <strong>Widgets on the visualizer</strong> is on above.</div>
      </div>
      <div class="note" v-else-if="settingsStore.screensaverStyle === 'stats'">
        <FontAwesomeIcon :icon="['fas', 'circle-info']" />
        <div>Not in use while <strong>{{ screensaverStyleLabel }}</strong> is picked above — these widgets show on the <strong>Widget dashboard</strong> type.</div>
      </div>
      <!-- DL-098: the clock is a real toggle — its own persisted
           flag, not a widgets-array entry (saved lists predate
           'clock', so array membership could never distinguish
           "turned off" from "old payload"). -->
      <div class="row">
        <div class="row-text">
          <span class="label">Clock</span>
          <p>Large time and date.</p>
        </div>
        <div class="row-control">
          <label class="switch"><span class="sr-only">Clock</span><input type="checkbox" :checked="settingsStore.screensaverClockEnabled" @change="settingsStore.screensaverClockEnabled = !settingsStore.screensaverClockEnabled" /><span class="track"></span></label>
        </div>
      </div>
      <template v-for="w in screensaverWidgetOptions" :key="w.id">
        <div class="row">
          <div class="row-text">
            <span class="label">{{ w.label }}</span>
            <p>{{ w.description }}</p>
          </div>
          <div class="row-control">
            <button
              v-if="widgetHasOptions(w.id) && settingsStore.screensaverWidgets.includes(w.id)"
              type="button"
              class="btn quiet sm"
              :aria-expanded="openWidgetCard === w.id"
              @click="toggleWidgetCard(w.id)"
            >
              Options
              <FontAwesomeIcon :icon="['fas', 'chevron-down']" class="chev" :class="{ 'chevron-open': openWidgetCard === w.id }" />
            </button>
            <label class="switch">
              <span class="sr-only">{{ w.label }}</span>
              <input type="checkbox" :checked="settingsStore.screensaverWidgets.includes(w.id)" @change="toggleScreensaverWidget(w.id)" />
              <span class="track"></span>
            </label>
          </div>
        </div>
        <Collapse v-if="widgetHasOptions(w.id) && settingsStore.screensaverWidgets.includes(w.id)" :open="openWidgetCard === w.id">
          <div class="row stack row-inset widget-detail">
            <!-- weather: location + widget size -->
            <template v-if="w.id === 'weather'">
              <div class="grid-3">
                <label class="stack-8">
                  <span class="muted field-label">Location</span>
                  <select v-model="settings.weatherLocationMode" class="select" aria-label="Weather location source">
                    <option value="auto">Automatic (this device)</option>
                    <option value="manual">Set a city manually</option>
                  </select>
                </label>
                <label v-if="settings.weatherLocationMode === 'manual'" class="stack-8">
                  <span class="muted field-label">City</span>
                  <input v-model="settings.weatherManualCity" type="text" class="input" placeholder="e.g. Tel Aviv" @keyup.enter="refreshWeatherWidget" />
                </label>
                <label class="stack-8">
                  <span class="muted field-label">Widget size <b class="val-inline">{{ settingsStore.screensaverWeatherSize }}%</b></span>
                  <input type="range" min="50" max="300" step="10" :value="settingsStore.screensaverWeatherSize" @input="settingsStore.screensaverWeatherSize = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverWeatherSize, 50, 300)" class="slider-bare" aria-label="Weather widget size" />
                </label>
              </div>
              <p v-if="settings.weatherLocationMode !== 'manual'" class="muted field-note">Detects this machine's location automatically — no permission prompt needed. Falls back to a manual city if unavailable. Also feeds the docked weather card.</p>
            </template>
            <!-- news -->
            <template v-else-if="w.id === 'news'">
              <div class="stack-12">
                <label class="stack-8">
                  <span class="muted field-label">Feed URLs — one RSS or Atom URL per line; blank uses the built-in sources</span>
                  <textarea v-model="settingsStore.newsFeeds" class="input textarea" rows="3" placeholder="https://feeds.bbci.co.uk/news/world/rss.xml&#10;https://hnrss.org/frontpage"></textarea>
                </label>
                <div class="widget-detail-foot">
                  <label class="stack-8 field-inline">
                    <span class="muted field-label">Seconds per headline</span>
                    <input v-model.number="settingsStore.newsRotateSeconds" type="number" min="3" max="60" class="input w-110" />
                  </label>
                  <button type="button" class="btn sm" :disabled="testingNews" @click="handleTestNews">
                    <FontAwesomeIcon :icon="['fas', testingNews ? 'spinner' : 'plug']" :spin="testingNews" /> Test feeds
                  </button>
                  <SettingResetButton label="News feeds" :at-default="settingsStore.newsFeeds === SETTINGS_DEFAULTS.newsFeeds && settingsStore.newsRotateSeconds === SETTINGS_DEFAULTS.newsRotateSeconds" @reset="settingsStore.newsFeeds = SETTINGS_DEFAULTS.newsFeeds; settingsStore.newsRotateSeconds = SETTINGS_DEFAULTS.newsRotateSeconds" />
                </div>
                <p v-if="newsTestResult" class="test-result" :class="{ ok: newsTestResult.ok }">
                  <FontAwesomeIcon :icon="['fas', newsTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ newsTestResult.text }}
                </p>
              </div>
            </template>
            <!-- sports -->
            <template v-else-if="w.id === 'sports'">
              <div class="stack-12">
                <label class="stack-8">
                  <span class="muted field-label">Feed URLs — blank uses ESPN, BBC Sport and Sky Sports</span>
                  <textarea v-model="settingsStore.sportsFeeds" class="input textarea" rows="3" placeholder="https://www.espn.com/espn/rss/news&#10;https://feeds.bbci.co.uk/sport/rss.xml"></textarea>
                </label>
                <div class="widget-detail-foot">
                  <button type="button" class="btn sm" :disabled="testingSports" @click="handleTestSports">
                    <FontAwesomeIcon :icon="['fas', testingSports ? 'spinner' : 'plug']" :spin="testingSports" /> Test feeds
                  </button>
                  <SettingResetButton label="Sports feeds" :at-default="settingsStore.sportsFeeds === SETTINGS_DEFAULTS.sportsFeeds" @reset="settingsStore.sportsFeeds = SETTINGS_DEFAULTS.sportsFeeds" />
                </div>
                <p v-if="sportsTestResult" class="test-result" :class="{ ok: sportsTestResult.ok }">
                  <FontAwesomeIcon :icon="['fas', sportsTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ sportsTestResult.text }}
                </p>
              </div>
            </template>
            <!-- market -->
            <template v-else-if="w.id === 'market'">
              <div class="stack-12">
                <label class="stack-8">
                  <span class="muted field-label">Symbols — comma-separated stock tickers and crypto, mixable</span>
                  <input v-model="settingsStore.marketTickers" type="text" class="input" placeholder="BTC, ETH, AAPL, MSFT, NVDA" />
                </label>
                <div class="widget-detail-foot">
                  <button type="button" class="btn sm" :disabled="testingMarket" @click="handleTestMarket">
                    <FontAwesomeIcon :icon="['fas', testingMarket ? 'spinner' : 'plug']" :spin="testingMarket" /> Test connection
                  </button>
                  <SettingResetButton label="Market symbols" :at-default="settingsStore.marketTickers === SETTINGS_DEFAULTS.marketTickers" @reset="settingsStore.marketTickers = SETTINGS_DEFAULTS.marketTickers" />
                </div>
                <p v-if="marketTestResult" class="test-result" :class="{ ok: marketTestResult.ok }">
                  <FontAwesomeIcon :icon="['fas', marketTestResult.ok ? 'circle-check' : 'circle-exclamation']" /> {{ marketTestResult.text }}
                </p>
              </div>
            </template>
            <!-- world clock -->
            <template v-else-if="w.id === 'worldclock'">
              <div class="stack-12">
                <label class="stack-8">
                  <span class="muted field-label">Cities — one per line: a city name, an IANA zone, or Label=Zone</span>
                  <textarea v-model="settingsStore.worldClockTimezones" class="input textarea" rows="3" :placeholder="'New York\nLondon\nTokyo'"></textarea>
                </label>
                <div class="widget-detail-foot">
                  <span class="muted field-note">Blank shows New York, London and Tokyo.</span>
                  <SettingResetButton label="World clock cities" :at-default="settingsStore.worldClockTimezones === SETTINGS_DEFAULTS.worldClockTimezones" @reset="settingsStore.worldClockTimezones = SETTINGS_DEFAULTS.worldClockTimezones" />
                </div>
              </div>
            </template>
          </div>
        </Collapse>
      </template>
      <div v-if="settingsStore.screensaverWidgets.some(w => ['news', 'sports', 'market', 'worldclock'].includes(w))" class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Widget text size</span>
            <p>Scales the news, sports, market and world-clock text. Touch mode already enlarges them — this adjusts on top.</p>
          </div>
          <SettingResetButton label="Widget text size" :at-default="settingsStore.screensaverWidgetSize === SETTINGS_DEFAULTS.screensaverWidgetSize" @reset="settingsStore.screensaverWidgetSize = SETTINGS_DEFAULTS.screensaverWidgetSize" />
        </div>
        <div class="row-control">
          <div class="slider">
            <span class="cap">80%</span>
            <input type="range" min="80" max="250" step="10" :value="settingsStore.screensaverWidgetSize" @input="settingsStore.screensaverWidgetSize = Number(($event.target as HTMLInputElement).value)" :style="sliderFill(settingsStore.screensaverWidgetSize, 80, 250)" aria-label="Widget text size" />
            <span class="cap">250%</span>
            <span class="val">{{ settingsStore.screensaverWidgetSize }}%</span>
          </div>
        </div>
      </div>
    </div>
  </section>

</div>

<div class="rail">
  <div class="preview">
    <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'moon']" /> Screensaver preview</div>
    <div class="preview-stage preview-stage-bg preview-stage-ss" :class="screensaverPreviewClass" :style="screensaverPreviewStyle">
      <div class="ss-mock">
        <div v-if="settingsStore.screensaverClockEnabled" class="ss-mock-clock" :style="{ fontSize: `${Math.round(46 * settingsStore.screensaverWidgetSize / 100)}px` }">12:34</div>
        <div v-if="settingsStore.screensaverClockEnabled" class="ss-mock-date">Monday, 21 September</div>
        <div class="ss-mock-chips">
          <span v-if="settingsStore.screensaverWidgets.includes('weather')" :style="{ fontSize: `${12 * settingsStore.screensaverWeatherSize / 100}px` }">☀ 27° Tel Aviv</span>
          <span v-if="settingsStore.screensaverWidgets.includes('market')">BTC ▲ 1.4%</span>
          <span v-if="settingsStore.screensaverWidgets.includes('worldclock')">NY 05:34</span>
        </div>
        <div v-if="settingsStore.screensaverWidgets.includes('news') || settingsStore.screensaverWidgets.includes('sports')" class="ss-mock-ticker" :style="{ fontSize: `${12 * settingsStore.screensaverWidgetSize / 100}px` }">
          {{ settingsStore.screensaverWidgets.includes('news') && settingsStore.screensaverWidgets.includes('sports') ? 'Headline ticker — news and sports rotate here' : settingsStore.screensaverWidgets.includes('news') ? 'Headline ticker — news rotates here' : 'Headline ticker — sports rotate here' }}
        </div>
      </div>
    </div>
    <div class="preview-foot">Live layout. Drag widgets in Customise layout to rearrange.</div>
  </div>
</div>
        </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import BackgroundPicker, { type BackgroundPickerGroup } from '@/components/BackgroundPicker.vue'
import SettingResetButton from '@/components/SettingResetButton.vue'
import Collapse from '@/components/Collapse.vue'
import apiClient from '@/api/client'
import { useWeather } from '@/composables/useWeather'
import { sendUiCommand } from '@/composables/useUiCommands'
import { testNewsConnection, parseFeedList, DEFAULT_SPORTS_FEEDS } from '@/services/newsService'
import { testMarketConnection, parseTickers } from '@/services/marketService'
import { isImageBackground } from '@/data/backgrounds'
import { sliderFill } from '@/utils/sliderFill'
import { isStandaloneSettingsRoute } from '@/utils/openStandaloneSettings'
import { useBackgroundPreview } from '@/composables/useBackgroundPreview'
import SkinPreview from '@/components/screensaver/SkinPreview.vue'
import { SPECTRUM_SKINS } from '@/services/spectrumSkins'
import { saverTypeLabel } from '@/services/screensaverTypes'

const router = useRouter()
const route = useRoute()
const isStandaloneSettings = computed(() => isStandaloneSettingsRoute(route))
const settingsStore = useSettingsStore()
const notificationsStore = useNotificationsStore()
const settings = computed(() => settingsStore)
const { screensaverPreviewClass, screensaverPreviewStyle, backgroundsByGroup } = useBackgroundPreview()

defineEmits<{ (e: 'customize-layout'): void }>()

const { refresh: refreshWeatherWidget } = useWeather()

function handleTestScreensaver() {
  sendUiCommand('show_screensaver')
  if (!isStandaloneSettings.value) {
    // Same-tab settings: the dashboard is unmounted right now, so the queued
    // command only fires once it remounts. Navigate back so the preview is
    // actually seen instead of looking like nothing happened.
    router.push('/')
    return
  }
  notificationsStore.success(
    'Screensaver triggered',
    'It is now showing on the deck window — tap it to dismiss.'
  )
}

const screensaverBgFileInput = ref<HTMLInputElement | null>(null)
const uploadingScreensaverBackground = ref(false)

// Screensaver gets its own background picker: 'default' means the classic
// dark screensaver look, not the dashboard's gradient, so the option is
// relabeled here instead of reusing backgroundPickerGroups.
const screensaverPickerGroups = computed<BackgroundPickerGroup[]>(() => [
  { label: 'Default', options: [{ id: 'default', label: 'Default (Dark)' }] },
  ...(isCustomScreensaverBackground.value
    ? [
        {
          label: 'Custom Background',
          options: [{ id: settingsStore.screensaverBackground, label: 'Custom Uploaded Image' }]
        }
      ]
    : []),
  { label: 'Gradients', options: backgroundsByGroup.value.gradient },
  { label: 'Animated', options: backgroundsByGroup.value.animated }
])

const isCustomScreensaverBackground = computed(() =>
  isImageBackground(settingsStore.screensaverBackground)
)

const handleScreensaverBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingScreensaverBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      settingsStore.screensaverBackground = url
      notificationsStore.success('Screensaver background updated', 'Custom background applied successfully.')
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingScreensaverBackground.value = false; if (target) target.value = '' }
}

const removeScreensaverBackground = () => {
  settingsStore.screensaverBackground = 'default'
  notificationsStore.success('Screensaver background removed', 'Reverted to the default dark look.')
}

const screensaverWidgetOptions = [
  { id: 'weather', label: 'Weather', description: 'Current temperature and conditions' },
  { id: 'news', label: 'News', description: 'Rotating headlines from free RSS feeds' },
  { id: 'sports', label: 'Sports News', description: 'Sports headlines from free RSS feeds' },
  { id: 'market', label: 'Stocks / Crypto', description: 'Free stock & crypto quotes — no key' },
  { id: 'worldclock', label: 'World Clock', description: 'Time in a few other cities' },
  { id: 'nowplaying', label: 'Now Playing', description: 'Current track, artist and album art (Windows)' },
]

// Only these widgets have an Options card — the rest are self-contained.
const widgetHasOptions = (id: string) =>
  ['weather', 'news', 'sports', 'market', 'worldclock'].includes(id)

// Widget config cards collapse to a header row — tap to expand one at a
// time so the tab fits a 600px touchscreen without scrolling.
const openWidgetCard = ref<string | null>(null)
function toggleWidgetCard(id: string) {
  openWidgetCard.value = openWidgetCard.value === id ? null : id
}

function toggleScreensaverWidget(id: string) {
  const list = settingsStore.screensaverWidgets
  const idx = list.indexOf(id)
  if (idx === -1) {
    settingsStore.screensaverWidgets = [...list, id]
  } else {
    settingsStore.screensaverWidgets = list.filter(w => w !== id)
    // Disabling the widget whose config card is open would leave
    // openWidgetCard pointing at a removed card — the picker stays
    // collapsed with nothing open to close. Release it.
    if (openWidgetCard.value === id) openWidgetCard.value = null
  }
}

// DL-028: section-level reset restores the default widget set — the
// DL-098 glanceable trio plus the clock flag, which sits in the same
// panel even though it persists as its own setting.
const screensaverWidgetsAtDefault = computed(() =>
  settingsStore.screensaverClockEnabled === SETTINGS_DEFAULTS.screensaverClockEnabled &&
  settingsStore.screensaverWidgets.length === SETTINGS_DEFAULTS.screensaverWidgets.length &&
  SETTINGS_DEFAULTS.screensaverWidgets.every(w => settingsStore.screensaverWidgets.includes(w))
)
function resetScreensaverWidgets() {
  settingsStore.screensaverWidgets = [...SETTINGS_DEFAULTS.screensaverWidgets]
  settingsStore.screensaverClockEnabled = SETTINGS_DEFAULTS.screensaverClockEnabled
}

// DL-123: spectrum screensaver mode — skin registry for the swatch grid.
const spectrumSkins = SPECTRUM_SKINS

// DL-125/133: the "not in use" notes name whichever style is picked.
const screensaverStyleLabel = computed(() => saverTypeLabel(settingsStore.screensaverStyle))

const spectrumAtDefault = computed(() =>
  settingsStore.screensaverStyle === SETTINGS_DEFAULTS.screensaverStyle &&
  settingsStore.screensaverShuffleMinutes === SETTINGS_DEFAULTS.screensaverShuffleMinutes &&
  settingsStore.spectrumSkin === SETTINGS_DEFAULTS.spectrumSkin &&
  settingsStore.spectrumShuffle === SETTINGS_DEFAULTS.spectrumShuffle &&
  settingsStore.spectrumShuffleMinutes === SETTINGS_DEFAULTS.spectrumShuffleMinutes &&
  settingsStore.spectrumMediaBar === SETTINGS_DEFAULTS.spectrumMediaBar
)
function resetSpectrumSettings() {
  settingsStore.screensaverStyle = SETTINGS_DEFAULTS.screensaverStyle
  settingsStore.screensaverShuffleMinutes = SETTINGS_DEFAULTS.screensaverShuffleMinutes
  settingsStore.spectrumSkin = SETTINGS_DEFAULTS.spectrumSkin
  settingsStore.spectrumShuffle = SETTINGS_DEFAULTS.spectrumShuffle
  settingsStore.spectrumShuffleMinutes = SETTINGS_DEFAULTS.spectrumShuffleMinutes
  settingsStore.spectrumMediaBar = SETTINGS_DEFAULTS.spectrumMediaBar
}

type TestResult = { ok: boolean; text: string }
const testingNews = ref(false)
const testingSports = ref(false)
const newsTestResult = ref<TestResult | null>(null)
const sportsTestResult = ref<TestResult | null>(null)
const marketTestResult = ref<TestResult | null>(null)

// Inline result next to the button plus a toast — toasts auto-dismiss, so
// the inline line is what persists as the visible answer.
function describeTestError(err: any, fallback: string): string {
  const status = err?.response?.status
  if (status === 429) return 'Server rate limit reached — wait a moment and retry.'
  if (!err?.response) return 'Server unreachable — is the backend running?'
  return err?.message || fallback
}

async function testFeeds(feeds: string[], testing: typeof testingNews, result: typeof newsTestResult) {
  testing.value = true
  result.value = null
  try {
    const count = await testNewsConnection(feeds)
    const text = `${count} headlines fetched`
    result.value = { ok: true, text }
    notificationsStore.success(
      'Feeds working',
      `Fetched ${count} headlines from ${feeds.length || 'the built-in'} ${feeds.length === 1 ? 'feed' : 'feeds'}.`
    )
  } catch (err: any) {
    const text = describeTestError(err, 'Could not read those feeds.')
    result.value = { ok: false, text }
    notificationsStore.error('Feed test failed', text)
  } finally {
    testing.value = false
  }
}
async function handleTestNews() {
  await testFeeds(parseFeedList(settingsStore.newsFeeds), testingNews, newsTestResult)
}
async function handleTestSports() {
  const feeds = parseFeedList(settingsStore.sportsFeeds)
  await testFeeds(feeds.length ? feeds : DEFAULT_SPORTS_FEEDS, testingSports, sportsTestResult)
}

const testingMarket = ref(false)
async function handleTestMarket() {
  testingMarket.value = true
  marketTestResult.value = null
  try {
    const tickers = parseTickers(settingsStore.marketTickers)
    await testMarketConnection(tickers)
    const text = tickers.length
      ? `Quotes fetched for ${tickers.join(', ')}`
      : 'Crypto prices fetched from CoinGecko'
    marketTestResult.value = { ok: true, text }
    notificationsStore.success('Market data connected', text + '.')
  } catch (err: any) {
    const text = describeTestError(err, 'Could not reach the price API.')
    marketTestResult.value = { ok: false, text }
    notificationsStore.error('Market connection failed', text)
  } finally {
    testingMarket.value = false
  }
}

function formatScreensaverTimeout(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s === 0 ? `${m}m` : `${m}m ${s}s`
}
</script>

<style scoped>
.widget-detail .grid-3 { margin-bottom: 12px; }
.slider-bare::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid var(--accent);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  cursor: pointer;
  transition: transform 0.12s var(--ease-out, ease);
}
.slider-bare:active::-webkit-slider-thumb { transform: scale(1.2); }
.slider-bare::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid var(--accent);
  transition: transform 0.12s var(--ease-out, ease);
}
.slider-bare:active::-moz-range-thumb { transform: scale(1.2); }
.slider-bare:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 6px;
}
.ss-mock-chips span {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.09);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: var(--fs-xs);
}
.skin-card:hover {
  border-color: var(--border-bright, rgba(255, 255, 255, 0.25)); }
.skin-card.skin-active {
  border-color: var(--accent, #7ab8ff);
  background: rgba(122, 184, 255, 0.08);
}
.skin-thumb {
  display: block;
  aspect-ratio: 16 / 9;
  border-radius: 4px;
  overflow: hidden;
  background: #050510;
}
.skin-name {
  font-size: clamp(11px, 1.1vw, 13px);
  color: var(--text);
  font-weight: 500;
}
@media (prefers-reduced-motion: reduce) {
  .slider-bare,
.slider-bare::-webkit-slider-thumb,
.slider-bare::-moz-range-thumb {
    transition: none; }
}
</style>
