<template>
  <div class="content">
    <div class="col col-about">
      <section class="panel">
        <div class="panel-body pad about-hero">
          <span class="nav-mark about-mark"><img :src="'/assets/branding/vdock-logo.jpg'" alt="VDock logo" class="nav-mark-img" /></span>
          <div class="about-hero-text">
            <div class="about-title-row">
              <h2 class="about-title">VDock</h2>
              <span class="nav-ver">v{{ appVersion }}</span>
            </div>
            <p class="muted about-desc">A virtual stream interface for controlling your computer with customisable buttons, macros, system metrics and intelligent app integration.</p>
            <div class="about-actions">
              <!-- Launch tutorial leads the row in the primary accent —
                   the one action here that changes app state. The Guide
                   opens in a new window from the side nav, and the repo
                   link lives in the
                   Build card + dock credit, so neither repeats here. -->
              <button type="button" class="btn primary" @click="launchTutorial">
                <FontAwesomeIcon :icon="['fas', 'route']" /> Launch tutorial
              </button>
              <button type="button" class="btn" @click="emit('request-feature')">
                <FontAwesomeIcon :icon="['fas', 'lightbulb']" /> Request a feature
              </button>
              <a class="btn" href="https://github.com/ponya5/VDock2/issues" target="_blank" rel="noopener"><FontAwesomeIcon :icon="['fas', 'bug']" /> Report an issue</a>
              <a class="btn" href="https://github.com/ponya5/VDock2" target="_blank" rel="noopener"><FontAwesomeIcon :icon="['fas', 'star']" /> Star the repo</a>
            </div>
          </div>
        </div>
      </section>

      <section class="panel" id="features">
        <div class="panel-head"><h2>What's in it</h2></div>
        <div class="panel-body">
          <div class="feature-list">
            <div v-for="feature in aboutFeatures" :key="feature.label" class="feature">
              <FontAwesomeIcon :icon="feature.icon" class="feature-icon" />
              <div class="feature-text">
                <div class="feature-title">{{ feature.label }}</div>
                <div class="muted feature-desc">{{ feature.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel" id="build">
        <div class="panel-head"><h2>Build</h2></div>
        <div class="panel-body">
          <dl class="kv-list">
            <div class="kv"><dt>Version</dt><dd>{{ appVersion }}</dd></div>
            <div class="kv"><dt>Licence</dt><dd>MIT — ponya5</dd></div>
            <div class="kv"><dt>Repository</dt><dd><a href="https://github.com/ponya5/VDock2" target="_blank" rel="noopener">github.com/ponya5/VDock2</a></dd></div>
          </dl>
        </div>
      </section>

      <div class="about-support">
        <a href="https://ko-fi.com/danielshalom" target="_blank" rel="noopener" class="kofi-btn">
          <img src="https://storage.ko-fi.com/cdn/cup-border.png" alt="Ko-fi" class="kofi-icon" />
          Buy me a coffee
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { useTutorial } from '@/services/tutorial'
import { version as appVersion } from '../../../../package.json'

const emit = defineEmits<{ (e: 'request-feature'): void }>()

const router = useRouter()

const aboutFeatures = [
  { icon: ['fas', 'table-cells-large'], label: 'Customizable touch button grid', desc: 'Scenes, pages, sliders and folders on a drag-and-drop deck.' },
  { icon: ['fas', 'wand-magic-sparkles'], label: 'Advanced macro automation', desc: 'Hotkeys, scripts and multi-step actions on a single tap.' },
  { icon: ['fas', 'gauge-high'], label: 'Real-time system metrics', desc: 'CPU, RAM, GPU and network at a glance.' },
  { icon: ['fas', 'plug'], label: 'Smart app integration & templates', desc: 'Scenes that follow the focused app, plus ready-made layouts.' },
  { icon: ['fas', 'chart-line'], label: 'Free stock & crypto tickers', desc: 'Live quotes on the screensaver — no API key needed.' },
  { icon: ['fas', 'newspaper'], label: 'News & sports widgets', desc: 'Rotating headlines from free RSS feeds.' },
  { icon: ['fas', 'cloud-sun'], label: 'Live weather, no API key', desc: 'Current conditions powered by open data.' },
  { icon: ['fas', 'image'], label: 'Animated backgrounds & transparency', desc: 'Gradients, particle scenes and per-scene artwork.' },
  { icon: ['fas', 'display'], label: 'Customizable screensaver', desc: 'Arrangeable widgets with drag-snap alignment.' },
  { icon: ['fas', 'hand-pointer'], label: 'Touch-optimized 7-inch interface', desc: 'Sized and spaced for dedicated touch panels.' },
]

// "Launch Tutorial" — flag the request, then go to the dashboard where the
// tour measures live targets on mount.
function launchTutorial() {
  useTutorial().requestLaunch()
  router.push('/')
}
</script>

<style scoped>
.nav-ver {
  margin-left: auto;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--accent-ghost);
  color: #9cc0ff;
  font-size: var(--fs-xs);
  font-variant-numeric: tabular-nums;
}
.kv-list { margin: 0; }
.kv {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 9px 0;
  border-bottom: 1px solid var(--line-soft);
  font-size: var(--fs-sm);
}
.kv:last-child { border-bottom: 0; }
.kv dt { color: var(--text-2); }
.kv dd { margin: 0; font-family: var(--mono); font-size: var(--fs-sm); }
.col-about { max-width: 880px; }
.about-hero { display: flex; align-items: center; gap: 16px; }
.about-mark { width: 52px; height: 52px; border-radius: 14px; }
.about-title { margin: 0; font-size: var(--fs-xl); font-weight: 650; }
.about-title-row { display: flex; align-items: baseline; gap: 10px; }
.about-title-row .nav-ver { margin-left: 0; }
.about-support {
  position: sticky;
  bottom: 8px;
  z-index: 5;
  display: flex;
  justify-content: center;
  padding: 4px 0 8px;
}
.kofi-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  background: #ff5e5b;
  color: #fff;
  border-radius: var(--radius-full);
  text-decoration: none;
  font-size: var(--fs-xs);
  font-weight: 600;
  min-height: 30px;
  flex-shrink: 0;
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}
.kofi-btn:hover { opacity: 0.9; transform: translateY(-1px); }
.kofi-icon { width: 18px; height: 18px; object-fit: contain; }
.feature-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 28px; }
.feature {
  display: flex;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line-soft);
}
.feature:last-child { border-bottom: 0; }
@media (min-width: 881px) {
.feature:nth-last-child(2):nth-child(odd) { border-bottom: 0; }
}
.feature-icon { color: var(--accent); margin-top: 2px; flex: none; }
.feature-text { min-width: 0; }
.feature-title { font-size: var(--fs-sm); font-weight: 600; color: var(--text); }
.feature-desc { font-size: var(--fs-xs); margin-top: 2px; }
@media (max-width: 880px) {
.about-hero { flex-direction: column; align-items: flex-start; }
}

@media (max-width: 880px) {
.feature-list { grid-template-columns: 1fr; } }
</style>
