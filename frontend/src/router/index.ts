import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'

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
      component: () => import('@/views/EditView.vue')
    },
    {
      path: '/profiles',
      name: 'profiles',
      component: () => import('@/views/ProfilesView.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { canBeStandalone: true }
    },
    {
      path: '/guide',
      name: 'guide',
      component: () => import('@/views/GuideView.vue'),
      meta: { canBeStandalone: true }
    }
  ]
})

router.beforeEach((to) => {
  if (to.query.standalone === '1' && !to.meta.canBeStandalone) {
    return {
      path: '/settings',
      query: { ...to.query, standalone: '1' },
    }
  }
})

export default router
