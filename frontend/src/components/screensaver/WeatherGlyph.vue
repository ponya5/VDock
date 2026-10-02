<script setup lang="ts">
// Animated weather glyph (DL-136): a pure-SVG scene driven by the real
// WMO code + Open-Meteo's is_day flag — sun with slowly orbiting rays by
// day, a spinning crescent moon + twinkling stars by night, clouds,
// rain, snow, fog, storm, and a wind-streak overlay. All motion is CSS
// keyframes; prefers-reduced-motion freezes every scene legibly.
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  code?: number | null
  isDay?: boolean
  windy?: boolean
  unavailable?: boolean
}>(), { code: null, isDay: true, windy: false, unavailable: false })

type Scene =
  | 'sun' | 'moon' | 'sun-cloud' | 'moon-cloud' | 'overcast'
  | 'fog' | 'drizzle' | 'rain' | 'snow' | 'storm' | 'cloud'

const scene = computed<Scene>(() => {
  if (props.unavailable || props.code === null || props.code === undefined) return 'cloud'
  const c = props.code
  if (c >= 95) return 'storm'
  if ([71, 73, 75, 77, 85, 86].includes(c)) return 'snow'
  if ([61, 63, 65, 80, 81, 82].includes(c)) return 'rain'
  if ([51, 53, 55].includes(c)) return 'drizzle'
  if ([45, 48].includes(c)) return 'fog'
  if (c === 3) return 'overcast'
  if (c === 2) return props.isDay ? 'sun-cloud' : 'moon-cloud'
  if (c === 0 || c === 1) return props.isDay ? 'sun' : 'moon'
  return 'cloud'
})
</script>

<template>
  <svg class="weather-glyph" :class="{ 'is-dim': unavailable }" viewBox="0 0 64 64"
    aria-hidden="true">
    <defs>
      <radialGradient id="wg-sun" cx="42%" cy="38%" r="70%">
        <stop offset="0%" stop-color="#ffe9a8" />
        <stop offset="60%" stop-color="#ffd152" />
        <stop offset="100%" stop-color="#f5a83c" />
      </radialGradient>
      <radialGradient id="wg-moon" cx="38%" cy="35%" r="75%">
        <stop offset="0%" stop-color="#fdfdff" />
        <stop offset="100%" stop-color="#c9d2f2" />
      </radialGradient>
      <linearGradient id="wg-cloud" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff" />
        <stop offset="100%" stop-color="#c9d4e6" />
      </linearGradient>
      <linearGradient id="wg-cloud-dark" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#aab4cc" />
        <stop offset="100%" stop-color="#7c8aa8" />
      </linearGradient>
    </defs>

    <!-- Reusable cloud silhouette -->
    <defs>
      <path id="wg-cloud-path" d="M 17 46
        a 9 9 0 0 1 -1.4 -17.8
        a 11.5 11.5 0 0 1 22.2 -3.4
        a 8.5 8.5 0 0 1 9.2 8.4
        a 8 8 0 0 1 -4.5 12.8
        Z" />
    </defs>

    <!-- ======== Sun ======== -->
    <g v-if="scene === 'sun'">
      <g class="wg-sun-rays">
        <line v-for="i in 8" :key="i" x1="32" y1="9" x2="32" y2="15"
          :transform="`rotate(${(i - 1) * 45} 32 30)`" />
      </g>
      <circle cx="32" cy="30" r="11" fill="url(#wg-sun)" />
    </g>

    <!-- ======== Moon ======== -->
    <g v-else-if="scene === 'moon'">
      <circle class="wg-star s1" cx="14" cy="12" r="1.1" />
      <circle class="wg-star s2" cx="50" cy="10" r="0.9" />
      <circle class="wg-star s3" cx="55" cy="24" r="1.2" />
      <g class="wg-moon-spin">
        <!-- Crescent = outer arc (r 13) back along a flatter inner arc. The
             inner radius must exceed half the 26-unit chord or the SVG
             spec scales it up to 13 and the two arcs coincide (zero area:
             the moon vanishes and only the stars remain). -->
        <path class="wg-moon-body" fill="url(#wg-moon)" d="M 41.5 19
          a 13 13 0 1 0 0 26
          a 17 17 0 0 1 0 -26 Z" />
      </g>
    </g>

    <!-- ======== Partly cloudy ======== -->
    <g v-else-if="scene === 'sun-cloud' || scene === 'moon-cloud'">
      <g v-if="scene === 'sun-cloud'">
        <g class="wg-sun-rays small">
          <line v-for="i in 8" :key="i" x1="22" y1="9" x2="22" y2="13"
            :transform="`rotate(${(i - 1) * 45} 22 18)`" />
        </g>
        <circle cx="22" cy="18" r="7" fill="url(#wg-sun)" />
      </g>
      <g v-else class="wg-moon-spin small">
        <path class="wg-moon-body" fill="url(#wg-moon)" d="M 30.5 8.5
          a 9.5 9.5 0 1 0 0 19
          a 12.5 12.5 0 0 1 0 -19 Z" />
      </g>
      <!-- Positioning transform lives on the wrapper: a CSS transform
           animation on the <use> itself would override its attribute. -->
      <g transform="translate(8 2)"><use href="#wg-cloud-path" class="wg-cloud-fg" /></g>
    </g>

    <!-- ======== Overcast / generic cloud ======== -->
    <g v-else-if="scene === 'overcast' || scene === 'cloud'">
      <use href="#wg-cloud-path" class="wg-cloud-back" transform="translate(-6 -7) scale(0.8)" />
      <g transform="translate(8 4)"><use href="#wg-cloud-path" class="wg-cloud-fg" /></g>
    </g>

    <!-- ======== Fog ======== -->
    <g v-else-if="scene === 'fog'">
      <use href="#wg-cloud-path" class="wg-cloud-dim" transform="translate(8 0)" />
      <g class="wg-fog-lines">
        <rect x="14" y="46" width="26" height="2.6" rx="1.3" />
        <rect class="l2" x="24" y="51" width="30" height="2.6" rx="1.3" />
        <rect class="l3" x="10" y="56" width="24" height="2.6" rx="1.3" />
      </g>
    </g>

    <!-- ======== Drizzle / Rain / Snow / Storm ======== -->
    <g v-else>
      <g transform="translate(8 -2)">
        <use href="#wg-cloud-path"
          :class="scene === 'storm' ? 'wg-cloud-storm' : 'wg-cloud-fg'" />
      </g>
      <g v-if="scene === 'drizzle'" class="wg-rain">
        <line class="d1" x1="24" y1="44" x2="22.5" y2="50" />
        <line class="d3" x1="40" y1="44" x2="38.5" y2="50" />
      </g>
      <g v-else-if="scene === 'rain'" class="wg-rain">
        <line class="d1" x1="22" y1="44" x2="20" y2="52" />
        <line class="d2" x1="32" y1="44" x2="30" y2="52" />
        <line class="d3" x1="42" y1="44" x2="40" y2="52" />
        <line class="d4" x1="48" y1="44" x2="46" y2="52" />
      </g>
      <g v-else-if="scene === 'snow'" class="wg-snow">
        <circle class="f1" cx="23" cy="46" r="1.7" />
        <circle class="f2" cx="32" cy="48" r="1.9" />
        <circle class="f3" cx="41" cy="46" r="1.7" />
        <circle class="f4" cx="48" cy="49" r="1.5" />
      </g>
      <g v-else-if="scene === 'storm'">
        <g class="wg-rain">
          <line class="d1" x1="20" y1="44" x2="18" y2="51" />
          <line class="d3" x1="45" y1="44" x2="43" y2="51" />
        </g>
        <path class="wg-bolt" d="M 33 40 l -6.5 11 h 5 l -3 10 11 -13 h -5.5 l 4 -8 Z" />
      </g>
    </g>

    <!-- ======== Wind overlay ======== -->
    <g v-if="windy" class="wg-wind">
      <path class="w1" d="M 6 20 q 9 -5 18 0 t 18 0" />
      <path class="w2" d="M 12 56 q 9 5 18 0 t 18 0" />
    </g>
  </svg>
</template>

<style scoped>
.weather-glyph {
  width: 1em;
  height: 1em;
  display: block;
  overflow: visible;
}
.weather-glyph.is-dim {
  opacity: 0.45;
  filter: saturate(0.4);
}

/* --- Sun --- */
.wg-sun-rays line {
  stroke: #ffd76a;
  stroke-width: 2.6;
  stroke-linecap: round;
}
.wg-sun-rays {
  animation: wg-spin 32s linear infinite;
  transform-box: view-box;
}
.wg-sun-rays.small {
  animation-duration: 26s;
}
/* rotate() needs an origin in view-box units */
.wg-sun-rays { transform-origin: 32px 30px; }
.wg-sun-rays.small { transform-origin: 22px 18px; }

/* --- Moon --- */
.wg-moon-spin {
  animation: wg-moon-sway 14s ease-in-out infinite alternate;
  transform-box: view-box;
  transform-origin: 32px 32px;
}
.wg-moon-spin.small { transform-origin: 30px 18px; }
.wg-star {
  fill: #e8ecff;
  animation: wg-twinkle 3.2s ease-in-out infinite;
}
.wg-star.s2 { animation-delay: -1.1s; }
.wg-star.s3 { animation-delay: -2.3s; }

/* --- Clouds --- */
.wg-cloud-fg {
  fill: url(#wg-cloud);
  opacity: 0.95;
  animation: wg-bob 7s ease-in-out infinite alternate;
}
.wg-cloud-back {
  fill: url(#wg-cloud-dark);
  opacity: 0.55;
}
.wg-cloud-dim {
  fill: url(#wg-cloud-dark);
  opacity: 0.75;
}
.wg-cloud-storm {
  fill: url(#wg-cloud-dark);
  opacity: 0.95;
}

/* --- Rain --- */
.wg-rain line {
  stroke: #8ec2ff;
  stroke-width: 2;
  stroke-linecap: round;
  animation: wg-drop 1.15s linear infinite;
}
.wg-rain .d2 { animation-delay: -0.38s; }
.wg-rain .d3 { animation-delay: -0.76s; }
.wg-rain .d4 { animation-delay: -0.57s; }

/* --- Snow --- */
.wg-snow circle {
  fill: #ffffff;
  animation: wg-flake 2.6s linear infinite;
}
.wg-snow .f2 { animation-delay: -0.9s; }
.wg-snow .f3 { animation-delay: -1.7s; }
.wg-snow .f4 { animation-delay: -0.45s; }

/* --- Bolt --- */
.wg-bolt {
  fill: #ffd76a;
  animation: wg-flash 3s ease-in-out infinite;
}

/* --- Fog --- */
.wg-fog-lines rect {
  fill: rgba(255, 255, 255, 0.55);
  animation: wg-mist 5s ease-in-out infinite alternate;
}
.wg-fog-lines .l2 { animation-delay: -1.7s; }
.wg-fog-lines .l3 { animation-delay: -3.3s; }

/* --- Wind --- */
.wg-wind path {
  fill: none;
  stroke: rgba(255, 255, 255, 0.65);
  stroke-width: 2;
  stroke-linecap: round;
  animation: wg-gust 3.4s ease-in-out infinite;
}
.wg-wind .w2 { animation-delay: -1.6s; }

@keyframes wg-spin { to { transform: rotate(360deg); } }
@keyframes wg-moon-sway {
  from { transform: rotate(-16deg); }
  to { transform: rotate(16deg); }
}
@keyframes wg-twinkle {
  0%, 100% { opacity: 0.25; }
  50% { opacity: 1; }
}
@keyframes wg-bob {
  from { transform: translateX(-1.6px); }
  to { transform: translateX(1.6px); }
}
@keyframes wg-drop {
  0% { transform: translateY(0); opacity: 0; }
  18% { opacity: 1; }
  82% { opacity: 1; }
  100% { transform: translateY(9px); opacity: 0; }
}
@keyframes wg-flake {
  0% { transform: translate(0, 0); opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 1; }
  100% { transform: translate(-3px, 9px); opacity: 0; }
}
@keyframes wg-flash {
  0%, 64%, 100% { opacity: 0.35; }
  70%, 78% { opacity: 1; }
  74% { opacity: 0.4; }
}
@keyframes wg-mist {
  from { transform: translateX(-5px); opacity: 0.35; }
  to { transform: translateX(5px); opacity: 0.75; }
}
@keyframes wg-gust {
  0%, 100% { transform: translateX(-4px); opacity: 0.15; }
  50% { transform: translateX(4px); opacity: 0.8; }
}

@media (prefers-reduced-motion: reduce) {
  .weather-glyph * {
    animation: none !important;
  }
}
</style>
