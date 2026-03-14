<template>
  <canvas ref="canvasRef" class="lightning-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watchEffect } from 'vue'

interface Props {
  hue?: number
  xOffset?: number
  speed?: number
  intensity?: number
  size?: number
}

const props = withDefaults(defineProps<Props>(), {
  hue: 260,
  xOffset: 0,
  speed: 1,
  intensity: 1,
  size: 1,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

const VERT_SRC = `
attribute vec2 aPosition;
void main() {
  gl_Position = vec4(aPosition, 0.0, 1.0);
}
`

const FRAG_SRC = `
precision mediump float;
uniform vec2 iResolution;
uniform float iTime;
uniform float uHue;
uniform float uXOffset;
uniform float uSpeed;
uniform float uIntensity;
uniform float uSize;

#define OCTAVE_COUNT 10

vec3 hsv2rgb(vec3 c) {
  vec3 rgb = clamp(abs(mod(c.x * 6.0 + vec3(0.0,4.0,2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return c.z * mix(vec3(1.0), rgb, c.y);
}

float hash11(float p) {
  p = fract(p * .1031);
  p *= p + 33.33;
  p *= p + p;
  return fract(p);
}

float hash12(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * .1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

mat2 rotate2d(float theta) {
  float c = cos(theta);
  float s = sin(theta);
  return mat2(c, -s, s, c);
}

float noise(vec2 p) {
  vec2 ip = floor(p);
  vec2 fp = fract(p);
  float a = hash12(ip);
  float b = hash12(ip + vec2(1.0, 0.0));
  float c = hash12(ip + vec2(0.0, 1.0));
  float d = hash12(ip + vec2(1.0, 1.0));
  vec2 t = smoothstep(0.0, 1.0, fp);
  return mix(mix(a, b, t.x), mix(c, d, t.x), t.y);
}

float fbm(vec2 p) {
  float value = 0.0;
  float amplitude = 0.5;
  for (int i = 0; i < OCTAVE_COUNT; ++i) {
    value += amplitude * noise(p);
    p *= rotate2d(0.45);
    p *= 2.0;
    amplitude *= 0.5;
  }
  return value;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 uv = fragCoord / iResolution.xy;
  uv = 2.0 * uv - 1.0;
  uv.x *= iResolution.x / iResolution.y;
  uv.x += uXOffset;
  uv += 2.0 * fbm(uv * uSize + 0.8 * iTime * uSpeed) - 1.0;
  float dist = abs(uv.x);
  vec3 baseColor = hsv2rgb(vec3(uHue / 360.0, 0.7, 0.8));
  vec3 col = baseColor * pow(mix(0.0, 0.07, hash11(iTime * uSpeed)) / dist, 1.0) * uIntensity;
  fragColor = vec4(col, 1.0);
}

void main() {
  mainImage(gl_FragColor, gl_FragCoord.xy);
}
`

function compileShader(gl: WebGLRenderingContext, source: string, type: number): WebGLShader | null {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.warn('Shader compile error:', gl.getShaderInfoLog(shader))
    gl.deleteShader(shader)
    return null
  }
  return shader
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const resizeCanvas = () => {
    canvas.width = canvas.clientWidth
    canvas.height = canvas.clientHeight
  }
  resizeCanvas()
  window.addEventListener('resize', resizeCanvas, { passive: true })

  const gl = canvas.getContext('webgl')
  if (!gl) {
    console.warn('WebGL not supported — Lightning background unavailable')
    return
  }

  const vert = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER)
  const frag = compileShader(gl, FRAG_SRC, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const program = gl.createProgram()!
  gl.attachShader(program, vert)
  gl.attachShader(program, frag)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.warn('Program link error:', gl.getProgramInfoLog(program))
    return
  }
  gl.useProgram(program)

  const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1])
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW)

  const aPos = gl.getAttribLocation(program, 'aPosition')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0)

  const uRes       = gl.getUniformLocation(program, 'iResolution')
  const uTime      = gl.getUniformLocation(program, 'iTime')
  const uHueLoc    = gl.getUniformLocation(program, 'uHue')
  const uXOff      = gl.getUniformLocation(program, 'uXOffset')
  const uSpeedLoc  = gl.getUniformLocation(program, 'uSpeed')
  const uIntLoc    = gl.getUniformLocation(program, 'uIntensity')
  const uSizeLoc   = gl.getUniformLocation(program, 'uSize')

  const startTime = performance.now()

  const render = () => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resizeCanvas()
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.uniform2f(uRes, canvas.width, canvas.height)
    gl.uniform1f(uTime, (performance.now() - startTime) / 1000)
    gl.uniform1f(uHueLoc,   props.hue)
    gl.uniform1f(uXOff,     props.xOffset)
    gl.uniform1f(uSpeedLoc, props.speed)
    gl.uniform1f(uIntLoc,   props.intensity)
    gl.uniform1f(uSizeLoc,  props.size)
    gl.drawArrays(gl.TRIANGLES, 0, 6)
    rafId = requestAnimationFrame(render)
  }

  const onVisibility = () => {
    if (!document.hidden && rafId === 0) render()
  }
  document.addEventListener('visibilitychange', onVisibility)

  render()

  cleanup = () => {
    cancelAnimationFrame(rafId)
    rafId = 0
    window.removeEventListener('resize', resizeCanvas)
    document.removeEventListener('visibilitychange', onVisibility)
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.lightning-container {
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
