<template>
  <div ref="rootEl" class="plasma-wave-container" aria-hidden="true" />
</template>

<script setup>
// Ported from reactbits.dev PlasmaWave. The renderer internals are kept verbatim
// from the upstream React component; only the React shell was replaced
// (useRef/useState/useEffect/useMemo/useCallback -> plain boxes + mount-time
// effects). Plain JS script: upstream code is untyped and untouched on purpose.
import { onMounted, onUnmounted, ref } from 'vue'
import { Renderer, Camera, Transform, Program, Mesh, Geometry } from 'ogl';


function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  return [r, g, b];
}

const VERT = /* glsl */ `
attribute vec2 position;
void main() {
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const FRAG = /* glsl */ `
precision highp float;
uniform float iTime;
uniform vec2  iResolution;
uniform vec2  uOffset;
uniform float uRotation;
uniform float uFocalLength;
uniform float uSpeed1;
uniform float uSpeed2;
uniform float uDir2;
uniform float uBend1;
uniform float uBend2;
uniform vec3  uColor1;
uniform vec3  uColor2;
uniform float uLightMode;

const float lt   = 0.3;
const float pi   = 3.14159;
const float pi2  = 6.28318;
const float pi_2 = 1.5708;
#define MAX_STEPS 14

void mainImage(out vec4 C, in vec2 U) {
  float t = iTime * pi;
  float s = 1.0;
  float d = 0.0;
  vec2  R = iResolution;

  vec3 o = vec3(0.0, 0.0, -7.0);
  vec3 u = normalize(vec3((U - 0.5 * R) / R.y, uFocalLength));
  vec2 k = vec2(0.0);
  vec3 p;

  float t1 = t * 0.7;
  float t2 = t * 0.9;
  float tSpeed1 = t * uSpeed1;
  float tSpeed2 = t * uSpeed2 * uDir2;

  for (int i = 0; i < MAX_STEPS; ++i) {
    p = o + u * d;
    p.x -= 15.0;

    float px = p.x;
    float wob1 = uBend1 + sin(t1 + px * 0.8) * 0.1;
    float wob2 = uBend2 + cos(t2 + px * 1.1) * 0.1;

    float px2 = px + pi_2;
    vec2 sinOffset = sin(vec2(px, px2) + tSpeed1) * wob1;
    vec2 cosOffset = cos(vec2(px, px2) + tSpeed2) * wob2;

    vec2 yz = p.yz;
    float pxLt = px + lt;
    k.x = max(pxLt, length(yz - sinOffset) - lt);
    k.y = max(pxLt, length(yz - cosOffset) - lt);

    float current = min(k.x, k.y);
    s = min(s, current);
    if (s < 0.001 || d > 300.0) break;
    d += s * 0.7;
  }

  float sqrtD = sqrt(d);
  vec3 raw = max(cos(d * pi2) - s * sqrtD - vec3(k, 0.0), 0.0);
  float field = max(raw.r, max(raw.g, raw.b));
  float outerMask = smoothstep(0.0, 0.055, field);
  float glowMask = smoothstep(0.012, 0.13, field);
  float coreMask = smoothstep(0.075, 0.27, field);
  if (uLightMode < 0.5 && field < 0.15) discard;
  raw.gb += uLightMode > 0.5 ? 0.1 * glowMask : 0.1;
  raw = raw * 0.4 + raw.brg * 0.6 + raw * raw;
  float lum = dot(raw, vec3(0.299, 0.587, 0.114));
  float w1 = max(0.0, 1.0 - k.x * 2.0);
  float w2 = max(0.0, 1.0 - k.y * 2.0);
  float wt = w1 + w2 + 0.001;
  vec3 baseColor = (uColor1 * w1 + uColor2 * w2) / wt;
  vec3 c = baseColor * lum * 3.5;
  if (uLightMode > 0.5) {
    float lightW1 = exp(-max(k.x, 0.0) * 4.0);
    float lightW2 = exp(-max(k.y, 0.0) * 4.0);
    vec3 lightBase = (uColor1 * lightW1 + uColor2 * lightW2) / (lightW1 + lightW2 + 0.001);
    float lightLuma = dot(lightBase, vec3(0.299, 0.587, 0.114));
    vec3 vividColor = clamp(pow(max(mix(vec3(lightLuma), lightBase, 1.35), 0.0), vec3(0.64)) * 1.14, 0.0, 1.0);
    float colorPresence = clamp(outerMask * 0.34 + glowMask * 1.08 + coreMask * 0.22, 0.0, 1.0);
    vec3 lightColor = mix(vec3(1.0), vividColor, colorPresence);
    lightColor = mix(lightColor, vec3(1.0), coreMask * smoothstep(0.16, 0.95, lum) * 0.1);
    C = vec4(lightColor, 1.0);
  } else {
    C = vec4(c, 1.0);
  }
}

void main() {
  vec2 coord = gl_FragCoord.xy + uOffset;
  coord -= 0.5 * iResolution;
  float c = cos(uRotation), s = sin(uRotation);
  coord = mat2(c, -s, s, c) * coord;
  coord += 0.5 * iResolution;

  vec4 color;
  mainImage(color, coord);
  gl_FragColor = color;
}
`;

const props = defineProps({
  onError: { type: Function, default: undefined }
})

const rootEl = ref(null)
const canvasEl = ref(null)
const hooks = { setReady: () => {} }
let cleanup = null

onMounted(() => {
  if (!rootEl.value) return
  cleanup = mountPlasmaWave(rootEl.value, null, hooks, { onError: props.onError })
})

onUnmounted(() => {
  cleanup?.()
  cleanup = null
})

function mountPlasmaWave(rootEl, canvasEl, hooks, props) {
  // React-compat shims: catalog renders with default props, so refs become
  // plain boxes and effects are collected then run once on mount.
  const useRef = v => ({ current: v });
  const useState = v => {
    const o = { value: v };
    return [o, n => { o.value = n }];
  };
  const useMemo = fn => fn();
  const useCallback = fn => fn;
  const __effects = [];
  const useEffect = fn => {
    __effects.push(fn);
  };

  const {
    xOffset = 0,
    yOffset = 0,
    rotationDeg = 0,
    focalLength = 0.8,
    speed1 = 0.05,
    speed2 = 0.05,
    dir2 = 1.0,
    bend1 = 1,
    bend2 = 0.5,
    colors = ['#A855F7', '#06B6D4'],
    lightMode = false
  } = props;

  const propsRef = useRef(props);
  propsRef.current = props;

  const containerRef = { current: rootEl };

  useEffect(() => {
    const ctn = containerRef.current;
    if (!ctn) return;

    const renderer = new Renderer({
      alpha: true,
      dpr: Math.min(window.devicePixelRatio, 1.5),
      antialias: true,
      depth: false,
      stencil: false,
      premultipliedAlpha: false,
      preserveDrawingBuffer: false,
      powerPreference: 'high-performance'
    });

    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    ctn.appendChild(gl.canvas);

    const camera = new Camera(gl);
    const scene = new Transform();

    const geometry = new Geometry(gl, {
      position: { size: 2, data: new Float32Array([-1, -1, 3, -1, -1, 3]) }
    });

    const uniformOffset = new Float32Array([xOffset, yOffset]);
    const uniformResolution = new Float32Array([1, 1]);
    const c1 = hexToRgb(colors[0]);
    const c2 = hexToRgb(colors[1]);

    const program = new Program(gl, {
      vertex: VERT,
      fragment: FRAG,
      uniforms: {
        iTime: { value: 0 },
        iResolution: { value: uniformResolution },
        uOffset: { value: uniformOffset },
        uRotation: { value: (rotationDeg * Math.PI) / 180 },
        uFocalLength: { value: focalLength },
        uSpeed1: { value: speed1 },
        uSpeed2: { value: speed2 },
        uDir2: { value: dir2 },
        uBend1: { value: bend1 },
        uBend2: { value: bend2 },
        uColor1: { value: c1 },
        uColor2: { value: c2 },
        uLightMode: { value: lightMode ? 1 : 0 }
      }
    });

    new Mesh(gl, { geometry, program }).setParent(scene);

    function resize() {
      if (!ctn) return;
      const { width, height } = ctn.getBoundingClientRect();
      renderer.setSize(width, height);
      uniformResolution[0] = width * renderer.dpr;
      uniformResolution[1] = height * renderer.dpr;
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    }

    const ro = new ResizeObserver(resize);
    ro.observe(ctn);
    resize();

    const startTime = performance.now();
    let animateId;

    const update = (now) => {
      const {
        xOffset: xOff = 0,
        yOffset: yOff = 0,
        rotationDeg: rot = 0,
        focalLength: fLen = 0.8,
        speed1: s1 = 0.05,
        speed2: s2 = 0.05,
        dir2: d2 = 1.0,
        bend1: b1 = 1,
        bend2: b2 = 0.5,
        colors: cols = ['#A855F7', '#06B6D4'],
        lightMode: isLight = false
      } = propsRef.current;

      uniformOffset[0] = xOff;
      uniformOffset[1] = yOff;
      program.uniforms.iTime.value = (now - startTime) * 0.001;
      program.uniforms.uRotation.value = (rot * Math.PI) / 180;
      program.uniforms.uFocalLength.value = fLen;
      program.uniforms.uSpeed1.value = s1;
      program.uniforms.uSpeed2.value = s2;
      program.uniforms.uDir2.value = d2;
      program.uniforms.uBend1.value = b1;
      program.uniforms.uBend2.value = b2;
      program.uniforms.uColor1.value = hexToRgb(cols[0]);
      program.uniforms.uColor2.value = hexToRgb(cols[1]);
      program.uniforms.uLightMode.value = isLight ? 1 : 0;

      renderer.render({ scene, camera });
      animateId = requestAnimationFrame(update);
    };

    animateId = requestAnimationFrame(update);

    return () => {
      cancelAnimationFrame(animateId);
      ro.disconnect();
      if (ctn && gl.canvas.parentNode === ctn) {
        ctn.removeChild(gl.canvas);
      }
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const __cleanups = [];
  for (const fn of __effects) {
    const c = fn();
    if (typeof c === 'function') __cleanups.push(c);
  }
  return () => __cleanups.forEach(c => c());
}

</script>

<style scoped>
.plasma-wave-container {
  width: 100%;
  height: 100%;
}
</style>
