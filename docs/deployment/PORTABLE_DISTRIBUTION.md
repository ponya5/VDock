# VDock Portable Distribution Guide

**Version:** 1.0  
**Last Updated:** October 21, 2025

---

## Overview

The VDock Portable Distribution is a self-contained package that allows users to extract and run VDock on Windows without complex installation procedures. Everything needed except Python and Node.js runtimes is included in the package.

---

## 📦 Building the Portable Package

### Prerequisites (Developer Machine)

- Windows 10/11
- Python 3.8+
- Node.js 16+
- Git
- 7-Zip (optional, for better compression)

### Build Steps

1. **Clone/Navigate to VDock repository:**
   ```bat
   cd C:\path\to\VDock
   ```

2. **Run the portable builder:**
   ```bat
   scripts\build-portable.bat
   ```

3. **Wait for completion:**
   - Frontend build: ~2-3 minutes
   - File copying: ~30 seconds
   - Compression: ~1 minute
   - **Total:** ~5 minutes

4. **Output:**
   - `VDock-Portable.zip` (~50 MB compressed)
   - `VDock-Portable\` directory (for testing)

### What Gets Packaged

✅ **Included:**
- Frontend production build (static files)
- Backend Python source code
- All templates and assets
- Documentation
- Automated launcher script
- Configuration files

❌ **Not Included (Downloaded on First Run):**
- Python packages (via pip)
- Node.js packages (via npm)
- Python virtual environment

---

## 📤 Distributing to Users

### Package Contents

```
VDock-Portable.zip
├── launch.bat           # Main launcher
├── README-PORTABLE.txt  # Quick start guide
├── REQUIREMENTS.txt     # System requirements
├── LICENSE              # License information
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── actions/
│   ├── auth/
│   ├── models/
│   ├── plugins/
│   ├── routes/
│   ├── utils/
│   ├── data/
│   │   └── templates/  # IDE & system templates
│   ├── Assets/
│   └── Avatars/
├── frontend/
│   ├── dist/           # Production build
│   ├── package.json
│   └── package-lock.json
└── docs/
    ├── README.md
    ├── guides/
    ├── technical/
    └── ...
```

### Distribution Methods

#### Method 1: Direct Download
1. Upload `VDock-Portable.zip` to:
   - GitHub Releases
   - Cloud storage (Google Drive, Dropbox)
   - Your website
2. Provide download link to users

#### Method 2: USB Drive
1. Copy `VDock-Portable.zip` to USB drive
2. Users extract and run from USB (portable mode)

#### Method 3: Network Share
1. Place on company network share
2. Users access and extract locally

---

## 👤 User Installation Guide

### End-User Prerequisites

**Required:**
- Windows 10 or Windows 11
- Python 3.8+ ([Download](https://www.python.org/downloads/))
  - ⚠️ **Important:** Check "Add Python to PATH" during installation
- Node.js 16+ ([Download](https://nodejs.org/))
- Internet connection (first launch only)

**Recommended:**
- 4 GB RAM minimum
- 1 GB free disk space

### Installation Steps (For End Users)

#### Step 1: Extract the Package
1. Download `VDock-Portable.zip`
2. Right-click → "Extract All..."
3. Choose destination (e.g., `C:\VDock`)
4. Extract

#### Step 2: Install Prerequisites
If Python or Node.js are not installed:

**Python:**
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ **CHECK "Add Python to PATH"**
4. Click "Install Now"
5. Restart terminal/command prompt

**Node.js:**
1. Download LTS from https://nodejs.org/
2. Run installer
3. Accept defaults
4. Complete installation

#### Step 3: Launch VDock
1. Navigate to extracted folder
2. Double-click `launch.bat`
3. **First launch:** Wait 3-5 minutes for dependency installation
4. **Subsequent launches:** Opens in ~10 seconds

#### Step 4: Access VDock
- Browser opens automatically to http://localhost:3000
- **Default Login:**
  - Username: `admin`
  - Password: `admin`
- Change password after first login!

---

## 🚀 Launcher Behavior

### First Launch

```
[1/7] Checking Python... ✓
[2/7] Checking Node.js... ✓
[3/7] Setting up virtual environment...
      Creating venv... (30s)
[4/7] Installing Python dependencies...
      Installing packages... (2-3 min)
[5/7] Installing frontend dependencies...
      Installing packages... (1-2 min)
[6/7] Starting backend server... ✓
[7/7] Starting frontend server... ✓

Opening browser...
```

**Total Time:** 3-5 minutes

### Subsequent Launches

```
[1/7] Checking Python... ✓
[2/7] Checking Node.js... ✓
[3/7] Virtual environment exists ✓
[4/7] Dependencies installed ✓
[5/7] Dependencies installed ✓
[6/7] Starting backend... ✓
[7/7] Starting frontend... ✓

Opening browser...
```

**Total Time:** ~10 seconds

---

## 🔧 Troubleshooting

### Issue: "Python is not recognized"

**Cause:** Python not in system PATH

**Solution:**
1. Reinstall Python
2. **Check "Add Python to PATH"**
3. OR manually add to PATH:
   - Settings → System → About → Advanced System Settings
   - Environment Variables → Path → Edit
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python39`

### Issue: "Node is not recognized"

**Cause:** Node.js not in system PATH

**Solution:**
1. Reinstall Node.js
2. Accept default installation location
3. Restart command prompt
4. Verify: `node --version`

### Issue: "Port already in use"

**Cause:** Another application using port 5000 or 3000

**Solution:**
1. Close conflicting applications
2. Check Task Manager for:
   - Python processes
   - Node.js processes
3. Kill processes if needed
4. Relaunch VDock

### Issue: "pip install failed"

**Cause:** Network issues or pip not updated

**Solution:**
```bat
cd backend
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

### Issue: "npm install failed"

**Cause:** Network issues or npm cache

**Solution:**
```bat
cd frontend
npm cache clean --force
npm install
```

### Issue: Backend won't start

**Cause:** Python dependencies missing or corrupt

**Solution:**
```bat
cd backend
rmdir /s venv
# Re-run launch.bat
```

### Issue: Frontend shows error

**Cause:** Node modules corrupt

**Solution:**
```bat
cd frontend
rmdir /s node_modules
# Re-run launch.bat
```

---

## 🔒 Security Considerations

### For Distributors

1. **Scan for malware** before distributing
2. **Sign the package** if possible (code signing certificate)
3. **Provide checksums** (SHA256) for verification
4. **Use HTTPS** for download links

### For Users

1. **Change default password immediately**
2. **Don't expose to internet** (use behind firewall)
3. **Keep Python/Node.js updated**
4. **Run antivirus scan** on downloaded files

---

## 📊 Package Size Breakdown

| Component | Compressed | Extracted |
|-----------|------------|-----------|
| Backend (Python source) | ~5 MB | ~15 MB |
| Frontend (production build) | ~10 MB | ~30 MB |
| Assets (images, GIFs) | ~30 MB | ~50 MB |
| Documentation | ~2 MB | ~5 MB |
| Templates & Config | ~1 MB | ~3 MB |
| **Total** | **~50 MB** | **~100 MB** |

**After First Launch:**
- Python packages: ~200 MB
- Node.js packages: ~300 MB
- **Total on Disk:** ~600 MB

---

## ⚙️ Customizing the Portable Build

### Exclude Large Assets

Edit `build-portable.bat`:

```bat
REM Skip animated assets
REM xcopy /E /I /Y /Q backend\Assets "%BUILD_DIR%\backend\Assets" >nul
```

### Pre-install Dependencies

Bundle Python packages:

```bat
REM In build script, after creating venv:
cd "%BUILD_DIR%\backend"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
deactivate
cd "%ROOT_DIR%"
```

**Note:** This increases zip size to ~200 MB but eliminates first-launch wait.

### Change Default Ports

Edit `backend/config.py`:

```python
PORT = 5001  # Change from 5000
```

Edit `launch.bat`:

```bat
echo Backend:  http://localhost:5001
start http://localhost:5001
```

---

## 📝 Version Management

### Updating the Portable Package

1. **Increment version** in build script:
   ```bat
   set ZIP_NAME=VDock-Portable-v1.1.zip
   ```

2. **Update CHANGELOG:**
   ```
   ## v1.1 - 2025-10-22
   - Added quick templates
   - Fixed touch mode
   ```

3. **Rebuild:**
   ```bat
   scripts\build-portable.bat
   ```

4. **Test extraction and launch**

5. **Distribute new version**

### User Upgrade Process

**Option 1: Clean Install**
1. Extract new version to different folder
2. Copy `backend/data/profiles` from old to new
3. Launch new version

**Option 2: In-Place Upgrade**
1. Close VDock
2. Backup `backend/data` folder
3. Extract new version, overwrite files
4. Launch

---

## ✅ Testing Checklist

Before distributing:

- [ ] Extract to clean folder
- [ ] Run on **Windows 10** machine
- [ ] Run on **Windows 11** machine
- [ ] Test **without** Python installed (error message)
- [ ] Test **without** Node.js installed (error message)
- [ ] Test **first launch** (full install)
- [ ] Test **second launch** (quick start)
- [ ] Verify all templates load
- [ ] Test button actions
- [ ] Test file uploads
- [ ] Check browser opens automatically
- [ ] Verify default login works
- [ ] Test on **offline machine** (after first launch)
- [ ] Scan with **antivirus**

---

## 🎯 Support & Feedback

### For Users

1. Read `README-PORTABLE.txt` first
2. Check `docs/` folder for guides
3. Report issues with:
   - Windows version
   - Python version (`python --version`)
   - Node.js version (`node --version`)
   - Error messages (screenshots)

### For Developers

1. Test on clean VM before release
2. Monitor GitHub issues
3. Update documentation as needed
4. Consider automated builds (CI/CD)

---

## 📄 License

VDock Portable Edition follows the same license as the main project. See `LICENSE` file in the package.

---

*Last updated: October 21, 2025*  
*VDock Portable Distribution v1.0*

