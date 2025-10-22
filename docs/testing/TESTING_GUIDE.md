# VDock Button Actions Testing Guide

## Summary of Changes

### 1. Fixed Duplicate Actions ✅
**Issue**: Volume Up, Volume Down, and Mute appeared in both "Media Control" and "Audio Control" categories.

**Fix**: 
- Removed duplicate volume controls from Media Control category
- Consolidated all audio controls into "Audio & Volume" category
- Media Control now only contains: Play/Pause, Next Track, Previous Track, Stop

### 2. Optimized Category Order ✅
**New Order** (Most frequently used first):
1. **Quick Launch** - Common apps (Browser, Calculator, Notepad, etc.)
2. **System** - Power, Lock, Brightness, Task Manager, etc.
3. **Audio & Volume** - Volume controls and microphone
4. **Media Control** - Play/Pause, Next/Previous track
5. **Window Management** - Minimize, Maximize, Close, Show Desktop
6. **Web & Apps** - Open URL, Apps, Folders, Files
7. **Text & Input** - Type Text, Hotkeys, Macros
8. **Monitor Metrics** - CPU, Memory, GPU stats
9. **Time & Date** - World Clock, Timer, Countdown
10. **Weather** - Weather Query
11. **Navigation** - Page navigation
12. **Streaming (OBS)** - OBS controls
13. **Custom Media** - Custom icons, GIFs, videos

### 3. Added Backend Support for New Actions ✅
**New Actions Added to Backend** (`backend/actions/cross_platform_action.py`):
- `microphone_mute` - Mute microphone
- `microphone_unmute` - Unmute microphone
- `run_command` - Run custom shell commands
- `close_app` - Close applications by name
- `empty_recycle_bin` - Empty recycle bin/trash

### 4. Added Category Reordering UI ✅
**Features**:
- Up/Down arrow buttons appear on hover for each category
- Move categories up or down in the list
- Buttons are disabled at list boundaries
- Reordering is hidden when searching

---

## Testing Instructions

### Pre-Testing Setup
1. **Refresh your browser** (Ctrl+F5) to load the new frontend code
2. **Ensure backend is running** on port 3000
3. **Open browser console** (F12) to monitor for errors

### Test Plan

#### ✅ Test 1: Check for Duplicates
1. Open Edit Mode
2. Expand all categories
3. **Verify**: No duplicate actions appear across categories
4. **Expected**: Volume Up/Down/Mute only in "Audio & Volume", not in "Media Control"

#### ✅ Test 2: Verify Category Order
1. Open Edit Mode
2. **Verify** categories appear in this order:
   - Quick Launch (first)
   - System
   - Audio & Volume
   - Media Control
   - Window Management
   - Web & Apps
   - Text & Input
   - Monitor Metrics
   - Time & Date
   - Weather
   - Navigation
   - Streaming (OBS)
   - Custom Media (last)

#### ✅ Test 3: Test Category Reordering
1. Open Edit Mode
2. Hover over any category header
3. **Verify**: Up/Down arrow buttons appear
4. Click "Down" arrow on "Quick Launch"
5. **Expected**: "Quick Launch" moves below "System"
6. Click "Up" arrow on "Quick Launch"
7. **Expected**: "Quick Launch" moves back to first position
8. **Verify**: Up arrow is disabled on first category
9. **Verify**: Down arrow is disabled on last category

#### 🧪 Test 4: Quick Launch Buttons (8 buttons)
**Test each button by dragging to deck and clicking:**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Web Browser | Opens Google in default browser | ⏳ |
| File Explorer | Opens Windows Explorer | ⏳ |
| Calculator | Opens Calculator app | ⏳ |
| Notepad | Opens Notepad | ⏳ |
| Command Prompt | Opens CMD | ⏳ |
| PowerShell | Opens PowerShell | ⏳ |
| Paint | Opens MS Paint | ⏳ |
| Snipping Tool | Opens Snipping Tool | ⏳ |

#### 🧪 Test 5: System Buttons (8 buttons - excluding shutdown/sleep)
**Test each button:**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Lock Screen | Locks the computer | ⏳ |
| Brightness Up | Increases screen brightness | ⏳ |
| Brightness Down | Decreases screen brightness | ⏳ |
| Empty Recycle Bin | Empties recycle bin | ⏳ |
| Task Manager | Opens Task Manager | ⏳ |
| Control Panel | Opens Control Panel | ⏳ |
| Device Manager | Opens Device Manager | ⏳ |

**Skip Testing** (Destructive):
- ❌ Shutdown
- ❌ Restart
- ❌ Sleep

#### 🧪 Test 6: Audio & Volume Buttons (5 buttons)
**Test each button:**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Volume Up | Increases system volume | ⏳ |
| Volume Down | Decreases system volume | ⏳ |
| Mute/Unmute | Toggles system mute | ⏳ |
| Mute Microphone | Mutes microphone | ⏳ |
| Unmute Microphone | Unmutes microphone | ⏳ |

#### 🧪 Test 7: Media Control Buttons (4 buttons)
**Test with media player open (Spotify, YouTube, etc.):**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Play/Pause | Toggles media playback | ⏳ |
| Next Track | Skips to next track | ⏳ |
| Previous Track | Goes to previous track | ⏳ |
| Stop | Stops playback | ⏳ |

#### 🧪 Test 8: Window Management Buttons (5 buttons)
**Test with a window open (e.g., Notepad):**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Minimize Window | Minimizes active window (Win+Down) | ⏳ |
| Maximize Window | Maximizes active window (Win+Up) | ⏳ |
| Close Window | Closes active window (Alt+F4) | ⏳ |
| Switch Window | Opens task switcher (Alt+Tab) | ⏳ |
| Show Desktop | Shows desktop (Win+D) | ⏳ |

#### 🧪 Test 9: Web & Apps Buttons (5 buttons)
**Test each button:**

| Button | Expected Result | Status |
|--------|----------------|--------|
| Screenshot | Takes a screenshot | ⏳ |
| Run Command | Runs configured command | ⏳ |
| Close Application | Closes specified app | ⏳ |

**Skip** (Require configuration):
- Open URL (needs URL)
- Open Application (needs app path)
- Open Folder (needs folder path)
- Open File (needs file path)

---

## Console Error Monitoring

### What to Check:
1. **No 429 errors** - Rate limiting should be disabled
2. **No "Invalid configuration" errors** - All actions should have proper config
3. **No undefined action errors** - Backend should support all actions
4. **Success notifications** - Each button click should show success/failure

### Common Errors to Watch For:
- ❌ `Action Failed - Invalid configuration for cross_platform action`
- ❌ `Unknown action: <action_name>`
- ❌ `429 Too Many Requests`
- ❌ `Action type not specified`

---

## Testing Checklist

### Pre-Test
- [ ] Backend running on port 3000
- [ ] Frontend loaded and refreshed
- [ ] Browser console open
- [ ] Edit mode enabled

### Category Organization
- [ ] No duplicate actions found
- [ ] Categories in correct order
- [ ] Category reordering works
- [ ] Up/Down buttons appear on hover
- [ ] Boundary buttons are disabled

### Button Testing
- [ ] Quick Launch buttons (8/8 tested)
- [ ] System buttons (7/10 tested, 3 skipped)
- [ ] Audio buttons (5/5 tested)
- [ ] Media buttons (4/4 tested)
- [ ] Window Management (5/5 tested)
- [ ] Web & Apps (3/7 tested, 4 need config)

### Error Checking
- [ ] No console errors
- [ ] No 429 rate limit errors
- [ ] No invalid configuration errors
- [ ] Success notifications appear

---

## Notes

### Backend Actions
All new actions are implemented in `backend/actions/cross_platform_action.py`:
- Uses Windows API via ctypes when available
- Falls back to PowerShell commands
- Cross-platform support (Windows, macOS, Linux)

### Frontend Changes
- `DashboardView.vue`: Reorganized categories, removed duplicates, added reordering
- Volume step changed from 10 to 2000 (NirCmd format)
- All new button cases properly configured

### Known Limitations
- Microphone mute/unmute may require admin privileges on some systems
- Brightness control may not work on all hardware
- Some actions require NirCmd for full functionality

---

## Report Template

After testing, report results using this format:

```
## Test Results

### Categories
- ✅ No duplicates found
- ✅ Order is correct
- ✅ Reordering works

### Quick Launch (8 buttons)
- ✅ Browser: Works
- ✅ File Explorer: Works
- ❌ Calculator: Error - [describe error]
- ...

### Console Errors
- [List any errors seen]

### Issues Found
1. [Issue description]
2. [Issue description]
```

