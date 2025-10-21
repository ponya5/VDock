# 📦 VDock Distribution Guide

**How to Package and Share VDock with Your Friends**

---

## 🎯 Quick Overview

This guide shows you how to package VDock into a ZIP file that you can easily share with friends. They'll be able to extract and run VDock without needing to install anything manually.

---

## 📋 Pre-Distribution Checklist

Before creating your distribution package, make sure:

- [ ] VDock is working correctly on your machine
- [ ] All dependencies are installed (check `requirements.txt`)
- [ ] Frontend is built (`npm run build` in frontend directory)
- [ ] No sensitive data in configuration files
- [ ] `.env` files are NOT included (only `.env.example`)

---

## 🚀 Method 1: Quick ZIP (Recommended for Friends)

### Step 1: Clean Up Development Files

Open PowerShell or Command Prompt in the VDock directory and run:

```powershell
# Remove Python cache files
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse | Remove-Item -Recurse -Force

# Remove node_modules (will be reinstalled by user)
Remove-Item "frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# Remove Python virtual environment (will be created by user)
Remove-Item "backend\venv" -Recurse -Force -ErrorAction SilentlyContinue

# Remove user data
Remove-Item "backend\data\profiles\*.json" -Force -ErrorAction SilentlyContinue
Remove-Item "backend\data\uploads\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "backend\data\*.log" -Force -ErrorAction SilentlyContinue

# Remove .env files (keep .env.example)
Remove-Item "backend\.env" -Force -ErrorAction SilentlyContinue
Remove-Item "frontend\.env" -Force -ErrorAction SilentlyContinue
```

### Step 2: Create the ZIP File

#### Windows (PowerShell):
```powershell
# Navigate to parent directory
cd ..

# Create ZIP file
Compress-Archive -Path "VDock" -DestinationPath "VDock-Portable.zip" -Force

Write-Host "✅ Created: VDock-Portable.zip"
```

#### Windows (Using 7-Zip if installed):
```cmd
cd ..
7z a -tzip VDock-Portable.zip VDock -xr!node_modules -xr!venv -xr!__pycache__ -xr!*.pyc
```

#### macOS/Linux:
```bash
cd ..
zip -r VDock-Portable.zip VDock -x "*/node_modules/*" "*/venv/*" "*/__pycache__/*" "*.pyc" "*.log" "*/.env"
```

### Step 3: Share the ZIP File

The `VDock-Portable.zip` file is now ready to share! You can:
- Upload to Google Drive, Dropbox, or OneDrive
- Share via WeTransfer or similar services
- Upload to GitHub Releases (if you have a repo)

**Typical file size:** 50-100 MB (without node_modules and venv)

---

## 📥 Instructions for Your Friends

Include these instructions with the ZIP file:

### For Windows Users:

1. **Extract the ZIP file**
   - Right-click `VDock-Portable.zip` → Extract All
   - Choose a location (e.g., `C:\VDock`)

2. **Install the app**
   - Double-click `install.bat`
   - Wait for installation to complete (5-10 minutes)

3. **Launch VDock**
   - Double-click the "VDock" shortcut on your desktop
   - OR double-click `launch.bat` in the VDock folder

4. **First time setup**
   - The app will open in your browser at `http://localhost:3000`
   - Default password: `admin` (change this immediately in settings!)

### For macOS/Linux Users:

1. **Extract the ZIP file**
   ```bash
   unzip VDock-Portable.zip
   cd VDock
   ```

2. **Install the app**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Launch VDock**
   ```bash
   ./launch.sh
   ```

---

## 🔧 Method 2: Advanced Distribution (With Pre-built Frontend)

This method includes the built frontend, so users don't need to run `npm install`:

### Step 1: Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 2: Clean and Prepare

```powershell
# Clean development files (same as Method 1)
# ... run cleanup commands from Method 1 ...

# Verify frontend build exists
Test-Path "frontend\dist"  # Should return True
```

### Step 3: Create Distribution ZIP

```powershell
cd ..
Compress-Archive -Path "VDock" -DestinationPath "VDock-Complete.zip" -Force -CompressionLevel Optimal
```

**File size:** ~100-150 MB (includes built frontend)

---

## 🎨 Method 3: Minimal Distribution (Developers Only)

For sharing with other developers who want to modify the code:

### What to Include:
- Source code (all `.py`, `.vue`, `.ts` files)
- Configuration files (`.env.example`, `package.json`, `requirements.txt`)
- Documentation (`docs/` folder)
- Installation scripts (`install.bat`, `install.sh`)

### What to Exclude:
- `node_modules/`
- `venv/` or any virtual environments
- `__pycache__/` and `*.pyc` files
- `.env` files (keep `.env.example`)
- `frontend/dist/` and `frontend/build/`
- `backend/data/profiles/` (user data)
- `backend/data/uploads/` (user uploads)
- Log files (`*.log`)

---

## 📋 Create a README for Distribution

Create a simple `SETUP.md` file to include with your distribution:

```markdown
# VDock Setup Instructions

## Quick Start

### Windows:
1. Extract all files
2. Run `install.bat`
3. Run `launch.bat`

### macOS/Linux:
1. Extract all files
2. Run `chmod +x install.sh && ./install.sh`
3. Run `./launch.sh`

## First Login
- Open: http://localhost:3000
- Default password: admin
- **Change the password immediately in Settings!**

## Requirements
- Python 3.8+ (will be installed if missing)
- Node.js 16+ (will be installed if missing)

## Support
For issues, check the docs/ folder or visit [your support link]

## Security Notes
- Always change the default password
- Don't expose VDock to the internet without proper security
- Keep your .env file private

Enjoy VDock! 🎉
```

---

## 🔒 Security Notes for Distribution

### Important Warnings:

1. **Remove ALL sensitive data before sharing:**
   - API keys
   - Passwords
   - Personal profiles
   - Upload files
   - Log files

2. **Include security reminders:**
   - Tell users to change default passwords
   - Warn against exposing the app to the internet
   - Remind them to set strong passwords

3. **Check `.env.example`:**
   - Make sure it doesn't contain real credentials
   - Ensure all sensitive values are placeholders

### Verification Command:

```powershell
# Search for potential sensitive data
Select-String -Path "backend\*.env" -Pattern "api_key|password|secret" -CaseSensitive
```

---

## 📊 Distribution Package Sizes

| Package Type | Includes | Size (approx) |
|--------------|----------|---------------|
| **Minimal** | Source code only | ~20-30 MB |
| **Standard** | Source + Scripts | ~50-70 MB |
| **Complete** | Built frontend included | ~100-150 MB |
| **With venv** | Python packages pre-installed | ~300-500 MB |

**Recommendation:** Use **Standard** package for most users.

---

## 🎯 Automated Distribution Script

Create `create-distribution.ps1`:

```powershell
# VDock Distribution Creator
Write-Host "Creating VDock distribution package..." -ForegroundColor Cyan

# Clean up
Write-Host "Cleaning development files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__,*.pyc -Recurse | Remove-Item -Recurse -Force
Remove-Item "frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "backend\venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "backend\data\profiles\*.json" -Force -ErrorAction SilentlyContinue
Remove-Item "backend\data\*.log" -Force -ErrorAction SilentlyContinue
Remove-Item "backend\.env" -Force -ErrorAction SilentlyContinue

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
cd frontend
npm run build
cd ..

# Create ZIP
Write-Host "Creating ZIP file..." -ForegroundColor Yellow
cd ..
Compress-Archive -Path "VDock" -DestinationPath "VDock-v1.0.zip" -Force

Write-Host "✅ Distribution package created: VDock-v1.0.zip" -ForegroundColor Green
Write-Host "File size: $((Get-Item 'VDock-v1.0.zip').Length / 1MB) MB" -ForegroundColor Cyan
```

Usage:
```powershell
.\create-distribution.ps1
```

---

## 🤝 Sharing Best Practices

### Good Practices:
- ✅ Test the ZIP on another machine before sharing
- ✅ Include installation instructions
- ✅ Mention system requirements
- ✅ Provide support contact info
- ✅ Include a CHANGELOG if updated

### What NOT to Do:
- ❌ Don't include your personal data
- ❌ Don't include real API keys
- ❌ Don't share `.env` files
- ❌ Don't include unnecessary dependencies
- ❌ Don't forget to test the package first

---

## 📞 Troubleshooting for Users

Common issues your friends might encounter:

### "Python not found"
- Install Python 3.8+ from python.org
- Make sure "Add Python to PATH" is checked during installation

### "npm not found"
- Install Node.js from nodejs.org
- Restart terminal after installation

### "Port 5000 already in use"
- Close other applications using port 5000
- Or change PORT in backend/.env

### "Cannot connect to backend"
- Make sure backend is running (check backend terminal)
- Check firewall settings
- Try http://127.0.0.1:3000 instead of localhost

---

## 🎉 You're Done!

Your VDock distribution package is ready to share with friends! They'll have a fully functional virtual stream deck in just a few clicks.

**Questions?** Check the full documentation in `docs/` folder.

---

*Last updated: October 21, 2025*
