<template>
  <!-- DL-153: the clock half — own 1 s timer, never touches the face. -->
  <div class="robot-clock">
    <div class="rc-time">{{ hh }}<span class="rc-colon" :class="{ dim: now.getSeconds() % 2 === 1 }">:</span>{{ mm }}<span v-if="ampm" class="rc-ampm">{{ ampm }}</span></div>
    <div class="rc-date">{{ dateText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const now = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => { timer = setInterval(() => { now.value = new Date() }, 1000) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

// Locale decides 12/24 h (same as the stats saver's clock).
const parts = computed(() => new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit' }).formatToParts(now.value))
const hh = computed(() => parts.value.find(p => p.type === 'hour')?.value ?? '')
const mm = computed(() => parts.value.find(p => p.type === 'minute')?.value ?? '')
const ampm = computed(() => parts.value.find(p => p.type === 'dayPeriod')?.value ?? '')
const dateText = computed(() => now.value.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' }))
</script>

<style scoped>
.robot-clock { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #fff; user-select: none; }
.rc-time { font-size: clamp(56px, 13vw, 200px); font-weight: 200; letter-spacing: 0.02em; font-variant-numeric: tabular-nums; line-height: 1; text-shadow: 0 0 18px rgba(255, 255, 255, 0.35); }
.rc-colon { transition: opacity 0.4s ease; }
.rc-colon.dim { opacity: 0.25; }
.rc-ampm { font-size: 0.25em; margin-left: 0.3em; opacity: 0.7; }
.rc-date { margin-top: 0.8em; font-size: clamp(14px, 2.2vw, 32px); font-weight: 300; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; }
</style>
