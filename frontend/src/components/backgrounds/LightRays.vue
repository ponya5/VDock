<template>
  <canvas ref="canvasRef" class="light-rays-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  raysOrigin?: 'top-center' | 'top-left' | 'top-right' | 'left' | 'right' | 'bottom-left' | 'bottom-center' | 'bottom-right'
  raysColor?: string
  raysSpeed?: number
  lightSpread?: number
  rayLength?: number
  followMouse?: boolean
  mouseInfluence?: number
  noiseAmount?: number
  distortion?: number
  pulsating?: boolean
  fadeDistance?: number
  saturation?: number
}

const props = withDefaults(defineProps<Props>(), {
  raysOrigin: 'top-center',
  raysColor: '#ffffff',
  raysSpeed: 1,
  lightSpread: 0.5,
  rayLength: 3,
  followMouse: true,
  mouseInfluence: 0.1,
  noiseAmount: 0,
  distortion: 0,
  pulsating: false,
  fadeDistance: 1,
  saturation: 1,
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
precision highp float;

uniform float uTime;
uniform vec2  uResolution;
uniform vec2  uRayPos;
uniform vec2  uRayDir;
uniform vec3  uRaysColor;
uniform float uRaysSpeed;
uniform float uLightSpread;
uniform float uRayLength;
uniform float uPulsating;
uniform float uFadeDistance;
uniform float uSaturation;
uniform vec2  uMousePos;
uniform float uMouseInfluence;
uniform float uNoiseAmount;
uniform float uDistortion;

varying vec2 vUv;

float noise(vec2 st) {
  return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
}

float rayStrength(vec2 raySource, vec2 rayRefDirection, vec2 coord,
                  float seedA, float seedB, float speed) {
  vec2  sourceToCoord = coord - raySource;
  vec2  dirNorm       = normalize(sourceToCoord);
  float cosAngle      = dot(dirNorm, rayRefDirection);
  float distortedAngle = cosAngle + uDistortion
    * sin(uTime * 2.0 + length(sourceToCoord) * 0.01) * 0.2;

  float spreadFactor = pow(max(distortedAngle, 0.0), 1.0 / max(uLightSpread, 0.001));
  float distance     = length(sourceToCoord);
  float maxDistance  = uResolution.x * uRayLength;
  float lengthFalloff = clamp((maxDistance - distance) / maxDistance, 0.0, 1.0);
  float fadeFalloff   = clamp(
    (uResolution.x * uFadeDistance - distance) / (uResolution.x * uFadeDistance),
    0.5, 1.0);
  float pulse = uPulsating > 0.5
    ? (0.8 + 0.2 * sin(uTime * speed * 3.0))
    : 1.0;

  float baseStrength = clamp(
    (0.45 + 0.15 * sin(distortedAngle * seedA + uTime * speed)) +
    (0.30 + 0.20 * cos(-distortedAngle * seedB + uTime * speed)),
    0.0, 1.0);

  return baseStrength * lengthFalloff * fadeFalloff * spreadFactor * pulse;
}

void main() {
  vec2 coord = vec2(gl_FragCoord.x, uResolution.y - gl_FragCoord.y);

  vec2 finalRayDir = uRayDir;
  if (uMouseInfluence > 0.0) {
    vec2 mouseScreenPos = uMousePos * uResolution;
    vec2 mouseDirection = normalize(mouseScreenPos - uRayPos);
    finalRayDir = normalize(mix(uRayDir, mouseDirection, uMouseInfluence));
  }

  float r1 = rayStrength(uRayPos, finalRayDir, coord, 36.2214, 21.11349, 1.5 * uRaysSpeed);
  float r2 = rayStrength(uRayPos, finalRayDir, coord, 22.3991, 18.0234,  1.1 * uRaysSpeed);
  vec4 col = vec4(1.0) * (r1 * 0.5 + r2 * 0.4);

  if (uNoiseAmount > 0.0) {
    float n = noise(coord * 0.01 + uTime * 0.1);
    col.rgb *= (1.0 - uNoiseAmount + uNoiseAmount * n);
  }

  float brightness = 1.0 - (coord.y / uResolution.y);
  col.x *= 0.1 + brightness * 0.8;
  col.y *= 0.3 + brightness * 0.6;
  col.z *= 0.5 + brightness * 0.5;

  if (uSaturation != 1.0) {
    float gray = dot(col.rgb, vec3(0.299, 0.587, 0.114));
    col.rgb = mix(vec3(gray), col.rgb, uSaturation);
  }

  col.rgb *= uRaysColor;
  gl_FragColor = col;
}
`

function hexToRgb(hex: string): [number, number, number] {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return m
    ? [parseInt(m[1], 16) / 255, parseInt(m[2], 16) / 255, parseInt(m[3], 16) / 255]
    : [1, 1, 1]
}

function getAnchorAndDir(origin: string, w: number, h: number): { anchor: [number, number]; dir: [number, number] } {
  const outside = 0.2
  switch (origin) {
    case 'top-left':     return { anchor: [0,              -outside * h],       dir: [0,  1] }
    case 'top-right':    return { anchor: [w,              -outside * h],       dir: [0,  1] }
    case 'left':         return { anchor: [-outside * w,   0.5 * h],            dir: [1,  0] }
    case 'right':        return { anchor: [(1 + outside)*w, 0.5 * h],           dir: [-1, 0] }
    case 'bottom-left':  return { anchor: [0,              (1 + outside) * h],  dir: [0, -1] }
    case 'bottom-center':return { anchor: [0.5 * w,        (1 + outside) * h],  dir: [0, -1] }
    case 'bottom-right': return { anchor: [w,              (1 + outside) * h],  dir: [0, -1] }
    default:             return { anchor: [0.5 * w,        -outside * h],       dir: [0,  1] }
  }
}

function compileShader(gl: WebGLRenderingContext, src: string, type: number): WebGLShader | null {
  const s = gl.createShader(type)
  if (!s) return null
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.warn('LightRays shader error:', gl.getShaderInfoLog(s))
    gl.deleteShader(s)
    return null
  }
  return s
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const mouse = { x: 0.5, y: 0.5 }
  const smoothMouse = { x: 0.5, y: 0.5 }

  const resize = () => {
    canvas.width  = canvas.clientWidth
    canvas.height = canvas.clientHeight
  }
  resize()
  window.addEventListener('resize', resize, { passive: true })

  const gl = canvas.getContext('webgl', { alpha: true, premultipliedAlpha: false })
  if (!gl) { console.warn('WebGL unavailable — LightRays background disabled'); return }

  gl.enable(gl.BLEND)
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

  const vert = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER)
  const frag = compileShader(gl, FRAG_SRC, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert)
  gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('LightRays link error:', gl.getProgramInfoLog(prog))
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

  const uTime         = gl.getUniformLocation(prog, 'uTime')
  const uRes          = gl.getUniformLocation(prog, 'uResolution')
  const uRayPos       = gl.getUniformLocation(prog, 'uRayPos')
  const uRayDir       = gl.getUniformLocation(prog, 'uRayDir')
  const uRaysColor    = gl.getUniformLocation(prog, 'uRaysColor')
  const uRaysSpeed    = gl.getUniformLocation(prog, 'uRaysSpeed')
  const uLightSpread  = gl.getUniformLocation(prog, 'uLightSpread')
  const uRayLength    = gl.getUniformLocation(prog, 'uRayLength')
  const uPulsating    = gl.getUniformLocation(prog, 'uPulsating')
  const uFadeDistance = gl.getUniformLocation(prog, 'uFadeDistance')
  const uSaturation   = gl.getUniformLocation(prog, 'uSaturation')
  const uMousePos     = gl.getUniformLocation(prog, 'uMousePos')
  const uMouseInfl    = gl.getUniformLocation(prog, 'uMouseInfluence')
  const uNoiseAmount  = gl.getUniformLocation(prog, 'uNoiseAmount')
  const uDistortion   = gl.getUniformLocation(prog, 'uDistortion')

  const start = performance.now()

  const render = () => {
    if (document.hidden) { rafId = requestAnimationFrame(render); return }
    resize()
    gl.viewport(0, 0, canvas.width, canvas.height)
    gl.clearColor(0, 0, 0, 0)
    gl.clear(gl.COLOR_BUFFER_BIT)

    // smooth mouse
    const sm = 0.92
    smoothMouse.x = smoothMouse.x * sm + mouse.x * (1 - sm)
    smoothMouse.y = smoothMouse.y * sm + mouse.y * (1 - sm)

    const { anchor, dir } = getAnchorAndDir(props.raysOrigin, canvas.width, canvas.height)
    const [cr, cg, cb] = hexToRgb(props.raysColor)

    gl.uniform1f(uTime,         (performance.now() - start) / 1000)
    gl.uniform2f(uRes,          canvas.width, canvas.height)
    gl.uniform2f(uRayPos,       anchor[0], anchor[1])
    gl.uniform2f(uRayDir,       dir[0], dir[1])
    gl.uniform3f(uRaysColor,    cr, cg, cb)
    gl.uniform1f(uRaysSpeed,    props.raysSpeed)
    gl.uniform1f(uLightSpread,  props.lightSpread)
    gl.uniform1f(uRayLength,    props.rayLength)
    gl.uniform1f(uPulsating,    props.pulsating ? 1.0 : 0.0)
    gl.uniform1f(uFadeDistance, props.fadeDistance)
    gl.uniform1f(uSaturation,   props.saturation)
    gl.uniform2f(uMousePos,     smoothMouse.x, smoothMouse.y)
    gl.uniform1f(uMouseInfl,    props.followMouse ? props.mouseInfluence : 0.0)
    gl.uniform1f(uNoiseAmount,  props.noiseAmount)
    gl.uniform1f(uDistortion,   props.distortion)

    gl.drawArrays(gl.TRIANGLES, 0, 6)
    rafId = requestAnimationFrame(render)
  }

  const onMouseMove = (e: MouseEvent) => {
    const rect = canvas.getBoundingClientRect()
    mouse.x = (e.clientX - rect.left) / rect.width
    mouse.y = (e.clientY - rect.top)  / rect.height
  }

  const onVis = () => { if (!document.hidden && rafId === 0) render() }
  document.addEventListener('visibilitychange', onVis)
  if (props.followMouse) window.addEventListener('mousemove', onMouseMove, { passive: true })
  render()

  cleanup = () => {
    cancelAnimationFrame(rafId)
    rafId = 0
    window.removeEventListener('resize', resize)
    window.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('visibilitychange', onVis)
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.light-rays-container {
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
