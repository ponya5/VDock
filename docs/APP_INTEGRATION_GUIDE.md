# App Integration Guide

## 🎯 Overview

The **App Integration** feature allows VDock to automatically detect running applications and switch to dedicated scenes with pre-configured buttons and macros specific to that application.

For example, when you open **Cursor.exe**, VDock can automatically switch to a "Cursor" scene with predefined shortcuts like:
- Ctrl+Shift+P (Command Palette)
- Ctrl+B (Toggle Sidebar)
- Ctrl+` (Toggle Terminal)
- Custom code snippets
- File templates

---

## 🚀 Quick Start

### 1. Open App Integration Settings
1. Go to **Settings** → **Integration** tab
2. Click **"Refresh Apps"** to load running applications
3. See list of currently running apps with exe names

### 2. Enable Integration for an App
1. Find your desired application (e.g., `Cursor.exe`)
2. Toggle the **Enable** switch → **Enabled**
3. A dropdown appears to select or create a scene

### 3. Create or Select Scene
**Option A - Create New Scene**:
1. With integration enabled, dropdown shows "Create New Scene"
2. Click the **+ (Plus) icon** in the Actions column
3. New scene is automatically created with the app's name
4. Scene appears in dashboard

**Option B - Use Existing Scene**:
1. Select an existing scene from the dropdown
2. Scene will be associated with this app

### 4. Configure Scene
1. Go to **Dashboard** → Navigate to the app scene
2. Add buttons specific to that application:
   - **Macros** for common workflows
   - **Hotkeys** for shortcuts
   - **Commands** for app-specific actions
   - **System Metrics** if needed

---

## 🔧 Features

### Auto-Detection of Running Apps
- VDock scans for running applications
- Shows app name and executable (e.g., `Cursor.exe`)
- Real-time refresh capability

### Toggle Integration
- **Enable/Disable** per app
- Visual toggle switch
- Instant activation

### Scene Management
- **Create new scenes** automatically
- **Link to existing scenes**
- **Scene naming** matches app name
- **Auto-created flag** for tracking

### Visual Interface
- **App Icon** for easy identification
- **Status Indicator** (Enabled/Disabled)
- **Scene Dropdown** for selection
- **Action Buttons** for quick access

---

## 📋 How It Works

### Architecture

```
┌─────────────────┐
│  Running Apps   │  ← Backend scans for running processes
│  (psutil)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  App Detection  │  ← API endpoint: /metrics/running-apps
│  Backend API    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Settings UI    │  ← User enables integration & selects scene
│  Integration Tab│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  App-Scene      │  ← Mapping stored in localStorage
│  Mapping        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto Scene     │  ← (Future) Monitor active window & switch
│  Switching      │
└─────────────────┘
```

### Data Structure

**App Integration Object**:
```typescript
{
  appExe: string       // e.g., "Cursor.exe"
  appName: string      // e.g., "Cursor"
  sceneId: string      // UUID of associated scene
  enabled: boolean     // Integration active?
  autoSwitch: boolean  // Auto-switch when app opens?
}
```

**Auto-Created Scene**:
```typescript
{
  id: string
  name: string          // App name
  buttons: Button[]
  triggeredByApp: string  // App exe that triggers this scene
  autoCreated: boolean    // Flag for auto-created scenes
}
```

---

## 🎨 UI Components

### App Integration List

| Column | Description |
|--------|-------------|
| **Application** | App name + executable |
| **Status** | Enable/Disable toggle |
| **Scene** | Scene dropdown selector |
| **Actions** | Configure & Create buttons |

### Actions
- **⚙️ Configure**: Advanced settings (coming soon)
- **➕ Create Scene**: Auto-generate scene for app

### Summary
- Shows count of enabled integrations
- Visual indicator at bottom of list

---

## 📂 Storage

### LocalStorage Keys
- `appIntegrations`: Array of AppIntegration objects
- Persists across sessions
- Synced with profile scenes

### Backend API
- `GET /api/metrics/running-apps`: Fetch running applications
- Returns: `[{ name, exe, pid, path }]`

---

## 🔮 Current Limitations

### Manual Scene Switching
- Currently, scene switching is **manual**
- User must navigate to the app's scene
- **Future**: Automatic detection & switching

### No Real-Time Monitoring
- App list requires manual refresh
- **Future**: Background monitoring service

### Basic Configuration
- Limited per-app settings
- **Future**: Advanced configuration modal
  - Custom triggers
  - Scene switching rules
  - Button templates

---

## 🚧 Future Enhancements

### Phase 1: Auto Scene Switching (Planned)
```javascript
// Background service monitors active window
setInterval(() => {
  const activeApp = getActiveWindowProcess()
  const integration = findIntegrationForApp(activeApp)
  
  if (integration && integration.enabled && integration.autoSwitch) {
    switchToScene(integration.sceneId)
  }
}, 1000) // Check every second
```

### Phase 2: Advanced Configuration
- **Trigger Rules**: On app open, on focus, on startup
- **Scene Templates**: Pre-configured button layouts per app type
- **Multi-App Profiles**: Switch based on app combinations

### Phase 3: Smart Suggestions
- **ML-Based**: Suggest buttons based on app type
- **Usage Analytics**: Recommend buttons based on frequency
- **Community Templates**: Share scene configurations

---

## 📖 Use Cases

### 1. Development Environments

**Cursor/VSCode**:
- Ctrl+Shift+P → Command Palette
- Ctrl+B → Toggle Sidebar
- Ctrl+` → Toggle Terminal
- Ctrl+P → Quick Open
- F5 → Debug

**Visual Studio**:
- F5 → Start Debugging
- Ctrl+K, Ctrl+D → Format Document
- Ctrl+Shift+B → Build Solution
- Ctrl+/ → Comment Toggle

### 2. Content Creation

**Photoshop**:
- Ctrl+T → Free Transform
- Ctrl+Shift+N → New Layer
- Alt+Backspace → Fill Foreground
- Ctrl+J → Duplicate Layer

**Premiere Pro**:
- Space → Play/Pause
- C → Razor Tool
- V → Selection Tool
- Ctrl+K → Cut

### 3. Gaming

**OBS Studio**:
- Start/Stop Recording
- Switch Scene
- Toggle Mute
- Instant Replay

**Discord**:
- Mute/Unmute
- Deafen
- Screen Share
- Quick Emoji Reactions

### 4. Productivity

**Browser (Chrome/Firefox)**:
- Ctrl+T → New Tab
- Ctrl+W → Close Tab
- Ctrl+Shift+T → Reopen Tab
- Ctrl+L → Focus Address Bar

**Excel**:
- Ctrl+C/V → Copy/Paste
- Alt+= → AutoSum
- F2 → Edit Cell
- Ctrl+Shift+L → Toggle Filter

---

## 🛠️ Technical Details

### Backend Implementation

**File**: `backend/utils/system_metrics.py`
```python
def get_running_applications():
    """Returns a list of running applications (processes with window titles)."""
    running_apps = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if not proc.info['exe']:
                continue
            
            running_apps.append({
                "name": proc.info['name'],
                "exe": proc.info['exe'].split('\\')[-1],
                "pid": proc.info['pid'],
                "path": proc.info['exe']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Deduplicate by exe name
    deduplicated_apps = {}
    for app in running_apps:
        if app['exe'] not in deduplicated_apps:
            deduplicated_apps[app['exe']] = app
    
    return list(deduplicated_apps.values())
```

### Frontend Implementation

**File**: `frontend/src/views/SettingsView.vue`

**Key Functions**:
- `refreshRunningApps()`: Fetch running apps from API
- `toggleAppIntegration(app)`: Enable/disable integration
- `updateAppScene(appExe, sceneId)`: Link app to scene
- `createSceneForApp(app)`: Auto-create scene
- `saveAppIntegrations()`: Persist to localStorage
- `loadAppIntegrations()`: Load from localStorage

---

## 📝 Example Configuration

### Cursor IDE Integration

```json
{
  "appExe": "Cursor.exe",
  "appName": "Cursor",
  "sceneId": "scene-1697123456789",
  "enabled": true,
  "autoSwitch": true
}
```

### Scene with Buttons

```json
{
  "id": "scene-1697123456789",
  "name": "Cursor",
  "triggeredByApp": "Cursor.exe",
  "autoCreated": true,
  "buttons": [
    {
      "id": "btn-1",
      "label": "Command Palette",
      "action": {
        "type": "hotkey",
        "keys": ["ctrl", "shift", "p"]
      }
    },
    {
      "id": "btn-2",
      "label": "Toggle Terminal",
      "action": {
        "type": "hotkey",
        "keys": ["ctrl", "`"]
      }
    },
    {
      "id": "btn-3",
      "label": "Format Document",
      "action": {
        "type": "macro",
        "steps": [
          { "type": "hotkey", "keys": ["ctrl", "shift", "i"] },
          { "type": "delay", "delay": 200 },
          { "type": "hotkey", "keys": ["enter"] }
        ]
      }
    }
  ]
}
```

---

## ✅ Checklist for Setup

- [ ] Navigate to Settings → Integration
- [ ] Click "Refresh Apps" to load running applications
- [ ] Find your target application in the list
- [ ] Toggle integration to "Enabled"
- [ ] Click "+ Create Scene" or select existing scene
- [ ] Go to Dashboard → Find the new scene
- [ ] Add buttons specific to that application
- [ ] Test buttons work correctly
- [ ] (Optional) Configure advanced settings

---

## 🐛 Troubleshooting

### App Not Appearing in List
- **Solution**: Click "Refresh Apps" button
- **Reason**: App might have started after page load

### Integration Not Saving
- **Solution**: Check browser console for errors
- **Reason**: LocalStorage might be full or disabled

### Scene Not Created
- **Solution**: Ensure at least one page exists in profile
- **Reason**: Scenes need a parent page

### Buttons Not Working
- **Solution**: Verify app has focus/is active
- **Reason**: Hotkeys/macros need target app focused

---

## 📚 Related Documentation

- [Macro System Guide](./NEW_FEATURES_SUMMARY.md#macro-system)
- [System Metrics Guide](./NEW_FEATURES_SUMMARY.md#system-metrics)
- [Quick Start Guide](./QUICK_START_NEW_FEATURES.md)
- [Complete Features Guide](./COMPLETE_FEATURES_GUIDE.md)

---

**Happy Automating! 🚀**
