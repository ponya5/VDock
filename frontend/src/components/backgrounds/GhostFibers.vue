<template>
  <div ref="containerRef" class="ghost-fibers-container" :data-ready="ready || undefined">
    <canvas ref="canvasRef" class="ghost-fibers-canvas" />
  </div>
</template>

<script setup lang="ts">
// Ported from reactbits.dev GhostFibers (ogl/WebGL).
import { onMounted, onUnmounted, ref } from 'vue'
import { Mesh, Program, Renderer, Triangle } from 'ogl'

const props = withDefaults(
  defineProps<{
    speed?: number
    scale?: number
    rotation?: number
    layers?: number
    waveAmplitude?: number
    waveFrequency?: number
    twist?: number
    lineFrequency?: number
    glow?: number
    brightness?: number
    grain?: number
    vignette?: number
    colorA?: string
    colorB?: string
    colorC?: string
    onError?: (error: Error) => void
  }>(),
  {
    speed: 0.15,
    scale: 0.85,
    rotation: -4,
    layers: 2.4,
    waveAmplitude: 0.7,
    waveFrequency: 2,
    twist: 0.32,
    lineFrequency: 0.7,
    glow: 0.4,
    brightness: 1.1,
    grain: 0.04,
    vignette: 1.25,
    colorA: '#000000',
    colorB: '#ff9a3c',
    colorC: '#ffe9d1',
    onError: undefined
  }
)

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const ready = ref(false)

const vertex = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`

const fragment = `
precision highp float;
uniform float uTime;
uniform vec2 uResolution;
uniform float uSpeed;
uniform float uScale;
uniform float uRotation;
uniform float uLayers;
uniform float uWaveAmp;
uniform float uWaveFreq;
uniform float uTwist;
uniform float uLineFreq;
uniform float uGlow;
uniform float uBrightness;
uniform float uGrain;
uniform float uVignette;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uColorC;
varying vec2 vUv;

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

void main() {
  vec2 uv = vUv * 2.0 - 1.0;
  uv.x *= uResolution.x / uResolution.y;

  float angle = radians(uRotation);
  float c = cos(angle);
  float s = sin(angle);
  uv = mat2(c, -s, s, c) * uv;

  vec2 p = uv * uScale;
  float t = uTime * uSpeed;

  float w1 = sin(p.x * uWaveFreq + t) + 0.35 * sin(p.x * uWaveFreq * 1.7 - t * 0.8);
  float w2 = sin(p.x * uWaveFreq * 1.25 - t * 0.6 + p.y * uTwist);
  p.y += (w1 * 0.65 + w2 * 0.35) * uWaveAmp;

  float r = length(p);
  float acc = 0.0;
  for (float i = 0.0; i < 4.0; i += 1.0) {
    if (i >= uLayers) break;
    float fi = i / max(uLayers, 1.0);
    float freq = uLineFreq * (1.0 + fi * 0.9);
    float v = abs(sin(p.y * freq - r * (0.5 + fi * 0.7) + t * (0.6 + fi * 0.35)));
    float line = smoothstep(0.0, 0.9, 1.0 - v);
    acc += line * (1.0 - fi * 0.55);
  }
  acc /= max(uLayers, 1.0);
  acc = pow(acc, 1.25 - uGlow * 0.45);

  vec3 col = mix(uColorA, uColorB, acc);
  col = mix(col, uColorC, pow(acc, 3.0) * 0.6);
  col *= uBrightness;
  float vig = smoothstep(1.45, 0.25, length(uv));
  col *= mix(1.0, vig, uVignette);
  col += (hash(vUv * uResolution + t) - 0.5) * uGrain;

  gl_FragColor = vec4(col, 1.0);
}
`

function hexToRgb(hex: string): [number, number, number] {
  const normalized = hex.replace('#', '')
  const full =
    normalized.length === 3
      ? normalized
          .split('')
          .map(c => c + c)
          .join('')
      : normalized
  const num = parseInt(full, 16)
  return [((num >> 16) & 255) / 255, ((num >> 8) & 255) / 255, (num & 255) / 255]
}

let cleanup: (() => void) | null = null

onMounted(() => {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas) return

  let renderer: Renderer | null = null
  try {
    renderer = new Renderer({
      canvas,
      dpr: Math.min(window.devicePixelRatio, 2),
      alpha: true,
      antialias: false,
      powerPreference: 'low-power'
    })
  } catch (error) {
    props.onError?.(error instanceof Error ? error : new Error(String(error)))
    return
  }
  const gl = renderer.gl

  const geometry = new Triangle(gl)
  const program = new Program(gl, {
    vertex,
    fragment,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: [1, 1] },
      uSpeed: { value: props.speed },
      uScale: { value: props.scale },
      uRotation: { value: props.rotation },
      uLayers: { value: props.layers },
      uWaveAmp: { value: props.waveAmplitude },
      uWaveFreq: { value: props.waveFrequency },
      uTwist: { value: props.twist },
      uLineFreq: { value: props.lineFrequency },
      uGlow: { value: props.glow },
      uBrightness: { value: props.brightness },
      uGrain: { value: props.grain },
      uVignette: { value: props.vignette },
      uColorA: { value: hexToRgb(props.colorA) },
      uColorB: { value: hexToRgb(props.colorB) },
      uColorC: { value: hexToRgb(props.colorC) }
    }
  })
  const mesh = new Mesh(gl, { geometry, program })

  let frame = 0
  let running = true
  let visible = true
  let lastTime = performance.now()
  let elapsed = 0

  const resize = () => {
    const width = container.clientWidth || 1
    const height = container.clientHeight || 1
    renderer!.setSize(width, height)
    program.uniforms.uResolution.value = [gl.canvas.width, gl.canvas.height]
  }

  const render = (now: number) => {
    if (!running) return
    frame = requestAnimationFrame(render)
    if (!visible || document.hidden) {
      lastTime = now
      return
    }
    const delta = Math.min((now - lastTime) / 1000, 0.05)
    lastTime = now
    elapsed += delta
    program.uniforms.uTime.value = elapsed
    try {
      renderer!.render({ scene: mesh })
    } catch (error) {
      running = false
      props.onError?.(error instanceof Error ? error : new Error(String(error)))
      return
    }
    if (!ready.value) ready.value = true
  }

  const resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(container)
  resize()

  const intersectionObserver = new IntersectionObserver(
    entries => {
      visible = entries[0]?.isIntersecting ?? true
    },
    { threshold: 0 }
  )
  intersectionObserver.observe(container)

  const handleVisibility = () => {
    lastTime = performance.now()
  }
  document.addEventListener('visibilitychange', handleVisibility)

  frame = requestAnimationFrame(render)

  cleanup = () => {
    running = false
    if (frame) cancelAnimationFrame(frame)
    resizeObserver.disconnect()
    intersectionObserver.disconnect()
    document.removeEventListener('visibilitychange', handleVisibility)
    const loseContext = gl.getExtension('WEBGL_lose_context')
    loseContext?.loseContext()
  }
})

onUnmounted(() => {
  cleanup?.()
  cleanup = null
})
</script>

<style scoped>
.ghost-fibers-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.ghost-fibers-canvas {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 400ms ease;
}

.ghost-fibers-container[data-ready='true'] .ghost-fibers-canvas {
  opacity: 1;
}
</style>
