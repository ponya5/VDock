import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Profile, Page, Button, Scene, ActionResult } from '@/types'
import apiClient from '@/api/client'
import socketClient from '@/api/socket'
import { useSettingsStore } from './settings'
import {
  createDefaultScene,
  createFactoryIdeScene,
  isFactoryIdeSceneName,
  isUntouchedLegacyCursorScene
} from '@/utils/defaultProfile'
import { useMobileViewport } from '@/utils/mobileViewport'

export const LAST_PROFILE_STORAGE_KEY = 'vdock_last_profile'

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

    // Every profile must have exactly one isDefault scene. Older/existing profiles
    // won't have one yet — append the factory default scene. Appending (rather than
    // prepending) keeps scene index 0 pointing at whatever scene was already first,
    // so migration never silently swaps which scene an existing user lands on.
    if (!migratedProfile.scenes.some((s) => s.isDefault)) {
      migratedProfile.scenes = [...migratedProfile.scenes, createDefaultScene()]
    }

    // DL-066 follow-up: a "Cursor" scene created before the layout fix still
    // carries the old Composer/Chat/Palette/Accept/Reject/Quick Open button
    // set on a mis-sized grid. Auto-upgrade it in place, but only while it's
    // byte-for-byte the untouched factory scene — this must never overwrite
    // a scene the user has actually customised (see
    // `isUntouchedLegacyCursorScene`). A hand-edited Cursor scene keeps
    // SceneEditor's explicit "Reset to Default" as its own opt-in path.
    migratedProfile.scenes = migratedProfile.scenes.map((scene) => {
      if (!isUntouchedLegacyCursorScene(scene)) return scene
      const fresh = createFactoryIdeScene('Cursor')
      if (!fresh) return scene
      return { ...scene, pages: fresh.pages, icon: fresh.icon, color: fresh.color }
    })

    currentProfile.value = migratedProfile
    currentSceneIndex.value = 0
    currentPageIndex.value = 0
    // Reset history when loading a new profile. Loading never writes — the
    // migration above is in-memory only and rides along with the next real edit's
    // auto-save, same as migrateProfileToScenes.
    history.value = [JSON.parse(JSON.stringify(migratedProfile))]
    historyIndex.value = 0

    // Persisted here (rather than via a component-level watcher) so it's
    // updated immediately regardless of which view called setProfile —
    // e.g. ProfilesView setting a newly created/loaded profile and then
    // navigating to '/' must not be undone by DashboardView's onMounted
    // reloading a stale profile id from localStorage.
    localStorage.setItem(LAST_PROFILE_STORAGE_KEY, migratedProfile.id)
  }

  /**
   * Resets the given scene back to its factory layout — either the single
   * `isDefault` Media scene (`createDefaultScene`) or one of the built-in IDE
   * scenes identified by name (Claude Code / Cursor, DL-066 follow-up). No-ops
   * for anything else — this must never be able to wipe a user's custom scene.
   */
  function resetScene(sceneId: string) {
    if (!currentProfile.value) return
    const scene = currentProfile.value.scenes.find((s) => s.id === sceneId)
    if (!scene) return

    const fresh = scene.isDefault
      ? createDefaultScene()
      : isFactoryIdeSceneName(scene.name)
        ? createFactoryIdeScene(scene.name)
        : null
    if (!fresh) return

    scene.name = fresh.name
    scene.icon = fresh.icon
    scene.color = fresh.color
    scene.pages = fresh.pages
    scene.buttonSize = fresh.buttonSize
    scene.overlay_style = fresh.overlay_style
    scene.transition_style = fresh.transition_style
    scene.stagger_order = fresh.stagger_order

    addToHistory()
    saveProfile()
  }

  function migrateProfileToScenes(profile: Profile): Profile {
            
    // If profile already has scenes, return as-is
    if (profile.scenes && profile.scenes.length > 0) {
                        // Ensure dockedButtons exists - preserve existing if present
      if (!profile.dockedButtons) {
        profile.dockedButtons = []
              } else {
              }
      return profile
    }

        // Migrate from old pages structure to scenes structure
    const migratedProfile = { ...profile }
    
    // PRESERVE existing dockedButtons or create empty array
    migratedProfile.dockedButtons = profile.dockedButtons || []
        
    if (profile.pages && profile.pages.length > 0) {
            // Create a default scene with all existing pages
      migratedProfile.scenes = [{
        id: `scene_${Date.now()}`,
        name: 'Default Scene',
        pages: profile.pages
      }]
      // Remove old pages property
      delete (migratedProfile as any).pages
    } else {
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
      // Auto-save profile after removing page, matching addPage/updatePage
      saveProfile()
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

  async function applyGlobalButtonStyle(updates: { animation?: string; iconLoop?: string; effect?: string }): Promise<boolean> {
    if (!currentProfile.value) return false

    const applyToButton = (button: Button) => {
      if (updates.animation !== undefined) {
        button.style = {
          ...button.style,
          animation: updates.animation === 'none' ? undefined : (updates.animation as any)
        }
        // layers.behaviour takes priority over style.animation in DeckButton's
        // buttonClasses (`layers?.behaviour ?? style?.animation`), so a button
        // seeded with a behaviour (e.g. defaultProfile's Volume Down/Previous)
        // would otherwise silently ignore this global animation choice.
        if (button.layers?.behaviour) {
          button.layers = { ...button.layers, behaviour: undefined }
        }
      }
      if (updates.iconLoop !== undefined) {
        const existingIcon = button.layers?.icon
        const iconType = existingIcon?.type ?? (button.icon_type as any) ?? 'fontawesome'
        const iconValue = existingIcon?.value ?? button.icon ?? 'star'
        button.layers = {
          ...button.layers,
          icon: updates.iconLoop === 'none'
            ? (existingIcon ? { ...existingIcon, loop: undefined } : undefined)
            : { type: iconType, value: iconValue, loop: updates.iconLoop as any, size: existingIcon?.size }
        }
      }
      if (updates.effect !== undefined) {
        button.layers = {
          ...button.layers,
          effect: updates.effect === 'none' ? undefined : { type: updates.effect as any, tint: 'brand' }
        }
      }
    }

    for (const scene of currentProfile.value.scenes) {
      for (const page of scene.pages) {
        for (const button of page.buttons) {
          applyToButton(button)
        }
      }
    }
    // Docked sidebar buttons live outside scene/pages — without this they
    // keep their old design while the grid changes, and the always-visible
    // sidebar makes the apply look broken.
    for (const button of currentProfile.value.dockedButtons ?? []) {
      applyToButton(button)
    }

    addToHistory()
    // Awaited (unlike the fire-and-forget saveProfile() calls elsewhere in
    // this store) so callers can safely tell other open VDock windows to
    // refresh only once the change has actually reached the backend —
    // otherwise a same-tick refresh request could race the PUT and pull
    // back stale data. Returned so a failed save can't masquerade as
    // "applied" in the caller's toast.
    return await saveProfile()
  }

  function toggleEditMode() {
    // Phones are a control surface only — every edit-mode affordance routes
    // through this function, so blocking entry here covers the header
    // button, long-press gestures, and any future caller. Toggling OFF is
    // always allowed in case a session was already in edit mode.
    if (!isEditMode.value && useMobileViewport().isMobileViewport.value) return
    isEditMode.value = !isEditMode.value
  }

  // Last save failure, surfaced by callers that report save errors — the
  // boolean alone can't distinguish "backend down" from a 500.
  const lastProfileSaveError = ref<string | null>(null)

  async function saveProfile(): Promise<boolean> {
    if (!currentProfile.value) return false

    lastProfileSaveError.value = null
    try {
            const response = await apiClient.put(`/profiles/${currentProfile.value.id}`, currentProfile.value)
            if (!response.data.success) {
              lastProfileSaveError.value = response.data.error || 'The server reported the save as failed.'
            }
            return response.data.success
    } catch (error: any) {
      console.error('Failed to save profile:', error)
      const status = error?.response?.status
      const detail = error?.response?.data?.error || error?.message
      lastProfileSaveError.value = status ? `HTTP ${status}${detail ? ` — ${detail}` : ''}` : (detail || 'Server unreachable')
      return false
    }
  }

  /**
   * Resolve when a background action finishes.
   *
   * Polling is the primary channel, not a fallback. The backend also emits an
   * `action_job` event, but on the current server stack (Flask-SocketIO in
   * threading mode behind Werkzeug) events emitted from an HTTP handler or a
   * background thread never reach clients -- only those emitted from inside a
   * Socket.IO handler do. The listener is kept because it costs nothing and
   * starts working the moment the server runs under an async worker; until
   * then the poll is what actually resolves this.
   */
  function awaitActionJob(jobId: string, actionType: string): Promise<ActionResult> {
    return new Promise((resolve) => {
      let settled = false

      const finish = (result: ActionResult) => {
        if (settled) return
        settled = true
        socketClient.off('action_job', onEvent)
        clearInterval(poll)
        clearTimeout(giveUp)
        resolve(result)
      }

      const onEvent = (payload: any) => {
        if (payload?.job_id !== jobId) return
        if (payload.status === 'running') return
        finish(payload.result ?? { success: false, message: 'Action finished' })
      }

      socketClient.on('action_job', onEvent)

      const checkOnce = async () => {
        try {
          const { data } = await apiClient.get(`/actions/jobs/${jobId}`)
          if (data?.status && data.status !== 'running') {
            finish(data.result ?? { success: false, message: 'Action finished' })
          }
        } catch {
          // Transient; the next tick will try again.
        }
      }

      // Short actions finish in well under a second, so check straight away
      // rather than making every press wait out a full interval.
      const poll = setInterval(checkOnce, 700)
      void checkOnce()

      const giveUp = setTimeout(() => {
        finish({
          success: false,
          message: `${actionType} is still running`,
          data: { job_id: jobId }
        })
      }, 10 * 60 * 1000)
    })
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

    if (button.action.type === 'goto_page') {
      // Pages are 1-based in the UI and 0-based in the store.
      const requested = Number(button.action.config?.page ?? 1)
      const pageCount = currentScene.value?.pages?.length ?? 0
      const index = Math.round(requested) - 1

      if (!Number.isFinite(requested) || index < 0 || index >= pageCount) {
        return {
          success: false,
          message: `Page ${requested} does not exist in this scene`
        }
      }
      setPage(index)
      return { success: true, message: `Page ${index + 1}` }
    }

    if (button.action.type === 'next_scene') {
      nextScene()
      return { success: true, message: 'Next scene' }
    }

    if (button.action.type === 'previous_scene') {
      previousScene()
      return { success: true, message: 'Previous scene' }
    }

    if (button.action.type === 'switch_scene') {
      const wanted = String(button.action.config?.scene ?? '').trim().toLowerCase()
      const scenes = currentProfile.value?.scenes ?? []
      const index = scenes.findIndex(s => s.name.trim().toLowerCase() === wanted)

      if (index === -1) {
        return {
          success: false,
          message: wanted
            ? `No scene named "${button.action.config?.scene}"`
            : 'No scene configured for this button'
        }
      }
      setScene(index)
      return { success: true, message: `Scene: ${scenes[index].name}` }
    }
    
    return executeAction(button.action, button.id)
  }

  /**
   * Dispatch any action object (a button's release_action, a slider's live
   * value push) with an owning button id for state/toast attribution.
   */
  async function executeAction(action: { type: string; config: Record<string, any> }, buttonId: string) {
    try {
      const response = await apiClient.post('/actions/execute', {
        action,
        button_id: buttonId
      })

      // A long action (a Claude Code prompt, a gh command) cannot finish
      // inside the request -- the backend runs it in the background and
      // returns 202 with a job id. Wait for the `action_job` event instead of
      // letting axios time out at 30s while the work carries on invisibly.
      if (response.data?.pending && response.data.job_id) {
        return await awaitActionJob(response.data.job_id, action.type)
      }

      // Handle fullscreen action locally
      if (action.type === 'system_control' &&
          action.config?.action === 'fullscreen' &&
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
    // Only check collisions with enabled buttons - disabled buttons don't occupy space
    const hasCollision = currentPage.value.buttons.some(existingButton => {
      if (!existingButton.enabled) return false // Skip disabled buttons
      return checkButtonCollision(button, existingButton)
    })
    
    if (hasCollision) {
      console.warn('Position already occupied:', button.position)
      return
    }
    
    currentPage.value.buttons.push(button)
        addToHistory()
    // Auto-save profile after adding button
    saveProfile()
  }

  function moveButton(buttonId: string, newPosition: { row: number; col: number }) {
    if (!currentPage.value) return
    
    const button = currentPage.value.buttons.find(b => b.id === buttonId)
    if (!button) return
    
    // Create a temporary button with the new position to check for collisions
    const tempButton = { ...button, position: newPosition }
    
    // Check if new position is already occupied (including multi-cell buttons)
    // Only check collisions with enabled buttons - disabled buttons don't occupy space
    const hasCollision = currentPage.value.buttons.some(existingButton => {
      if (existingButton.id === buttonId) return false
      if (!existingButton.enabled) return false // Skip disabled buttons
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
      }

  /**
   * Exchange two buttons' positions atomically. Two sequential moveButton calls
   * can't express a swap — the first move always collides with the button that
   * hasn't left yet — so touch drag-to-reorder needs this as one operation.
   * Sizes may differ, so the swapped placements are still validated against
   * the grid bounds and every other button.
   */
  function swapButtons(id1: string, id2: string) {
    if (!currentPage.value || id1 === id2) return false
    const a = currentPage.value.buttons.find(b => b.id === id1)
    const b = currentPage.value.buttons.find(b => b.id === id2)
    if (!a || !b) return false

    const posA = { ...a.position }
    const posB = { ...b.position }
    const testA = { ...a, position: posB }
    const testB = { ...b, position: posA }

    const { rows, cols } = currentPage.value.grid_config
    const inBounds = (btn: Button) =>
      btn.position.row >= 0 && btn.position.col >= 0 &&
      btn.position.row + btn.size.rows <= rows &&
      btn.position.col + btn.size.cols <= cols
    if (!inBounds(testA) || !inBounds(testB)) return false

    // Swapped footprints must not overlap each other or any third button.
    if (checkButtonCollision(testA, testB)) return false
    const collidesThird = (btn: Button) =>
      currentPage.value!.buttons.some(other =>
        other.id !== id1 && other.id !== id2 && other.enabled && checkButtonCollision(btn, other)
      )
    if (collidesThird(testA) || collidesThird(testB)) return false

    a.position = posB
    b.position = posA
    addToHistory()
    saveProfile()
    return true
  }

  /**
   * Merge two horizontally adjacent slider buttons into one wide slider.
   * The left button keeps its config/style and absorbs the right button's
   * columns; the right button is removed. One history entry, so undo
   * restores both buttons in a single step.
   */
  function mergeSliderButtons(leftId: string, rightId: string) {
    if (!currentPage.value) return false
    const left = currentPage.value.buttons.find(b => b.id === leftId)
    const right = currentPage.value.buttons.find(b => b.id === rightId)
    if (!left || !right) return false
    if (left.action?.type !== 'slider' || right.action?.type !== 'slider') return false

    const adjacent =
      left.position.row === right.position.row &&
      left.size.rows === right.size.rows &&
      right.position.col === left.position.col + left.size.cols
    if (!adjacent) return false

    left.size = { ...left.size, cols: left.size.cols + right.size.cols }
    currentPage.value.buttons.splice(
      currentPage.value.buttons.findIndex(b => b.id === rightId), 1
    )
    addToHistory()
    saveProfile()
    return true
  }

  /**
   * Grow a slider one column to the right. The target cell must be inside the
   * grid and free across every row the slider spans; if it holds a same-height
   * slider this becomes a merge. One history entry.
   */
  function expandSliderButton(id: string) {
    const page = currentPage.value
    const btn = page?.buttons.find(b => b.id === id)
    if (!page || !btn || btn.action?.type !== 'slider') return false

    const cols = page.grid_config.cols
    const nextCol = btn.position.col + btn.size.cols
    if (nextCol >= cols) return false

    for (let r = btn.position.row; r < btn.position.row + btn.size.rows; r++) {
      const occupant = page.buttons.find(b =>
        b.enabled &&
        b.id !== id &&
        b.position.col <= nextCol &&
        nextCol < b.position.col + b.size.cols &&
        b.position.row <= r &&
        r < b.position.row + b.size.rows
      )
      if (!occupant) continue
      // Occupied: only mergeable when it's a same-top, same-height slider
      if (
        occupant.action?.type === 'slider' &&
        occupant.position.row === btn.position.row &&
        occupant.size.rows === btn.size.rows &&
        occupant.position.col === nextCol
      ) {
        return mergeSliderButtons(id, occupant.id)
      }
      return false
    }

    btn.size = { ...btn.size, cols: btn.size.cols + 1 }
    addToHistory()
    saveProfile()
    return true
  }

  /** Narrow a wide slider back by one column (rightmost column freed). */
  function shrinkSliderButton(id: string) {
    const btn = currentPage.value?.buttons.find(b => b.id === id)
    if (!btn || btn.action?.type !== 'slider' || btn.size.cols <= 1) return false
    btn.size = { ...btn.size, cols: btn.size.cols - 1 }
    addToHistory()
    saveProfile()
    return true
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
    resetScene,
    setPage,
    nextPage,
    previousPage,
    addPage,
    removePage,
    updatePage,
    addButton,
    removeButton,
    moveButton,
    swapButtons,
    mergeSliderButtons,
    expandSliderButton,
    shrinkSliderButton,
    updateButton,
    getButton,
    applyGlobalButtonStyle,
    toggleEditMode,
    saveProfile,
    lastProfileSaveError,
    executeButtonAction,
    executeAction
  }
})

