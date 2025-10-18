# Changelog

All notable changes to VDock will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Circular Page Navigation**: Next/Previous page buttons now loop around (next on last page returns to first, previous on first page goes to last)
- **Quick Add Page Button**: Added "Add Page" button in dashboard footer for quick page creation
- **Explicit Save Profile Button**: Added "Save Profile" button in footer with toast notifications
- **Larger Scene Buttons**: Increased scene button size for better accessibility (44px minimum height, larger fonts and icons)
- **Navigation Action Category**: Added Next Page, Previous Page, and Home Page button actions in sidebar
- **Hotkey Backward Compatibility**: Support for both legacy string format (`"Ctrl+Shift+P"`) and new array format (`["ctrl", "shift", "p"]`)
- **Docked Sidebar System**: Persistent sidebar with pinned buttons across all pages
- **Production Readiness**: Added `.env.example`, production checklist, and comprehensive `.gitignore`

### Fixed
- **Cursor Button Hotkeys**: Fixed "Invalid configuration" error for Cursor scene hotkey buttons
- **Scene Button Persistence**: Scenes now properly save and persist when navigating away
- **Page Auto-Save**: Pages automatically save to backend when created or modified
- **Action Validation**: All 13 buttons across 3 scenes now validate and execute correctly

### Changed
- **Scene Navigation UI**: Improved button styling, spacing, and visual hierarchy
- **Footer Layout**: Better organization with spacers and aligned buttons
- **Test Coverage**: Added comprehensive action testing script (`test_all_actions.py`)

### Security
- Updated `.gitignore` to exclude sensitive data and temporary files
- Added `.env.example` template for secure configuration

## [0.1.0] - Previous Release

### Initial Features
- Multi-profile system with avatar support
- Customizable button grid with drag-and-drop
- 26+ dashboard backgrounds
- Multiple action types (URL, Program, Command, Hotkey, System Control)
- System metrics monitoring (CPU, RAM, GPU, etc.)
- Time widgets (World Clock, Timer, Countdown)
- Weather integration
- Scene management system
- Button animations and effects
- Asset management system
- Cross-platform action support
- Flask backend with Python 3.13
- Vue 3 frontend with TypeScript
- Real-time action execution
- Profile import/export

## Testing Status

### Latest Test Results (2025-10-18)
```
Total buttons tested: 13
Unique action types: 3
Action types: cross_platform, hotkey, system_control

Results:
  ✅ Valid:       13
  ⚠️  Invalid:     0
  ❌ Unsupported: 0
  ❌ Errors:      0
```

**Scenes Tested:**
- Main Scene (5 buttons): Full Screen, Mute, Volume Up, Brightness Up, Stop
- Cursor Scene (8 buttons): Command Palette, Quick Open, AI Chat, Find in Files, Toggle Terminal, Multi-Cursor, Select Next Match, Comment Line
- Demo Scene: GPU Memory Frequency metric

**All action types validated:**
- ✅ `system_control` - Fullscreen toggle
- ✅ `cross_platform` - Volume, brightness, media controls
- ✅ `hotkey` - Keyboard shortcuts (both formats)

---

## Migration Notes

### Upgrading to Latest Version

**Backend:**
1. Restart backend server to load updated hotkey action code
2. No database migrations required
3. Profile data structure is backward compatible

**Frontend:**
1. Clear browser cache if scene buttons don't appear
2. Hard refresh (Ctrl+Shift+R) recommended

**Features:**
- Existing hotkey buttons will work with both old and new formats
- New navigation buttons available in sidebar under "Navigation" category
- Scenes persist automatically, but can use "Save Profile" button for explicit saving

---

[Unreleased]: https://github.com/yourusername/VDock/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/VDock/releases/tag/v0.1.0
