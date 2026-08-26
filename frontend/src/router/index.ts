import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import EditView from '@/views/EditView.vue'
import SettingsView from '@/views/SettingsView.vue'
import ProfilesView from '@/views/ProfilesView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/edit',
      name: 'edit',
      component: EditView
    },
    {
      path: '/profiles',
      name: 'profiles',
      component: ProfilesView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { canBeStandalone: true }
    }
  ]
})

router.beforeEach((to) => {
  if (to.query.standalone === '1' && to.path !== '/settings') {
    return {
      path: '/settings',
      query: { ...to.query, standalone: '1' },
    }
  }
})

export default router
