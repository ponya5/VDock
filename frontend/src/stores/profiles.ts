import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Profile } from '@/types'
import apiClient from '@/api/client'

interface ProfileSummary {
  id: string
  name: string
  description: string
  icon?: string
  avatar?: string
  theme: string
  scene_count: number
}

export const useProfilesStore = defineStore('profiles', () => {
  const profiles = ref<(ProfileSummary | Profile)[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadProfiles() {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiClient.get('/profiles')
      profiles.value = response.data.profiles
    } catch (err) {
      console.error('Failed to load profiles from backend:', err)
      // Fallback: load from localStorage
      try {
        const localProfiles: Profile[] = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && key.startsWith('vdock_profile_')) {
            const profileData = localStorage.getItem(key)
            if (profileData) {
              try {
                localProfiles.push(JSON.parse(profileData))
              } catch (parseErr) {
                console.warn('Failed to parse profile from localStorage:', parseErr)
              }
            }
          }
        }
        profiles.value = localProfiles
        console.log(`Loaded ${localProfiles.length} profiles from localStorage`)
      } catch (storageErr) {
        error.value = 'Failed to load profiles'
        console.error('Failed to load profiles from localStorage:', storageErr)
      }
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

  async function exportProfile(profileId: string): Promise<Profile | null> {
    try {
      const response = await apiClient.get(`/profiles/${profileId}/export`)
      if (response.data.success) {
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to export profile:', err)
      return null
    }
  }

  async function importProfile(profileData: any): Promise<Profile | null> {
    try {
      const response = await apiClient.post('/profiles/import', profileData)
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

  async function updateProfile(profileId: string, data: Partial<Profile>): Promise<Profile | null> {
    try {
      const response = await apiClient.put(`/profiles/${profileId}`, data)
      if (response.data.success) {
        // Update local profile immediately
        const profileIndex = profiles.value.findIndex(p => p.id === profileId)
        if (profileIndex !== -1) {
          // Convert full profile to summary format for consistency
          const profileSummary = {
            id: response.data.profile.id,
            name: response.data.profile.name,
            description: response.data.profile.description,
            icon: response.data.profile.icon,
            avatar: response.data.profile.avatar,
            theme: response.data.profile.theme,
            scene_count: response.data.profile.scenes?.length || 0
          }
          // Ensure reactivity by replacing the entire array
          const updatedProfiles = [...profiles.value]
          updatedProfiles[profileIndex] = profileSummary
          profiles.value = updatedProfiles
        }
        
        // Always reload profiles to ensure consistency
        await loadProfiles()
        return response.data.profile
      }
      return null
    } catch (err) {
      console.error('Failed to update profile:', err)
      // Fallback: update local profile and save to localStorage
      const profileIndex = profiles.value.findIndex(p => p.id === profileId)
      if (profileIndex !== -1) {
        const updatedProfile = {
          ...profiles.value[profileIndex],
          ...data,
          updated_at: new Date().toISOString()
        }
        console.log('Updated profile:', updatedProfile)
        // Ensure reactivity by replacing the entire array
        const updatedProfiles = [...profiles.value]
        updatedProfiles[profileIndex] = updatedProfile
        profiles.value = updatedProfiles
        
        // Save to localStorage as backup
        try {
          localStorage.setItem(`vdock_profile_${profileId}`, JSON.stringify(updatedProfile))
        } catch (storageErr) {
          console.warn('Failed to save profile to localStorage:', storageErr)
        }
        
        // Reload profiles even in fallback mode
        await loadProfiles()
        return updatedProfile
      }
      return null
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


  return {
    profiles,
    loading,
    error,
    loadProfiles,
    getProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    duplicateProfile,
    exportProfile,
    importProfile
  }
})

