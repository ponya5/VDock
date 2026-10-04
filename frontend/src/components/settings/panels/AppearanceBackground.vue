<template>
        <div class="content has-rail">
<div class="col">
  <section class="panel" id="dashboard-bg">
    <div class="panel-head">
      <h2>Dashboard background</h2>
      <span class="hint">One background for the whole dashboard — animated effects included.</span>
      <span class="spacer"></span>
      <SettingResetButton label="Background style" :at-default="settings.background === SETTINGS_DEFAULTS.background" @reset="settings.background = SETTINGS_DEFAULTS.background" />
    </div>
    <div class="panel-body">
      <div class="row stack picker-row">
        <BackgroundPicker
          class="settings-isolate"
          v-model="settings.background"
          :groups="backgroundPickerGroups"
          @change="settingsStore.saveSettings()"
        />
      </div>
      <div class="row stack">
        <div class="row-head">
          <div class="row-text">
            <span class="label">Custom image or GIF</span>
            <p>PNG, JPG, WEBP or GIF. Replaces the style above.</p>
          </div>
        </div>
        <div class="row-control">
          <div class="drop">
            <FontAwesomeIcon :icon="['fas', 'upload']" />
            <span>{{ isCustomBackground ? 'A custom image is active.' : 'Drop a file here, or browse. Animated GIFs loop behind the keys.' }}</span>
            <input ref="backgroundFileInput" type="file" accept="image/*,.gif" @change="handleBackgroundUpload" style="display:none" />
            <button type="button" class="btn sm" :disabled="uploadingBackground" @click="($refs.backgroundFileInput as HTMLInputElement).click()">
              <FontAwesomeIcon :icon="uploadingBackground ? ['fas', 'spinner'] : ['fas', 'upload']" :spin="uploadingBackground" />
              {{ uploadingBackground ? 'Uploading…' : 'Choose file…' }}
            </button>
            <button v-if="isCustomBackground" type="button" class="btn danger sm" @click="removeCustomBackground">
              <FontAwesomeIcon :icon="['fas', 'trash']" /> Remove
            </button>
          </div>
        </div>
        <div v-if="isCustomBackground" class="bg-thumb">
          <img :src="settings.background" alt="Custom background" />
        </div>
      </div>
    </div>
  </section>

  <section class="panel" id="scene-bg">
    <div class="panel-head">
      <h2>Per-scene overrides</h2>
      <span class="hint">A scene can replace the dashboard background while it is open.</span>
    </div>
    <div class="panel-body">
      <input ref="sceneBackgroundFileInput" type="file" accept="image/*,.gif" @change="handleSceneBackgroundUpload" style="display:none" />
      <div v-for="scene in sceneList" :key="scene.id" class="row">
        <div class="row-text">
          <span class="label">{{ scene.name }}<span v-if="currentScene?.id === scene.id" class="chip row-now">current</span></span>
          <p>{{ sceneBackgroundDesc(scene) }}</p>
        </div>
        <div class="row-control">
          <img v-if="sceneEffectiveImage(scene)" :src="sceneEffectiveImage(scene)" class="scene-thumb" :alt="`${scene.name} background`" />
          <label v-if="sceneAppEntryFor(scene) && !scene.background?.image" class="switch" :title="`Use the bundled ${sceneAppEntryFor(scene)!.label} artwork`">
            <span class="sr-only">Use app default for {{ scene.name }}</span>
            <input type="checkbox" :checked="!scene.disableAppBackground" @change="toggleAppDefaultBackgroundFor(scene, $event)" />
            <span class="track"></span>
          </label>
          <button type="button" class="btn sm" :disabled="uploadingSceneBackground" @click="pickSceneBackground(scene)">
            {{ scene.background?.image ? 'Change…' : 'Set background' }}
          </button>
          <button v-if="scene.background?.image" type="button" class="btn quiet sm" :title="`Remove ${scene.name} override`" @click="removeSceneBackgroundFor(scene)">
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>
      <p v-if="!sceneList.length" class="muted row-empty">No scenes in this profile yet — add one on the dashboard.</p>
    </div>
  </section>

  <div class="note">
    <FontAwesomeIcon :icon="['fas', 'circle-info']" />
    <div>
      Looking for the screensaver background? It lives with the rest of the screensaver, under
      <a href="#" @click.prevent="$emit('open-screensaver-background')">Appearance → Screen saver</a>.
    </div>
  </div>
</div>

<div class="rail">
  <div class="preview">
    <div class="preview-head"><FontAwesomeIcon :icon="['fas', 'eye']" /> Preview</div>
    <div class="preview-stage preview-stage-bg preview-stage-bg-tall" :class="previewBackgroundClass" :style="previewBackgroundStyle">
      <div v-if="previewBgComponent" class="preview-bg-clip">
        <div class="preview-bg-viewport">
          <BackgroundHost
            embedded
            :component="previewBgComponent"
            :key="settingsStore.background"
            @error="onPreviewBgError"
          />
        </div>
      </div>
      <div v-else-if="previewBgUnavailable" class="preview-bg-note">Preview unavailable on this device</div>
      <div class="mock-grid mock-grid-ghost">
        <span v-for="i in 6" :key="i" class="mock-key ghost"></span>
      </div>
    </div>
    <div class="preview-foot">{{ backgroundPickerGroups.flatMap(g => g.options).find(o => o.id === settings.background)?.label ?? 'Custom' }} at {{ settings.buttonTransparency }}% key transparency.</div>
  </div>
</div>
        </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSettingsStore, SETTINGS_DEFAULTS } from '@/stores/settings'
import { useDashboardStore } from '@/stores/dashboard'
import { useNotificationsStore } from '@/stores/notifications'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import BackgroundPicker, { type BackgroundPickerGroup } from '@/components/BackgroundPicker.vue'
import SettingResetButton from '@/components/SettingResetButton.vue'
import apiClient from '@/api/client'
import type { Scene } from '@/types'
import { isImageBackground, resolveBackground } from '@/data/backgrounds'
import { appForScene } from '@/data/appBackgrounds'
import BackgroundHost from '@/components/backgrounds/BackgroundHost.vue'
import { useAppIntegrations } from '@/composables/useAppIntegrations'
import { useBackgroundPreview } from '@/composables/useBackgroundPreview'

const settingsStore = useSettingsStore()
const dashboardStore = useDashboardStore()
const notificationsStore = useNotificationsStore()
const settings = computed(() => settingsStore)
const appIntegrations = useAppIntegrations()
const { previewBackgroundClass, previewBackgroundStyle, backgroundsByGroup } = useBackgroundPreview()

defineEmits<{ (e: 'open-screensaver-background'): void }>()

// The real component for 'component'-kind backgrounds, rendered inside the
// scaled-viewport stage (see template). Falls back to the checkerboard via
// previewBackgroundStyle when the component reports an init failure.
const bgPreviewFailed = ref<string | null>(null)
const previewBgComponent = computed(() => {
  const option = resolveBackground(settingsStore.background)
  return option.kind === 'component' && bgPreviewFailed.value !== option.id
    ? option.component
    : null
})
function onPreviewBgError(err: unknown) {
  console.warn('[settings-preview] background fell back:', settingsStore.background, err)
  bgPreviewFailed.value = settingsStore.background
}

// A failed component leaves a bare checkerboard that reads as a corrupted
// render — label it so the stage explains itself.
const previewBgUnavailable = computed(() => bgPreviewFailed.value === settingsStore.background)

const backgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingBackground = ref(false)
const sceneBackgroundFileInput = ref<HTMLInputElement | null>(null)
const uploadingSceneBackground = ref(false)
const backgroundPickerGroups = computed<BackgroundPickerGroup[]>(() => {
  const groups: BackgroundPickerGroup[] = [
    { label: 'Default', options: backgroundsByGroup.value.default },
    ...(isCustomBackground.value
      ? [
          {
            label: 'Custom Background',
            options: [{ id: settings.value.background, label: 'Custom Uploaded Image' }]
          }
        ]
      : []),
    { label: 'Gradients', options: backgroundsByGroup.value.gradient },
    { label: 'Animated', options: backgroundsByGroup.value.animated }
  ]
  return groups
})

const isCustomBackground = computed(() => isImageBackground(settings.value.background))

const currentScene = computed(() => dashboardStore.currentScene)

// DL-054: per-scene background rows — every scene in the profile gets a row,
// not just the active one. The hidden file input is shared; sceneBgTargetId
// remembers which row's Pick button opened it.
const sceneList = computed<Scene[]>(() => dashboardStore.currentProfile?.scenes ?? [])
const sceneBgTargetId = ref<string | null>(null)

function sceneAppEntryFor(scene: Scene) {
  return appForScene(scene, appIntegrations.value)
}
function sceneEffectiveImage(scene: Scene): string | undefined {
  if (scene.background?.image) return scene.background.image
  return scene.disableAppBackground ? undefined : sceneAppEntryFor(scene)?.image
}
function sceneBackgroundDesc(scene: Scene): string {
  if (scene.background?.image) return 'Custom image override'
  if (scene.disableAppBackground) return 'Using the dashboard background'
  const app = sceneAppEntryFor(scene)
  return app ? `Bundled ${app.label} artwork` : 'Using the dashboard background'
}
function pickSceneBackground(scene: Scene) {
  sceneBgTargetId.value = scene.id
  sceneBackgroundFileInput.value?.click()
}
function toggleAppDefaultBackgroundFor(scene: Scene, event: Event) {
  const enabled = (event.target as HTMLInputElement).checked
  dashboardStore.updateScene(scene.id, { disableAppBackground: !enabled })
}
function removeSceneBackgroundFor(scene: Scene) {
  dashboardStore.updateScene(scene.id, { background: undefined })
  const app = sceneAppEntryFor(scene)
  notificationsStore.success(
    'Scene background removed',
    app ? `Reverted to the ${app.label} default.` : `Background cleared for "${scene.name}".`
  )
}

const handleBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      settingsStore.background = url
      notificationsStore.success('Background updated', 'Custom background applied successfully.')
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingBackground.value = false; if (target) target.value = '' }
}

const handleSceneBackgroundUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  const scene = sceneList.value.find(s => s.id === sceneBgTargetId.value)
  if (!file || !scene) return
  if (!['image/png','image/jpeg','image/jpg','image/gif'].includes(file.type)) { notificationsStore.error('Invalid file', 'Please upload a PNG, JPG, or GIF image.'); return }
  if (file.size > 10 * 1024 * 1024) { notificationsStore.error('File too large', 'Maximum file size is 10MB.'); return }
  uploadingSceneBackground.value = true
  try {
    const formData = new FormData()
    formData.append('file', file); formData.append('type', 'dashboard_background')
    const response = await apiClient.post('/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (response.data.success) {
      const url = response.data.url.startsWith('/api') ? response.data.url : '/api' + response.data.url
      dashboardStore.updateScene(scene.id, { background: { type: 'image', image: url } })
      notificationsStore.success('Scene background updated', `Background applied to "${scene.name}".`)
    } else { notificationsStore.error('Upload failed', response.data.error || 'Unknown error') }
  } catch (error: any) { notificationsStore.error('Upload failed', error.message || 'Unknown error') }
  finally { uploadingSceneBackground.value = false; sceneBgTargetId.value = null; if (target) target.value = '' }
}

const removeCustomBackground = () => { settingsStore.background = 'default'; notificationsStore.success('Background removed', 'Reverted to default background.') }
</script>

<style scoped>
.mock-grid-ghost .mock-key {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
}
</style>
