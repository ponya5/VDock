<template>
  <!-- DL-153: the robot face. Everything here is bound to the FaceFrame the
       stage's rAF loop produces; nothing animates on its own (no CSS
       keyframes, no SMIL). The glow is a blurred copy under the face
       with a filter that never changes. -->
  <svg
    class="robot-face"
    viewBox="-20 -40 240 200"
    preserveAspectRatio="xMidYMid meet"
    :data-expression="frame.expression"
    :data-icon="frame.icon.id ?? ''"
    :data-accessory="frame.accessory.id ?? ''"
    aria-hidden="true"
  >
    <defs>
      <filter id="robot-glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="5" />
      </filter>
    </defs>
    <g :transform="frame.transform">
      <!-- glow copy (static filter) + crisp face, faded together while an icon shows -->
      <g :opacity="frame.faceOpacity">
        <g filter="url(#robot-glow)" opacity="0.55">
          <path :d="frame.eyeL" fill="#fff" :opacity="frame.eyeOpacityL" />
          <path :d="frame.eyeR" fill="#fff" :opacity="frame.eyeOpacityR" />
          <path :d="frame.mouth" fill="#fff" stroke="#fff" stroke-width="5" stroke-linejoin="round" :opacity="frame.mouthOpacity" />
        </g>
        <path data-part="eye" :d="frame.eyeL" fill="#fff" :opacity="frame.eyeOpacityL" />
        <path data-part="eye" :d="frame.eyeR" fill="#fff" :opacity="frame.eyeOpacityR" />
        <path data-part="mouth" :d="frame.mouth" fill="#fff" stroke="#fff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" :opacity="frame.mouthOpacity" />
        <path :d="frame.tongue" fill="#ff9a4d" :opacity="frame.tongueOpacity * frame.mouthOpacity" />
        <ellipse :cx="frame.eyeLCenter[0] - 6" :cy="frame.eyeLCenter[1] + 34" rx="11" ry="5" fill="#ff6fa8" :opacity="frame.blush * 0.7" />
        <ellipse :cx="frame.eyeRCenter[0] + 6" :cy="frame.eyeRCenter[1] + 34" rx="11" ry="5" fill="#ff6fa8" :opacity="frame.blush * 0.7" />
        <g v-if="frame.glyphL.id" :data-glyph="frame.glyphL.id" :opacity="frame.glyphL.opacity"
           :transform="`translate(${frame.eyeLCenter[0]} ${frame.eyeLCenter[1]}) scale(${frame.glyphL.scale * 1.5})`">
          <RobotArt :def="EYE_GLYPHS[frame.glyphL.id]" :t="frame.t" :level="level" />
        </g>
        <g v-if="frame.glyphR.id" :data-glyph="frame.glyphR.id" :opacity="frame.glyphR.opacity"
           :transform="`translate(${frame.eyeRCenter[0]} ${frame.eyeRCenter[1]}) scale(${frame.glyphR.scale * 1.5})`">
          <RobotArt :def="EYE_GLYPHS[frame.glyphR.id]" :t="frame.t" :level="level" />
        </g>
        <g v-if="frame.mouthGlyph.id" :data-mouth-glyph="frame.mouthGlyph.id" :opacity="frame.mouthGlyph.opacity"
           :transform="`translate(${frame.mouthCenter[0]} ${frame.mouthCenter[1]}) scale(${frame.mouthGlyph.scale})`">
          <RobotArt :def="MOUTH_GLYPHS[frame.mouthGlyph.id]" :t="frame.t" :level="level" />
        </g>
      </g>
      <g v-if="frame.accessory.id" :data-accessory="frame.accessory.id" :opacity="frame.accessory.opacity"
         :transform="`translate(0 ${frame.accessory.dy})`">
        <RobotArt :def="ACCESSORIES[frame.accessory.id]" :t="frame.t" :level="level" />
      </g>
    </g>
    <!-- status icon: centred, outside the face transform so it stays steady -->
    <g v-if="frame.icon.id" :data-icon-shown="frame.icon.id" :opacity="frame.icon.opacity"
       :transform="`translate(100 70) scale(${frame.icon.scale * 1.4})`">
      <RobotArt :def="ICONS[frame.icon.id]" :t="frame.t" :level="level" />
    </g>
    <g v-for="p in frame.props" :key="p.key" :data-prop="p.id"
       :opacity="propEnvelope(p.age, PROPS[p.id].life ?? 2000).opacity"
       :transform="`translate(${(PROPS[p.id].anchor ?? [170, 40])[0]} ${(PROPS[p.id].anchor ?? [170, 40])[1]}) scale(${propEnvelope(p.age, PROPS[p.id].life ?? 2000).scale})`">
      <RobotArt :def="PROPS[p.id]" :t="p.age" :level="level" />
    </g>
  </svg>
</template>

<script setup lang="ts">
import RobotArt from './RobotArt.vue'
import { EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES, propEnvelope } from '@/services/robot/robotArt'
import type { FaceFrame } from '@/services/robot/animator'

defineProps<{ frame: FaceFrame; level: number }>()
</script>

<style scoped>
.robot-face { width: 100%; height: 100%; overflow: visible; display: block; }
</style>
