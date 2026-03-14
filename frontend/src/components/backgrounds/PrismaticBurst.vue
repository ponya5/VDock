<template>
  <canvas ref="canvasRef" class="prismatic-burst-container" :style="{ mixBlendMode }" />
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  animationType?: 'rotate' | 'rotate3d' | 'hover'
  intensity?: number
  speed?: number
  distort?: number
  paused?: boolean
  offset?: { x: number; y: number }
  hoverDampness?: number
  rayCount?: number
  mixBlendMode?: string
  colors?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  animationType: 'rotate3d',
  intensity: 2,
  speed: 0.5,
  distort: 0,
  paused: false,
  offset: () => ({ x: 0, y: 0 }),
  hoverDampness: 0.25,
  rayCount: 0,
  mixBlendMode: 'lighten',
  colors: () => ['#ff007a', '#4d3dff', '#ffffff'],
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let rafId = 0
let cleanup: (() => void) | null = null

const VERT = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`

// WebGL 1 port of the full ray-marcher shader
const FRAG = `
precision highp float;
precision highp int;

uniform vec2  uResolution;
uniform float uTime;
uniform float uIntensity;
uniform float uSpeed;
uniform int   uAnimType;
uniform vec2  uMouse;
uniform int   uColorCount;
uniform float uDistort;
uniform vec2  uOffset;
uniform sampler2D uGradient;
uniform float uNoiseAmount;
uniform int   uRayCount;

varying vec2 vUv;

float hash21(vec2 p) {
  p = floor(p);
  float f = 52.9829189 * fract(dot(p, vec2(0.065, 0.005)));
  return fract(f);
}

mat2 rot30() { return mat2(0.8, -0.5, 0.5, 0.8); }

float layeredNoise(vec2 fragPx) {
  vec2 p = mod(fragPx + vec2(uTime * 30.0, -uTime * 21.0), 1024.0);
  vec2 q = rot30() * p;
  float n = 0.0;
  n += 0.40 * hash21(q);
  n += 0.25 * hash21(q * 2.0  + 17.0);
  n += 0.20 * hash21(q * 4.0  + 47.0);
  n += 0.10 * hash21(q * 8.0  + 113.0);
  n += 0.05 * hash21(q * 16.0 + 191.0);
  return n;
}

vec3 rayDir(vec2 frag, vec2 res, vec2 offset, float dist) {
  float focal = res.y * max(dist, 0.001);
  return normalize(vec3(2.0 * (frag - offset) - res, focal));
}

float edgeFade(vec2 frag, vec2 res, vec2 offset) {
  vec2 toC = frag - 0.5 * res - offset;
  float r = length(toC) / (0.5 * min(res.x, res.y));
  float x = clamp(r, 0.0, 1.0);
  float q = x * x * x * (x * (x * 6.0 - 15.0) + 10.0);
  float s = q * 0.5;
  s = pow(s, 1.5);
  float tail = 1.0 - pow(1.0 - s, 2.0);
  s = mix(s, tail, 0.2);
  float dn = (layeredNoise(frag * 0.15) - 0.5) * 0.0015 * s;
  return clamp(s + dn, 0.0, 1.0);
}

mat3 rotX(float a) { float c=cos(a),s=sin(a); return mat3(1.0,0.0,0.0, 0.0,c,-s, 0.0,s,c); }
mat3 rotY(float a) { float c=cos(a),s=sin(a); return mat3(c,0.0,s, 0.0,1.0,0.0, -s,0.0,c); }
mat3 rotZ(float a) { float c=cos(a),s=sin(a); return mat3(c,-s,0.0, s,c,0.0, 0.0,0.0,1.0); }

vec3 sampleGradient(float t) {
  t = clamp(t, 0.0, 1.0);
  return texture2D(uGradient, vec2(t, 0.5)).rgb;
}

vec2 rot2(vec2 v, float a) {
  float s = sin(a), c = cos(a);
  return mat2(c, -s, s, c) * v;
}

float bendAngle(vec3 q, float t) {
  return 0.8 * sin(q.x * 0.55 + t * 0.6)
       + 0.7 * sin(q.y * 0.50 - t * 0.5)
       + 0.6 * sin(q.z * 0.60 + t * 0.7);
}

void main() {
  vec2 frag = gl_FragCoord.xy;
  float t = uTime * uSpeed;
  float jitterAmp = 0.1 * clamp(uNoiseAmount, 0.0, 1.0);

  vec3 dir = rayDir(frag, uResolution, uOffset, 1.0);
  float marchT = 0.0;
  vec3 col = vec3(0.0);
  float n = layeredNoise(frag);

  vec4 c = cos(t * 0.2 + vec4(0.0, 33.0, 11.0, 0.0));
  mat2 M2 = mat2(c.x, c.y, c.z, c.w);
  float amp = clamp(uDistort, 0.0, 50.0) * 0.15;

  mat3 rot3dMat = mat3(1.0);
  if (uAnimType == 1) {
    vec3 ang = vec3(t * 0.31, t * 0.21, t * 0.17);
    rot3dMat = rotZ(ang.z) * rotY(ang.y) * rotX(ang.x);
  }

  mat3 hoverMat = mat3(1.0);
  if (uAnimType == 2) {
    vec2 m = uMouse * 2.0 - 1.0;
    vec3 ang = vec3(m.y * 0.6, m.x * 0.6, 0.0);
    hoverMat = rotY(ang.y) * rotX(ang.x);
  }

  for (int i = 0; i < 44; ++i) {
    vec3 P = marchT * dir;
    P.z -= 2.0;
    float rad = length(P);
    vec3 Pl = P * (10.0 / max(rad, 0.000001));

    if (uAnimType == 0) {
      Pl.xz = M2 * Pl.xz;
    } else if (uAnimType == 1) {
      Pl = rot3dMat * Pl;
    } else {
      Pl = hoverMat * Pl;
    }

    float stepLen = min(rad - 0.3, n * jitterAmp) + 0.1;
    float grow = smoothstep(0.35, 3.0, marchT);
    float a1 = amp * grow * bendAngle(Pl * 0.6, t);
    float a2 = 0.5 * amp * grow * bendAngle(Pl.zyx * 0.5 + 3.1, t * 0.9);

    vec3 Pb = Pl;
    Pb.xz = rot2(Pb.xz, a1);
    Pb.xy = rot2(Pb.xy, a2);

    float rayPattern = smoothstep(0.5, 0.7,
      sin(Pb.x + cos(Pb.y) * cos(Pb.z)) *
      sin(Pb.z + sin(Pb.y) * cos(Pb.x + t)));

    if (uRayCount > 0) {
      float ang = atan(Pb.y, Pb.x);
      float comb = 0.5 + 0.5 * cos(float(uRayCount) * ang);
      comb = pow(comb, 3.0);
      rayPattern *= smoothstep(0.15, 0.95, comb);
    }

    vec3 spectralDefault = 1.0 + vec3(
      cos(marchT * 3.0 + 0.0),
      cos(marchT * 3.0 + 1.0),
      cos(marchT * 3.0 + 2.0));

    float saw = fract(marchT * 0.25);
    float tRay = saw * saw * (3.0 - 2.0 * saw);
    vec3 userGradient = 2.0 * sampleGradient(tRay);
    vec3 spectral = (uColorCount > 0) ? userGradient : spectralDefault;

    vec3 base = (0.05 / (0.4 + stepLen))
      * smoothstep(5.0, 0.0, rad)
      * spectral;

    col += base * rayPattern;
    marchT += stepLen;
  }

  col *= edgeFade(frag, uResolution, uOffset);
  col *= uIntensity;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
`

function hexToRgb(hex: string): [number, number, number] {
  let h = hex.trim().replace('#', '')
  if (h.length === 3) h = h[0]+h[0]+h[1]+h[1]+h[2]+h[2]
  const v = parseInt(h, 16)
  return [((v >> 16) & 255) / 255, ((v >> 8) & 255) / 255, (v & 255) / 255]
}

function buildGradientData(colors: string[]): Uint8Array {
  const count = Math.max(colors.length, 1)
  const data = new Uint8Array(count * 4)
  for (let i = 0; i < count; i++) {
    const [r, g, b] = hexToRgb(colors[i] ?? '#ffffff')
    data[i * 4 + 0] = Math.round(r * 255)
    data[i * 4 + 1] = Math.round(g * 255)
    data[i * 4 + 2] = Math.round(b * 255)
    data[i * 4 + 3] = 255
  }
  return data
}

function compile(gl: WebGLRenderingContext, src: string, type: number): WebGLShader | null {
  const s = gl.createShader(type)
  if (!s) return null
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    console.warn('PrismaticBurst shader error:', gl.getShaderInfoLog(s))
    gl.deleteShader(s)
    return null
  }
  return s
}

const ANIM_TYPE: Record<string, number> = { rotate: 0, rotate3d: 1, hover: 2 }

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  const mouse = { x: 0.5, y: 0.5 }
  const smoothMouse = { x: 0.5, y: 0.5 }

  const resize = () => { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight }
  resize()
  window.addEventListener('resize', resize, { passive: true })
  window.addEventListener('mousemove', (e: MouseEvent) => {
    mouse.x = e.clientX / window.innerWidth
    mouse.y = e.clientY / window.innerHeight
  }, { passive: true })

  const gl = canvas.getContext('webgl', { alpha: false })
  if (!gl) { console.warn('WebGL unavailable — PrismaticBurst disabled'); return }

  const vert = compile(gl, VERT, gl.VERTEX_SHADER)
  const frag = compile(gl, FRAG, gl.FRAGMENT_SHADER)
  if (!vert || !frag) return

  const prog = gl.createProgram()!
  gl.attachShader(prog, vert); gl.attachShader(prog, frag)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.warn('PrismaticBurst link error:', gl.getProgramInfoLog(prog)); return
  }
  gl.useProgram(prog)

  // Full-screen triangle with UV
  const verts = new Float32Array([
    -1, -1,  0, 0,
     3, -1,  2, 0,
    -1,  3,  0, 2,
  ])
  const buf = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buf)
  gl.bufferData(gl.ARRAY_BUFFER, verts, gl.STATIC_DRAW)
  const stride = 4 * 4
  const aPos = gl.getAttribLocation(prog, 'position')
  gl.enableVertexAttribArray(aPos)
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, stride, 0)
  const aUv = gl.getAttribLocation(prog, 'uv')
  gl.enableVertexAttribArray(aUv)
  gl.vertexAttribPointer(aUv, 2, gl.FLOAT, false, stride, 8)

  // Gradient texture
  const gradTex = gl.createTexture()!
  const uploadGradient = (colors: string[]) => {
    const data = buildGradientData(colors)
    gl.bindTexture(gl.TEXTURE_2D, gradTex)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, colors.length, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, data)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  }
  uploadGradient(props.colors)

  const uRes       = gl.getUniformLocation(prog, 'uResolution')
  const uTime      = gl.getUniformLocation(prog, 'uTime')
  const uInt       = gl.getUniformLocation(prog, 'uIntensity')
  const uSpd       = gl.getUniformLocation(prog, 'uSpeed')
  const uAnimType  = gl.getUniformLocation(prog, 'uAnimType')
  const uMouse     = gl.getUniformLocation(prog, 'uMouse')
  const uColorCnt  = gl.getUniformLocation(prog, 'uColorCount')
  const uDist      = gl.getUniformLocation(prog, 'uDistort')
  const uOff       = gl.getUniformLocation(prog, 'uOffset')
  const uGrad      = gl.getUniformLocation(prog, 'uGradient')
  const uNoise     = gl.getUniformLocation(prog, 'uNoiseAmount')
  const uRayCnt    = gl.getUniformLocation(prog, 'uRayCount')

  gl.uniform1i(uGrad, 0)

  const start = performance.now()
  let lastColors = props.colors.join(',')

  const render = () => {
    if (document.hidden || props.paused) { rafId = requestAnimationFrame(render); return }
    resize()
    gl.viewport(0, 0, canvas.width, canvas.height)

    // smooth mouse
    const d = props.hoverDampness
    smoothMouse.x += (mouse.x - smoothMouse.x) * d
    smoothMouse.y += (mouse.y - smoothMouse.y) * d

    // re-upload gradient only when colors change
    const colKey = props.colors.join(',')
    if (colKey !== lastColors) { uploadGradient(props.colors); lastColors = colKey }

    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, gradTex)

    gl.uniform2f(uRes,      canvas.width, canvas.height)
    gl.uniform1f(uTime,     (performance.now() - start) / 1000)
    gl.uniform1f(uInt,      props.intensity)
    gl.uniform1f(uSpd,      props.speed)
    gl.uniform1i(uAnimType, ANIM_TYPE[props.animationType] ?? 1)
    gl.uniform2f(uMouse,    smoothMouse.x, smoothMouse.y)
    gl.uniform1i(uColorCnt, props.colors.length)
    gl.uniform1f(uDist,     props.distort)
    gl.uniform2f(uOff,      props.offset.x, props.offset.y)
    gl.uniform1f(uNoise,    0.8)
    gl.uniform1i(uRayCnt,   props.rayCount ?? 0)

    gl.drawArrays(gl.TRIANGLES, 0, 3)
    rafId = requestAnimationFrame(render)
  }

  const onVis = () => { if (!document.hidden && !props.paused && rafId === 0) render() }
  document.addEventListener('visibilitychange', onVis)
  render()

  cleanup = () => {
    cancelAnimationFrame(rafId); rafId = 0
    window.removeEventListener('resize', resize)
    document.removeEventListener('visibilitychange', onVis)
  }
})

onUnmounted(() => cleanup?.())
</script>

<style scoped>
.prismatic-burst-container {
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
