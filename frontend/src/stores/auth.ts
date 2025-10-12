import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const isAuthenticated = computed(() => !!token.value)

  function initAuth() {
    // Check for stored token
    const storedToken = localStorage.getItem('vdock_token')
    if (storedToken) {
      token.value = storedToken
      apiClient.setAuthToken(storedToken)
    }
  }

  async function login(password: string): Promise<boolean> {
    try {
      const response = await apiClient.post('/auth/login', { password })
      if (response.data.success && response.data.token) {
        token.value = response.data.token
        localStorage.setItem('vdock_token', response.data.token)
        apiClient.setAuthToken(response.data.token)
        return true
      }
      return false
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }

  function logout() {
    token.value = null
    localStorage.removeItem('vdock_token')
    apiClient.setAuthToken(null)
  }

  async function verifyToken(): Promise<boolean> {
    if (!token.value) return false
    
    try {
      await apiClient.get('/auth/verify')
      return true
    } catch (error) {
      // Token is invalid, clear it
      logout()
      return false
    }
  }

  return {
    token,
    isAuthenticated,
    initAuth,
    login,
    logout,
    verifyToken
  }
})

