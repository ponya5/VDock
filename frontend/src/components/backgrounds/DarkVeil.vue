<template>
  <canvas ref="canvas" class="dark-veil"></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const canvas = ref<HTMLCanvasElement | null>(null);
let reqId: number;

onMounted(() => {
  const el = canvas.value;
  if (!el) return;
  const ctx = el.getContext('2d');
  if (!ctx) return;

  const resize = () => {
    el.width = window.innerWidth;
    el.height = window.innerHeight;
  };
  window.addEventListener('resize', resize);
  resize();

  const particles: { x: number, y: number, vx: number, vy: number, size: number, alpha: number }[] = [];
  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * el.width,
      y: Math.random() * el.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      alpha: Math.random() * 0.5 + 0.1
    });
  }

  const render = () => {
    ctx.clearRect(0, 0, el.width, el.height);
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0) p.x = el.width;
      if (p.x > el.width) p.x = 0;
      if (p.y < 0) p.y = el.height;
      if (p.y > el.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
      ctx.fill();
    });
    reqId = requestAnimationFrame(render);
  };
  render();

  onUnmounted(() => {
    window.removeEventListener('resize', resize);
    cancelAnimationFrame(reqId);
  });
});
</script>

<style scoped>
.dark-veil {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
  opacity: 0.8;
}
</style>
