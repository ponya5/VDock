<template>
  <canvas ref="canvasRef" class="silk-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  speed?: number
  scale?: number
  color?: string
  noiseIntensity?: number
  rotation?: number
}

const props = withDefaults(defineProps<Props>(), {
  speed: 5,
  scale: 1,
  color: '#7B7481',
  noiseIntensity: 1.5,
  rotation: 0,
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

const FRAG_SRC = `
precision mediump float;

uniform float uTime;
uniform vec3  uColor;
uniform float uSpeed;
uniform float uScale;
uniform float uRotation;
uniform float uNoiseIntensity;

varying vec2 vUv;

const float e = 2.71828182845904523536;

float noise(vec2 texCoord) {
  float G = e;
  vec2  r = (G * sin(G * texCoord));
  return fract(r.x * r.y * (1.0 + texCoord.x));
}

vec2 rotateUvs(vec2 uv, float angle) {
  float c = cos(angle);
  float s = sin(angle);
  mat2  rot = mat2(c, -s, s, c);
  return rot * uv;
}

void main() {
  float rnd     = noise(gl_FragCoord.xy);
  vec2  uv      = rotateUvs(vUv * uScale, uRotation);
  vec2  tex     = uv * uScale;
  float tOffset = uSpeed * uTime;

  tex.y += 0.03 * sin(8.0 * tex.x - tOffset);

  float pattern = 0.6 +
    0.4 * sin(5.0 * (tex.x + tex.y +
      cos(3.0 * tex.x + 5.0 * tex.y) +
      0.02 * tOffset) +
      sin(20.0 * (tex.x + tex.y - 0.1 * tOffset)));

  vec4 col = vec4(uColor, 1.0) * vec4(pattern) - rnd / 15.0 * uNoiseIntensity;
  col.a = 1.0;
  gl_FragColor = col;
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
    console.warn('Silk shader error:', gl.getShaderInfoLog(s))
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

  const gl = canvas.getContext('webgl', { alpha: false })
  if (!gl) { console.warn('WebGL unavailable — Silk background disabled'); return }

  const vert = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER)
  const frag = compileShader(gl, FRAG_SRC, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert)
  gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('Silk link error:', gl.getProgramInfoLog(prog))
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

  const uTime  = gl.getUniformLocation(prog, 'uTime')
  const uColor = gl.getUniformLocation(prog, 'uColor')
  const uSpeed = gl.getUniformLocation(prog, 'uSpeed')
  const uScale = gl.getUniformLocation(prog, 'uScale')
  const uRot   = gl.getUniformLocation(prog, 'uRotation')
  const uNoise = gl.getUniformLocation(prog, 'uNoiseIntensity')

  const start = performance.now()

  const render = () => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resize()
    gl.viewport(0, 0, canvas.width, canvas.height)

    const [r, g, b] = hexToRgb(props.color)
    gl.uniform1f(uTime,  (performance.now() - start) / 1000 * 0.1)
    gl.uniform3f(uColor, r, g, b)
    gl.uniform1f(uSpeed, props.speed)
    gl.uniform1f(uScale, props.scale)
    gl.uniform1f(uRot,   props.rotation)
    gl.uniform1f(uNoise, props.noiseIntensity)

    gl.drawArrays(gl.TRIANGLES, 0, 6)
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
.silk-container {
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
