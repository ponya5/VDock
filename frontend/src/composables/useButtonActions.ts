import { ref, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useSettingsStore } from '@/stores/settings'
import { useProfilesStore } from '@/stores/profiles'
import { useNotificationsStore } from '@/stores/notifications'
import type { Button, ActionResult } from '@/types'
import { presetRegistry, presetToButton } from '@/data/presets'

export function useButtonActions() {
  const dashboardStore = useDashboardStore()
  const settingsStore = useSettingsStore()
  const profilesStore = useProfilesStore()
  const notificationsStore = useNotificationsStore()

  const currentProfile = computed(() => dashboardStore.currentProfile)
  const currentScene = computed(() => dashboardStore.currentScene)
  const currentPage = computed(() => dashboardStore.currentPage)

  const editingButton = ref<Button | null>(null)
  const clipboardButton = ref<Button | null>(null)
  const selectedAction = ref<any>(null)

  const actionResult = ref<ActionResult | null>(null)
  let actionResultTimeout: ReturnType<typeof setTimeout> | null = null

  function showActionResult(result: ActionResult) {
    if (result.success) {
      notificationsStore.success('Action Executed', result.message)
    } else {
      notificationsStore.error(
        'Action Failed',
        result.message,
        result.data?.details || undefined
      )
    }
    
    actionResult.value = result

    if (actionResultTimeout) {
      clearTimeout(actionResultTimeout)
    }

    actionResultTimeout = setTimeout(() => {
      actionResult.value = null
    }, 3000)
  }

  function handleButtonClick(button: Button) {
    if (!button.action) return

    // Handle UI control actions locally
    if (button.action.type === 'ui_control') {
      const action = button.action.config.action
      const step = button.action.config.step || 10
      
      if (action === 'ui_brightness_up') {
        const newBrightness = Math.min(200, settingsStore.uiBrightness + step)
        settingsStore.uiBrightness = newBrightness
        showActionResult({
          success: true,
          message: `UI brightness: ${newBrightness}%`
        })
        return
      } else if (action === 'ui_brightness_down') {
        const newBrightness = Math.max(10, settingsStore.uiBrightness - step)
        settingsStore.uiBrightness = newBrightness
        showActionResult({
          success: true,
          message: `UI brightness: ${newBrightness}%`
        })
        return
      } else if (action === 'ui_brightness_set') {
        const value = button.action.config.value || 100
        settingsStore.uiBrightness = value
        showActionResult({
          success: true,
          message: `UI brightness set to ${value}%`
        })
        return
      } else if (action === 'toggle_header') {
        settingsStore.showHeader = !settingsStore.showHeader
        showActionResult({
          success: true,
          message: settingsStore.showHeader ? 'Header shown' : 'Header hidden'
        })
        return
      }
    }

    // Skip execution for display-only types
    const displayOnlyTypes = [
      'weather',
      'time_world_clock',
      'time_timer', 
      'time_countdown',
      'metric_memory',
      'metric_cpu_usage',
      'metric_cpu_frequency',
      'metric_internet_speed',
      'metric_harddisk',
      'metric_gpu_temperature',
      'metric_gpu_frequency',
      'metric_gpu_usage',
      'metric_gpu_memory_freq',
      'metric_gpu_memory_usage'
    ]

    if (displayOnlyTypes.includes(button.action.type)) {
      return
    }

    dashboardStore.executeButtonAction(button).then((result) => {
      showActionResult(result)
    })
  }

  function handleButtonEdit(button: Button) {
    editingButton.value = { ...button }
  }

  function handleButtonCopy(button: Button) {
    clipboardButton.value = { ...button }
    showActionResult({
      success: true,
      message: `Button "${button.label}" copied to clipboard`
    })
  }

  function handleButtonDelete(buttonId: string) {
    if (confirm('Are you sure you want to delete this button?')) {
      dashboardStore.removeButton(buttonId)
    }
  }

  function handleButtonMove(buttonId: string, newPosition: { row: number; col: number }) {
    dashboardStore.moveButton(buttonId, newPosition)
  }

  function handleActionDrop(action: any, position: { row: number; col: number }) {
    const button = resolveButtonForAction(action, position)
    if (button) {
      dashboardStore.addButton(button)
    }
  }

  function handlePlaceholderClick(position: { row: number; col: number }) {
    if (clipboardButton.value) {
      const newButton: Button = {
        ...clipboardButton.value,
        id: `button_${Date.now()}`,
        label: `${clipboardButton.value.label} (Copy)`,
        position: { row: position.row, col: position.col }
      }
      dashboardStore.addButton(newButton)
      showActionResult({
        success: true,
        message: `Button "${newButton.label}" pasted`
      })
    } else {
      const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const button: Button = {
        id: buttonId,
        label: 'New Button',
        icon_type: 'fontawesome',
        icon: ['fas', 'home'],
        shape: 'rounded',
        position: { row: position.row, col: position.col },
        size: { rows: 1, cols: 1 },
        style: {
          backgroundColor: '#2c3e50',
          textColor: '#ffffff'
        },
        enabled: true
      }
      editingButton.value = button
    }
  }

  function handlePlaceholderLongPress(position: { row: number; col: number }) {
    if (!dashboardStore.isEditMode) {
      dashboardStore.toggleEditMode()
    }
    const newButton: Button = {
      id: `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      position: position,
      size: { rows: 1, cols: 1 },
      enabled: true,
      shape: 'rectangle'
    }
    editingButton.value = newButton
  }

  function handleDeckButtonLongPress(button: Button) {
    if (!dashboardStore.isEditMode) {
      dashboardStore.toggleEditMode()
    }
    editingButton.value = { ...button }
  }

  function handleAddDockedButton(position: { row: number; col: number }) {
    const newButton: Button = {
      id: `docked_${Date.now()}`,
      label: 'New Button',
      secondary_label: '',
      icon: ['fas', 'star'],
      icon_type: 'fontawesome',
      media_url: null,
      media_type: null,
      shape: 'rounded',
      position: { row: position.row, col: position.col },
      size: { rows: 1, cols: 1 },
      style: {
        backgroundColor: '#3498db',
        textColor: '#ffffff'
      },
      tooltip: '',
      enabled: true
    }
    
    if (currentProfile.value) {
      const updatedProfile = {
        ...currentProfile.value,
        dockedButtons: [...(currentProfile.value.dockedButtons || []), newButton]
      }
      dashboardStore.setProfile(updatedProfile)
      dashboardStore.saveProfile().then(() => {
        showActionResult({
          success: true,
          message: `Button added to docked sidebar`
        })
      })
    }
  }

  function handleDockedButtonDelete(buttonId: string) {
    if (confirm('Are you sure you want to delete this docked button?')) {
      const updatedDockedButtons = currentProfile.value?.dockedButtons?.filter(btn => btn.id !== buttonId) || []
      if (currentProfile.value) {
        const updatedProfile = {
          ...currentProfile.value,
          dockedButtons: updatedDockedButtons
        }
        dashboardStore.setProfile(updatedProfile)
        dashboardStore.saveProfile().then(() => {
          showActionResult({
            success: true,
            message: 'Docked button deleted'
          })
        })
      }
    }
  }

  function handleDockedButtonDrop(event: DragEvent, position: { row: number; col: number }) {
    if (!event.dataTransfer) return
    try {
      const buttonData = event.dataTransfer.getData('application/vdock-button')
      if (buttonData) {
        const button = JSON.parse(buttonData)
        const dockedButton: Button = {
          ...button,
          id: `docked_${Date.now()}`,
          position: { row: position.row, col: position.col },
          size: { rows: 1, cols: 1 }
        }
        if (currentProfile.value) {
          const updatedProfile = {
            ...currentProfile.value,
            dockedButtons: [...(currentProfile.value.dockedButtons || []), dockedButton]
          }
          dashboardStore.setProfile(updatedProfile)
          showActionResult({
            success: true,
            message: `Button docked successfully`
          })
        }
      }
    } catch (err) {
      console.error('Failed to handle docked drop:', err)
      showActionResult({
        success: false,
        message: `Failed to dock button: ${err}`
      })
    }
  }

  function handleDockedPlaceholderClick(position: { row: number; col: number }) {
    if (clipboardButton.value && currentProfile.value) {
      const pastedButton: Button = {
        ...clipboardButton.value,
        id: `docked_${Date.now()}`,
        position: { row: position.row, col: position.col },
        size: { rows: 1, cols: 1 }
      }
      const updatedProfile = {
        ...currentProfile.value,
        dockedButtons: [...(currentProfile.value.dockedButtons || []), pastedButton]
      }
      dashboardStore.setProfile(updatedProfile)
      showActionResult({
        success: true,
        message: 'Button pasted to docked sidebar'
      })
    } else {
      handleAddDockedButton(position)
    }
  }

  function handleButtonSave(button: Button) {
    const isDockedButton = currentProfile.value?.dockedButtons?.some(btn => btn.id === button.id)
    if (isDockedButton) {
      const updatedDockedButtons = currentProfile.value?.dockedButtons?.map(btn => 
        btn.id === button.id ? button : btn
      ) || []
      if (currentProfile.value) {
        const updatedProfile = {
          ...currentProfile.value,
          dockedButtons: updatedDockedButtons
        }
        dashboardStore.setProfile(updatedProfile)
        dashboardStore.saveProfile().then(() => {
          showActionResult({
            success: true,
            message: `Button saved successfully`
          })
        })
      }
    } else {
      dashboardStore.updateButton(button.id, button)
      showActionResult({
        success: true,
        message: `Button saved`
      })
    }
    editingButton.value = null
  }

  function selectAction(action: any) {
    selectedAction.value = action
    if (!currentPage.value) return
    const config = currentPage.value.grid_config
    let emptyPos = null
    outer: for (let r = 0; r < config.rows; r++) {
      for (let c = 0; c < config.cols; c++) {
        const isOccupied = currentPage.value.buttons.some(b => 
          b.position.row <= r && r < b.position.row + b.size.rows &&
          b.position.col <= c && c < b.position.col + b.size.cols
        )
        if (!isOccupied) {
          emptyPos = { row: r, col: c }
          break outer
        }
      }
    }
    if (emptyPos) {
      const newButton = resolveButtonForAction(action, emptyPos)
      if (newButton && currentProfile.value && currentScene.value && currentPage.value) {
        dashboardStore.addButton(newButton)
        editingButton.value = { ...newButton }
      }
    } else {
      alert('No empty slots available on this page.')
    }
  }

  function createFallbackButton(action: any, position: { row: number; col: number }): Button {
    const buttonId = `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const baseButton: Button = {
      id: buttonId,
      label: action.name,
      icon_type: 'fontawesome',
      icon: action.icon,
      shape: 'rounded',
      position: { row: position.row, col: position.col },
      size: { rows: 1, cols: 1 },
      style: {
        backgroundColor: '#2c3e50',
        textColor: '#ffffff'
      },
      enabled: true
    }
    if (action.id === 'custom-icon') {
      return {
        ...baseButton,
        label: 'Custom Icon',
        icon_type: 'custom',
        icon: '',
        media_type: 'image',
        media_url: '',
        style: { ...baseButton.style, backgroundColor: '#2c3e50' }
      }
    }
    return baseButton
  }

  function resolveButtonForAction(action: any, position: { row: number; col: number }): Button {
    const preset = presetRegistry.find((p) => p.id === action.id || p.name === action.name)
    if (preset) {
      return presetToButton(preset, position)
    }
    return createFallbackButton(action, position)
  }

  return {
    editingButton,
    clipboardButton,
    selectedAction,
    actionResult,
    showActionResult,
    handleButtonClick,
    handleButtonEdit,
    handleButtonCopy,
    handleButtonDelete,
    handleButtonMove,
    handleActionDrop,
    handlePlaceholderClick,
    handlePlaceholderLongPress,
    handleDeckButtonLongPress,
    handleAddDockedButton,
    handleDockedButtonDelete,
    handleDockedButtonDrop,
    handleDockedPlaceholderClick,
    handleButtonSave,
    selectAction,
    resolveButtonForAction
  }
}
