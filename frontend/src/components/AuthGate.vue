<template>
  <Teleport to="body">
    <div v-if="locked" class="auth-gate" role="dialog" aria-modal="true" aria-label="VDock is locked">
      <div class="gate-card">
        <div class="gate-icon">
          <FontAwesomeIcon :icon="['fas', 'lock']" />
        </div>
        <h1 class="gate-title">VDock is locked</h1>
        <p class="gate-sub">Enter the deck password to continue.</p>
        <form class="gate-form" @submit.prevent="submit">
          <input
            ref="inputEl"
            v-model="password"
            type="password"
            class="gate-input"
            placeholder="Deck password"
            autocomplete="current-password"
            :disabled="busy"
          />
          <button type="submit" class="gate-btn" :disabled="busy || !password">
            <FontAwesomeIcon :icon="['fas', busy ? 'spinner' : 'arrow-right']" :spin="busy" />
            {{ busy ? 'Unlocking…' : 'Unlock' }}
          </button>
        </form>
        <p v-if="error" class="gate-error" role="alert">{{ error }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { authState, login } from '@/services/auth'

const password = ref('')
const error = ref('')
const busy = ref(false)
const inputEl = ref<HTMLInputElement | null>(null)

const locked = computed(() => authState.required && !authState.unlocked)

// Focus the field the moment the gate appears — the panel is touch-first but
// a keyboard-equipped browser shouldn't have to tap first either.
watch(locked, (isLocked) => {
  if (isLocked) nextTick(() => inputEl.value?.focus())
}, { immediate: true })

async function submit() {
  if (busy.value || !password.value) return
  busy.value = true
  error.value = ''
  const result = await login(password.value)
  busy.value = false
  if (result.ok) {
    // Reload so the whole app boots with the token attached — config,
    // socket, every service — instead of trying to re-init in place with
    // a half-loaded unauthenticated state.
    window.location.reload()
    return
  }
  error.value = result.error || 'Unlock failed'
  password.value = ''
  nextTick(() => inputEl.value?.focus())
}
</script>

<style scoped>
/* Above the agent alert (30000) — nothing interactive may sit over a lock. */
.auth-gate {
  position: fixed;
  inset: 0;
  z-index: 40000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 10, 18, 0.72);
  -webkit-backdrop-filter: blur(18px) saturate(0.8);
  backdrop-filter: blur(18px) saturate(0.8);
}

.gate-card {
  width: min(380px, calc(100vw - 32px));
  padding: clamp(24px, 4.5vh, 40px);
  border-radius: 22px;
  background: rgba(20, 24, 38, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.09);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
  text-align: center;
  animation: gate-in 0.24s ease-out;
}

@keyframes gate-in {
  from { transform: translateY(12px) scale(0.98); opacity: 0; }
  to { transform: none; opacity: 1; }
}

.gate-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 18px;
  background: rgba(122, 162, 255, 0.12);
  border: 1px solid rgba(122, 162, 255, 0.3);
  color: #7aa2ff;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.gate-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #e8ecf8;
  margin-bottom: 6px;
}

.gate-sub {
  font-size: 0.92rem;
  color: rgba(232, 236, 248, 0.55);
  margin-bottom: 20px;
}

.gate-form {
  display: flex;
  gap: 8px;
}

.gate-input {
  flex: 1;
  min-width: 0;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(0, 0, 0, 0.35);
  color: #e8ecf8;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.15s ease;
}

.gate-input:focus {
  border-color: #7aa2ff;
}

.gate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 18px;
  border-radius: 12px;
  border: none;
  background: #7aa2ff;
  color: #0a0e1c;
  font-size: 0.95rem;
  font-weight: 700;
  white-space: nowrap;
  touch-action: manipulation;
  cursor: pointer;
}

.gate-btn:disabled {
  opacity: 0.45;
  cursor: default;
}

.gate-btn:not(:disabled):active { transform: scale(0.97); }

.gate-error {
  margin-top: 12px;
  font-size: 0.88rem;
  color: #ff9d7a;
}
</style>
