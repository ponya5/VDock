<template>
  <!-- DL-165: Wingy's typing desk - a glowing laptop seen in perspective on a wooden desk, "buddy UI" on the
       screen with coloured code lines, a lit key grid and sparkles rising off the keys. Scene space, back to front. -->
  <g stroke-linecap="round" stroke-linejoin="round">
    <!-- wooden desk top -->
    <path :d="wide ? 'M-30 116 L230 104 L230 150 L-30 150 Z' : 'M-30 116 L150 103 L160 150 L-30 150 Z'" fill="url(#rb-wood)" stroke="#fff" stroke-width="1.6" opacity="0.98" />
    <path :d="wide ? 'M-30 116 L230 104' : 'M-30 116 L150 103'" stroke="#fff" stroke-width="1.2" opacity="0.35" fill="none" />

    <!-- screen: glow halo, dark panel, outline -->
    <path :d="SCREEN" fill="none" stroke="#6cc7ff" stroke-width="7" opacity="0.22" />
    <path :d="SCREEN" fill="#080d24" stroke="#bfe6ff" stroke-width="2" />
    <text transform="translate(3 68) rotate(-7)" font-size="7.5" font-weight="700" fill="#fff" stroke="none" font-family="system-ui, sans-serif" opacity="0.95">buddy UI</text>
    <!-- code lines "typing" themselves out -->
    <path :d="line(0, 41 + 3 * Math.sin(t / (fast ? 90 : 300)))" stroke="#ff6fa8" stroke-width="3.2" fill="none" />
    <path :d="line(1, 45 + 4 * Math.sin(t / (fast ? 80 : 260) + 1))" stroke="#ffd84d" stroke-width="3.2" fill="none" />
    <path :d="line(2, 24 + 5 * Math.abs(Math.sin(t / (fast ? 110 : 380) + 2)))" stroke="#6cc7ff" stroke-width="3.2" fill="none" />
    <path :d="line(3, 30 + 4 * Math.abs(Math.sin(t / (fast ? 95 : 330) + 3)))" stroke="#ff9a4d" stroke-width="3.2" fill="none" />

    <!-- keyboard deck -->
    <path :d="DECK" fill="none" stroke="#6cc7ff" stroke-width="6" opacity="0.2" />
    <path :d="DECK" fill="#0b1130" stroke="#bfe6ff" stroke-width="1.8" />
    <g fill="none" stroke="#8fd4ff" stroke-width="0.7">
      <rect v-for="(k, i) in keys" :key="i" :x="k.x - k.w" :y="k.y - k.h" :width="k.w * 2" :height="k.h * 2" rx="0.8"
            :fill="lit(i)" :opacity="lit(i) === 'none' ? 0.7 : 0.95" />
    </g>

    <!-- sparkles rising off the keys -->
    <g stroke="none">
      <circle v-for="n in 8" :key="`sp-${n}`"
              :cx="f(64 + n * 4.2 + Math.sin(t / 260 + n) * 3)" :cy="f(104 - ((t / (fast ? 9 : 17) + n * 7) % 24))" r="1.4"
              :fill="['#6cc7ff', '#ff6fa8', '#ffd84d', '#fff'][n % 4]"
              :opacity="f(1 - ((t / (fast ? 9 : 17) + n * 7) % 24) / 24)" />
    </g>
  </g>
</template>

<script setup lang="ts">
const props = defineProps<{ t: number; fast?: boolean; wide?: boolean }>()
const f = (n: number) => Math.round(n * 100) / 100

const SCREEN = 'M-10 56 L58 48 L62 100 L-6 108 Z'
// deck corners: back-left, back-right, front-right, front-left (perspective: wider at the front)
const B0 = [-6, 108], B1 = [62, 100], F1 = [106, 130], F0 = [-32, 136]
const DECK = `M${B0} L${B1} L${F1} L${F0} Z`

const lerp = (a: number, b: number, k: number) => a + (b - a) * k
const keys: Array<{ x: number; y: number; w: number; h: number }> = []
for (let r = 0; r < 5; r++) {
  for (let c = 0; c < 11; c++) {
    const u = (c + 0.5) / 11
    const v = (r + 0.7) / 5.6
    const topX = lerp(B0[0], B1[0], u), topY = lerp(B0[1], B1[1], u)
    const botX = lerp(F0[0], F1[0], u), botY = lerp(F0[1], F1[1], u)
    keys.push({ x: lerp(topX, botX, v), y: lerp(topY, botY, v), w: lerp(1.7, 3.1, v), h: lerp(0.9, 1.5, v) })
  }
}

/** A key lights up briefly, pseudo-randomly, as if it was just struck. */
function lit(i: number): string {
  const slot = Math.floor(props.t / (props.fast ? 70 : 150))
  const h = (i * 7919 + slot * 104729) % 17
  if (h === 0) return '#ff6fa8'
  if (h === 1) return '#6cc7ff'
  if (h === 2) return '#ffd84d'
  return 'none'
}

/** Code line i on the slanted screen, `len` units long. */
function line(i: number, len: number): string {
  const x0 = 2 + i * 0.6
  const y0 = 77 + i * 8.2 - i * 0.9
  return `M${f(x0)} ${f(y0)} L${f(x0 + len)} ${f(y0 - len * 0.12)}`
}
</script>
