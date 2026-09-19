<template>
  <div ref="containerRef" class="gradient-waves-container" :data-ready="ready || undefined">
    <canvas ref="canvasRef" class="gradient-waves-canvas" />
  </div>
</template>

<script setup lang="ts">
// Ported from reactbits.dev GradientWaves (ogl/WebGL).
import { onMounted, onUnmounted, ref } from 'vue'
import { Mesh, Program, Renderer, Triangle } from 'ogl'

const props = withDefaults(
  defineProps<{
    speed?: number
    amplitude?: number
    smoothness?: number
    wireframe?: boolean
    waveColor?: string
    crestColor?: string
    noiseScale?: number
    noiseAmp?: number
    turbulence?: number
    tilt?: number
    zoom?: number
    detail?: number
    focusNear?: number
    focusFar?: number
    fogNear?: number
    fogFar?: number
    brightness?: number
    opacity?: number
    grain?: number
    horizonColor?: string
    backgroundColor?: string
    mouseStrength?: number
    mouseSize?: number
    parallax?: number
    onError?: (error: Error) => void
  }>(),
  {
    speed: 0.75,
    amplitude: 26,
    smoothness: 0.5,
    wireframe: false,
    waveColor: '#006aff',
    crestColor: '#00ffe1',
    noiseScale: 1.3,
    noiseAmp: 0.45,
    turbulence: 0.75,
    tilt: -4,
    zoom: 1.18,
    detail: 3,
    focusNear: 7.5,
    focusFar: 12,
    fogNear: 10,
    fogFar: 21,
    brightness: 0.9,
    opacity: 0.85,
    grain: 0.02,
    horizonColor: '#02060f',
    backgroundColor: '#000000',
    mouseStrength: 1.5,
    mouseSize: 1.25,
    parallax: 0.3,
    onError: undefined
  }
)

const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const ready = ref(false)

const vertex = `#version 300 es
in vec2 position;
in vec2 uv;
out vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`

// GLSL 300 es: fwidth() (used by the wireframe overlay) has no extension path
// in WebGL2 ES-1.00 shaders, so the shaders run as ES 3.00 where it is core.
const fragment = `#version 300 es
precision highp float;
out vec4 fragColor;
uniform vec2 uResolution;
uniform float uTime;
uniform float uSpeed;
uniform float uAmplitude;
uniform float uSmoothness;
uniform int uWireframe;
uniform vec3 uWaveColor;
uniform vec3 uCrestColor;
uniform float uNoiseScale;
uniform float uNoiseAmp;
uniform float uTurbulence;
uniform float uTilt;
uniform float uZoom;
uniform int uDetail;
uniform float uFocusNear;
uniform float uFocusFar;
uniform float uFogNear;
uniform float uFogFar;
uniform float uBrightness;
uniform float uOpacity;
uniform float uGrain;
uniform vec3 uHorizonColor;
uniform vec3 uBackgroundColor;
uniform vec2 uMouse;
uniform vec2 uMouseVel;
uniform float uMouseStrength;
uniform float uMouseSize;
uniform float uParallax;
in vec2 vUv;

#define MAX_STEPS 44
#define SURFACE_EPS 0.006
#define FAR_PLANE 60.0

float hash21(vec2 p) {
  p = fract(p * vec2(234.34, 435.345));
  p += dot(p, p + 34.23);
  return fract(p.x * p.y);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.55;
  for (int i = 0; i < 4; i++) {
    if (i >= uDetail) break;
    v += a * noise(p);
    p = p * 2.07 + vec2(13.7, 9.2);
    a *= 0.5;
  }
  return v;
}

vec2 swirl(vec2 p, float amt) {
  float r = length(p);
  float a = atan(p.y, p.x) + amt * exp(-r * 0.4);
  return vec2(cos(a), sin(a)) * r;
}

float seaHeight(vec2 p, float t) {
  vec2 q = p * uNoiseScale;
  q += vec2(t * 0.12, -t * 0.08);
  q += (uMouseVel * 0.6 + (uMouse - 0.5) * uParallax) * 0.35;
  q = swirl(q, uTurbulence * 0.12 * sin(t * 0.25));
  float h = fbm(q + vec2(t * 0.55, -t * 0.35));
  float chop = noise(p * 4.2 + vec2(t * 1.6, t * 0.9));
  float amp = uAmplitude * (0.55 + 0.45 * uNoiseAmp * chop);
  return h * amp * 0.12;
}

vec3 calcNormal(vec2 p, float t, float eps) {
  float hC = seaHeight(p, t);
  float hX = seaHeight(p + vec2(eps, 0.0), t);
  float hY = seaHeight(p + vec2(0.0, eps), t);
  return normalize(vec3(hC - hX, eps, hC - hY));
}

float mapScene(vec3 pos, float t) {
  return pos.y - seaHeight(pos.xz, t);
}

float rayMarch(vec3 ro, vec3 rd, float t) {
  float dist = 0.0;
  for (int i = 0; i < MAX_STEPS; i++) {
    vec3 pos = ro + rd * dist;
    float h = mapScene(pos, t);
    if (abs(h) < SURFACE_EPS || dist > FAR_PLANE) break;
    dist += h * uSmoothness;
  }
  return dist;
}

vec3 skyGradient(vec3 rd) {
  float v = pow(max(rd.y, 0.0), 0.8);
  vec3 sky = mix(uHorizonColor, uWaveColor, v);
  float glow = pow(max(dot(rd, normalize(vec3(0.2, 0.5, -1.0))), 0.0), 6.0);
  return sky + uCrestColor * glow * 0.35;
}

vec3 applyFog(vec3 col, float dist, vec3 rd) {
  float fogAmt = smoothstep(uFogNear, uFogFar, dist);
  vec3 fogCol = mix(uHorizonColor, uWaveColor, clamp(rd.y * 0.5 + 0.5, 0.0, 1.0));
  return mix(col, fogCol, fogAmt);
}

vec3 shadeSea(vec3 pos, vec3 n, vec3 rd, float t, float dist) {
  float fres = pow(1.0 - max(dot(n, -rd), 0.0), 5.0);
  vec3 refl = skyGradient(reflect(rd, n));
  vec3 base = mix(uWaveColor * 0.5, uWaveColor, clamp(pos.y * 0.2 + 0.5, 0.0, 1.0));
  vec3 col = mix(base, refl, 0.2 + fres * 0.7);
  float foam = smoothstep(0.62, 0.78, fbm(pos.xz * 1.4 + vec2(t * 0.4)));
  float crest = smoothstep(0.015, 0.08, pos.y);
  col = mix(col, uCrestColor, max(foam * 0.65, crest * 0.35));
  return applyFog(col, dist, rd);
}

vec3 shadeSeaWire(vec3 pos, vec3 n, vec3 rd, float t, float dist) {
  vec3 base = mix(uWaveColor * 0.6, uWaveColor * 1.15, clamp(pos.y * 1.1, 0.0, 1.0));
  float crest = smoothstep(0.015, 0.1, pos.y);
  vec3 col = mix(base, uCrestColor, crest * 0.85);
  return applyFog(col, dist, rd);
}

vec3 addWireOverlay(vec3 col, vec3 pos) {
  vec2 g = abs(fract(pos.xz * 0.8) - 0.5) / fwidth(pos.xz * 0.8);
  float line = 1.0 - min(min(g.x, g.y), 1.0);
  float fade = exp(-length(pos) * 0.03);
  return col + vec3(line) * uCrestColor * fade * 0.5;
}

float gridMask(vec2 p) {
  vec2 g = abs(fract(p) - 0.5);
  return smoothstep(0.48, 0.5, max(g.x, g.y));
}

float vignette(vec2 uv) {
  vec2 q = uv * (1.0 - uv);
  return pow(q.x * q.y * 18.0, 0.32);
}

void main() {
  vec2 uv = vUv;
  vec2 ndc = uv * 2.0 - 1.0;
  vec2 m = uMouse - 0.5;

  float t = uTime * uSpeed;
  float aspect = uResolution.x / max(uResolution.y, 1.0);
  vec3 ro = vec3(0.0, 4.1, 11.0);
  ro.xz += m * uParallax * vec2(aspect, 1.0);
  vec3 ta = vec3(0.0, 0.0, 0.0);

  vec3 fw = normalize(ta - ro);
  vec3 rt = normalize(cross(fw, vec3(0.0, 1.0, 0.0)));
  vec3 up = cross(rt, fw);
  vec3 rd = normalize(fw * uZoom + rt * ndc.x * aspect + up * (ndc.y + uTilt * 0.1));

  float dist = rayMarch(ro, rd, t);
  vec3 col;
  if (dist < FAR_PLANE) {
    vec3 pos = ro + rd * dist;
    float eps = 0.02 + dist * 0.006;
    vec3 n = calcNormal(pos.xz, t, eps);
    col = (uWireframe == 1) ? shadeSeaWire(pos, n, rd, t, dist) : shadeSea(pos, n, rd, t, dist);
    if (uWireframe == 1) col = addWireOverlay(col, pos);
  } else {
    col = (uWireframe == 1) ? uBackgroundColor : skyGradient(rd);
  }

  float depthBlur = smoothstep(uFocusFar, uFocusNear, dist);
  col = mix(col, col * (0.85 + 0.15 * depthBlur), 0.35);

  float d = distance(uv, uMouse);
  float radius = uMouseSize * 0.22;
  float strength = exp(-pow(d / max(radius, 0.0001), 2.0));
  float rip = sin(d * 40.0 - t * 2.0) * 0.5 + 0.5;
  col += uCrestColor * strength * rip * uMouseStrength * 0.18;

  col *= uBrightness;
  float vig = vignette(uv);
  col *= vig;
  col += (hash21(uv * uResolution.xy + uTime) - 0.5) * uGrain;
  col = clamp(col, 0.0, 1.0);
  fragColor = vec4(col, uOpacity);
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
      uResolution: { value: [1, 1] },
      uTime: { value: 0 },
      uSpeed: { value: props.speed },
      uAmplitude: { value: props.amplitude },
      uSmoothness: { value: props.smoothness },
      uWireframe: { value: props.wireframe ? 1 : 0 },
      uWaveColor: { value: hexToRgb(props.waveColor) },
      uCrestColor: { value: hexToRgb(props.crestColor) },
      uNoiseScale: { value: props.noiseScale },
      uNoiseAmp: { value: props.noiseAmp },
      uTurbulence: { value: props.turbulence },
      uTilt: { value: props.tilt },
      uZoom: { value: props.zoom },
      uDetail: { value: props.detail },
      uFocusNear: { value: props.focusNear },
      uFocusFar: { value: props.focusFar },
      uFogNear: { value: props.fogNear },
      uFogFar: { value: props.fogFar },
      uBrightness: { value: props.brightness },
      uOpacity: { value: props.opacity },
      uGrain: { value: props.grain },
      uHorizonColor: { value: hexToRgb(props.horizonColor) },
      uBackgroundColor: { value: hexToRgb(props.backgroundColor) },
      uMouse: { value: [0.5, 0.5] },
      uMouseVel: { value: [0, 0] },
      uMouseStrength: { value: props.mouseStrength },
      uMouseSize: { value: props.mouseSize },
      uParallax: { value: props.parallax }
    }
  })
  const mesh = new Mesh(gl, { geometry, program })

  let frame = 0
  let running = true
  let visible = true
  let lastTime = performance.now()
  let elapsed = 0
  const targetMouse = { x: 0.5, y: 0.5 }
  const currentMouse = { x: 0.5, y: 0.5 }

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
    currentMouse.x += (targetMouse.x - currentMouse.x) * 0.12
    currentMouse.y += (targetMouse.y - currentMouse.y) * 0.12
    program.uniforms.uMouse.value = [currentMouse.x, currentMouse.y]
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
    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    targetMouse.x = Math.min(Math.max(x, 0), 1)
    targetMouse.y = Math.min(Math.max(1 - y, 0), 1)
    const vel = program.uniforms.uMouseVel.value as [number, number]
    vel[0] = Math.min(Math.max(vel[0] + event.movementX * 0.004, -0.6), 0.6)
    vel[1] = Math.min(Math.max(vel[1] + event.movementY * 0.004, -0.6), 0.6)
    canvas.style.setProperty('--gradient-waves-mx', `${event.clientX - rect.left}px`)
    canvas.style.setProperty('--gradient-waves-my', `${event.clientY - rect.top}px`)
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
.gradient-waves-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.gradient-waves-canvas {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0;
  transition: opacity 400ms ease;
}

.gradient-waves-container[data-ready='true'] .gradient-waves-canvas {
  opacity: v-bind('props.opacity');
}
</style>
