<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  nowPlayingIcon,
  nowPlayingSourceLabel,
  useNowPlaying,
} from '@/services/nowPlaying'

defineProps<{ layoutEdit?: boolean }>()

const { track, playing, available, artUrl } = useNowPlaying()

// A 404 from the art endpoint (cache deleted between payload and fetch)
// falls back to the music icon instead of a broken image.
const artFailed = ref(false)
watch(artUrl, () => { artFailed.value = false })
const showArt = computed(() => Boolean(artUrl.value) && !artFailed.value)

// The socket only emits on change, so between payloads the bar advances at
// 1 Hz from the last reported position and re-anchors on the next emit.
const displayPosition = ref(0)
watch(track, (t) => { displayPosition.value = t?.position_s ?? 0 }, { immediate: true })

const tick = window.setInterval(() => {
  const t = track.value
  if (!t?.playing || !t.duration_s) return
  displayPosition.value = Math.min(displayPosition.value + 1, t.duration_s)
}, 1000)
onUnmounted(() => window.clearInterval(tick))

const showProgress = computed(() => Boolean(track.value?.duration_s))
const progressPct = computed(() => {
  const duration = track.value?.duration_s ?? 0
  return duration > 0 ? Math.min(100, (displayPosition.value / duration) * 100) : 0
})

// Site-aware tag: "YouTube" beats "chrome.exe" when the backend has
// attributed the browser session to a site.
const sourceTag = computed(() => nowPlayingSourceLabel(track.value))
const brandIcon = computed(() => nowPlayingIcon(track.value))
const brandClass = computed(() =>
  track.value?.site ? `is-${track.value.site.toLowerCase()}` : '')

// Honest states: null = never heard yet (loading), false = unsupported,
// true + no track = the honest "Nothing playing".
const emptyText = computed(() => {
  if (available.value === null) return 'Loading…'
  if (available.value === false) return 'Not supported on this system'
  return 'Nothing playing'
})
</script>

<template>
  <section class="np-widget">
    <div class="np-head">
      <h2>Now Playing</h2>
      <span class="np-hairline"></span>
    </div>

    <div v-if="track" class="np-body">
      <div class="np-art" :class="{ 'np-art-paused': !playing }">
        <img v-if="showArt" :src="artUrl ?? ''" alt="" @error="artFailed = true" />
        <FontAwesomeIcon v-else :icon="brandIcon || ['fas', 'music']" class="np-art-icon np-brand" :class="brandClass" />
        <span class="np-glyph">
          <FontAwesomeIcon :icon="['fas', playing ? 'play' : 'pause']" />
        </span>
      </div>
      <div class="np-meta">
        <div class="np-title" :title="track.title">{{ track.title }}</div>
        <div class="np-artist">{{ track.artist || 'Unknown artist' }}</div>
        <span v-if="sourceTag" class="np-source">{{ sourceTag }}</span>
        <div v-if="showProgress" class="np-progress" role="presentation">
          <div class="np-progress-fill" :style="{ width: `${progressPct}%` }"></div>
        </div>
      </div>
    </div>

    <div v-else class="np-empty">
      <FontAwesomeIcon :icon="['fas', 'music']" class="np-empty-icon" />
      <span>{{ emptyText }}</span>
    </div>
  </section>
</template>

<style scoped>
/* Mirrors ScreenSaver.vue's .ss-section / .ss-section-head / .ss-empty
   language — small-caps head, hairline, dim secondary text. */
.np-widget {
  display: flex;
  flex-direction: column;
  gap: clamp(0.8rem, 2vh, 1.6rem);
  width: 230px;
  max-width: 100%;
  min-width: 0;
}

.np-head {
  display: flex;
  align-items: center;
  gap: 1.1rem;
}

.np-head h2 {
  margin: 0;
  font-size: clamp(0.6rem, 1.1vw, 1rem);
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(255, 255, 255, 0.5);
}

.np-hairline {
  flex-grow: 1;
  height: 1px;
  background-color: rgba(255, 255, 255, 0.14);
}

.np-body {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.np-art {
  position: relative;
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
}

.np-art img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.np-art-paused img {
  opacity: 0.55;
}

.np-art-icon {
  font-size: 1.4rem;
  color: rgba(255, 255, 255, 0.4);
}

.np-brand.is-youtube { color: #ff4a45; }
.np-brand.is-spotify { color: #1db954; }
.np-brand.is-twitch { color: #9146ff; }

.np-glyph {
  position: absolute;
  right: 4px;
  bottom: 4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.62);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.55rem;
}

.np-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.np-title {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: clamp(0.95rem, 1.4vw, 1.35rem);
  line-height: 1.2;
  color: rgba(255, 255, 255, 0.94);
}

.np-artist {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: clamp(0.7rem, 1vw, 0.95rem);
  line-height: 1.25;
  color: rgba(255, 255, 255, 0.6);
}

.np-source {
  margin-top: 2px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: clamp(0.5rem, 0.8vw, 0.7rem);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
}

.np-progress {
  align-self: stretch;
  margin-top: 6px;
  height: 3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.14);
  overflow: hidden;
}

.np-progress-fill {
  height: 100%;
  border-radius: 2px;
  background: var(--ss-accent, #f2b040);
  transition: width 1s linear;
}

.np-empty {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  font-size: 0.9em;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.75);
}

.np-empty-icon {
  opacity: 0.5;
}
</style>
