<template>
  <canvas ref="canvasRef" class="iridescence-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  color?: [number, number, number]
  mouseReact?: boolean
  amplitude?: number
  speed?: number
}

const props = withDefaults(defineProps<Props>(), {
  color: () => [0.5, 0.6, 0.8],
  mouseReact: true,
  amplitude: 0.1,
  speed: 1,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

// Matches the original OGL fragment shader exactly
const VERT = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`

const FRAG = `
precision highp float;
uniform float uTime;
uniform vec3 uColor;
uniform vec3 uResolution;
uniform vec2 uMouse;
uniform float uAmplitude;
uniform float uSpeed;
varying vec2 vUv;

void main() {
  float mr = min(uResolution.x, uResolution.y);
  vec2 uv = (vUv.xy * 2.0 - 1.0) * uResolution.xy / mr;
  uv += (uMouse - vec2(0.5)) * uAmplitude;
  float d = -uTime * 0.5 * uSpeed;
  float a = 0.0;
  for (float i = 0.0; i < 8.0; ++i) {
    a += cos(i - d - a * uv.x);
    d += sin(uv.y * i + a);
  }
  d += uTime * 0.5 * uSpeed;
  vec3 col = vec3(cos(uv * vec2(d, a)) * 0.6 + 0.4, cos(a + d) * 0.5 + 0.5);
  col = cos(col * cos(vec3(d, a, 2.5)) * 0.5 + 0.5) * uColor;
  gl_FragColor = vec4(col, 1.0);
}
`

function compile(gl: WebGLRenderingContext, src: string, type: number) {
  const s = gl.createShader(type)!
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.warn('Iridescence shader:', gl.getShaderInfoLog(s))
    return null
  }
  return s
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const mouse = { x: 0.5, y: 0.5 }

  const resize = () => { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight }
  resize()
  window.addEventListener('resize', resize, { passive: true })

  const gl = canvas.getContext('webgl')
  if (!gl) { console.warn('WebGL unavailable — Iridescence disabled'); return }

  const vert = compile(gl, VERT, gl.VERTEX_SHADER)
  const frag = compile(gl, FRAG, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert); gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.warn('Iridescence link:', gl.getProgramInfoLog(prog)); return }
  gl.useProgram(prog)

  // Full-screen triangle (OGL Triangle equivalent): 3 verts covering clip space
  // position + uv interleaved: x, y, u, v
  const verts = new Float32Array([
    -1, -1,  0, 0,
     3, -1,  2, 0,
    -1,  3,  0, 2,
  ])
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)

  const stride = 4 * 4 // 4 floats * 4 bytes
  const aPos = gl.getAttribLocation(prog, 'position')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, stride, 0)

  const aUv = gl.getAttribLocation(prog, 'uv')
  gl.enableVertexAttribArray(aUv)
  gl.vertexAttribPointer(aUv, 2, gl.FLOAT, false, stride, 2 * 4)

  const uTime  = gl.getUniformLocation(prog, 'uTime')
  const uColor = gl.getUniformLocation(prog, 'uColor')
  const uRes   = gl.getUniformLocation(prog, 'uResolution')
  const uMouse = gl.getUniformLocation(prog, 'uMouse')
  const uAmp   = gl.getUniformLocation(prog, 'uAmplitude')
  const uSpd   = gl.getUniformLocation(prog, 'uSpeed')

  const onMove = (e: MouseEvent) => {
    if (!props.mouseReact) return
    const rect = canvas.getBoundingClientRect()
    mouse.x = (e.clientX - rect.left) / rect.width
    mouse.y = 1.0 - (e.clientY - rect.top) / rect.height
  }
  if (props.mouseReact) canvas.addEventListener('mousemove', onMove, { passive: true })

  const render = (ts: number) => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resize()
    gl.viewport(0, 0, canvas.width, canvas.height)

    const [cr, cg, cb] = props.color
    gl.uniform1f(uTime, ts * 0.001)
    gl.uniform3f(uColor, cr, cg, cb)
    gl.uniform3f(uRes, canvas.width, canvas.height, canvas.width / canvas.height)
    gl.uniform2f(uMouse, mouse.x, mouse.y)
    gl.uniform1f(uAmp, props.amplitude)
    gl.uniform1f(uSpd, props.speed)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
    rafId = requestAnimationFrame(render)
  }

  const onVis = () => { if (!document.hidden && rafId === 0) requestAnimationFrame(render) }
  document.addEventListener('visibilitychange', onVis)
  rafId = requestAnimationFrame(render)

  cleanup = () => {
    cancelAnimationFrame(rafId); rafId = 0
    window.removeEventListener('resize', resize)
    canvas.removeEventListener('mousemove', onMove)
    document.removeEventListener('visibilitychange', onVis)
    gl.getExtension('WEBGL_lose_context')?.loseContext()
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.iridescence-container {
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
