import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Profile, Page, Button, Scene } from '@/types'
import apiClient from '@/api/client'
import { useSettingsStore } from './settings'

export const useDashboardStore = defineStore('dashboard', () => {
  const currentProfile = ref<Profile | null>(null)
  const currentSceneIndex = ref(0)
  const currentPageIndex = ref(0)
  const isEditMode = ref(false)
  const history = ref<Profile[]>([])
  const historyIndex = ref(-1)
  const maxHistory = 50

  const currentScene = computed(() => {
    if (!currentProfile.value || !currentProfile.value.scenes.length) return null
    return currentProfile.value.scenes[currentSceneIndex.value]
  })

  const currentPage = computed(() => {
    if (!currentScene.value || !currentScene.value.pages.length) return null
    return currentScene.value.pages[currentPageIndex.value]
  })

  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  function setProfile(profile: Profile) {
    // Migrate old profiles from pages to scenes structure
    const migratedProfile = migrateProfileToScenes(profile)
    
    currentProfile.value = migratedProfile
    currentSceneIndex.value = 0
    currentPageIndex.value = 0
    // Reset history when loading a new profile
    history.value = [JSON.parse(JSON.stringify(migratedProfile))]
    historyIndex.value = 0
  }

  function migrateProfileToScenes(profile: Profile): Profile {
    console.log('DashboardStore: migrating profile', profile)
    console.log('DashboardStore: scenes count:', profile.scenes?.length)
    console.log('DashboardStore: scenes data:', JSON.stringify(profile.scenes, null, 2))
    
    // If profile already has scenes, return as-is
    if (profile.scenes && profile.scenes.length > 0) {
      console.log('DashboardStore: profile already has scenes')
      console.log('DashboardStore: scene 0 pages:', profile.scenes[0]?.pages?.length)
      console.log('DashboardStore: scene 0 page 0 buttons:', profile.scenes[0]?.pages?.[0]?.buttons?.length)
      // Ensure dockedButtons exists - preserve existing if present
      if (!profile.dockedButtons) {
        profile.dockedButtons = []
        console.log('DashboardStore: added empty dockedButtons array')
      } else {
        console.log('DashboardStore: profile already has dockedButtons', profile.dockedButtons.length)
      }
      return profile
    }

    console.log('DashboardStore: migrating from pages to scenes')
    // Migrate from old pages structure to scenes structure
    const migratedProfile = { ...profile }
    
    // PRESERVE existing dockedButtons or create empty array
    migratedProfile.dockedButtons = profile.dockedButtons || []
    console.log('DashboardStore: preserved/initialized dockedButtons', migratedProfile.dockedButtons.length)
    
    if (profile.pages && profile.pages.length > 0) {
      console.log('DashboardStore: creating scene from existing pages', profile.pages.length)
      // Create a default scene with all existing pages
      migratedProfile.scenes = [{
        id: `scene_${Date.now()}`,
        name: 'Default Scene',
        pages: profile.pages
      }]
      // Remove old pages property
      delete (migratedProfile as any).pages
    } else {
      console.log('DashboardStore: creating empty scene structure')
      // Create empty scene structure
      migratedProfile.scenes = [{
        id: `scene_${Date.now()}`,
        name: 'Default Scene',
        pages: [{
          id: `page_${Date.now()}`,
          name: 'Page 1',
          buttons: [],
          grid_config: { rows: 4, cols: 5 }
        }]
      }]
    }

    console.log('DashboardStore: migrated profile', migratedProfile)
    return migratedProfile
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

  function setScene(index: number) {
    if (!currentProfile.value) return
    if (index >= 0 && index < currentProfile.value.scenes.length) {
      currentSceneIndex.value = index
      currentPageIndex.value = 0 // Reset to first page of new scene
    }
  }

  function nextScene() {
    if (!currentProfile.value) return
    if (currentSceneIndex.value < currentProfile.value.scenes.length - 1) {
      currentSceneIndex.value++
      currentPageIndex.value = 0
    }
  }

  function previousScene() {
    if (currentSceneIndex.value > 0) {
      currentSceneIndex.value--
      currentPageIndex.value = 0
    }
  }

  function setPage(index: number) {
    if (!currentScene.value) return
    if (index >= 0 && index < currentScene.value.pages.length) {
      currentPageIndex.value = index
    }
  }

  function nextPage() {
    if (!currentScene.value) return
    if (currentPageIndex.value < currentScene.value.pages.length - 1) {
      currentPageIndex.value++
    } else {
      // Circular navigation: go back to first page
      currentPageIndex.value = 0
    }
  }

  function previousPage() {
    if (currentPageIndex.value > 0) {
      currentPageIndex.value--
    } else {
      // Circular navigation: go to last page
      if (currentScene.value) {
        currentPageIndex.value = currentScene.value.pages.length - 1
      }
    }
  }

  function addScene(scene?: Scene) {
    if (!currentProfile.value) return
    
    if (!scene) {
      // Create a new scene with default page
      const settingsStore = useSettingsStore()
      scene = {
        id: `scene_${Date.now()}`,
        name: `Scene ${currentProfile.value.scenes.length + 1}`,
        pages: [{
          id: `page_${Date.now()}`,
          name: 'Page 1',
          buttons: [],
          grid_config: {
            rows: settingsStore.defaultGridRows,
            cols: settingsStore.defaultGridCols
          }
        }]
      }
    }
    
    currentProfile.value.scenes.push(scene)
    addToHistory()
    // Auto-save profile after adding scene
    saveProfile()
  }

  function removeScene(sceneId: string) {
    if (!currentProfile.value) return
    const index = currentProfile.value.scenes.findIndex(s => s.id === sceneId)
    if (index !== -1) {
      currentProfile.value.scenes.splice(index, 1)
      if (currentSceneIndex.value >= currentProfile.value.scenes.length) {
        currentSceneIndex.value = Math.max(0, currentProfile.value.scenes.length - 1)
      }
      addToHistory()
      // Auto-save profile after removing scene
      saveProfile()
    }
  }

  function updateScene(sceneId: string, updates: Partial<Scene>) {
    if (!currentProfile.value) return
    const scene = currentProfile.value.scenes.find(s => s.id === sceneId)
    if (scene) {
      Object.assign(scene, updates)
      addToHistory()
      // Auto-save profile after updating scene
      saveProfile()
    }
  }

  function addPage(page?: Page) {
    if (!currentScene.value) return

    const settingsStore = useSettingsStore()

    if (!page) {
      // Create a new page with default grid size from settings
      page = {
        id: `page_${Date.now()}`,
        name: `Page ${currentScene.value.pages.length + 1}`,
        buttons: [],
        grid_config: {
          rows: settingsStore.defaultGridRows,
          cols: settingsStore.defaultGridCols
        }
      }
    }

    currentScene.value.pages.push(page)
    addToHistory()
    // Auto-save profile after adding page
    saveProfile()
  }

  function removePage(pageId: string) {
    if (!currentScene.value) return
    const index = currentScene.value.pages.findIndex(p => p.id === pageId)
    if (index !== -1) {
      currentScene.value.pages.splice(index, 1)
      if (currentPageIndex.value >= currentScene.value.pages.length) {
        currentPageIndex.value = Math.max(0, currentScene.value.pages.length - 1)
      }
      addToHistory()
    }
  }

  function updatePage(pageId: string, updates: Partial<Page>) {
    if (!currentScene.value) return
    const page = currentScene.value.pages.find(p => p.id === pageId)
    if (page) {
      Object.assign(page, updates)
      addToHistory()
      // Auto-save profile after updating page
      saveProfile()
    }
  }

  function addButton(button: Button) {
    if (!currentPage.value) return
    currentPage.value.buttons.push(button)
    addToHistory()
    // Auto-save profile after adding button
    saveProfile()
  }

  function removeButton(buttonId: string) {
    if (!currentPage.value) return
    const index = currentPage.value.buttons.findIndex(b => b.id === buttonId)
    if (index !== -1) {
      currentPage.value.buttons.splice(index, 1)
      addToHistory()
      // Auto-save profile after removing button
      saveProfile()
    }
  }

  function updateButton(buttonId: string, updates: Partial<Button>) {
    if (!currentPage.value) return
    const button = currentPage.value.buttons.find(b => b.id === buttonId)
    if (button) {
      Object.assign(button, updates)
      addToHistory()
      // Auto-save profile after updating button
      saveProfile()
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
      console.log('DashboardStore: Saving profile...', {
        id: currentProfile.value.id,
        scenes: currentProfile.value.scenes.length,
        dockedButtons: currentProfile.value.dockedButtons?.length || 0
      })
      const response = await apiClient.put(`/profiles/${currentProfile.value.id}`, currentProfile.value)
      console.log('DashboardStore: Profile saved successfully', response.data.success)
      return response.data.success
    } catch (error) {
      console.error('Failed to save profile:', error)
      return false
    }
  }

  async function executeButtonAction(button: Button) {
    if (!button.action) return
    
    // Handle page navigation actions locally (frontend-only)
    if (button.action.type === 'next_page') {
      nextPage()
      return { success: true, message: 'Navigated to next page' }
    }
    
    if (button.action.type === 'previous_page') {
      previousPage()
      return { success: true, message: 'Navigated to previous page' }
    }
    
    if (button.action.type === 'home_page') {
      setPage(0)
      return { success: true, message: 'Navigated to home page' }
    }
    
    try {
      const response = await apiClient.post('/actions/execute', {
        action: button.action
      })
      
      // Handle fullscreen action locally
      if (button.action.type === 'system_control' && 
          button.action.config?.action === 'fullscreen' && 
          response.data.success) {
        toggleFullscreen()
      }
      
      return response.data
    } catch (error) {
      console.error('Failed to execute action:', error)
      return { success: false, message: 'Failed to execute action' }
    }
  }

  function toggleFullscreen() {
    try {
      if (!document.fullscreenElement) {
        // Enter fullscreen
        document.documentElement.requestFullscreen()
      } else {
        // Exit fullscreen
        document.exitFullscreen()
      }
    } catch (error) {
      console.error('Failed to toggle fullscreen:', error)
    }
  }

  function checkButtonCollision(button1: Button, button2: Button): boolean {
    const { row: row1, col: col1 } = button1.position
    const { rows: rows1, cols: cols1 } = button1.size
    const { row: row2, col: col2 } = button2.position
    const { rows: rows2, cols: cols2 } = button2.size
    
    // Check if rectangles overlap
    return !(
      row1 + rows1 <= row2 ||
      row2 + rows2 <= row1 ||
      col1 + cols1 <= col2 ||
      col2 + cols2 <= col1
    )
  }

  function addButton(button: Button) {
    if (!currentPage.value) return
    
    // Check if position is already occupied (including multi-cell buttons)
    const hasCollision = currentPage.value.buttons.some(existingButton => {
      return checkButtonCollision(button, existingButton)
    })
    
    if (hasCollision) {
      console.warn('Position already occupied:', button.position)
      return
    }
    
    currentPage.value.buttons.push(button)
    console.log('Added button:', button)
  }

  function moveButton(buttonId: string, newPosition: { row: number; col: number }) {
    if (!currentPage.value) return
    
    const button = currentPage.value.buttons.find(b => b.id === buttonId)
    if (!button) return
    
    // Create a temporary button with the new position to check for collisions
    const tempButton = { ...button, position: newPosition }
    
    // Check if new position is already occupied (including multi-cell buttons)
    const hasCollision = currentPage.value.buttons.some(existingButton => {
      if (existingButton.id === buttonId) return false
      return checkButtonCollision(tempButton, existingButton)
    })
    
    if (hasCollision) {
      console.warn('New position already occupied:', newPosition)
      return
    }
    
    button.position = newPosition
    addToHistory()
    // Auto-save profile after moving button
    saveProfile()
    console.log('Moved button:', buttonId, 'to:', newPosition)
  }

  return {
    currentProfile,
    currentScene,
    currentPage,
    currentSceneIndex,
    currentPageIndex,
    isEditMode,
    canUndo,
    canRedo,
    setProfile,
    addToHistory,
    undo,
    redo,
    setScene,
    nextScene,
    previousScene,
    addScene,
    removeScene,
    updateScene,
    setPage,
    nextPage,
    previousPage,
    addPage,
    removePage,
    updatePage,
    addButton,
    removeButton,
    moveButton,
    updateButton,
    getButton,
    toggleEditMode,
    saveProfile,
    executeButtonAction
  }
})

