# VDock Asset Upload Guide

## 📁 Complete Folder Structure

All assets are stored in the `frontend/public/assets/` directory, which is publicly accessible by the frontend.

```
frontend/public/assets/
├── icons/                          # Button Icons
│   ├── animated/                   # ✨ ANIMATED GIF ICONS FOR BUTTONS
│   │   ├── loading-spinner.gif
│   │   ├── pulse-glow.gif
│   │   ├── heart-beat.gif
│   │   └── ... (your GIF files)
│   ├── static/                     # Static PNG/SVG icons
│   │   ├── custom-icon-1.png
│   │   ├── custom-icon-2.svg
│   │   └── ... (your icon files)
│   └── index.json                  # Metadata (auto-generated)
│
├── buttons/                        # Button Backgrounds
│   ├── images/                     # 🖼️ STATIC IMAGE BACKGROUNDS
│   │   ├── texture-1.jpg
│   │   ├── pattern-1.png
│   │   └── ... (your images)
│   ├── gifs/                       # 🎬 ANIMATED GIF BACKGROUNDS
│   │   ├── gradient-flow.gif
│   │   ├── particles.gif
│   │   └── ... (your GIF files)
│   ├── videos/                     # 🎥 VIDEO BACKGROUNDS
│   │   ├── abstract-1.mp4
│   │   ├── neon-grid.webm
│   │   └── ... (your video files)
│   └── index.json                  # Metadata (auto-generated)
│
├── dashboard/                      # Dashboard Backgrounds
│   ├── images/                     # 🖼️ STATIC DASHBOARD BACKGROUNDS
│   │   ├── wallpaper-1.jpg
│   │   ├── pattern-1.png
│   │   └── ... (your images)
│   ├── gifs/                       # 🎬 ANIMATED DASHBOARD BACKGROUNDS
│   │   ├── ambient-1.gif
│   │   ├── subtle-motion.gif
│   │   └── ... (your GIF files)
│   ├── videos/                     # 🎥 VIDEO DASHBOARD BACKGROUNDS
│   │   ├── abstract-bg.mp4
│   │   ├── particles-bg.webm
│   │   └── ... (your video files)
│   └── index.json                  # Metadata (auto-generated)
│
└── uploads/                        # 📤 USER UPLOADS (via UI)
    ├── icons/
    ├── buttons/
    └── dashboard/
```

---

## 📤 Where to Upload Your Assets

### 1. Button Icons (Static & Animated)

**Folder**: `frontend/public/assets/icons/`

#### Static Icons
**Location**: `frontend/public/assets/icons/static/`
- **Formats**: PNG, SVG, JPG
- **Recommended Size**: 128x128 to 512x512 pixels
- **Max File Size**: 2 MB

#### Animated Icons
**Location**: `frontend/public/assets/icons/animated/`
- **Formats**: GIF
- **Recommended Size**: 128x128 to 256x256 pixels
- **Max File Size**: 2 MB
- **Frame Rate**: 15-30 FPS

**Examples**:
```
frontend/public/assets/icons/animated/
├── loading-spinner.gif      (Circular loading animation)
├── pulse-glow.gif           (Pulsing glow effect)
├── bouncing-arrow.gif       (Bouncing arrow)
├── rotating-gear.gif        (Gear rotation)
├── heart-beat.gif           (Beating heart)
├── star-sparkle.gif         (Sparkling star)
└── ... (your custom GIFs)
```

---

### 2. Button Backgrounds

**Folder**: `frontend/public/assets/buttons/`

#### Static Images
**Location**: `frontend/public/assets/buttons/images/`
- **Formats**: JPG, PNG, WebP
- **Recommended Size**: 256x256 to 512x512 pixels
- **Max File Size**: 5 MB

#### Animated GIFs
**Location**: `frontend/public/assets/buttons/gifs/`
- **Formats**: GIF
- **Recommended Size**: 256x256 to 512x512 pixels
- **Max File Size**: 3 MB
- **Optimization**: Use tools like gifsicle for compression

#### Videos
**Location**: `frontend/public/assets/buttons/videos/`
- **Formats**: MP4, WebM
- **Recommended Resolution**: 480p to 720p
- **Max File Size**: 5 MB
- **Codec**: H.264 (MP4) or VP9 (WebM)
- **Duration**: Short loops (5-15 seconds)

**Examples**:
```
frontend/public/assets/buttons/
├── images/
│   ├── carbon-fiber.jpg
│   ├── metal-texture.png
│   └── wood-grain.jpg
├── gifs/
│   ├── gradient-flow.gif
│   ├── particle-field.gif
│   └── energy-wave.gif
└── videos/
    ├── abstract-loop.mp4
    ├── neon-grid.webm
    └── liquid-motion.mp4
```

---

### 3. Dashboard Backgrounds

**Folder**: `frontend/public/assets/dashboard/`

#### Static Images
**Location**: `frontend/public/assets/dashboard/images/`
- **Formats**: JPG, PNG, WebP
- **Recommended Resolution**: 1920x1080 (Full HD) or 1280x720 (HD)
- **Max File Size**: 10 MB

#### Animated GIFs
**Location**: `frontend/public/assets/dashboard/gifs/`
- **Formats**: GIF
- **Recommended Resolution**: 1280x720 (HD)
- **Max File Size**: 10 MB
- **Note**: Large GIFs should be heavily optimized

#### Videos
**Location**: `frontend/public/assets/dashboard/videos/`
- **Formats**: MP4, WebM
- **Recommended Resolution**: 1920x1080 (Full HD) or 1280x720 (HD)
- **Max File Size**: 20 MB
- **Codec**: H.264 (MP4) or VP9 (WebM)
- **Duration**: Looping videos (15-60 seconds)
- **Optimization**: Use FFmpeg for compression

**Examples**:
```
frontend/public/assets/dashboard/
├── images/
│   ├── space-wallpaper.jpg
│   ├── abstract-art.png
│   └── minimalist-bg.jpg
├── gifs/
│   ├── subtle-particles.gif
│   ├── ambient-motion.gif
│   └── floating-shapes.gif
└── videos/
    ├── cosmic-nebula.mp4
    ├── particle-system.webm
    ├── gradient-waves.mp4
    └── geometric-flow.webm
```

---

## 🚀 Quick Upload Methods

### Method 1: Manual File Upload (Recommended)

1. **Navigate to the appropriate folder**
2. **Copy your files** into the folder
3. **Restart the frontend** to refresh the asset cache
4. **Files will be available immediately** in the Asset Picker

### Method 2: Web UI Upload (Coming Soon)

1. Go to Settings → Assets
2. Click "Upload Asset"
3. Select asset type (Icon/Button BG/Dashboard BG)
4. Choose file(s)
5. Add metadata (name, tags, description)
6. Upload
7. Asset available immediately

### Method 3: Bulk Upload Script

Use the provided upload script:

```bash
# Upload multiple icons
python scripts/upload_assets.py --type icons --folder /path/to/your/icons/

# Upload button backgrounds
python scripts/upload_assets.py --type buttons --folder /path/to/backgrounds/

# Upload dashboard backgrounds
python scripts/upload_assets.py --type dashboard --folder /path/to/dashboards/
```

---

## 📏 File Size & Format Guidelines

### Icons
| Type | Format | Size | Max File Size |
|------|--------|------|---------------|
| Static | PNG, SVG | 128-512px | 2 MB |
| Animated | GIF | 128-256px | 2 MB |

### Button Backgrounds
| Type | Format | Size | Max File Size |
|------|--------|------|---------------|
| Static | JPG, PNG, WebP | 256-512px | 5 MB |
| Animated | GIF | 256-512px | 3 MB |
| Video | MP4, WebM | 480-720p | 5 MB |

### Dashboard Backgrounds
| Type | Format | Resolution | Max File Size |
|------|--------|------------|---------------|
| Static | JPG, PNG, WebP | 1920x1080 | 10 MB |
| Animated | GIF | 1280x720 | 10 MB |
| Video | MP4, WebM | 1920x1080 | 20 MB |

---

## 🛠️ Asset Optimization Tools

### For GIFs
```bash
# Install gifsicle
brew install gifsicle  # Mac
apt-get install gifsicle  # Linux

# Optimize GIF
gifsicle -O3 --colors 128 input.gif -o output.gif

# Resize GIF
gifsicle --resize 256x256 input.gif > output.gif
```

### For Videos
```bash
# Install FFmpeg
brew install ffmpeg  # Mac
apt-get install ffmpeg  # Linux

# Compress video to < 5MB (for buttons)
ffmpeg -i input.mp4 -vf scale=720:720 -c:v libx264 -crf 28 -preset medium -c:a aac -b:a 128k output.mp4

# Compress video to < 20MB (for dashboard)
ffmpeg -i input.mp4 -vf scale=1920:1080 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k output.mp4

# Create looping video
ffmpeg -stream_loop -1 -i input.mp4 -t 30 -c copy output.mp4
```

### For Images
```bash
# Install ImageMagick
brew install imagemagick  # Mac
apt-get install imagemagick  # Linux

# Resize and optimize
convert input.jpg -resize 512x512 -quality 85 output.jpg

# Convert to WebP (better compression)
cwebp -q 80 input.jpg -o output.webp
```

---

## 📝 Asset Naming Conventions

### Good Names ✅
- `loading-spinner.gif`
- `carbon-fiber-texture.jpg`
- `neon-grid-animation.mp4`
- `space-wallpaper-4k.jpg`
- `heart-beat-icon.gif`

### Bad Names ❌
- `IMG_1234.gif`
- `Untitled.png`
- `asdasd.mp4`
- `New File (1).jpg`

**Rules**:
- Use lowercase
- Use hyphens (-) not spaces
- Be descriptive
- Include type/purpose in name

---

## 🎯 Asset Usage in VDock

### Button Icons

**Via ButtonEditor**:
1. Edit button
2. Icon Type: Custom Image
3. Click "Browse Icons"
4. Select your uploaded icon
5. Save

**Direct URL**:
```
/assets/icons/animated/loading-spinner.gif
/assets/icons/static/custom-icon.png
```

### Button Backgrounds

**Via ButtonEditor**:
1. Edit button
2. Background Media: GIF Animation / Video / Static Image
3. Click "Browse Media"
4. Select your uploaded background
5. Save

**Direct URL**:
```
/assets/buttons/gifs/gradient-flow.gif
/assets/buttons/videos/abstract-loop.mp4
/assets/buttons/images/texture.jpg
```

### Dashboard Backgrounds

**Via Settings**:
1. Settings → Appearance
2. Dashboard Background: Custom
3. Select from uploaded backgrounds
4. Apply

**Direct URL**:
```
/assets/dashboard/videos/cosmic-nebula.mp4
/assets/dashboard/gifs/ambient-motion.gif
/assets/dashboard/images/wallpaper.jpg
```

---

## 🔄 Refresh Assets After Upload

### Option 1: Auto-Refresh (Recommended)
- Assets are scanned every 5 minutes automatically
- New assets appear in Asset Picker automatically

### Option 2: Manual Refresh
1. Settings → Assets
2. Click "Refresh Asset Library"
3. All new assets will be indexed

### Option 3: Restart Frontend
```bash
cd frontend
npm run dev  # Development
npm run build  # Production
```

---

## 📊 Current Asset Statistics

After setup, you'll have:
- **Icons**: 130+ pre-installed + your uploads
- **Button Backgrounds**: 20+ pre-installed + your uploads
- **Dashboard Backgrounds**: 18+ pre-installed + your uploads

---

## 🎨 Free Asset Resources

### Icons (Animated)
- **Loading.io**: https://loading.io/icon/
- **Icons8 Animated**: https://icons8.com/animated-icons
- **LottieFiles**: https://lottiefiles.com/

### Button Backgrounds
- **Unsplash**: https://unsplash.com/
- **Pixabay**: https://pixabay.com/
- **Pexels**: https://www.pexels.com/

### Dashboard Backgrounds
- **Pexels Videos**: https://www.pexels.com/videos/
- **Pixabay Videos**: https://pixabay.com/videos/
- **Mixkit**: https://mixkit.co/

---

## 🚨 Troubleshooting

### Asset Not Showing Up
1. Check file is in correct folder
2. Verify file extension is supported
3. Check file size is under limit
4. Refresh asset library
5. Check browser console for errors

### Video Not Playing
1. Ensure codec is H.264 (MP4) or VP9 (WebM)
2. Check file size < 20MB
3. Verify video is not corrupted
4. Try different browser

### GIF Too Large
1. Use gifsicle to optimize
2. Reduce dimensions
3. Reduce color palette
4. Lower frame rate
5. Remove unnecessary frames

---

## 📞 Support

For issues:
1. Check file format and size
2. Verify folder structure
3. Check browser console
4. Review this guide
5. Check backend logs

---

**Happy Customizing! 🎨**
