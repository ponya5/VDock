/**
 * Pre-configured button action templates for quick creation
 */

export interface ButtonTemplate {
  id: string
  name: string
  description: string
  icon: [string, string] // FontAwesome icon
  category: string
  action: {
    type: string
    config: any
  }
  style?: {
    backgroundColor?: string
    textColor?: string
  }
}

export const BUTTON_TEMPLATES: ButtonTemplate[] = [
  // Media Controls
  {
    id: 'media-play-pause',
    name: 'Play/Pause',
    description: 'Toggle media playback',
    icon: ['fas', 'play'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'media_play_pause' }
    },
    style: {
      backgroundColor: '#10b981',
      textColor: '#ffffff'
    }
  },
  {
    id: 'media-next',
    name: 'Next Track',
    description: 'Skip to next media',
    icon: ['fas', 'forward-step'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'media_next' }
    },
    style: {
      backgroundColor: '#10b981',
      textColor: '#ffffff'
    }
  },
  {
    id: 'media-previous',
    name: 'Previous Track',
    description: 'Go to previous media',
    icon: ['fas', 'backward-step'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'media_previous' }
    },
    style: {
      backgroundColor: '#10b981',
      textColor: '#ffffff'
    }
  },
  {
    id: 'volume-up',
    name: 'Volume Up',
    description: 'Increase system volume',
    icon: ['fas', 'volume-high'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'volume_up', step: 10 }
    },
    style: {
      backgroundColor: '#3b82f6',
      textColor: '#ffffff'
    }
  },
  {
    id: 'volume-down',
    name: 'Volume Down',
    description: 'Decrease system volume',
    icon: ['fas', 'volume-low'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'volume_down', step: 10 }
    },
    style: {
      backgroundColor: '#3b82f6',
      textColor: '#ffffff'
    }
  },
  {
    id: 'mute',
    name: 'Mute',
    description: 'Mute/unmute system audio',
    icon: ['fas', 'volume-xmark'],
    category: 'media',
    action: {
      type: 'cross_platform',
      config: { action: 'volume_mute' }
    },
    style: {
      backgroundColor: '#ef4444',
      textColor: '#ffffff'
    }
  },

  // Browser
  {
    id: 'browser-new-tab',
    name: 'New Tab',
    description: 'Open new browser tab',
    icon: ['fas', 'plus'],
    category: 'browser',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 't'] }
    },
    style: {
      backgroundColor: '#8b5cf6',
      textColor: '#ffffff'
    }
  },
  {
    id: 'browser-close-tab',
    name: 'Close Tab',
    description: 'Close current tab',
    icon: ['fas', 'xmark'],
    category: 'browser',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'w'] }
    },
    style: {
      backgroundColor: '#ef4444',
      textColor: '#ffffff'
    }
  },
  {
    id: 'browser-refresh',
    name: 'Refresh',
    description: 'Refresh current page',
    icon: ['fas', 'arrows-rotate'],
    category: 'browser',
    action: {
      type: 'hotkey',
      config: { keys: ['f5'] }
    },
    style: {
      backgroundColor: '#06b6d4',
      textColor: '#ffffff'
    }
  },

  // System
  {
    id: 'screenshot',
    name: 'Screenshot',
    description: 'Take a screenshot',
    icon: ['fas', 'camera'],
    category: 'system',
    action: {
      type: 'hotkey',
      config: { keys: ['win', 'shift', 's'] }
    },
    style: {
      backgroundColor: '#f59e0b',
      textColor: '#ffffff'
    }
  },
  {
    id: 'lock-screen',
    name: 'Lock Screen',
    description: 'Lock computer',
    icon: ['fas', 'lock'],
    category: 'system',
    action: {
      type: 'hotkey',
      config: { keys: ['win', 'l'] }
    },
    style: {
      backgroundColor: '#ef4444',
      textColor: '#ffffff'
    }
  },

  // IDE
  {
    id: 'ide-save',
    name: 'Save',
    description: 'Save current file',
    icon: ['fas', 'floppy-disk'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 's'] }
    },
    style: {
      backgroundColor: '#16a085',
      textColor: '#ffffff'
    }
  },
  {
    id: 'ide-find',
    name: 'Find',
    description: 'Open find dialog',
    icon: ['fas', 'magnifying-glass'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'f'] }
    },
    style: {
      backgroundColor: '#3b82f6',
      textColor: '#ffffff'
    }
  },
  {
    id: 'ide-run',
    name: 'Run',
    description: 'Run program/script',
    icon: ['fas', 'play'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['f5'] }
    },
    style: {
      backgroundColor: '#10b981',
      textColor: '#ffffff'
    }
  },
  {
    id: 'ide-debug',
    name: 'Debug',
    description: 'Start debugging',
    icon: ['fas', 'bug'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['f5'] }
    },
    style: {
      backgroundColor: '#ef4444',
      textColor: '#ffffff'
    }
  },
  {
    id: 'ide-terminal',
    name: 'Terminal',
    description: 'Toggle terminal',
    icon: ['fas', 'terminal'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', '`'] }
    },
    style: {
      backgroundColor: '#1e1e1e',
      textColor: '#ffffff'
    }
  },
  {
    id: 'ide-comment',
    name: 'Comment',
    description: 'Toggle line comment',
    icon: ['fas', 'comment'],
    category: 'ide',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', '/'] }
    },
    style: {
      backgroundColor: '#95a5a6',
      textColor: '#ffffff'
    }
  },

  // Productivity
  {
    id: 'copy',
    name: 'Copy',
    description: 'Copy selection',
    icon: ['fas', 'copy'],
    category: 'productivity',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'c'] }
    },
    style: {
      backgroundColor: '#6366f1',
      textColor: '#ffffff'
    }
  },
  {
    id: 'paste',
    name: 'Paste',
    description: 'Paste from clipboard',
    icon: ['fas', 'paste'],
    category: 'productivity',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'v'] }
    },
    style: {
      backgroundColor: '#6366f1',
      textColor: '#ffffff'
    }
  },
  {
    id: 'undo',
    name: 'Undo',
    description: 'Undo last action',
    icon: ['fas', 'rotate-left'],
    category: 'productivity',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'z'] }
    },
    style: {
      backgroundColor: '#8b5cf6',
      textColor: '#ffffff'
    }
  },
  {
    id: 'redo',
    name: 'Redo',
    description: 'Redo last undone action',
    icon: ['fas', 'rotate-right'],
    category: 'productivity',
    action: {
      type: 'hotkey',
      config: { keys: ['ctrl', 'y'] }
    },
    style: {
      backgroundColor: '#8b5cf6',
      textColor: '#ffffff'
    }
  }
]

export const TEMPLATE_CATEGORIES = [
  { id: 'media', name: 'Media Controls', icon: ['fas', 'music'] },
  { id: 'browser', name: 'Browser', icon: ['fas', 'globe'] },
  { id: 'system', name: 'System', icon: ['fas', 'desktop'] },
  { id: 'ide', name: 'IDE/Coding', icon: ['fas', 'code'] },
  { id: 'productivity', name: 'Productivity', icon: ['fas', 'briefcase'] }
]

export function getTemplatesByCategory(category: string): ButtonTemplate[] {
  return BUTTON_TEMPLATES.filter(t => t.category === category)
}

export function getTemplateById(id: string): ButtonTemplate | undefined {
  return BUTTON_TEMPLATES.find(t => t.id === id)
}

