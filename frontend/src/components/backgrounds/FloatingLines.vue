<template>
  <canvas ref="canvas" class="floating-lines"></canvas>
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

  let time = 0;
  const render = () => {
    ctx.clearRect(0, 0, el.width, el.height);
    time += 0.01;

    ctx.beginPath();
    ctx.moveTo(0, el.height / 2);
    for (let x = 0; x < el.width; x += 10) {
      const y = Math.sin(x * 0.01 + time) * 50 + Math.sin(x * 0.005 - time * 0.8) * 30;
      ctx.lineTo(x, el.height / 2 + y);
    }
    ctx.strokeStyle = 'rgba(102, 126, 234, 0.3)';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(0, el.height / 2);
    for (let x = 0; x < el.width; x += 10) {
      const y = Math.cos(x * 0.015 - time * 1.2) * 40 + Math.sin(x * 0.008 + time) * 40;
      ctx.lineTo(x, el.height / 2 + y + 30);
    }
    ctx.strokeStyle = 'rgba(78, 205, 196, 0.2)';
    ctx.lineWidth = 3;
    ctx.stroke();

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
.floating-lines {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: -1;
  pointer-events: none;
}
</style>
