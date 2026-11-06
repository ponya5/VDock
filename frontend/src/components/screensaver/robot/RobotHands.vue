<template>
  <!-- DL-155 / DL-163: Wingy's 3D-shaded articulated hands (and laptop).
       Each finger has proximal + distal phalanx articulation, knuckle joints,
       contoured sleeve/cuff with LED status accent, and clap/cover motion FX. -->
  <g :data-scene="scene" :opacity="opacity">
    <g v-if="def.laptop" :transform="`translate(0 ${(1 - u) * 70 - 14})`" data-part="laptop">
      <rect x="50" y="92" width="100" height="54" rx="7" fill="url(#rb-metal-dark)" stroke="#6b7396" stroke-width="0.8" />
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
    <!-- Clap sonic burst rings when hands meet -->
    <g v-if="scene === 'clap' && clapImpact > 0.45" :opacity="f((clapImpact - 0.45) * 1.6)" fill="none" stroke="#ffd84d" stroke-width="2.2" stroke-linecap="round">
      <path d="M100 102 V92 M88 106 L80 98 M112 106 L120 98 M86 146 L78 154 M114 146 L122 154" />
    </g>
    <g
      v-for="(h, i) in poses"
      v-show="h.visible"
      :key="i"
      :data-hand="i === 0 ? 'left' : 'right'"
      :transform="`translate(${f(h.x)} ${f(h.y)}) ${h.mirror ? 'scale(-1 1)' : ''} rotate(${f(h.rot)})`"
    >
      <!-- Contoured forearm sleeve + highlight -->
      <path d="M-96 -11 Q-56 -13 -22 -10 V10 Q-56 13 -96 11 Z" fill="url(#rb-sleeve)" />
      <path d="M-92 -7 Q-56 -9 -25 -7" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity="0.35" />
      <!-- Ribbed wrist cuff + glowing LED accent -->
      <rect x="-27" y="-14.5" width="15" height="29" rx="5.5" fill="url(#rb-cuff)" stroke="#9aa6dd" stroke-width="0.8" />
      <rect x="-21" y="-6" width="3.2" height="12" rx="1.6" fill="#6cc7ff" opacity="0.85" />
      <!-- Articulated 2-segment thumb -->
      <g :transform="`translate(1 -12.5) rotate(${f(h.thumb)})`">
        <rect x="-3" y="-4.5" width="12" height="8.6" rx="4.3" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.7" />
        <g :transform="`translate(8 0) rotate(${f(h.thumb * 0.35)})`">
          <rect x="-2" y="-4" width="10" height="8" rx="4" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.7" />
          <ellipse cx="4" cy="-1.2" rx="2.5" ry="1.3" fill="#fff" opacity="0.6" />
        </g>
      </g>
      <!-- Sculpted palm + knuckle ridge -->
      <ellipse cx="2.5" cy="0" rx="15.5" ry="14.5" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.9" />
      <path d="M-3 -7 Q2 0 -3 7" fill="none" stroke="#9aa6dd" stroke-width="1.1" stroke-linecap="round" opacity="0.55" />
      <!-- 2-segment articulated fingers (proximal + distal phalanx) -->
      <g v-for="(fg, fi) in FINGERS" :key="fi" :transform="`translate(10 ${fg.y}) rotate(${f(h.curl[fi])})`">
        <rect x="-2" y="-3.2" :width="fg.prox" height="6.4" rx="3.2" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.75" />
        <circle :cx="fg.prox - 2.5" cy="0" r="1.4" fill="#fff" opacity="0.45" />
        <g :transform="`translate(${fg.prox - 3} 0) rotate(${f(h.curl[fi] * 0.55)})`">
          <rect x="-1" y="-2.8" :width="fg.dist" height="5.6" rx="2.8" fill="url(#rb-skin)" stroke="#9aa6dd" stroke-width="0.75" />
          <ellipse :cx="fg.dist - 3.2" cy="-0.8" rx="2.2" ry="1.1" fill="#fff" opacity="0.65" />
        </g>
      </g>
      <!-- Palm specular highlight -->
      <ellipse cx="3" cy="-5.5" rx="6.5" ry="3.2" fill="#fff" opacity="0.55" />
    </g>
  </g>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { handPoses, SCENES, type SceneId } from '@/services/robot/scenes'
import { COLORS } from '@/services/robot/robotArt'

const props = defineProps<{ scene: SceneId; p: number; t: number; opacity: number }>()

const FINGERS = [
  { y: -9, len: 19, prox: 11.5, dist: 10.5 },
  { y: -3, len: 22, prox: 13, dist: 12 },
  { y: 3, len: 19, prox: 11.5, dist: 10.5 },
  { y: 9, len: 15, prox: 9.5, dist: 8.5 },
] as const
const keys = [0, 1, 2, 3, 4, 5, 6, 7]
const palette = [COLORS.pink, COLORS.blue, COLORS.yellow, COLORS.orange, COLORS.blue, COLORS.pink] as const

const def = computed(() => SCENES[props.scene])
const u = computed(() => Math.min(1, Math.max(0, props.p)))
const poses = computed(() => handPoses(props.scene, props.p, props.t))
const f = (n: number) => Math.round(n * 100) / 100
const clapImpact = computed(() => 1 - Math.abs(Math.sin(props.t / 1000 * 8)))

// Lines of "code" that grow and shrink while Wingy types.
const codeLines = computed(() => palette.map((color, i) => ({
  color,
  indent: (i % 3) * 5,
  width: 14 + 52 * (0.35 + 0.65 * Math.abs(Math.sin(props.t / 900 + i * 1.3))),
})))
const cursorX = computed(() => 8 + 40 * Math.abs(Math.sin(props.t / 700)))
const cursorOn = computed(() => Math.floor(props.t / 450) % 2 === 0)
</script>
