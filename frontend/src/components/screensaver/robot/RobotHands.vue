<template>
  <!-- DL-155: Wingy's hands (and the laptop they type on). Geometry comes from
       services/robot/scenes.ts; gradients are shared <defs> in RobotFace. -->
  <g :data-scene="scene" :opacity="opacity">
    <g v-if="def.laptop" :transform="`translate(0 ${(1 - u) * 70 - 14})`" data-part="laptop">
      <rect x="50" y="92" width="100" height="54" rx="7" fill="url(#rb-metal-dark)" />
      <rect x="55" y="97" width="90" height="44" rx="3.5" fill="url(#rb-screen)" />
      <rect
        v-for="(l, i) in codeLines"
        :key="i"
        :x="60 + l.indent" :y="102 + i * 7.4" :width="l.width" height="3.6" rx="1.8" :fill="l.color"
      />
      <rect :x="62 + cursorX" y="102" width="2.6" height="4" rx="1" fill="#fff" :opacity="cursorOn ? 1 : 0.15" />
      <path d="M38 146 H162 L156 162 Q155 164 152 164 H48 Q45 164 44 162 Z" fill="url(#rb-metal)" />
      <rect v-for="k in keys" :key="k" :x="k * 11 + 52" y="150" width="8" height="3.4" rx="1" fill="#6b7396" opacity="0.6" />
      <rect v-for="k in keys" :key="`b${k}`" :x="k * 11 + 52" y="156" width="8" height="3.4" rx="1" fill="#6b7396" opacity="0.6" />
      <rect x="84" y="147" width="32" height="2" rx="1" fill="#fff" opacity="0.35" />
    </g>
    <g
      v-for="(h, i) in poses"
      v-show="h.visible"
      :key="i"
      :data-hand="i === 0 ? 'left' : 'right'"
      :transform="`translate(${f(h.x)} ${f(h.y)}) ${h.mirror ? 'scale(-1 1)' : ''} rotate(${f(h.rot)})`"
    >
      <rect x="-96" y="-12" width="84" height="24" rx="8" fill="url(#rb-sleeve)" />
      <rect x="-26" y="-14" width="14" height="28" rx="5" fill="url(#rb-cuff)" />
      <g :transform="`translate(2 -13) rotate(${f(h.thumb)})`">
        <rect x="-3" y="-4.5" width="17" height="9" rx="4.5" fill="url(#rb-skin)" />
      </g>
      <ellipse cx="2" cy="0" rx="15" ry="14.5" fill="url(#rb-skin)" />
      <g v-for="(fg, fi) in FINGERS" :key="fi" :transform="`translate(10 ${fg.y}) rotate(${f(h.curl[fi])})`">
        <rect x="-2" y="-3" :width="fg.len" height="6" rx="3" fill="url(#rb-skin)" />
      </g>
      <ellipse cx="3" cy="-5" rx="6" ry="3" fill="#fff" opacity="0.5" />
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { handPoses, SCENES, type SceneId } from '@/services/robot/scenes'
import { COLORS } from '@/services/robot/robotArt'

const props = defineProps<{ scene: SceneId; p: number; t: number; opacity: number }>()

const FINGERS = [{ y: -9, len: 19 }, { y: -3, len: 22 }, { y: 3, len: 19 }, { y: 9, len: 15 }] as const
const keys = [0, 1, 2, 3, 4, 5, 6, 7]
const palette = [COLORS.pink, COLORS.blue, COLORS.yellow, COLORS.orange, COLORS.blue, COLORS.pink] as const

const def = computed(() => SCENES[props.scene])
const u = computed(() => Math.min(1, Math.max(0, props.p)))
const poses = computed(() => handPoses(props.scene, props.p, props.t))
const f = (n: number) => Math.round(n * 100) / 100

// Lines of "code" that grow and shrink while Wingy types.
const codeLines = computed(() => palette.map((color, i) => ({
  color,
  indent: (i % 3) * 5,
  width: 14 + 52 * (0.35 + 0.65 * Math.abs(Math.sin(props.t / 900 + i * 1.3))),
})))
const cursorX = computed(() => 8 + 40 * Math.abs(Math.sin(props.t / 700)))
const cursorOn = computed(() => Math.floor(props.t / 450) % 2 === 0)
</script>
