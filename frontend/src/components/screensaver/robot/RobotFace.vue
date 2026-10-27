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
      <linearGradient v-for="g in GRADIENTS" :id="g.id" :key="g.id" :x1="g.x1 ?? 0" :y1="g.y1 ?? 0" :x2="g.x2 ?? 1" :y2="g.y2 ?? 1">
        <stop v-for="(st, i) in g.stops" :key="i" :offset="st[0]" :stop-color="st[1]" />
      </linearGradient>
    </defs>
    <g :transform="frame.transform">
      <g v-if="frame.deco.rage > 0.02" :opacity="frame.deco.rage * (0.32 + 0.14 * Math.sin(frame.t / 1000 * 9))">
        <ellipse cx="100" cy="72" rx="86" ry="56" fill="#ff2a2a" filter="url(#robot-glow)" />
      </g>
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
        <ellipse cx="0" cy="0" :transform="`translate(${frame.eyeLCenter[0] - 6} ${frame.eyeLCenter[1] + 34})`" rx="11" ry="5" fill="#ff6fa8" :opacity="frame.blush * 0.7" />
        <ellipse cx="0" cy="0" :transform="`translate(${frame.eyeRCenter[0] + 6} ${frame.eyeRCenter[1] + 34})`" rx="11" ry="5" fill="#ff6fa8" :opacity="frame.blush * 0.7" />
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
      <!-- DL-156 decorations: pupils, tear, thought bubbles, rage glow -->
      <g v-if="frame.deco.pupil > 0.02" :opacity="frame.deco.pupil * frame.faceOpacity" fill="#9a9a9a">
        <circle :cx="frame.eyeLCenter[0]" :cy="frame.eyeLCenter[1] + 2" r="6" />
        <circle :cx="frame.eyeRCenter[0]" :cy="frame.eyeRCenter[1] + 2" r="6" />
      </g>
      <g v-if="frame.deco.tear > 0.02" :opacity="frame.deco.tear"
         :transform="`translate(${frame.eyeRCenter[0] + 4} ${frame.eyeRCenter[1] + 22 + ((frame.t / 1000 * 14) % 14)})`">
        <path d="M0 -8 C5 -1 6 3 0 6 C-6 3 -5 -1 0 -8 Z" fill="url(#rb-blue)" stroke="#fff" stroke-width="1.5" />
      </g>
      <g v-if="frame.deco.bubbleDots > 0.02" :opacity="frame.deco.bubbleDots" fill="none" stroke="#fff" stroke-width="2"
         :transform="`translate(${frame.eyeRCenter[0] + 40} ${frame.eyeRCenter[1] - 36}) scale(${0.8 + 0.2 * frame.deco.bubbleDots})`">
        <ellipse cx="0" cy="0" rx="22" ry="14" fill="#000" /><path d="M-14 11 L-22 20 L-6 13" fill="#000" />
        <circle v-for="i in 3" :key="i" :cx="(i - 2) * 10" :cy="-Math.max(0, Math.sin(frame.t / 1000 * 7 - i)) * 3" r="2.1" fill="#fff" stroke="none" />
      </g>
      <g v-if="frame.deco.bubbleQ > 0.02" :opacity="frame.deco.bubbleQ" fill="none" stroke="#fff" stroke-width="2"
         :transform="`translate(${frame.eyeRCenter[0] + 36} ${frame.eyeRCenter[1] - 38 + Math.sin(frame.t / 1000 * 3) * 2})`">
        <ellipse cx="0" cy="0" rx="24" ry="14" fill="#000" />
        <circle cx="-22" cy="19" r="3" fill="#000" /><circle cx="-28" cy="26" r="1.8" fill="#000" />
        <text x="0" y="5" text-anchor="middle" font-size="15" font-weight="700" fill="#fff" stroke="none">???</text>
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
    <RobotScenery v-if="frame.scene.id && SCENES[frame.scene.id].toon" :scene="frame.scene.id" :p="frame.scene.p" :t="frame.t" :opacity="frame.scene.opacity" />
    <RobotHands v-else-if="frame.scene.id" :scene="frame.scene.id" :p="frame.scene.p" :t="frame.t" :opacity="frame.scene.opacity" />
    <g v-for="p in frame.props" :key="p.key" :data-prop="p.id"
       :opacity="propEnvelope(p.age, PROPS[p.id].life ?? 2000).opacity"
       :transform="propTransform(p.id, PROPS[p.id].anchor ?? [170, 40], propEnvelope(p.age, PROPS[p.id].life ?? 2000).scale * ((PROPS[p.id] as ArtDef).scale ?? 1), p.age)">
      <RobotArt :def="PROPS[p.id]" :t="p.age" :level="level" />
      <RobotHeldHand v-if="HELD[p.id]" :held="HELD[p.id]!" :slide="heldSlide(p.age, PROPS[p.id].life ?? 2000)" :t="p.age" />
    </g>
  </svg>
</template>

<script setup lang="ts">
import RobotArt from './RobotArt.vue'
import RobotHands from './RobotHands.vue'
import RobotScenery from './RobotScenery.vue'
import { SCENES } from '@/services/robot/scenes'
import RobotHeldHand from './RobotHeldHand.vue'
import { HELD, heldSlide, propTransform } from '@/services/robot/heldProps'
import { EYE_GLYPHS, MOUTH_GLYPHS, ICONS, PROPS, ACCESSORIES, GRADIENTS, propEnvelope, type ArtDef } from '@/services/robot/robotArt'
import type { FaceFrame } from '@/services/robot/animator'

defineProps<{ frame: FaceFrame; level: number }>()
</script>

<style scoped>
.robot-face { width: 100%; height: 100%; overflow: visible; display: block; }
</style>
