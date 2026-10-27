<template>
  <div
    ref="rootEl"
    class="robot-stage"
    :class="{ 'face-right': settings.robotFaceSide === 'right' }"
    :data-mood="engineState.mood"
    :data-reaction="engineState.reaction ?? ''"
    :data-baseline="engineState.baseline"
    :data-expression="frame.expression"
    :data-icon="frame.icon.id ?? ''"
    @pointermove="onPointerMove"
    @pointerleave="onPointerLeave"
  >
    <!-- DL-153: robot buddy saver — face half + clock half. Mouse movement and
         finger drags on the face are play; a click anywhere (or a tap) still
         bubbles to ScreenSaver's root dismiss handler. -->
    <div
      class="rs-face"
      @touchstart.stop="onFaceTouchStart"
      @touchmove="onFaceTouchMove"
      @touchend="onFaceTouchEnd"
      @touchcancel="onFaceTouchCancel"
    >
      <div class="rs-face-box">
        <RobotFace ref="faceCmp" :frame="frame" :level="bobLevel" />
      </div>
      <RobotBubble :text="settings.robotQuips ? quip : null" />
    </div>
    <div class="rs-clock"><RobotClock /></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import RobotFace from './robot/RobotFace.vue'
import RobotClock from './robot/RobotClock.vue'
import RobotBubble from './robot/RobotBubble.vue'
import { useSettingsStore } from '@/stores/settings'
import { FaceAnimator, type FaceFrame } from '@/services/robot/animator'
import { PointerSense, type PointerGesture } from '@/services/robot/pointerSense'
import { MoodEngine, type RobotCommand } from '@/services/robot/moodEngine'
import { localDay, resolveMood, useRobotSignals } from '@/services/robot/signals'

const settings = useSettingsStore()
const rootEl = ref<HTMLElement | null>(null)
const faceCmp = ref<{ $el: SVGSVGElement } | null>(null)
const animator = new FaceAnimator()
const sense = new PointerSense()
const { signals, audioLevel, start: startSignals, stop: stopSignals } = useRobotSignals()
const engine = new MoodEngine({
  mood: resolveMood(settings.robotMood, localDay(new Date())),
  quips: settings.robotQuips,
  reactTo: settings.robotReactTo,
})
const engineState = reactive({ ...engine.state })
const frame = shallowRef<FaceFrame>(animator.frame())
const quip = ref<string | null>(null)
const bobLevel = computed(() => (settings.robotReactTo.music ? audioLevel.value : 0))

let raf = 0
let last = -1
let tickTimer: ReturnType<typeof setInterval> | null = null
let quipTimer: ReturnType<typeof setTimeout> | null = null
let gestureQueue: PointerGesture[] = []

function loop(ts: number): void {
  const dt = last < 0 ? 16.7 : ts - last
  last = ts
  animator.setBob(bobLevel.value)
  animator.step(dt, ts)
  frame.value = animator.frame()
  raf = requestAnimationFrame(loop)
}
function startLoop(): void { if (!raf) { last = -1; raf = requestAnimationFrame(loop) } }
function stopLoop(): void { if (raf) { cancelAnimationFrame(raf); raf = 0 } }

function apply(cmds: RobotCommand[]): void {
  for (const c of cmds) {
    switch (c.type) {
      case 'expr': animator.setExpression(c.id); break
      case 'seq': animator.playSequence(c.id); break
      case 'icon': animator.setIcon(c.id); break
      case 'prop': animator.addProp(c.id); break
      case 'accessory': animator.setAccessory(c.id); break
      case 'quip':
        quip.value = c.text
        if (quipTimer) clearTimeout(quipTimer)
        quipTimer = setTimeout(() => { quip.value = null }, 3500)
        break
    }
  }
}

function tick(): void {
  const now = performance.now()
  const gestures = [...gestureQueue, ...sense.tick(now)]
  gestureQueue = []
  if (sense.lastMoveAt > 0 && now - sense.lastMoveAt > 120_000) animator.setLook(null)
  apply(engine.step(signals.value, gestures, sense.lastMoveAt, now))
  Object.assign(engineState, engine.state)
}

function toFace(clientX: number, clientY: number): { x: number; y: number } | null {
  const svg = faceCmp.value?.$el
  const ctm = svg?.getScreenCTM?.()
  if (!svg || !ctm) return null
  const p = new DOMPoint(clientX, clientY).matrixTransform(ctm.inverse())
  return { x: p.x / 200, y: p.y / 200 }
}

function onPointerMove(e: PointerEvent): void {
  const p = toFace(e.clientX, e.clientY)
  if (!p) return
  gestureQueue.push(...sense.move(p.x, p.y, performance.now()))
  animator.setLook(sense.look())
}
function onPointerLeave(): void {
  gestureQueue.push(...sense.leave(performance.now()))
  animator.setLook(null)
}

// Touch: a drag on the face is play, a tap still dismisses (via the
// browser's synthetic click bubbling to the saver root).
let touchStart: { x: number; y: number; t: number } | null = null
let touchMoved = 0
function onFaceTouchCancel(): void {
  touchStart = null
  touchMoved = 0
}
function onFaceTouchStart(e: TouchEvent): void {
  const t = e.touches[0]
  touchStart = t ? { x: t.clientX, y: t.clientY, t: performance.now() } : null
  touchMoved = 0
}
function onFaceTouchMove(e: TouchEvent): void {
  const t = e.touches[0]
  if (!t || !touchStart) return
  touchMoved = Math.max(touchMoved, Math.hypot(t.clientX - touchStart.x, t.clientY - touchStart.y))
}
function onFaceTouchEnd(e: TouchEvent): void {
  const t = e.changedTouches[0]
  if (touchStart && t) touchMoved = Math.max(touchMoved, Math.hypot(t.clientX - touchStart.x, t.clientY - touchStart.y))
  const held = touchStart ? performance.now() - touchStart.t : 0
  if (touchMoved >= 8 || held >= 300) e.preventDefault()
  touchStart = null
}

function onVisibility(): void { if (document.hidden) stopLoop(); else startLoop() }

watch(signals, tick)
watch(
  () => [settings.robotMood, settings.robotQuips, settings.robotReactTo] as const,
  ([mood, quips, reactTo]) => engine.configure({ mood: resolveMood(mood, localDay(new Date())), quips, reactTo }),
  { deep: true },
)

let reducedMq: MediaQueryList | null = null
const onReduced = () => animator.setReducedMotion(Boolean(reducedMq?.matches))
onMounted(() => {
  reducedMq = typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : null
  onReduced()
  reducedMq?.addEventListener?.('change', onReduced)
  startSignals()
  tick()
  tickTimer = setInterval(tick, 500)
  document.addEventListener('visibilitychange', onVisibility)
  startLoop()
})
onBeforeUnmount(() => {
  stopLoop()
  if (tickTimer) clearInterval(tickTimer)
  if (quipTimer) clearTimeout(quipTimer)
  document.removeEventListener('visibilitychange', onVisibility)
  reducedMq?.removeEventListener?.('change', onReduced)
  stopSignals()
})
</script>

<style scoped>
.robot-stage {
  position: absolute; inset: 0; background: #000;
  display: grid; grid-template-columns: 1fr 1fr; grid-template-areas: 'face clock';
}
.robot-stage.face-right { grid-template-areas: 'clock face'; }
.rs-face { grid-area: face; position: relative; display: flex; align-items: center; justify-content: center; touch-action: none; min-width: 0; min-height: 0; }
.rs-face-box { width: 70%; height: 70%; }
.rs-clock { grid-area: clock; min-width: 0; min-height: 0; }
@media (orientation: portrait) {
  .robot-stage, .robot-stage.face-right { grid-template-columns: 1fr; grid-template-rows: 60% 40%; grid-template-areas: 'face' 'clock'; }
  .rs-face-box { width: 85%; height: 85%; }
}
</style>
