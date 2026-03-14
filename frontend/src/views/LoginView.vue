<template>
  <div class="login-view">
    <div class="login-card card">
      <div class="login-header">
        <h1>VDock</h1>
        <p>Virtual Stream Deck</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="input"
            placeholder="Enter password"
            :disabled="loading"
            autocomplete="current-password"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button 
          type="submit" 
          class="btn btn-primary w-full"
          :disabled="loading || !password"
        >
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <div class="login-footer">
        <p>
          <small>
            First time? Use the default password from your configuration.
          </small>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!password.value) return

  loading.value = true
  error.value = ''

  try {
    const success = await authStore.login(password.value)
    if (success) {
      router.push('/')
    } else {
      error.value = 'Invalid password'
    }
  } catch (err) {
    error.value = 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-view {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--color-background) 0%, var(--color-surface) 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  margin: var(--spacing-md);
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.login-header h1 {
  font-size: clamp(2.00rem, 2vw + 1.25rem, 3.00rem);
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: var(--spacing-xs);
}

.login-header p {
  color: var(--color-text-secondary);
  font-size: clamp(0.80rem, 2vw + 0.50rem, 1.20rem);
}

.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--color-text);
}

.error-message {
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: rgba(231, 76, 60, 0.1);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-md);
  color: var(--color-error);
  margin-bottom: var(--spacing-md);
  font-size: clamp(0.70rem, 2vw + 0.44rem, 1.05rem);
}

.login-footer {
  margin-top: var(--spacing-lg);
  text-align: center;
  color: var(--color-text-secondary);
}

.w-full {
  min-height: 48px; /* Touch target */
}

@media (max-width: 480px) {
  .login-card {
    margin: var(--spacing-sm);
    padding: var(--spacing-md);
  }
  .input {
    min-height: 48px;
  }
}
</style>

