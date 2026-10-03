<template>
  <div v-if="connection.status !== 'connected'" class="connection-banner" role="status" data-testid="connection-banner">
    <template v-if="connection.status === 'reconnecting'">
      <span class="cb-text">Reconnecting…</span>
    </template>
    <template v-else>
      <span class="cb-text">Can't reach VDock at {{ host }} — is the PC awake?</span>
      <button type="button" class="cb-retry" @click="socketClient.ensureConnected()">Retry</button>
    </template>
  </div>
</template>

<script setup lang="ts">
import socketClient from '@/api/socket'
import { connection } from '@/services/connection'

const host = window.location.hostname
</script>

<style scoped>
/* Overlay only: it floats above the deck so showing it never moves a key. */
.connection-banner {
  position: fixed;
  top: max(8px, env(safe-area-inset-top));
  left: 50%;
  transform: translateX(-50%);
  z-index: 9000;
  max-width: min(92vw, 520px);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(245, 165, 36, 0.5);
  background: rgba(38, 30, 13, 0.94);
  color: #ffd89e;
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
}
.cb-text { padding-right: 6px; }
.cb-retry {
  min-height: 44px;
  min-width: 64px;
  padding: 0 14px;
  border: 1px solid rgba(255, 216, 158, 0.5);
  border-radius: 999px;
  background: rgba(245, 165, 36, 0.2);
  color: #fff;
  font: inherit;
  cursor: pointer;
}
.cb-retry:active { transform: scale(0.96); }
</style>
