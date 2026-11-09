<script setup lang="ts">
/**
 * DL-129: face for `action.type === 'now_playing'` — a two-cell track card
 * fed by the SMTC monitor (useNowPlaying). Art left, title/artist right,
 * a state line, and a progress bar when the app reports a duration.
 * The press itself is intercepted upstream (media_play_pause toggle) —
 * this component is display only.
 */
import { computed, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
  nowPlayingIcon,
  nowPlayingSourceLabel,
  useNowPlaying,
} from '@/services/nowPlaying'

const props = defineProps<{ compact?: boolean }>()

const { track, playing, available, artUrl } = useNowPlaying()

const artFailed = ref(false)
watch(artUrl, () => { artFailed.value = false })

// Site-aware label/icon: "YouTube" + its logo beats "chrome.exe" + a note
// when the backend has attributed the session to a site.
const sourceLabel = computed(() => nowPlayingSourceLabel(track.value))
const brandIcon = computed(() => nowPlayingIcon(track.value))
const brandClass = computed(() =>
  track.value?.site ? `is-${track.value.site.toLowerCase()}` : '')

const progressPct = computed(() => {
  const t = track.value
  if (!t?.duration_s || !t.position_s) return null
  return Math.min(100, Math.max(0, (t.position_s / t.duration_s) * 100))
})

const stateText = computed(() => {
  if (available.value === false) return 'No media session'
  if (!track.value) return 'Nothing playing'
  return playing.value ? 'Playing' : 'Paused'
})
</script>

<template>
  <div class="np-face" :class="{ compact: props.compact }">
   <div class="np-inner">
    <template v-if="track">
      <div class="np-art" :class="{ 'is-paused': !playing }">
        <img v-if="artUrl && !artFailed" :src="artUrl" alt="" class="np-art-img" @error="artFailed = true" />
        <FontAwesomeIcon v-else :icon="brandIcon || ['fas', 'music']" class="np-art-fallback np-brand" :class="brandClass" />
      </div>
      <div class="np-meta">
        <span class="np-title">{{ track.title }}</span>
        <span class="np-artist">{{ [track.artist, sourceLabel].filter(Boolean).join(' · ') }}</span>
        <span class="np-state">
          <FontAwesomeIcon :icon="['fas', playing ? 'pause' : 'play']" />
          {{ stateText }}
        </span>
        <div v-if="progressPct !== null" class="np-progress">
          <div class="np-progress-fill" :style="{ width: `${progressPct}%` }" />
        </div>
      </div>
    </template>
    <template v-else>
      <div class="np-empty">
        <FontAwesomeIcon :icon="['fas', 'music']" />
        <span>{{ stateText }}</span>
      </div>
    </template>
   </div>
  </div>
</template>

<style scoped>
.np-face {
  width: 100%;
  height: 100%;
  /* DL-165: the card measures itself, so the art and text grow with the button. */
  container-type: size;
}

.np-inner {
  display: flex;
  align-items: center;
  gap: clamp(10px, 3cqh, 28px);
  width: 100%;
  height: 100%;
  padding: 6px 8px;
  box-sizing: border-box;
  overflow: hidden;
  text-align: left;
}

.np-art {
  position: relative;
  flex: none;
  width: clamp(40px, min(40cqw, 84cqh), 560px);
  aspect-ratio: 1;
  border-radius: clamp(8px, 3cqh, 20px);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.np-art.is-paused { opacity: 0.65; }

.np-art-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.np-art-fallback {
  font-size: clamp(1.4em, 12cqh, 5em);
  opacity: 0.5;
}

.np-brand { opacity: 0.9; }
.np-brand.is-youtube { color: #ff4a45; }
.np-brand.is-spotify { color: #1db954; }
.np-brand.is-twitch { color: #9146ff; }

.np-meta {
  display: flex;
  flex-direction: column;
  gap: clamp(2px, 1cqh, 8px);
  min-width: 0;
  flex: 1;
}

.np-title {
  font-weight: 700;
  font-size: clamp(0.92em, 8cqh, 3.6em);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.np-artist {
  font-size: clamp(0.78em, 5.6cqh, 2.4em);
  opacity: 0.78;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.np-state {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: clamp(0.66em, 4cqh, 1.5em);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  opacity: 0.7;
}

.np-progress {
  height: clamp(3px, 1.4cqh, 9px);
  width: 100%;
  max-width: clamp(80px, 62%, 560px);
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.14);
  overflow: hidden;
  margin-top: 3px;
}

.np-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: currentColor;
  opacity: 0.85;
  transition: width 1s linear;
}

.np-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  font-size: 0.8em;
  opacity: 0.55;
}

/* Tall / square cards: the art takes the top, big and centred, with the text below it. */
@container (max-aspect-ratio: 1/1) {
  .np-inner { flex-direction: column; justify-content: center; text-align: center; }
  .np-art { width: min(86cqw, 56cqh); }
  .np-meta { flex: none; align-items: center; width: 100%; }
  .np-state { justify-content: center; }
  .np-progress { max-width: 80%; }
}

.compact .np-artist,
.compact .np-progress { display: none; }
</style>
