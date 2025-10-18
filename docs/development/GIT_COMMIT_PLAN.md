# Git Commit Plan

## Files to ADD (New Production Files)

### Documentation
- ✅ `.env.example` - Environment configuration template
- ✅ `CHANGELOG.md` - Version history and changes
- ✅ `PRODUCTION_CHECKLIST.md` - Production readiness checklist

### Testing
- ✅ `backend/test_actions.py` - Individual action tests
- ✅ `backend/test_all_actions.py` - Comprehensive action validation

### Utilities (Optional - decide based on need)
- ⚠️ `launch_fixed.bat` - Fixed launch script (review if different from launch.bat)
- ⚠️ `frontend/src/components/AppShortcutManager.vue` - Review if actively used
- ⚠️ `frontend/src/data/` - Check what's in this folder
- ⚠️ `frontend/src/components/kokonutui/` - Interactive backgrounds (React components - needs Vue conversion)

## Files to COMMIT (Modified)

### Backend Changes
- ✅ `.gitignore` - Updated to exclude temp files and Claude artifacts
- ✅ `backend/actions/hotkey_action.py` - **CRITICAL** - Backward compatibility fix
- ✅ `backend/actions/cross_platform_action.py` - Cross-platform action improvements
- ✅ `backend/models/button.py` - Button model updates
- ✅ `backend/requirements.txt` - Dependency updates
- ✅ `backend/utils/app_monitor.py` - Monitoring improvements

### Frontend Changes
- ✅ `frontend/src/stores/dashboard.ts` - **CRITICAL** - Circular navigation, auto-save
- ✅ `frontend/src/views/DashboardView.vue` - **CRITICAL** - Add Page, Save Profile buttons, navigation actions
- ✅ `frontend/src/components/SceneNavigation.vue` - **CRITICAL** - Larger scene buttons
- ✅ `frontend/src/components/ButtonActionsSidebar.vue` - Navigation category expanded
- ✅ `frontend/src/components/SceneEditor.vue` - Scene editing improvements
- ✅ `frontend/src/stores/settings.ts` - Settings enhancements
- ✅ `frontend/src/views/SettingsView.vue` - UI improvements
- ✅ `frontend/src/components/DeckButton.vue` - Button rendering updates
- ✅ `frontend/src/components/DeckGrid.vue` - Grid improvements
- ✅ `frontend/src/components/DockedSidebar.vue` - Docked sidebar enhancements
- ✅ `frontend/src/components/MetricButton.vue` - Metric display updates
- ✅ `frontend/src/components/PerformanceMonitorButton.vue` - Performance monitoring
- ✅ `frontend/src/components/ButtonEditor.vue` - Editor improvements
- ✅ `frontend/src/components/AssetPicker.vue` - Asset management
- ✅ `frontend/src/services/appMonitor.ts` - App monitoring service
- ✅ `frontend/src/types/index.ts` - Type definitions
- ✅ `frontend/src/assets/styles/main.css` - Style updates

### Scripts
- ✅ `launch.bat` - Updated launch script

## Files to EXCLUDE (Temporary/Build/Generated)

The following are already in `.gitignore` and should NOT be committed:
- ❌ `.claude/` - Claude Code artifacts
- ❌ `ACTION_TEST_REPORT.md` - Temporary test report
- ❌ `MEDIA_CONTROLS_FIX_SUMMARY.md` - Temporary summary
- ❌ `NEXT_STEPS.md` - Temporary planning doc
- ❌ `nul` - Windows temp file
- ❌ `backend/data/profiles/*.json` - User data (except .gitkeep)
- ❌ `backend/__pycache__/` - Python cache
- ❌ `frontend/node_modules/` - Dependencies
- ❌ `backend/venv/` - Virtual environment

## Recommended Commit Strategy

### Commit 1: Critical Bug Fixes
```bash
git add backend/actions/hotkey_action.py
git add frontend/src/stores/dashboard.ts
git commit -m "fix: hotkey backward compatibility and circular page navigation

- Fix hotkey action to support both string and array formats
- Add circular navigation for pages (loop to first/last)
- Fix scene persistence issues
- Auto-save pages when created

Fixes #[issue-number] if applicable"
```

### Commit 2: Feature Additions
```bash
git add frontend/src/views/DashboardView.vue
git add frontend/src/components/SceneNavigation.vue
git add frontend/src/components/ButtonActionsSidebar.vue
git commit -m "feat: add page management and navigation improvements

- Add 'Add Page' button in footer for quick page creation
- Add 'Save Profile' button with toast notifications
- Increase scene button size for better accessibility
- Add navigation action buttons (Next/Previous/Home)
- Expand navigation category in sidebar by default"
```

### Commit 3: Production Readiness
```bash
git add .env.example CHANGELOG.md PRODUCTION_CHECKLIST.md .gitignore
git add backend/test_actions.py backend/test_all_actions.py
git commit -m "chore: prepare for production release

- Add environment configuration template
- Add comprehensive changelog
- Add production readiness checklist
- Update .gitignore to exclude temp files
- Add comprehensive action test suite

All tests passing: 13/13 buttons validated"
```

### Commit 4: UI/UX Improvements
```bash
git add frontend/src/components/*.vue
git add frontend/src/views/*.vue
git add frontend/src/assets/styles/main.css
git add frontend/src/services/appMonitor.ts
git add frontend/src/types/index.ts
git commit -m "style: improve UI/UX and component updates

- Enhance button editor and asset picker
- Improve docked sidebar styling
- Update metric and performance monitor displays
- Refine grid and button components
- Update type definitions"
```

### Commit 5: Backend Updates
```bash
git add backend/actions/*.py
git add backend/models/*.py
git add backend/utils/*.py
git add backend/requirements.txt
git commit -m "chore: update backend dependencies and utilities

- Update action handlers
- Improve button models
- Enhance app monitoring
- Update requirements"
```

### Commit 6: Build Scripts
```bash
git add launch.bat
git commit -m "chore: update launch script"
```

## Files Needing Review

### Check Before Committing:
1. **launch_fixed.bat** - Compare with `launch.bat`, keep only if needed
2. **frontend/src/components/AppShortcutManager.vue** - Is this actively used?
3. **frontend/src/data/** - What's in this folder? Config or generated data?
4. **frontend/src/components/kokonutui/** - React components, need Vue conversion to be useful

## Post-Commit Checklist

After committing:
1. ✅ Push to GitHub
2. ✅ Create a release tag (e.g., v0.2.0)
3. ✅ Update GitHub release notes with CHANGELOG
4. ✅ Ensure CI/CD pipeline passes (if configured)
5. ✅ Test deployment in staging environment
6. ✅ Update documentation links if needed

## Important Notes

**BEFORE PUSHING:**
1. Review all changes one more time
2. Ensure no sensitive data (passwords, tokens, keys) in any files
3. Verify `.gitignore` is working correctly
4. Test that all functionality still works
5. Run the test suite: `python backend/test_all_actions.py`

**BACKEND RESTART REQUIRED:**
The backend server MUST be restarted for the hotkey action fix to take effect!
```bash
# Close the backend window and restart:
cd backend
call venv\Scripts\activate.bat
python app.py
```
