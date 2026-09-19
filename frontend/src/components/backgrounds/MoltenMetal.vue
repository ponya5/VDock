<template>
  <div ref="containerRef" class="molten-metal-container" :data-ready="ready || undefined">
    <canvas ref="canvasRef" class="molten-metal-canvas" />
  </div>
</template>

<script setup lang="ts">
// Ported from reactbits.dev MoltenMetal (ogl/WebGL).
import { onMounted, onUnmounted, ref } from 'vue'
import { Mesh, Program, Renderer, Triangle } from 'ogl'

const props = withDefaults(
  defineProps<{
    speed?: number
    scale?: number
    detail?: number
    glow?: number
    coreSize?: number
    swirl?: number
    fold?: number
    blackPoint?: number
    brightness?: number
    colorMode?: number
    grain?: number
    opacity?: number
    colorA?: string
    colorB?: string
    colorC?: string
    mouseStrength?: number
    mouseRadius?: number
    onError?: (error: Error) => void
  }>(),
  {
    speed: 0.45,
    scale: 0.8,
    detail: 2,
    glow: 0.9,
    coreSize: 0.5,
    swirl: 1.2,
    fold: 1.15,
    blackPoint: 0.08,
    brightness: 1.15,
    colorMode: 0,
    grain: 0.03,
    opacity: 1,
    colorA: '#4f7cff',
    colorB: '#ff8a00',
    colorC: '#ffffff',
    mouseStrength: 0.55,
    mouseRadius: 1.6,
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
uniform float uDetail;
uniform float uGlow;
uniform float uCoreSize;
uniform float uSwirl;
uniform float uFold;
uniform float uBlackPoint;
uniform float uBrightness;
uniform int uColorMode;
uniform float uGrain;
uniform float uOpacity;
uniform vec2 uMouse;
uniform float uMouseStrength;
uniform float uMouseRadius;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uColorC;
varying vec2 vUv;

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

vec2 rotate(vec2 p, float a) {
  float c = cos(a);
  float s = sin(a);
  return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}

vec2 swirlField(vec2 p, float amt) {
  float r = length(p);
  float a = atan(p.y, p.x);
  a += amt / (0.12 + r);
  return vec2(cos(a), sin(a)) * r;
}

float fbm(vec2 p, float t, float mouseHeat) {
  float v = 0.0;
  float amp = 0.55;
  vec2 q = p;
  for (int i = 0; i < 6; i += 1) {
    if (float(i) >= uDetail + 2.0) break;
    q = swirlField(q + vec2(t * 0.18, -t * 0.12), uSwirl * (0.65 + 0.4 * amp));
    float n = noise(q * uFold + vec2(t * 0.35, -t * 0.28) + i * 1.7);
    n = pow(n, 1.1 + uGlow * 0.5);
    v += n * amp;
    q = rotate(q, 0.65 + amp * 0.2);
    amp *= 0.55;
  }
  v = max(0.0, v - uBlackPoint * (0.6 + 0.3 * sin(t * 0.9)));
  return v * (1.0 + mouseHeat * 0.5);
}

vec3 palette(float v) {
  v = clamp(v, 0.0, 1.0);
  vec3 c1 = uColorA;
  vec3 c2 = uColorB;
  vec3 c3 = uColorC;
  vec3 col = mix(c1, c2, smoothstep(0.05, 0.72, v));
  col = mix(col, c3, smoothstep(0.62, 0.98, v));
  return col;
}

void main() {
  vec2 uv = vUv * 2.0 - 1.0;
  uv.x *= uResolution.x / uResolution.y;
  vec2 p = uv * uScale;
  float t = uTime * uSpeed;

  vec2 m = (uMouse - 0.5) * vec2(uResolution.x / uResolution.y, 1.0) * uScale;
  float md = length(uv * uScale - m);
  float fall = uMouseRadius;
  float heat = exp(-pow(md / fall, 2.0)) * uMouseStrength;

  float v = fbm(p + vec2(t * 0.3, -t * 0.22), t, heat);
  float core = smoothstep(uCoreSize, uCoreSize * 0.15, v);
  vec3 col = palette(v + core * 0.22);

  col *= uBrightness * (0.6 + 0.5 * heat);
  col += (hash(vUv * uResolution + t) - 0.5) * uGrain;
  gl_FragColor = vec4(col, uOpacity);
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
  const maxTexSize = gl.getParameter(gl.MAX_TEXTURE_SIZE) || 2048

  const geometry = new Triangle(gl)
  const program = new Program(gl, {
    vertex,
    fragment,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: [1, 1] },
      uSpeed: { value: props.speed },
      uScale: { value: props.scale },
      uDetail: { value: props.detail },
      uGlow: { value: props.glow },
      uCoreSize: { value: props.coreSize },
      uSwirl: { value: props.swirl },
      uFold: { value: props.fold },
      uBlackPoint: { value: props.blackPoint },
      uBrightness: { value: props.brightness },
      uColorMode: { value: props.colorMode },
      uGrain: { value: props.grain },
      uOpacity: { value: props.opacity },
      uMouse: { value: [0.5, 0.5] },
      uMouseStrength: { value: props.mouseStrength },
      uMouseRadius: { value: props.mouseRadius },
      uColorA: { value: hexToRgb(props.colorA) },
      uColorB: { value: hexToRgb(props.colorB) },
      uColorC: { value: hexToRgb(props.colorC) }
    }
  })
  const mesh = new Mesh(gl, { geometry, program })

  let frame = 0
  let running = true
  let visible = true
  let hasInteracted = false
  let lastTime = performance.now()
  let elapsed = 0

  const resize = () => {
    const width = container.clientWidth || 1
    const height = container.clientHeight || 1
    renderer!.setSize(width, height)
    program.uniforms.uResolution.value = [gl.canvas.width, gl.canvas.height]
    canvas.style.setProperty('--molten-metal-maxtex', `${maxTexSize}px`)
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

  const handleMouse = (event: MouseEvent) => {
    if (!hasInteracted) {
      hasInteracted = true
      canvas.classList.add('has-interacted')
    }
    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    program.uniforms.uMouse.value = [x, 1 - y]
    canvas.style.setProperty('--molten-metal-mx', `${event.clientX - rect.left}px`)
    canvas.style.setProperty('--molten-metal-my', `${event.clientY - rect.top}px`)
  }
  window.addEventListener('mousemove', handleMouse, { passive: true })

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
    window.removeEventListener('mousemove', handleMouse)
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
.molten-metal-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.molten-metal-canvas {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 400ms ease;
  touch-action: none;
}

.molten-metal-container[data-ready='true'] .molten-metal-canvas {
  opacity: v-bind('props.opacity');
}
</style>
