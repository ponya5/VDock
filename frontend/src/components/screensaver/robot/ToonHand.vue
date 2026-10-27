<template>
  <!-- DL-156: storyboard-style hand — black fill, white outline. Shapes are drawn
       twice (white fat layer, then black on top) so overlaps keep one clean outline. -->
  <g>
    <g fill="#fff" stroke="#fff" stroke-width="5" stroke-linejoin="round">
      <ellipse v-for="(e, i) in shape.parts" :key="`o${i}`" :cx="e[0]" :cy="e[1]" :rx="e[2]" :ry="e[3]" :transform="`rotate(${e[4]} ${e[0]} ${e[1]})`" />
    </g>
    <g fill="#000">
      <ellipse v-for="(e, i) in shape.parts" :key="`f${i}`" :cx="e[0]" :cy="e[1]" :rx="e[2]" :ry="e[3]" :transform="`rotate(${e[4]} ${e[0]} ${e[1]})`" />
    </g>
    <path :d="shape.lines" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
    <path v-if="tap" :d="curlPath" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" />
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export type ToonKind = 'fist' | 'mitten' | 'open' | 'point'
type Part = readonly [number, number, number, number, number] // cx, cy, rx, ry, rot

const SHAPES: Record<ToonKind, { parts: Part[]; lines: string }> = {
  fist: {
    parts: [[0, 3, 16, 14, 0], [-9, -8, 6.5, 6, 0], [0, -11, 6.5, 6, 0], [9, -9, 6, 6, 0], [15, -2, 5, 5.5, 0], [-12, 8, 5, 8, 20]],
    lines: 'M-4 -6 Q-4 0 -9 2 M5 -6 Q5 1 1 3 M12 -4 Q12 2 8 5',
  },
  mitten: {
    parts: [[0, 0, 22, 12, 0], [16, 4, 8, 8, 0], [10, -9, 7, 6, 0], [-14, -8, 5, 7, -20]],
    lines: 'M6 -4 Q10 2 4 6 M13 -2 Q17 4 11 8',
  },
  open: {
    parts: [[0, 6, 16, 15, 0], [-14, -12, 5, 13, -22], [-5, -19, 5, 15, -7], [6, -19, 5, 15, 7], [15, -12, 5, 12, 22], [-18, 4, 5.5, 11, -62]],
    lines: 'M-8 -2 Q-9 6 -4 10 M6 0 Q8 6 5 10',
  },
  point: {
    parts: [[0, 4, 15, 13, 0], [-9, -6, 6, 6, 0], [8, -7, 6, 6, 0], [14, 0, 5, 5.5, 0], [-12, 9, 5, 7, 20], [-4, -20, 5, 14, -8]],
    lines: 'M-2 -4 Q1 -2 -1 2 M5 -3 Q8 0 5 3',
  },
}

const props = defineProps<{ kind: ToonKind; t?: number; tap?: boolean }>()
const shape = computed(() => SHAPES[props.kind])
// finger-curl line that flicks while typing
const curlPath = computed(() => {
  const k = Math.max(0, Math.sin((props.t ?? 0) / 1000 * 13))
  return `M${-6 + k * 3} 6 Q-2 ${10 + k * 2} ${4 + k * 2} 7`
})
</script>
