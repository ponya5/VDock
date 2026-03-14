<template>
  <canvas ref="canvasRef" class="light-pillar-container" :style="{ mixBlendMode }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  topColor?: string
  bottomColor?: string
  intensity?: number
  rotationSpeed?: number
  glowAmount?: number
  pillarWidth?: number
  pillarHeight?: number
  noiseIntensity?: number
  pillarRotation?: number
  mixBlendMode?: string
  quality?: 'low' | 'medium' | 'high'
}

const props = withDefaults(defineProps<Props>(), {
  topColor: '#5227FF',
  bottomColor: '#FF9FFC',
  intensity: 1,
  rotationSpeed: 0.3,
  glowAmount: 0.002,
  pillarWidth: 3,
  pillarHeight: 0.4,
  noiseIntensity: 0.5,
  pillarRotation: 25,
  mixBlendMode: 'screen',
  quality: 'high',
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

const VERT_SRC = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = aPosition * 0.5 + 0.5;
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`

// Quality-dependent constants injected at runtime
function buildFragSrc(quality: 'low' | 'medium' | 'high'): string {
  const settings = {
    low:    { iterations: 24, waveIterations: 1, stepMult: '1.5', precision: 'mediump' },
    medium: { iterations: 40, waveIterations: 2, stepMult: '1.2', precision: 'mediump' },
    high:   { iterations: 80, waveIterations: 4, stepMult: '1.0', precision: 'highp'  },
  }[quality]

  return `
precision ${settings.precision} float;

uniform vec2  uResolution;
uniform float uTime;
uniform vec3  uTopColor;
uniform vec3  uBottomColor;
uniform float uIntensity;
uniform float uGlowAmount;
uniform float uPillarWidth;
uniform float uPillarHeight;
uniform float uNoiseIntensity;
uniform float uRotCos;
uniform float uRotSin;
uniform float uPillarRotCos;
uniform float uPillarRotSin;
uniform float uWaveSin;
uniform float uWaveCos;

varying vec2 vUv;

const float STEP_MULT = ${settings.stepMult};
const int   MAX_ITER  = ${settings.iterations};
const int   WAVE_ITER = ${settings.waveIterations};

void main() {
  vec2 uv = (vUv * 2.0 - 1.0) * vec2(uResolution.x / uResolution.y, 1.0);
  // pillar rotation
  uv = vec2(uPillarRotCos * uv.x - uPillarRotSin * uv.y,
            uPillarRotSin * uv.x + uPillarRotCos * uv.y);

  vec3 ro = vec3(0.0, 0.0, -10.0);
  vec3 rd = normalize(vec3(uv, 1.0));

  float rotC = uRotCos;
  float rotS = uRotSin;

  vec3 col = vec3(0.0);
  float t = 0.1;

  for (int i = 0; i < MAX_ITER; i++) {
    vec3 p = ro + rd * t;
    // scene rotation
    p.xz = vec2(rotC * p.x - rotS * p.z, rotS * p.x + rotC * p.z);

    vec3 q = p;
    q.y = p.y * uPillarHeight + uTime;

    float freq = 1.0;
    float amp  = 1.0;
    for (int j = 0; j < WAVE_ITER; j++) {
      q.xz = vec2(uWaveCos * q.x - uWaveSin * q.z,
                  uWaveSin * q.x + uWaveCos * q.z);
      q += cos(q.zxy * freq - uTime * float(j) * 2.0) * amp;
      freq *= 2.0;
      amp  *= 0.5;
    }

    float d     = length(cos(q.xz)) - 0.2;
    float bound = length(p.xz) - uPillarWidth;
    float k     = 4.0;
    float h     = max(k - abs(d - bound), 0.0);
    d = max(d, bound) + h * h * 0.0625 / k;
    d = abs(d) * 0.15 + 0.01;

    float grad = clamp((15.0 - p.y) / 30.0, 0.0, 1.0);
    col += mix(uBottomColor, uTopColor, grad) / d;

    t += d * STEP_MULT;
    if (t > 50.0) break;
  }

  float widthNorm = uPillarWidth / 3.0;
  col = tanh(col * uGlowAmount / widthNorm);

  // dither noise
  float noise = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);
  col -= (noise - 0.5) / 15.0 * uNoiseIntensity;

  gl_FragColor = vec4(col * uIntensity, 1.0);
}
`
}

function hexToVec3(hex: string): [number, number, number] {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  return [r, g, b]
}

function compileShader(gl: WebGLRenderingContext, src: string, type: number): WebGLShader | null {
  const s = gl.createShader(type)
  if (!s) return null
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.warn('LightPillar shader error:', gl.getShaderInfoLog(s))
    gl.deleteShader(s)
    return null
  }
  return s
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isLowEnd  = isMobile || (navigator.hardwareConcurrency != null && navigator.hardwareConcurrency <= 4)
  let effectiveQuality = props.quality
  if (isLowEnd && effectiveQuality === 'high') effectiveQuality = 'medium'
  if (isMobile && effectiveQuality !== 'low')  effectiveQuality = 'low'

  const pixelRatio = effectiveQuality === 'high' ? Math.min(window.devicePixelRatio, 2) : effectiveQuality === 'medium' ? 0.65 : 0.5
  const targetFPS  = effectiveQuality === 'low' ? 30 : 60
  const frameTime  = 1000 / targetFPS

  const resize = () => {
    canvas.width  = canvas.clientWidth  * pixelRatio
    canvas.height = canvas.clientHeight * pixelRatio
  }
  resize()
  window.addEventListener('resize', resize, { passive: true })

  const gl = canvas.getContext('webgl', { premultipliedAlpha: false, alpha: false })
  if (!gl) { console.warn('WebGL unavailable — LightPillar background disabled'); return }

  const vert = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER)
  const frag = compileShader(gl, buildFragSrc(effectiveQuality), gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert)
  gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('LightPillar link error:', gl.getProgramInfoLog(prog))
    return
  }
  gl.useProgram(prog)

  const verts = new Float32Array([-1, -1,  1, -1,  -1, 1,  -1, 1,  1, -1,  1, 1])
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
  const aPos = gl.getAttribLocation(prog, 'aPosition')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  const uRes      = gl.getUniformLocation(prog, 'uResolution')
  const uTime     = gl.getUniformLocation(prog, 'uTime')
  const uTop      = gl.getUniformLocation(prog, 'uTopColor')
  const uBot      = gl.getUniformLocation(prog, 'uBottomColor')
  const uInt      = gl.getUniformLocation(prog, 'uIntensity')
  const uGlow     = gl.getUniformLocation(prog, 'uGlowAmount')
  const uPW       = gl.getUniformLocation(prog, 'uPillarWidth')
  const uPH       = gl.getUniformLocation(prog, 'uPillarHeight')
  const uNoise    = gl.getUniformLocation(prog, 'uNoiseIntensity')
  const uRotCos   = gl.getUniformLocation(prog, 'uRotCos')
  const uRotSin   = gl.getUniformLocation(prog, 'uRotSin')
  const uPRotCos  = gl.getUniformLocation(prog, 'uPillarRotCos')
  const uPRotSin  = gl.getUniformLocation(prog, 'uPillarRotSin')
  const uWaveSin  = gl.getUniformLocation(prog, 'uWaveSin')
  const uWaveCos  = gl.getUniformLocation(prog, 'uWaveCos')

  // Pre-compute static uniforms
  const pillarRotRad = (props.pillarRotation * Math.PI) / 180
  const waveSin = Math.sin(0.4)
  const waveCos = Math.cos(0.4)

  const start = performance.now()
  let lastTime = start
  let timeAcc = 0

  const render = (now: number) => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }

    const delta = now - lastTime
    if (delta >= frameTime) {
      lastTime = now - (delta % frameTime)
      timeAcc += 0.016 * props.rotationSpeed

      resize()
      gl.viewport(0, 0, canvas.width, canvas.height)
      gl.clearColor(0, 0, 0, 1)
      gl.clear(gl.COLOR_BUFFER_BIT)

      const [tr, tg, tb] = hexToVec3(props.topColor)
      const [br, bg, bb] = hexToVec3(props.bottomColor)

      gl.uniform2f(uRes, canvas.width, canvas.height)
      gl.uniform1f(uTime, timeAcc)
      gl.uniform3f(uTop, tr, tg, tb)
      gl.uniform3f(uBot, br, bg, bb)
      gl.uniform1f(uInt, props.intensity)
      gl.uniform1f(uGlow, props.glowAmount)
      gl.uniform1f(uPW, props.pillarWidth)
      gl.uniform1f(uPH, props.pillarHeight)
      gl.uniform1f(uNoise, props.noiseIntensity)
      gl.uniform1f(uRotCos, Math.cos(timeAcc * 0.3))
      gl.uniform1f(uRotSin, Math.sin(timeAcc * 0.3))
      gl.uniform1f(uPRotCos, Math.cos(pillarRotRad))
      gl.uniform1f(uPRotSin, Math.sin(pillarRotRad))
      gl.uniform1f(uWaveSin, waveSin)
      gl.uniform1f(uWaveCos, waveCos)

      gl.drawArrays(gl.TRIANGLES, 0, 6)
    }

    rafId = requestAnimationFrame(render)
  }

  const onVis = () => { if (!document.hidden && rafId === 0) render(performance.now()) }
  document.addEventListener('visibilitychange', onVis)
  rafId = requestAnimationFrame(render)

  cleanup = () => {
    cancelAnimationFrame(rafId)
    rafId = 0
    window.removeEventListener('resize', resize)
    document.removeEventListener('visibilitychange', onVis)
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.light-pillar-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
  display: block;
}
</style>
