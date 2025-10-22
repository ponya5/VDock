import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/views/DashboardView.vue'
import EditView from '@/views/EditView.vue'
import LoginView from '@/views/LoginView.vue'
import SettingsView from '@/views/SettingsView.vue'
import ProfilesView from '@/views/ProfilesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    },
    {
      path: '/edit',
      name: 'edit',
      component: EditView,
      meta: { requiresAuth: true }
    },
    {
      path: '/profiles',
      name: 'profiles',
      component: ProfilesView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  // Check if auth is enabled from settings
  const settingsStore = await import('@/stores/settings').then(m => m.useSettingsStore())
  
  // Load server config if not already loaded
  if (!settingsStore.serverConfig) {
    await settingsStore.loadServerConfig()
  }
  
  const authEnabled = settingsStore.authEnabled

  if (authEnabled && requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login' })
  } else if (authEnabled && to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else if (!authEnabled && to.name === 'login') {
    // Skip login if auth is disabled
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router

