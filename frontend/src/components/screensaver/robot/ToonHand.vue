<template>
  <!-- DL-156 / DL-163: storyboard-style articulated hand — white rim outline,
       deep black fill, wrist cuff, inner specular highlights, and per-finger
       phase-offset animation driven by the stage rAF clock `t`. -->
  <g :data-toon-hand="kind">
    <!-- Fat white silhouette layer so overlapping parts fuse into one clean outline -->
    <g fill="#fff" stroke="#fff" stroke-width="5.2" stroke-linejoin="round" stroke-linecap="round">
      <rect
        v-if="cuff"
        :x="cuff.x" :y="cuff.y" :width="cuff.w" :height="cuff.h" :rx="cuff.rx"
        :transform="cuff.rot ? `rotate(${cuff.rot} ${cuff.x + cuff.w / 2} ${cuff.y + cuff.h / 2})` : undefined"
      />
      <ellipse
        v-for="(e, i) in animatedParts"
        :key="`o${i}`"
        :cx="e[0]" :cy="e[1]" :rx="e[2]" :ry="e[3]"
        :transform="`rotate(${e[4]} ${e[0]} ${e[1]})`"
      />
    </g>
    <!-- Crisp black fill layer -->
    <g fill="#000" stroke="none">
      <rect
        v-if="cuff"
        :x="cuff.x" :y="cuff.y" :width="cuff.w" :height="cuff.h" :rx="cuff.rx"
        :transform="cuff.rot ? `rotate(${cuff.rot} ${cuff.x + cuff.w / 2} ${cuff.y + cuff.h / 2})` : undefined"
      />
      <ellipse
        v-for="(e, i) in animatedParts"
        :key="`f${i}`"
        :cx="e[0]" :cy="e[1]" :rx="e[2]" :ry="e[3]"
        :transform="`rotate(${e[4]} ${e[0]} ${e[1]})`"
      />
    </g>
    <!-- Cuff accent seam + rivet -->
    <g v-if="cuff" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round" opacity="0.75">
      <path :d="cuff.seam" />
    </g>
    <!-- Inner specular rim highlight for depth -->
    <path
      v-if="shape.shine"
      :d="shape.shine"
      fill="none"
      stroke="#fff"
      stroke-width="2"
      stroke-linecap="round"
      opacity="0.38"
    />
    <!-- Knuckle & palm crease lines -->
    <path :d="dynamicLines" fill="none" stroke="#fff" stroke-width="1.85" stroke-linecap="round" stroke-linejoin="round" />
    <!-- Dynamic finger-tap / key-strike / drum motion arcs -->
    <path v-if="tap || kind === 'drum'" :d="curlPath" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" />
    <path v-if="strikeSparks" :d="strikeSparks" fill="none" stroke="#6cc7ff" stroke-width="1.7" stroke-linecap="round" opacity="0.85" />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type ToonKind =
  | 'fist' | 'mitten' | 'open' | 'point'
  | 'typing' | 'drum' | 'thumbsup' | 'stretch' | 'facepalm' | 'peace'

type Part = readonly [number, number, number, number, number] // cx, cy, rx, ry, rot
interface CuffDef { x: number; y: number; w: number; h: number; rx: number; rot?: number; seam: string }
interface ShapeDef {
  parts: Part[]
  lines: string
  shine?: string
  cuff?: CuffDef
}

const SHAPES: Record<ToonKind, ShapeDef> = {
  fist: {
    parts: [[0, 3, 16, 14, 0], [-9, -8, 6.5, 6.2, -4], [0, -11, 6.5, 6.2, 0], [9, -9, 6, 6, 4], [15, -2, 5.2, 5.8, 10], [-12, 8, 5.5, 8.5, 22]],
    lines: 'M-4 -6 Q-4 0 -9 2 M5 -6 Q5 1 1 3 M12 -4 Q12 2 8 5',
    shine: 'M-11 -1 Q-6 -9 4 -9',
    cuff: { x: -13, y: 13, w: 26, h: 8, rx: 4, seam: 'M-9 17 H9' },
  },
  mitten: {
    parts: [[0, 0, 21, 12, 0], [16, 4, 7.5, 8.5, 14], [10, -8, 7.5, 6.5, 6], [2, -10, 7, 6, -2], [-14, -7, 5.5, 7.5, -22]],
    lines: 'M4 -5 Q8 1 2 5 M11 -3 Q15 3 9 7 M17 0 Q20 5 15 8',
    shine: 'M-14 -4 Q-4 -9 8 -6',
    cuff: { x: -24, y: -9, w: 9, h: 18, rx: 4, seam: 'M-20 -5 V5' },
  },
  typing: {
    // Articulated 4-finger + thumb typing hand (palm + thumb + index, middle, ring, pinky)
    parts: [
      [-2, -2, 18, 11, -6],      // 0: sculpted palm
      [-14, 5, 5.5, 8.5, 32],    // 1: thumb tucked near spacebar
      [15, -5, 5.2, 9.5, 28],    // 2: index finger reaching keys
      [11, -8, 5.2, 10, 18],     // 3: middle finger
      [5, -9, 5, 9.5, 8],        // 4: ring finger
      [-2, -8, 4.6, 8.5, -4],    // 5: pinky finger
    ],
    lines: 'M11 -7 Q15 -1 12 5 M6 -8 Q10 -2 7 4 M0 -8 Q4 -2 1 4',
    shine: 'M-14 -6 Q-3 -10 8 -7',
    cuff: { x: -25, y: -10, w: 9, h: 18, rx: 4, rot: -8, seam: 'M-21 -5 V5' },
  },
  drum: {
    // Hand resting on desk, fingers cascading in a boredom drum wave
    parts: [
      [-4, 2, 18, 11, 0],        // 0: resting palm
      [-16, 6, 6, 7, 40],        // 1: resting thumb
      [16, 4, 4.8, 9, 42],       // 2: index finger
      [11, 2, 4.8, 9.5, 32],     // 3: middle finger
      [5, 1, 4.6, 9, 22],        // 4: ring finger
      [-1, 1, 4.4, 8, 12],       // 5: pinky finger
    ],
    lines: 'M12 0 Q15 5 11 8 M6 -1 Q9 4 5 7 M0 0 Q3 4 -1 7',
    shine: 'M-15 -3 Q-4 -7 7 -4',
    cuff: { x: -26, y: -6, w: 9, h: 17, rx: 4, seam: 'M-22 -2 V6' },
  },
  open: {
    parts: [[0, 6, 16, 15, 0], [-14, -12, 5, 13, -22], [-5, -19, 5, 15, -7], [6, -19, 5, 15, 7], [15, -12, 5, 12, 22], [-18, 4, 5.5, 11, -62]],
    lines: 'M-8 -2 Q-9 6 -4 10 M6 0 Q8 6 5 10',
    shine: 'M-10 2 Q0 -3 9 2',
    cuff: { x: -13, y: 17, w: 26, h: 8, rx: 4, seam: 'M-8 21 H8' },
  },
  point: {
    parts: [[0, 4, 15, 13, 0], [-9, -6, 6, 6, 0], [8, -7, 6, 6, 0], [14, 0, 5, 5.5, 0], [-12, 9, 5, 7, 20], [-4, -20, 5.2, 14.5, -8]],
    lines: 'M-2 -4 Q1 -2 -1 2 M5 -3 Q8 0 5 3',
    shine: 'M-6 -28 Q-4 -32 -2 -26',
    cuff: { x: -12, y: 14, w: 24, h: 7, rx: 3.5, seam: 'M-7 17.5 H7' },
  },
  thumbsup: {
    parts: [
      [1, 3, 15, 13.5, 0],       // 0: fist palm
      [-12, -14, 6.2, 13.5, -14], // 1: big upward thumb
      [13, -6, 6.5, 5.5, 8],     // 2: curled index knuckle
      [14, 1, 6.5, 5.5, 6],      // 3: curled middle knuckle
      [13, 8, 6, 5.2, 4],        // 4: curled ring knuckle
      [10, 13, 5.2, 4.8, 0],     // 5: curled pinky knuckle
    ],
    lines: 'M6 -3 H14 M7 4 H15 M6 10 H13 M-7 -2 Q-3 2 -6 8',
    shine: 'M-14 -21 Q-12 -25 -9 -19',
    cuff: { x: -18, y: 8, w: 10, h: 18, rx: 4, rot: 12, seam: 'M-13 12 V22' },
  },
  stretch: {
    parts: [[0, 5, 15, 14, 0], [-15, -13, 4.8, 13.5, -28], [-5, -20, 4.8, 15.5, -9], [5, -20, 4.8, 15.5, 9], [15, -13, 4.8, 13, 28], [-18, 2, 5.2, 11, -68]],
    lines: 'M-7 0 Q-5 6 0 9 M6 0 Q5 6 1 9',
    shine: 'M-9 1 Q0 -4 9 1',
    cuff: { x: -12, y: 16, w: 24, h: 8, rx: 4, seam: 'M-7 20 H7' },
  },
  facepalm: {
    parts: [[0, 5, 17, 15, 0], [-13, -13, 5.2, 13, -16], [-4, -19, 5.2, 15, -4], [5, -19, 5.2, 15, 5], [14, -12, 5, 12.5, 16], [-18, 3, 5.5, 11, -52]],
    lines: 'M-8 -4 V6 M0 -6 V6 M8 -4 V6',
    shine: 'M-10 3 Q0 -2 10 3',
    cuff: { x: -13, y: 17, w: 26, h: 8, rx: 4, seam: 'M-8 21 H8' },
  },
  peace: {
    parts: [
      [0, 5, 15, 13.5, 0],       // 0: palm
      [-7, -18, 5, 15.5, -14],   // 1: index V finger
      [6, -18, 5, 15.5, 14],     // 2: middle V finger
      [12, 1, 6, 6.5, 12],       // 3: curled ring finger
      [14, 7, 5.5, 6, 18],       // 4: curled pinky
      [-11, 3, 6.5, 8.5, 36],    // 5: thumb holding ring finger
    ],
    lines: 'M-6 2 Q0 5 8 1 M6 5 Q11 6 10 10',
    shine: 'M-9 -26 Q-7 -30 -5 -24 M4 -26 Q6 -30 8 -24',
    cuff: { x: -12, y: 16, w: 24, h: 7.5, rx: 3.8, seam: 'M-7 20 H7' },
  },
}

const props = defineProps<{ kind: ToonKind; t?: number; tap?: boolean; fast?: boolean; phase?: number }>()
const shape = computed(() => SHAPES[props.kind] ?? SHAPES.mitten)
const cuff = computed(() => shape.value.cuff ?? null)
const r2 = (n: number) => Math.round(n * 100) / 100

// Per-finger procedural animation so fingers articulate instead of moving as a rigid block
const animatedParts = computed<Part[]>(() => {
  const base = shape.value.parts
  const t = props.t
  if (t === undefined) return base
  const s = t / 1000
  const ph = props.phase ?? 0
  const freq = props.fast ? 22 : 13

  if (props.kind === 'typing' || (props.kind === 'mitten' && props.tap)) {
    return base.map((p, i): Part => {
      if (i === 0) return [p[0], r2(p[1] + Math.sin(s * freq + ph) * 0.9), p[2], p[3], r2(p[4] + Math.sin(s * freq * 0.5 + ph) * 2.5)]
      if (i === 1) {
        // Thumb spacebar tap
        const th = Math.max(0, Math.sin(s * freq * 0.7 + ph + 0.5))
        return [p[0], r2(p[1] + th * 3.2), p[2], p[3], r2(p[4] + th * 12)]
      }
      // Individual finger strikes with distinct phase per finger
      const strike = Math.sin(s * freq + ph + i * 1.55)
      const down = Math.max(0, strike)
      const lift = Math.max(0, -strike) * 0.45
      return [
        r2(p[0] + down * 1.4),
        r2(p[1] + down * 5.2 - lift * 2.6),
        p[2],
        p[3],
        r2(p[4] + down * 22 - lift * 10),
      ]
    })
  }

  if (props.kind === 'drum') {
    // Cascading finger drum wave (pinky -> ring -> middle -> index -> pause)
    return base.map((p, i): Part => {
      if (i < 2) return p
      const wave = Math.sin(s * 6.5 + ph - (i - 2) * 0.85)
      const lift = Math.max(0, wave)
      return [
        p[0],
        r2(p[1] - lift * 6.5),
        p[2],
        p[3],
        r2(p[4] - lift * 24),
      ]
    })
  }

  if (props.kind === 'open' || props.kind === 'stretch') {
    // Secondary follow-through splay on each extended finger
    return base.map((p, i): Part => {
      if (i === 0) return p
      const sway = Math.sin(s * 7.5 + ph - i * 0.45) * (props.kind === 'stretch' ? 5.5 : 4)
      const stretchY = props.kind === 'stretch' ? -Math.abs(Math.sin(s * 4 + i * 0.3)) * 2.2 : 0
      return [p[0], r2(p[1] + stretchY), p[2], p[3], r2(p[4] + sway)]
    })
  }

  if (props.kind === 'thumbsup') {
    return base.map((p, i): Part => {
      if (i !== 1) return p
      const wiggle = Math.sin(s * 9 + ph) * 8
      return [p[0], r2(p[1] - Math.abs(Math.sin(s * 4.5)) * 1.8), p[2], p[3], r2(p[4] + wiggle)]
    })
  }

  if (props.kind === 'peace') {
    return base.map((p, i): Part => {
      if (i !== 1 && i !== 2) return p
      const dir = i === 1 ? -1 : 1
      const spread = Math.sin(s * 7 + ph) * 4 * dir
      return [p[0], p[1], p[2], p[3], r2(p[4] + spread)]
    })
  }

  if (props.kind === 'facepalm') {
    return base.map((p, i): Part => {
      if (i === 0) return p
      const tense = Math.sin(s * 12 + i) * 1.8
      return [p[0], p[1], p[2], p[3], r2(p[4] + tense)]
    })
  }

  return base
})

const dynamicLines = computed(() => {
  if (props.t === undefined) return shape.value.lines
  const s = props.t / 1000
  const ph = props.phase ?? 0
  if (props.kind === 'typing') {
    const k1 = Math.sin(s * (props.fast ? 22 : 13) + ph) * 2
    const k2 = Math.cos(s * (props.fast ? 22 : 13) + ph) * 2
    return `M11 ${r2(-7 + k1)} Q15 -1 12 ${r2(5 + k1)} M6 ${r2(-8 + k2)} Q10 -2 7 ${r2(4 + k2)} M0 -8 Q4 -2 1 4`
  }
  return shape.value.lines
})

// Finger-curl / impact line that flicks while typing or drumming
const curlPath = computed(() => {
  const s = (props.t ?? 0) / 1000
  const ph = props.phase ?? 0
  const freq = props.fast ? 22 : 13
  if (props.kind === 'drum') {
    const tap = Math.max(0, -Math.sin(s * 6.5 + ph))
    return `M${r2(12 - tap * 2)} 10 Q16 ${r2(12 + tap * 2)} ${r2(21 + tap * 2)} 10`
  }
  const k = Math.max(0, Math.sin(s * freq + ph))
  return `M${r2(-4 + k * 4)} 7 Q2 ${r2(11 + k * 3)} ${r2(10 + k * 3)} 8`
})

const strikeSparks = computed(() => {
  if (props.t === undefined || (props.kind !== 'typing' && !props.tap)) return ''
  const s = props.t / 1000
  const ph = props.phase ?? 0
  const freq = props.fast ? 22 : 13
  const pulse = Math.sin(s * freq + ph)
  if (pulse < 0.35) return ''
  const x = 14 + Math.floor(((s * 9 + ph) % 3)) * 4
  return `M${x} 11 L${x + 3} 14 M${x + 5} 10 L${x + 9} 12`
})
</script>
