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
          <FontAwesomeIcon 
            :icon="profile.icon ? parseIcon(profile.icon) : ['fas', 'folder']" 
          />
        </div>

        <div class="profile-info">
          <h3>{{ profile.name }}</h3>
          <p>{{ profile.description || 'No description' }}</p>
          <span class="profile-meta">{{ profile.page_count }} pages</span>
        </div>

        <div class="profile-actions">
          <button class="btn btn-primary" @click="loadProfile(profile.id)">
            <FontAwesomeIcon :icon="['fas', 'play']" /> Load
          </button>
          <button class="btn btn-secondary" @click="duplicateProfile(profile.id)">
            <FontAwesomeIcon :icon="['fas', 'copy']" />
          </button>
          <button class="btn btn-secondary" @click="exportProfile(profile.id)">
            <FontAwesomeIcon :icon="['fas', 'download']" />
          </button>
          <button class="btn btn-danger" @click="confirmDelete(profile.id)">
            <FontAwesomeIcon :icon="['fas', 'trash']" />
          </button>
        </div>
      </div>
    </div>

    <!-- Create Profile Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h2>Create New Profile</h2>
        <div class="form-group">
          <label>Name</label>
          <input v-model="newProfileName" type="text" class="input" placeholder="Profile name" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="newProfileDescription" class="textarea" placeholder="Optional description"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
          <button class="btn btn-primary" @click="createProfile" :disabled="!newProfileName">
            Create
          </button>
        </div>
      </div>
    </div>

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
import { useDeckStore } from '@/stores/deck'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const profilesStore = useProfilesStore()
const deckStore = useDeckStore()

const showCreateModal = ref(false)
const newProfileName = ref('')
const newProfileDescription = ref('')
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
    deckStore.setProfile(profile)
    router.push('/')
  }
}

async function createProfile() {
  if (!newProfileName.value) return

  const profile = await profilesStore.createProfile({
    name: newProfileName.value,
    description: newProfileDescription.value
  })

  if (profile) {
    showCreateModal.value = false
    newProfileName.value = ''
    newProfileDescription.value = ''
    
    // Optionally load the new profile
    deckStore.setProfile(profile)
    router.push('/')
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
  flex-wrap: wrap;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}
</style>

