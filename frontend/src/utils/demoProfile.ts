import type { Profile, Scene, Page, Button } from '@/types'

/**
 * Creates a demo profile with a comprehensive demo scene for first-time users
 */
export function createDemoProfile(): Profile {
  const profileId = `demo-profile-${Date.now()}`
  const sceneId = `demo-scene-${Date.now()}`
  const pageId = `demo-page-${Date.now()}`
  
  // Create demo buttons showcasing different VDock features
  const demoButtons: Button[] = [
    // Row 1: System Controls
    {
      id: `btn-${Date.now()}-1`,
      label: 'Volume Up',
      icon: ['fas', 'volume-up'],
      style: {
        backgroundColor: '#27ae60',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'volume_up'
        }
      },
      position: { row: 0, col: 0 }
    },
    {
      id: `btn-${Date.now()}-2`,
      label: 'Volume Down',
      icon: ['fas', 'volume-down'],
      style: {
        backgroundColor: '#e74c3c',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'volume_down'
        }
      },
      position: { row: 0, col: 1 }
    },
    {
      id: `btn-${Date.now()}-3`,
      label: 'Mute',
      icon: ['fas', 'volume-mute'],
      style: {
        backgroundColor: '#95a5a6',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'volume_mute'
        }
      },
      position: { row: 0, col: 2 }
    },
    {
      id: `btn-${Date.now()}-4`,
      label: 'World Time',
      icon: ['fas', 'globe'],
      style: {
        backgroundColor: '#3498db',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'time_options',
        config: {
          format: 'HH:mm:ss',
          timezone: 'UTC',
          show_date: true
        }
      },
      position: { row: 0, col: 3 }
    },
    {
      id: `btn-${Date.now()}-5`,
      label: 'Weather',
      icon: ['fas', 'cloud-sun'],
      style: {
        backgroundColor: '#f39c12',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'weather',
        config: {
          location: 'auto',
          unit: 'C',
          refresh_interval: 15
        }
      },
      position: { row: 0, col: 4 }
    },

    // Row 2: Media Controls
    {
      id: `btn-${Date.now()}-6`,
      label: 'Play/Pause',
      icon: ['fas', 'play'],
      style: {
        backgroundColor: '#9b59b6',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'media_play_pause'
        }
      },
      position: { row: 1, col: 0 }
    },
    {
      id: `btn-${Date.now()}-7`,
      label: 'Previous',
      icon: ['fas', 'step-backward'],
      style: {
        backgroundColor: '#8e44ad',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'media_previous'
        }
      },
      position: { row: 1, col: 1 }
    },
    {
      id: `btn-${Date.now()}-8`,
      label: 'Next',
      icon: ['fas', 'step-forward'],
      style: {
        backgroundColor: '#8e44ad',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'media_next'
        }
      },
      position: { row: 1, col: 2 }
    },
    {
      id: `btn-${Date.now()}-9`,
      label: 'Stop',
      icon: ['fas', 'stop'],
      style: {
        backgroundColor: '#c0392b',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'media_stop'
        }
      },
      position: { row: 1, col: 3 }
    },
    {
      id: `btn-${Date.now()}-10`,
      label: 'Brightness Up',
      icon: ['fas', 'sun'],
      style: {
        backgroundColor: '#f1c40f',
        textColor: '#2c3e50',
        iconSize: 32
      },
      action: {
        type: 'cross_platform',
        config: {
          action: 'brightness_up'
        }
      },
      position: { row: 1, col: 4 }
    },

    // Row 3: Applications & Shortcuts
    {
      id: `btn-${Date.now()}-11`,
      label: 'Open Folder',
      icon: ['fas', 'folder-open'],
      style: {
        backgroundColor: '#16a085',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'program',
        config: {
          path: navigator.platform.includes('Win') ? 'explorer.exe' : 
                navigator.platform.includes('Mac') ? 'open' : 'nautilus',
          args: navigator.platform.includes('Win') ? '' : 
                navigator.platform.includes('Mac') ? '.' : '.'
        }
      },
      position: { row: 2, col: 0 }
    },
    {
      id: `btn-${Date.now()}-12`,
      label: 'Copy',
      icon: ['fas', 'copy'],
      style: {
        backgroundColor: '#2980b9',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'hotkey',
        config: {
          keys: navigator.platform.includes('Mac') ? ['cmd', 'c'] : ['ctrl', 'c']
        }
      },
      position: { row: 2, col: 1 }
    },
    {
      id: `btn-${Date.now()}-13`,
      label: 'Paste',
      icon: ['fas', 'paste'],
      style: {
        backgroundColor: '#2980b9',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'hotkey',
        config: {
          keys: navigator.platform.includes('Mac') ? ['cmd', 'v'] : ['ctrl', 'v']
        }
      },
      position: { row: 2, col: 2 }
    },
    {
      id: `btn-${Date.now()}-14`,
      label: 'Screenshot',
      icon: ['fas', 'camera'],
      style: {
        backgroundColor: '#34495e',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'hotkey',
        config: {
          keys: navigator.platform.includes('Win') ? ['win', 'shift', 's'] :
                navigator.platform.includes('Mac') ? ['cmd', 'shift', '4'] : 
                ['print']
        }
      },
      position: { row: 2, col: 3 }
    },
    {
      id: `btn-${Date.now()}-15`,
      label: 'Task Manager',
      icon: ['fas', 'tasks'],
      style: {
        backgroundColor: '#e67e22',
        textColor: '#ffffff',
        iconSize: 32
      },
      action: {
        type: 'hotkey',
        config: {
          keys: navigator.platform.includes('Win') ? ['ctrl', 'shift', 'esc'] :
                navigator.platform.includes('Mac') ? ['cmd', 'option', 'esc'] :
                ['ctrl', 'alt', 'del']
        }
      },
      position: { row: 2, col: 4 }
    }
  ]

  // Create demo page
  const demoPage: Page = {
    id: pageId,
    name: 'Demo Page',
    buttons: demoButtons,
    grid_config: {
      rows: 3,
      cols: 5
    }
  }

  // Create demo scene
  const demoScene: Scene = {
    id: sceneId,
    name: 'Demo Scene',
    icon: 'star',
    color: '#e74c3c',
    pages: [demoPage],
    isActive: true,
    buttonSize: 1.0
  }

  // Create demo profile
  const demoProfile: Profile = {
    id: profileId,
    name: 'Welcome to VDock',
    description: 'A demo profile showcasing VDock\'s features. Feel free to customize or create your own!',
    icon: 'rocket',
    avatar: '/avatars/1.png',
    pages: [], // Backward compatibility
    scenes: [demoScene],
    dockedButtons: [
      // Add some useful docked buttons
      {
        id: `docked-${Date.now()}-1`,
        label: 'Settings',
        icon: ['fas', 'cog'],
        style: {
          backgroundColor: '#7f8c8d',
          textColor: '#ffffff',
          iconSize: 24
        },
        action: {
          type: 'url',
          config: {
            url: '/settings'
          }
        },
        position: { row: 0, col: 0 }
      },
      {
        id: `docked-${Date.now()}-2`,
        label: 'Profiles',
        icon: ['fas', 'user'],
        style: {
          backgroundColor: '#3498db',
          textColor: '#ffffff',
          iconSize: 24
        },
        action: {
          type: 'url',
          config: {
            url: '/profiles'
          }
        },
        position: { row: 1, col: 0 }
      }
    ],
    theme: 'default',
    settings: {
      autoSave: true,
      showGrid: true,
      snapToGrid: true,
      buttonSpacing: 8
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  return demoProfile
}

/**
 * Check if this is a first-time user (no profiles exist)
 */
export function isFirstTimeUser(profiles: any[]): boolean {
  return profiles.length === 0
}
