import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Profile, Page, Button } from '@/types'
import apiClient from '@/api/client'

export const useDeckStore = defineStore('deck', () => {
  const currentProfile = ref<Profile | null>(null)
  const currentPageIndex = ref(0)
  const isEditMode = ref(false)
  const history = ref<Profile[]>([])
  const historyIndex = ref(-1)
  const maxHistory = 50

  const currentPage = computed(() => {
    if (!currentProfile.value || !currentProfile.value.pages.length) return null
    return currentProfile.value.pages[currentPageIndex.value]
  })

  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  function setProfile(profile: Profile) {
    currentProfile.value = profile
    currentPageIndex.value = 0
    // Reset history when loading a new profile
    history.value = [JSON.parse(JSON.stringify(profile))]
    historyIndex.value = 0
  }

  function addToHistory() {
    if (!currentProfile.value) return
    
    // Remove any future history if we're not at the end
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }
    
    // Add current state to history
    history.value.push(JSON.parse(JSON.stringify(currentProfile.value)))
    historyIndex.value++
    
    // Limit history size
    if (history.value.length > maxHistory) {
      history.value.shift()
      historyIndex.value--
    }
  }

  function undo() {
    if (!canUndo.value) return
    
    historyIndex.value--
    currentProfile.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  }

  function redo() {
    if (!canRedo.value) return
    
    historyIndex.value++
    currentProfile.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  }

  function setPage(index: number) {
    if (!currentProfile.value) return
    if (index >= 0 && index < currentProfile.value.pages.length) {
      currentPageIndex.value = index
    }
  }

  function nextPage() {
    if (!currentProfile.value) return
    if (currentPageIndex.value < currentProfile.value.pages.length - 1) {
      currentPageIndex.value++
    }
  }

  function previousPage() {
    if (currentPageIndex.value > 0) {
      currentPageIndex.value--
    }
  }

  function addPage(page: Page) {
    if (!currentProfile.value) return
    currentProfile.value.pages.push(page)
    addToHistory()
  }

  function removePage(pageId: string) {
    if (!currentProfile.value) return
    const index = currentProfile.value.pages.findIndex(p => p.id === pageId)
    if (index !== -1) {
      currentProfile.value.pages.splice(index, 1)
      if (currentPageIndex.value >= currentProfile.value.pages.length) {
        currentPageIndex.value = Math.max(0, currentProfile.value.pages.length - 1)
      }
      addToHistory()
    }
  }

  function updatePage(pageId: string, updates: Partial<Page>) {
    if (!currentProfile.value) return
    const page = currentProfile.value.pages.find(p => p.id === pageId)
    if (page) {
      Object.assign(page, updates)
      addToHistory()
    }
  }

  function addButton(button: Button) {
    if (!currentPage.value) return
    currentPage.value.buttons.push(button)
    addToHistory()
  }

  function removeButton(buttonId: string) {
    if (!currentPage.value) return
    const index = currentPage.value.buttons.findIndex(b => b.id === buttonId)
    if (index !== -1) {
      currentPage.value.buttons.splice(index, 1)
      addToHistory()
    }
  }

  function updateButton(buttonId: string, updates: Partial<Button>) {
    if (!currentPage.value) return
    const button = currentPage.value.buttons.find(b => b.id === buttonId)
    if (button) {
      Object.assign(button, updates)
      addToHistory()
    }
  }

  function getButton(buttonId: string): Button | null {
    if (!currentPage.value) return null
    return currentPage.value.buttons.find(b => b.id === buttonId) || null
  }

  function toggleEditMode() {
    isEditMode.value = !isEditMode.value
  }

  async function saveProfile(): Promise<boolean> {
    if (!currentProfile.value) return false
    
    try {
      const response = await apiClient.put(`/profiles/${currentProfile.value.id}`, currentProfile.value)
      return response.data.success
    } catch (error) {
      console.error('Failed to save profile:', error)
      return false
    }
  }

  async function executeButtonAction(button: Button) {
    if (!button.action) return
    
    try {
      const response = await apiClient.post('/actions/execute', {
        action: button.action
      })
      return response.data
    } catch (error) {
      console.error('Failed to execute action:', error)
      return { success: false, message: 'Failed to execute action' }
    }
  }

  return {
    currentProfile,
    currentPage,
    currentPageIndex,
    isEditMode,
    canUndo,
    canRedo,
    setProfile,
    addToHistory,
    undo,
    redo,
    setPage,
    nextPage,
    previousPage,
    addPage,
    removePage,
    updatePage,
    addButton,
    removeButton,
    updateButton,
    getButton,
    toggleEditMode,
    saveProfile,
    executeButtonAction
  }
})

