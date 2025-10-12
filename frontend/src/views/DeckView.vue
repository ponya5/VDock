<template>
  <div class="deck-view">
    <header class="deck-header">
      <div class="header-left">
        <h1>{{ currentProfile?.name || 'VDock' }}</h1>
      </div>

      <div class="header-center">
        <PageNavigation
          v-if="currentProfile && currentProfile.pages.length > 1"
          :pages="currentProfile.pages"
          :current-page="currentPageIndex"
          @previous="previousPage"
          @next="nextPage"
          @go-to="setPage"
        />
      </div>

      <div class="header-right">
        <button class="btn btn-secondary" @click="router.push('/profiles')" title="Profiles">
          <FontAwesomeIcon :icon="['fas', 'folder-open']" />
        </button>
        <button class="btn btn-secondary" @click="toggleEditMode" title="Toggle Edit Mode">
          <FontAwesomeIcon :icon="['fas', isEditMode ? 'eye' : 'edit']" />
        </button>
        <button class="btn btn-secondary" @click="router.push('/settings')" title="Settings">
          <FontAwesomeIcon :icon="['fas', 'cog']" />
        </button>
      </div>
    </header>

    <main class="deck-main" :style="mainStyle">
      <DeckGrid
        v-if="currentPage"
        :page="currentPage"
        :is-edit-mode="isEditMode"
        @button-click="handleButtonClick"
        @button-edit="handleButtonEdit"
        @button-delete="handleButtonDelete"
        @swipe-left="nextPage"
        @swipe-right="previousPage"
      />

      <div v-else class="no-profile">
        <FontAwesomeIcon :icon="['fas', 'folder-open']" class="no-profile-icon" />
        <p>No profile loaded</p>
        <button class="btn btn-primary" @click="router.push('/profiles')">
          Select Profile
        </button>
      </div>
    </main>

    <footer v-if="isEditMode" class="deck-footer">
      <div class="edit-mode-toolbar">
        <button class="btn btn-secondary" @click="undo" :disabled="!canUndo">
          <FontAwesomeIcon :icon="['fas', 'undo']" /> Undo
        </button>
        <button class="btn btn-secondary" @click="redo" :disabled="!canRedo">
          <FontAwesomeIcon :icon="['fas', 'redo']" /> Redo
        </button>
        <button class="btn btn-primary" @click="addNewButton">
          <FontAwesomeIcon :icon="['fas', 'plus']" /> Add Button
        </button>
        <button class="btn btn-success" @click="saveProfile">
          <FontAwesomeIcon :icon="['fas', 'save']" /> Save
        </button>
      </div>
    </footer>

    <!-- Button Editor Modal -->
    <ButtonEditor
      v-if="editingButton"
      :button="editingButton"
      @save="handleButtonSave"
      @close="editingButton = null"
    />

    <!-- Action Result Toast -->
    <div v-if="actionResult" class="action-toast" :class="actionResult.success ? 'success' : 'error'">
      {{ actionResult.message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useDeckStore } from '@/stores/deck'
import { useProfilesStore } from '@/stores/profiles'
import type { Button, ActionResult } from '@/types'
import DeckGrid from '@/components/DeckGrid.vue'
import PageNavigation from '@/components/PageNavigation.vue'
import ButtonEditor from '@/components/ButtonEditor.vue'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

const router = useRouter()
const deckStore = useDeckStore()
const profilesStore = useProfilesStore()

const editingButton = ref<Button | null>(null)
const actionResult = ref<ActionResult | null>(null)
let actionResultTimeout: number | null = null

const currentProfile = computed(() => deckStore.currentProfile)
const currentPage = computed(() => deckStore.currentPage)
const currentPageIndex = computed(() => deckStore.currentPageIndex)
const isEditMode = computed(() => deckStore.isEditMode)
const canUndo = computed(() => deckStore.canUndo)
const canRedo = computed(() => deckStore.canRedo)

const mainStyle = computed(() => {
  if (!currentPage.value?.background) return {}
  
  const bg = currentPage.value.background
  if (bg.type === 'solid') {
    return { backgroundColor: bg.color }
  } else if (bg.type === 'gradient' && bg.gradient) {
    return {
      background: `linear-gradient(${bg.gradient.direction || '135deg'}, ${bg.gradient.from}, ${bg.gradient.to})`
    }
  } else if (bg.type === 'image' && bg.image) {
    return {
      backgroundImage: `url(${bg.image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

onMounted(async () => {
  // Load last used profile or first available profile
  const lastProfileId = localStorage.getItem('vdock_last_profile')
  if (lastProfileId) {
    const profile = await profilesStore.getProfile(lastProfileId)
    if (profile) {
      deckStore.setProfile(profile)
      return
    }
  }

  // Load first available profile
  await profilesStore.loadProfiles()
  if (profilesStore.profiles.length > 0) {
    const profile = await profilesStore.getProfile(profilesStore.profiles[0].id)
    if (profile) {
      deckStore.setProfile(profile)
    }
  }
})

watch(currentProfile, (profile) => {
  if (profile) {
    localStorage.setItem('vdock_last_profile', profile.id)
  }
})

function toggleEditMode() {
  deckStore.toggleEditMode()
}

function setPage(index: number) {
  deckStore.setPage(index)
}

function nextPage() {
  deckStore.nextPage()
}

function previousPage() {
  deckStore.previousPage()
}

function undo() {
  deckStore.undo()
}

function redo() {
  deckStore.redo()
}

async function handleButtonClick(button: Button) {
  if (!button.action) return

  const result = await deckStore.executeButtonAction(button)
  showActionResult(result)
}

function handleButtonEdit(button: Button) {
  editingButton.value = { ...button }
}

function handleButtonDelete(buttonId: string) {
  if (confirm('Delete this button?')) {
    deckStore.removeButton(buttonId)
  }
}

function handleButtonSave(button: Button) {
  deckStore.updateButton(button.id, button)
  editingButton.value = null
}

function addNewButton() {
  // Create a new empty button
  const newButton: Button = {
    id: `btn_${Date.now()}`,
    label: 'New Button',
    shape: 'rounded',
    position: { row: 0, col: 0 },
    size: { rows: 1, cols: 1 },
    enabled: true
  }
  deckStore.addButton(newButton)
  editingButton.value = newButton
}

async function saveProfile() {
  const success = await deckStore.saveProfile()
  if (success) {
    showActionResult({ success: true, message: 'Profile saved successfully' })
  } else {
    showActionResult({ success: false, message: 'Failed to save profile' })
  }
}

function showActionResult(result: ActionResult) {
  actionResult.value = result
  
  if (actionResultTimeout) {
    clearTimeout(actionResultTimeout)
  }
  
  actionResultTimeout = setTimeout(() => {
    actionResult.value = null
  }, 3000)
}
</script>

<style scoped>
.deck-view {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.deck-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.header-left,
.header-right {
  flex: 1;
  display: flex;
  gap: var(--spacing-sm);
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-text);
}

.header-right {
  justify-content: flex-end;
}

.header-center {
  flex: 2;
  display: flex;
  justify-content: center;
}

.deck-main {
  flex: 1;
  overflow: hidden;
}

.no-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--spacing-lg);
  color: var(--color-text-secondary);
}

.no-profile-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.deck-footer {
  padding: var(--spacing-md);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.edit-mode-toolbar {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: center;
  flex-wrap: wrap;
}

.action-toast {
  position: fixed;
  bottom: var(--spacing-lg);
  right: var(--spacing-lg);
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  animation: slideUp var(--transition-normal);
  z-index: 1000;
}

.action-toast.success {
  background-color: var(--color-success);
  color: white;
}

.action-toast.error {
  background-color: var(--color-error);
  color: white;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>

