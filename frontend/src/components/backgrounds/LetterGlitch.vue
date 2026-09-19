<template>
  <div ref="rootEl" class="letter-glitch-container" aria-hidden="true">
    <canvas ref="canvasEl" class="letter-glitch-canvas" />
    <div v-if="outerVignette" class="letter-glitch-vignette-outer" />
    <div v-if="centerVignette" class="letter-glitch-vignette-center" />
  </div>
</template>

<script setup>
// Ported from reactbits.dev LetterGlitch. The renderer internals are kept verbatim
// from the upstream React component; only the React shell was replaced
// (useRef/useState/useEffect/useMemo/useCallback -> plain boxes + mount-time
// effects). Plain JS script: upstream code is untyped and untouched on purpose.
import { onMounted, onUnmounted, ref } from 'vue'

const FALLBACK_RGB = { r: 255, g: 255, b: 255 };

const props = defineProps({
  onError: { type: Function, default: undefined },
  outerVignette: { type: Boolean, default: true },
  centerVignette: { type: Boolean, default: false }
})

const rootEl = ref(null)
const canvasEl = ref(null)
const hooks = { setReady: () => {} }
let cleanup = null

onMounted(() => {
  if (!rootEl.value) return
  cleanup = mountLetterGlitch(rootEl.value, canvasEl.value, hooks, { onError: props.onError, outerVignette: props.outerVignette, centerVignette: props.centerVignette })
})

onUnmounted(() => {
  cleanup?.()
  cleanup = null
})

function mountLetterGlitch(rootEl, canvasEl, hooks, {
  glitchColors = ['#2b4539', '#61dca3', '#61b3dc'],
  className = '',
  glitchSpeed = 50,
  centerVignette = false,
  outerVignette = true,
  smooth = true,
  lightMode = false,
  backgroundColor,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$&*()-_+=/[]{};:<>.,0123456789'
})  {
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

  const canvasRef = { current: canvasEl };
  const animationRef = useRef(null);
  const letters = useRef([]);
  const grid = useRef({ columns: 0, rows: 0 });
  const context = useRef(null);
  const lastGlitchTime = useRef(Date.now());

  const lettersAndSymbols = Array.from(characters);

  const fontSize = 16;
  const charWidth = 10;
  const charHeight = 20;

  const getRandomChar = () => {
    return lettersAndSymbols[Math.floor(Math.random() * lettersAndSymbols.length)];
  };

  const getRandomColor = () => {
    return glitchColors[Math.floor(Math.random() * glitchColors.length)];
  };

  const hexToRgb = hex => {
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, (m, r, g, b) => {
      return r + r + g + g + b + b;
    });

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : null;
  };

  // Interpolation happens in numbers, and the CSS string is only built at
  // paint time. Previously the formatted `rgb(...)` string was stored back
  // on the letter and fed to hexToRgb on the next frame, which returned null
  // and froze the transition after a single step.
  const mixRgb = (start, end, factor) => ({
    r: Math.round(start.r + (end.r - start.r) * factor),
    g: Math.round(start.g + (end.g - start.g) * factor),
    b: Math.round(start.b + (end.b - start.b) * factor)
  });

  const rgbToCss = ({ r, g, b }) => `rgb(${r}, ${g}, ${b})`;

  // An unparseable entry in glitchColors must not stall the animation.
  const getRandomRgb = () => hexToRgb(getRandomColor()) || FALLBACK_RGB;

  const calculateGrid = (width, height) => {
    const columns = Math.ceil(width / charWidth);
    const rows = Math.ceil(height / charHeight);
    return { columns, rows };
  };

  const initializeLetters = (columns, rows) => {
    grid.current = { columns, rows };
    const totalLetters = columns * rows;
    letters.current = Array.from({ length: totalLetters }, () => {
      const rgb = getRandomRgb();
      return {
        char: getRandomChar(),
        rgb,
        fromRgb: rgb,
        targetRgb: getRandomRgb(),
        colorProgress: 1
      };
    });
  };

  const resizeCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = parent.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;

    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;

    if (context.current) {
      context.current.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    const { columns, rows } = calculateGrid(rect.width, rect.height);
    initializeLetters(columns, rows);

    drawLetters();
  };

  const drawLetters = () => {
    if (!context.current || letters.current.length === 0) return;
    const ctx = context.current;
    const { width, height } = canvasRef.current.getBoundingClientRect();
    ctx.clearRect(0, 0, width, height);
    ctx.font = `${fontSize}px monospace`;
    ctx.textBaseline = 'top';

    letters.current.forEach((letter, index) => {
      const x = (index % grid.current.columns) * charWidth;
      const y = Math.floor(index / grid.current.columns) * charHeight;
      ctx.fillStyle = rgbToCss(letter.rgb);
      ctx.fillText(letter.char, x, y);
    });
  };

  const updateLetters = () => {
    if (!letters.current || letters.current.length === 0) return;

    const updateCount = Math.max(1, Math.floor(letters.current.length * 0.05));

    for (let i = 0; i < updateCount; i++) {
      const index = Math.floor(Math.random() * letters.current.length);
      if (!letters.current[index]) continue;

      letters.current[index].char = getRandomChar();
      // A new transition starts from the colour currently on screen, so a
      // letter picked again mid-fade continues instead of jumping.
      letters.current[index].fromRgb = letters.current[index].rgb;
      letters.current[index].targetRgb = getRandomRgb();

      if (!smooth) {
        letters.current[index].rgb = letters.current[index].targetRgb;
        letters.current[index].colorProgress = 1;
      } else {
        letters.current[index].colorProgress = 0;
      }
    }
  };

  const handleSmoothTransitions = () => {
    let needsRedraw = false;
    letters.current.forEach(letter => {
      if (letter.colorProgress < 1) {
        letter.colorProgress += 0.05;
        if (letter.colorProgress > 1) letter.colorProgress = 1;

        letter.rgb = mixRgb(letter.fromRgb, letter.targetRgb, letter.colorProgress);
        needsRedraw = true;
      }
    });

    if (needsRedraw) {
      drawLetters();
    }
  };

  const animate = () => {
    const now = Date.now();
    if (now - lastGlitchTime.current >= glitchSpeed) {
      updateLetters();
      drawLetters();
      lastGlitchTime.current = now;
    }

    if (smooth) {
      handleSmoothTransitions();
    }

    animationRef.current = requestAnimationFrame(animate);
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    context.current = canvas.getContext('2d');
    resizeCanvas();
    animate();

    let resizeTimeout;

    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        cancelAnimationFrame(animationRef.current);
        resizeCanvas();
        animate();
      }, 100);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationRef.current);
      window.removeEventListener('resize', handleResize);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [glitchSpeed, smooth]);

  const containerStyle = {
    position: 'relative',
    width: '100%',
    height: '100%',
    backgroundColor: backgroundColor || (lightMode ? '#ffffff' : '#000000'),
    overflow: 'hidden'
  };

  const canvasStyle = {
    display: 'block',
    width: '100%',
    height: '100%'
  };

  const outerVignetteStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    background: lightMode
      ? 'radial-gradient(circle, rgba(255,255,255,0) 58%, rgba(255,255,255,0.96) 100%)'
      : 'radial-gradient(circle, rgba(0,0,0,0) 60%, rgba(0,0,0,1) 100%)'
  };

  const centerVignetteStyle = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    pointerEvents: 'none',
    background: lightMode
      ? 'radial-gradient(circle, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 60%)'
      : 'radial-gradient(circle, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 60%)'
  };

  const __cleanups = [];
  for (const fn of __effects) {
    const c = fn();
    if (typeof c === 'function') __cleanups.push(c);
  }
  return () => __cleanups.forEach(c => c());
}

</script>

<style scoped>


.letter-glitch-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #000;
}
.letter-glitch-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
.letter-glitch-vignette-outer,
.letter-glitch-vignette-center {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.letter-glitch-vignette-outer {
  background: radial-gradient(circle, rgba(0, 0, 0, 0) 60%, rgba(0, 0, 0, 1) 100%);
}
.letter-glitch-vignette-center {
  background: radial-gradient(circle, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0) 60%);
}
</style>
