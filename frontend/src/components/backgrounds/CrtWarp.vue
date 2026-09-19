<template>
  <div ref="containerRef" class="crt-warp-container">
    <canvas ref="canvasRef" class="crt-warp-canvas" />
  </div>
</template>

<script setup lang="ts">
// Ported from reactbits.dev CRTWarp. The original uses three.js; the shader is
// plain fullscreen-quad GLSL, so it is rendered with ogl instead to avoid the
// three.js dependency.
import { onMounted, onUnmounted, ref } from 'vue'
import { Mesh, Program, Renderer, Triangle } from 'ogl'

const props = withDefaults(
  defineProps<{
    intensity?: number
    curvature?: number
    scanlineStrength?: number
    scanlineFrequency?: number
    waveAmp?: number
    waveFreq?: number
    bloom?: number
    noise?: number
    vignette?: number
    brightness?: number
    pixelation?: number
    rgbShift?: number
    pointerReact?: number
    colorA?: string
    colorB?: string
    backgroundColor?: string
    alpha?: number
    onError?: (error: Error) => void
  }>(),
  {
    intensity: 0.9,
    curvature: 0.22,
    scanlineStrength: 0.18,
    scanlineFrequency: 1.35,
    waveAmp: 0.02,
    waveFreq: 0.55,
    bloom: 0.3,
    noise: 0.08,
    vignette: 0.5,
    brightness: 1,
    pixelation: 0,
    rgbShift: 0.002,
    pointerReact: 0.7,
    colorA: '#ff6a00',
    colorB: '#ff3d00',
    backgroundColor: '#000000',
    alpha: 1,
    onError: undefined
  }
)

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)

const vertex = `
attribute vec3 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 1.0);
}
`

const fragment = `
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
uniform vec2 uPointer;
uniform vec2 uPointerTarget;
uniform float uPointerActive;
uniform float uIntensity;
uniform float uCurvature;
uniform float uScanlineStrength;
uniform float uScanlineFrequency;
uniform float uWaveAmp;
uniform float uWaveFreq;
uniform float uBloom;
uniform float uNoise;
uniform float uVignette;
uniform float uBrightness;
uniform float uPixelation;
uniform float uRgbShift;
uniform float uPointerReact;
uniform vec3 uColorA;
uniform vec3 uColorB;
uniform vec3 uBackground;
uniform float uAlpha;
varying vec2 vUv;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

vec2 curveUv(vec2 uv) {
  vec2 c = uv - 0.5;
  float r2 = dot(c, c);
  c *= 1.0 + uCurvature * r2 * 2.0;
  return c + 0.5;
}

vec3 grad(vec2 uv) {
  vec2 p = uv - 0.5;
  vec2 m = uPointer - 0.5;
  p -= m * uPointerReact * 0.15;
  float a = atan(p.y, p.x);
  float r = length(p) * 2.0;
  float w = sin(a * 3.0 + uTime * uWaveFreq * 6.2831) * uWaveAmp;
  float rr = r + w * (0.4 + 0.6 * uIntensity);
  vec2 q = vec2(cos(a), sin(a)) * rr + 0.5;
  float band = q.y * 1.4 - uTime * 0.06;
  float s1 = smoothstep(0.0, 1.0, fract(band));
  float s2 = smoothstep(0.2, 1.0, fract(band * 0.5 + 0.25));
  vec3 col = mix(uColorA, uColorB, s1);
  col = mix(col, uColorA * 0.6 + uColorB * 0.4, s2 * 0.4);
  float rings = sin(rr * 10.0 - uTime * 2.0);
  col += uColorB * rings * 0.08 * uIntensity;
  return col;
}

void main() {
  vec2 uv = vUv;
  if (uPixelation > 0.001) {
    float px = mix(1.0, 220.0, uPixelation);
    uv = floor(uv * px) / px;
  }
  vec2 cuv = curveUv(uv);
  vec3 col = vec3(0.0);
  if (uRgbShift > 0.0001) {
    float rs = uRgbShift * (0.5 + uIntensity * 0.5);
    col.r = grad(cuv + vec2(rs, 0.0)).r;
    col.g = grad(cuv).g;
    col.b = grad(cuv - vec2(rs, 0.0)).b;
  } else {
    col = grad(cuv);
  }
  float scan = sin(cuv.y * uScanlineFrequency * 900.0 + uTime * 6.0);
  float scanMask = mix(1.0, 0.72 + 0.28 * scan, uScanlineStrength * uIntensity);
  col *= scanMask;
  float n = hash(cuv * uResolution.xy + uTime * 60.0);
  col += (n - 0.5) * uNoise * uIntensity;
  col += grad(cuv) * uBloom * 0.35;
  vec2 e = cuv - 0.5;
  float vig = smoothstep(0.85, 0.25, dot(e, e) * 2.0);
  col *= mix(1.0, vig, uVignette * uIntensity);
  float pa = uPointerActive;
  if (pa > 0.001) {
    float md = distance(cuv, uPointer);
    col += uColorA * exp(-pow(md / 0.2, 2.0)) * 0.35 * pa;
  }
  col *= uBrightness;
  float edge = smoothstep(0.0, 0.02, cuv.x) * smoothstep(0.0, 0.02, cuv.y)
    * smoothstep(0.0, 0.02, 1.0 - cuv.x) * smoothstep(0.0, 0.02, 1.0 - cuv.y);
  col = mix(uBackground, col, edge);
  gl_FragColor = vec4(col, uAlpha);
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
      powerPreference: 'high-performance'
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
      uResolution: { value: [1, 1] },
      uTime: { value: 0 },
      uPointer: { value: [0.5, 0.5] },
      uPointerTarget: { value: [0.5, 0.5] },
      uPointerActive: { value: 0 },
      uIntensity: { value: props.intensity },
      uCurvature: { value: props.curvature },
      uScanlineStrength: { value: props.scanlineStrength },
      uScanlineFrequency: { value: props.scanlineFrequency },
      uWaveAmp: { value: props.waveAmp },
      uWaveFreq: { value: props.waveFreq },
      uBloom: { value: props.bloom },
      uNoise: { value: props.noise },
      uVignette: { value: props.vignette },
      uBrightness: { value: props.brightness },
      uPixelation: { value: props.pixelation },
      uRgbShift: { value: props.rgbShift },
      uPointerReact: { value: props.pointerReact },
      uColorA: { value: hexToRgb(props.colorA) },
      uColorB: { value: hexToRgb(props.colorB) },
      uBackground: { value: hexToRgb(props.backgroundColor) },
      uAlpha: { value: props.alpha }
    }
  })
  const mesh = new Mesh(gl, { geometry, program })

  let raf = 0
  let running = true
  let visible = true
  let hasInteracted = false
  const start = performance.now()

  const setSize = () => {
    const w = container.clientWidth || 1
    const h = container.clientHeight || 1
    renderer!.setSize(w, h)
    program.uniforms.uResolution.value = [gl.canvas.width, gl.canvas.height]
  }
  setSize()
  const resizeObserver = new ResizeObserver(setSize)
  resizeObserver.observe(container)

  const intersectionObserver = new IntersectionObserver(
    entries => {
      visible = entries[0]?.isIntersecting ?? true
    },
    { threshold: 0 }
  )
  intersectionObserver.observe(container)

  const onPointer = (e: PointerEvent) => {
    if (!hasInteracted) {
      hasInteracted = true
      canvas.classList.add('has-interacted')
    }
    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left) / Math.max(rect.width, 1)
    const y = (e.clientY - rect.top) / Math.max(rect.height, 1)
    program.uniforms.uPointerTarget.value = [x, 1 - y]
    program.uniforms.uPointerActive.value = 1
  }
  const onLeave = () => {
    program.uniforms.uPointerActive.value = 0
  }
  window.addEventListener('pointermove', onPointer, { passive: true })
  window.addEventListener('pointerleave', onLeave)
  window.addEventListener('blur', onLeave)

  const animate = () => {
    if (!running) return
    raf = requestAnimationFrame(animate)
    if (!visible || document.hidden) return
    program.uniforms.uTime.value = (performance.now() - start) / 1000
    const p = program.uniforms.uPointer.value as [number, number]
    const t = program.uniforms.uPointerTarget.value as [number, number]
    p[0] += (t[0] - p[0]) * 0.08
    p[1] += (t[1] - p[1]) * 0.08
    try {
      renderer!.render({ scene: mesh })
    } catch (error) {
      running = false
      props.onError?.(error instanceof Error ? error : new Error(String(error)))
      return
    }
  }
  raf = requestAnimationFrame(animate)

  cleanup = () => {
    running = false
    if (raf) cancelAnimationFrame(raf)
    resizeObserver.disconnect()
    intersectionObserver.disconnect()
    window.removeEventListener('pointermove', onPointer)
    window.removeEventListener('pointerleave', onLeave)
    window.removeEventListener('blur', onLeave)
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
.crt-warp-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.crt-warp-canvas {
  display: block;
  width: 100%;
  height: 100%;
  touch-action: none;
}
</style>
