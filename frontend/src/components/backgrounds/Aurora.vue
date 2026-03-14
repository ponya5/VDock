<template>
  <canvas ref="canvasRef" class="aurora-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  colorStops?: [string, string, string]
  blend?: number
  amplitude?: number
  speed?: number
}

const props = withDefaults(defineProps<Props>(), {
  colorStops: () => ['#7cff67', '#B19EEF', '#5227FF'],
  blend: 0.5,
  amplitude: 1.0,
  speed: 1,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

// WebGL 1 port — no #version 300 es, no 'out', use gl_FragColor
const VERT_SRC = `
attribute vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`

const FRAG_SRC = `
precision highp float;

uniform float uTime;
uniform float uAmplitude;
uniform vec3  uColorStops[3];
uniform vec2  uResolution;
uniform float uBlend;

vec3 permute(vec3 x) {
  return mod(((x * 34.0) + 1.0) * x, 289.0);
}

float snoise(vec2 v) {
  const vec4 C = vec4(
     0.211324865405187,  0.366025403784439,
    -0.577350269189626,  0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                         + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0),
                           dot(x12.xy, x12.xy),
                           dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

vec3 colorRamp(vec3 c0, vec3 c1, vec3 c2, float t) {
  if (t < 0.5) {
    return mix(c0, c1, t * 2.0);
  } else {
    return mix(c1, c2, (t - 0.5) * 2.0);
  }
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;

  vec3 rampColor = colorRamp(uColorStops[0], uColorStops[1], uColorStops[2], uv.x);

  float height = snoise(vec2(uv.x * 2.0 + uTime * 0.1, uTime * 0.25)) * 0.5 * uAmplitude;
  height = exp(height);
  height = (uv.y * 2.0 - height + 0.2);

  float intensity  = 0.6 * height;
  float midPoint   = 0.20;
  float auroraAlpha = smoothstep(midPoint - uBlend * 0.5, midPoint + uBlend * 0.5, intensity);

  vec3 auroraColor = intensity * rampColor;
  gl_FragColor = vec4(auroraColor * auroraAlpha, auroraAlpha);
}
`

function hexToRgb(hex: string): [number, number, number] {
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
    console.warn('Aurora shader error:', gl.getShaderInfoLog(s))
    gl.deleteShader(s)
    return null
  }
  return s
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const resize = () => {
    canvas.width  = canvas.clientWidth
    canvas.height = canvas.clientHeight
  }
  resize()
  window.addEventListener('resize', resize, { passive: true })

  const gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: true })
  if (!gl) { console.warn('WebGL unavailable — Aurora background disabled'); return }

  gl.enable(gl.BLEND)
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)

  const vert = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER)
  const frag = compileShader(gl, FRAG_SRC, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert)
  gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('Aurora link error:', gl.getProgramInfoLog(prog))
    return
  }
  gl.useProgram(prog)

  // Full-screen triangle (more efficient than quad)
  const verts = new Float32Array([-1, -1,  3, -1,  -1, 3])
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
  const aPos = gl.getAttribLocation(prog, 'position')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  const uTime       = gl.getUniformLocation(prog, 'uTime')
  const uAmplitude  = gl.getUniformLocation(prog, 'uAmplitude')
  const uColorStops = gl.getUniformLocation(prog, 'uColorStops')
  const uResolution = gl.getUniformLocation(prog, 'uResolution')
  const uBlend      = gl.getUniformLocation(prog, 'uBlend')

  const start = performance.now()

  const render = () => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resize()
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.clearColor(0, 0, 0, 0)
    gl.clear(gl.COLOR_BUFFER_BIT)

    const t = (performance.now() - start) / 1000 * props.speed * 0.1
    const stops = props.colorStops.flatMap(h => hexToRgb(h))

    gl.uniform1f(uTime,      t)
    gl.uniform1f(uAmplitude, props.amplitude)
    gl.uniform3fv(uColorStops, stops)
    gl.uniform2f(uResolution, canvas.width, canvas.height)
    gl.uniform1f(uBlend,     props.blend)

    gl.drawArrays(gl.TRIANGLES, 0, 3)
    rafId = requestAnimationFrame(render)
  }

  const onVis = () => { if (!document.hidden && rafId === 0) render() }
  document.addEventListener('visibilitychange', onVis)
  render()

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
.aurora-container {
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
