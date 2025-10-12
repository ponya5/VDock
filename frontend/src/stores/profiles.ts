import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Profile } from '@/types'
import apiClient from '@/api/client'

interface ProfileSummary {
  id: string
  name: string
  description: string
  icon?: string
  theme: string
  page_count: number
}

export const useProfilesStore = defineStore('profiles', () => {
  const profiles = ref<ProfileSummary[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadProfiles() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/profiles')
      profiles.value = response.data.profiles
    } catch (err) {
      error.value = 'Failed to load profiles'
      console.error('Failed to load profiles:', err)
    } finally {
      loading.value = false
    }
  }

  async function getProfile(profileId: string): Promise<Profile | null> {
    try {
      const response = await apiClient.get(`/profiles/${profileId}`)
      return response.data.profile
    } catch (err) {
      console.error('Failed to get profile:', err)
      return null
    }
  }

  async function createProfile(data: { name: string; description?: string; theme?: string }): Promise<Profile | null> {
    try {
      const response = await apiClient.post('/profiles', data)
      if (response.data.success) {
        await loadProfiles()
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to create profile:', err)
      return null
    }
  }

  async function deleteProfile(profileId: string): Promise<boolean> {
    try {
      const response = await apiClient.delete(`/profiles/${profileId}`)
      if (response.data.success) {
        await loadProfiles()
        return true
      }
      return false
    } catch (err) {
      console.error('Failed to delete profile:', err)
      return false
    }
  }

  async function duplicateProfile(profileId: string): Promise<Profile | null> {
    try {
      const response = await apiClient.post(`/profiles/${profileId}/duplicate`)
      if (response.data.success) {
        await loadProfiles()
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to duplicate profile:', err)
      return null
    }
  }

  async function exportProfile(profileId: string): Promise<Profile | null> {
    try {
      const response = await apiClient.get(`/profiles/export/${profileId}`)
      if (response.data.success) {
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to export profile:', err)
      return null
    }
  }

  async function importProfile(profileData: Profile): Promise<Profile | null> {
    try {
      const response = await apiClient.post('/profiles/import', { profile: profileData })
      if (response.data.success) {
        await loadProfiles()
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to import profile:', err)
      return null
    }
  }

  return {
    profiles,
    loading,
    error,
    loadProfiles,
    getProfile,
    createProfile,
    deleteProfile,
    duplicateProfile,
    exportProfile,
    importProfile
  }
})

