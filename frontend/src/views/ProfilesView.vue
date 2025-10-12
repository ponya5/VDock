<template>
  <div class="profiles-view">
    <header class="profiles-header">
      <h1>Profiles</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="showCreateModal = true">
          <FontAwesomeIcon :icon="['fas', 'plus']" /> New Profile
        </button>
        <button class="btn btn-secondary" @click="router.push('/')">
          <FontAwesomeIcon :icon="['fas', 'arrow-left']" /> Back
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <FontAwesomeIcon :icon="['fas', 'spinner']" spin class="loading-icon" />
      <p>Loading profiles...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else class="profiles-grid">
      <div
        v-for="profile in profiles"
        :key="profile.id"
        class="profile-card card"
      >
        <div class="profile-icon">
          <img 
            v-if="profile.avatar" 
            :src="profile.avatar" 
            :alt="profile.name"
            class="profile-avatar"
          />
          <FontAwesomeIcon 
            v-else
            :icon="profile.icon ? parseIcon(profile.icon) : ['fas', 'folder']" 
          />
        </div>

        <div class="profile-info">
          <h3>{{ profile.name }}</h3>
          <p>{{ profile.description || 'No description' }}</p>
          <span class="profile-meta">{{ profile.page_count }} pages</span>
        </div>

        <div class="profile-actions">
          <button class="btn btn-primary" @click="loadProfile(profile.id)" title="Load Profile">
            <FontAwesomeIcon :icon="['fas', 'play']" />
          </button>
          <button class="btn btn-secondary" @click="editProfile(profile)" title="Edit Profile">
            <FontAwesomeIcon :icon="['fas', 'edit']" />
          </button>
          <button class="btn btn-secondary" @click="duplicateProfile(profile.id)" title="Duplicate Profile">
            <FontAwesomeIcon :icon="['fas', 'copy']" />
          </button>
          <button class="btn btn-secondary" @click="exportProfile(profile.id)" title="Export Profile">
            <FontAwesomeIcon :icon="['fas', 'download']" />
          </button>
          <button class="btn btn-danger" @click="confirmDelete(profile.id)" title="Delete Profile">
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>
    </div>

    <!-- Create Profile Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal profile-creator">
        <div class="modal-header">
          <h2>Create New Profile</h2>
          <button class="close-btn" @click="showCreateModal = false">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Profile Name</label>
            <input v-model="newProfileName" type="text" class="input" placeholder="Enter profile name" />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newProfileDescription" class="textarea" placeholder="Optional description"></textarea>
          </div>

          <div class="form-group">
            <label>Avatar</label>
            <div class="avatar-selection">
              <div class="current-avatar" @click="showAvatarPicker = true">
                <img 
                  v-if="selectedAvatar" 
                  :src="selectedAvatar.url" 
                  :alt="selectedAvatar.name"
                  class="avatar-preview"
                />
                <div v-else class="avatar-placeholder">
                  <FontAwesomeIcon :icon="['fas', 'user']" />
                  <span>Choose Avatar</span>
                </div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>Theme</label>
            <select v-model="newProfileTheme" class="select">
              <option value="default">Default (Colorful)</option>
              <option value="light">Light Mode</option>
              <option value="dark">Dark Mode</option>
            </select>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
          <button class="btn btn-primary" @click="createProfile" :disabled="!newProfileName">
            Create Profile
          </button>
        </div>
      </div>

    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal profile-creator">
        <div class="modal-header">
          <h2>Edit Profile</h2>
          <button class="close-btn" @click="showEditModal = false">
            <FontAwesomeIcon :icon="['fas', 'times']" />
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>Profile Name</label>
            <input v-model="editProfileName" type="text" class="input" placeholder="Enter profile name" />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea v-model="editProfileDescription" class="textarea" placeholder="Optional description"></textarea>
          </div>

          <div class="form-group">
            <label>Avatar</label>
            <div class="avatar-selection">
              <div class="current-avatar" @click="showAvatarPicker = true">
                <img 
                  v-if="editSelectedAvatar" 
                  :src="editSelectedAvatar.url" 
                  :alt="editSelectedAvatar.name"
                  class="avatar-preview"
                />
                <img 
                  v-else-if="editingProfile?.avatar" 
                  :src="editingProfile.avatar" 
                  :alt="editingProfile.name"
                  class="avatar-preview"
                />
                <div v-else class="avatar-placeholder">
                  <FontAwesomeIcon :icon="['fas', 'user']" />
                  <span>Choose Avatar</span>
                </div>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>Theme</label>
            <select v-model="editProfileTheme" class="select">
              <option value="default">Default (Colorful)</option>
              <option value="light">Light Mode</option>
              <option value="dark">Dark Mode</option>
            </select>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
          <button class="btn btn-primary" @click="updateProfile" :disabled="!editProfileName">
            Update Profile
          </button>
        </div>
      </div>

    </div>

    <!-- Avatar Picker Modal -->
    <AvatarPicker 
      v-if="showAvatarPicker" 
      @select="handleAvatarPickerSelect" 
      @close="showAvatarPicker = false" 
    />

    <!-- Import Profile Button -->
    <div class="import-section">
      <button class="btn btn-secondary" @click="triggerImport">
        <FontAwesomeIcon :icon="['fas', 'upload']" /> Import Profile
      </button>
      <input 
        ref="fileInput" 
        type="file" 
        accept=".json" 
        style="display: none" 
        @change="handleFileImport"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProfilesStore } from '@/stores/profiles'
import { useDashboardStore } from '@/stores/dashboard'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import AvatarPicker from '@/components/AvatarPicker.vue'
import type { Avatar } from '@/assets/avatars'

const router = useRouter()
const profilesStore = useProfilesStore()
const dashboardStore = useDashboardStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showAvatarPicker = ref(false)
const newProfileName = ref('')
const newProfileDescription = ref('')
const newProfileTheme = ref('default')
const selectedAvatar = ref<Avatar | null>(null)
const editProfileName = ref('')
const editProfileDescription = ref('')
const editProfileTheme = ref('default')
const editSelectedAvatar = ref<Avatar | null>(null)
const editingProfile = ref<any>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const profiles = computed(() => profilesStore.profiles)
const loading = computed(() => profilesStore.loading)
const error = computed(() => profilesStore.error)

onMounted(() => {
  profilesStore.loadProfiles()
})

function parseIcon(iconString: string) {
  const parts = iconString.split(' ')
  if (parts.length === 2) {
    return [parts[0], parts[1].replace('fa-', '')]
  }
  return ['fas', 'folder']
}

async function loadProfile(profileId: string) {
  const profile = await profilesStore.getProfile(profileId)
  if (profile) {
    dashboardStore.setProfile(profile)
    router.push('/')
  }
}

async function createProfile() {
  if (!newProfileName.value) return

  const profile = await profilesStore.createProfile({
    name: newProfileName.value,
    description: newProfileDescription.value,
    avatar: selectedAvatar.value?.url,
    theme: newProfileTheme.value
  })

  if (profile) {
    showCreateModal.value = false
    newProfileName.value = ''
    newProfileDescription.value = ''
    newProfileTheme.value = 'default'
    selectedAvatar.value = null
    
    // Force refresh profiles list to show new profile
    await profilesStore.loadProfiles()
    
    // Optionally load the new profile
    dashboardStore.setProfile(profile)
    router.push('/')
  }
}

function handleAvatarPickerSelect(avatar: Avatar) {
  // Determine which context we're in based on which modal is open
  if (showCreateModal.value) {
    selectedAvatar.value = avatar
  } else if (showEditModal.value) {
    editSelectedAvatar.value = avatar
  }
  showAvatarPicker.value = false
}

function editProfile(profile: any) {
  console.log('Editing profile:', profile)
  console.log('Profile avatar:', profile.avatar)
  
  editingProfile.value = profile
  editProfileName.value = profile.name
  editProfileDescription.value = profile.description || ''
  editProfileTheme.value = profile.theme || 'default'
  
  // Set current avatar if exists
  if (profile.avatar) {
    console.log('Setting editSelectedAvatar with:', profile.avatar)
    editSelectedAvatar.value = {
      id: 'current',
      name: 'Current Avatar',
      url: profile.avatar,
      type: 'image',
      category: 'characters'
    }
  } else {
    console.log('No avatar found, setting editSelectedAvatar to null')
    editSelectedAvatar.value = null
  }
  
  showEditModal.value = true
}

async function updateProfile() {
  if (!editingProfile.value || !editProfileName.value) return

  const avatarUrl = editSelectedAvatar.value?.url || editingProfile.value.avatar
  console.log('Updating profile with avatar URL:', avatarUrl)
  console.log('Selected avatar:', editSelectedAvatar.value)
  console.log('Current profile avatar:', editingProfile.value.avatar)

  const updatedProfile = await profilesStore.updateProfile(editingProfile.value.id, {
    name: editProfileName.value,
    description: editProfileDescription.value,
    avatar: avatarUrl,
    theme: editProfileTheme.value
  })

  if (updatedProfile) {
    console.log('Profile updated successfully:', updatedProfile)
    showEditModal.value = false
    editingProfile.value = null
    editProfileName.value = ''
    editProfileDescription.value = ''
    editProfileTheme.value = 'default'
    editSelectedAvatar.value = null
    
    // Force refresh profiles list to show updated avatar
    await profilesStore.loadProfiles()
    console.log('Profiles reloaded:', profilesStore.profiles)
  }
}

async function duplicateProfile(profileId: string) {
  await profilesStore.duplicateProfile(profileId)
}

async function exportProfile(profileId: string) {
  const profile = await profilesStore.exportProfile(profileId)
  if (profile) {
    const blob = new Blob([JSON.stringify(profile, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${profile.name}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
}

function confirmDelete(profileId: string) {
  if (confirm('Are you sure you want to delete this profile?')) {
    profilesStore.deleteProfile(profileId)
  }
}

function triggerImport() {
  fileInput.value?.click()
}

async function handleFileImport(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    const text = await file.text()
    const profileData = JSON.parse(text)
    await profilesStore.importProfile(profileData)
  } catch (err) {
    alert('Failed to import profile: Invalid file format')
  }

  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>

<style scoped>
.profiles-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-xl);
}

.profiles-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.profiles-header h1 {
  font-size: 2rem;
  font-weight: bold;
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.loading,
.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  color: var(--color-text-secondary);
}

.loading-icon {
  font-size: 3rem;
}

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-xl);
}

.profile-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.profile-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.profile-icon {
  font-size: 3rem;
  color: var(--color-primary);
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-avatar {
  width: 60px;
  height: 60px;
  border-radius: var(--radius-full);
  object-fit: cover;
  border: 2px solid var(--color-primary);
}

.profile-info h3 {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: var(--spacing-xs);
}

.profile-info p {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-bottom: var(--spacing-sm);
}

.profile-meta {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-sm);
  background-color: var(--color-background);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.profile-actions {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: nowrap;
  justify-content: space-between;
}

.profile-actions .btn {
  flex: 1;
  min-width: 0;
  padding: var(--spacing-xs);
  font-size: 0.75rem;
  white-space: nowrap;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.import-section {
  position: fixed;
  bottom: var(--spacing-xl);
  right: var(--spacing-xl);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.profile-creator {
  width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.modal-header h2 {
  font-size: 1.5rem;
  font-weight: bold;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: var(--spacing-xs);
  transition: color var(--transition-fast);
}

.close-btn:hover {
  color: var(--color-text);
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}

.avatar-selection {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.current-avatar {
  width: 80px;
  height: 80px;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast);
  background-color: var(--color-surface);
}

.current-avatar:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-light);
}

.avatar-preview {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: var(--color-text-secondary);
  font-size: 0.7rem;
  width: 100%;
  height: 100%;
  text-align: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}
</style>

