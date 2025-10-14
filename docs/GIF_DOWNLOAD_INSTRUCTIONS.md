# Animated GIF Download Instructions

## Quick Start - Download Free Animated GIFs

### Recommended Free Sources

#### 1. **Loading.io** (https://loading.io/icon/)
**Best for**: Loading spinners, progress indicators
**License**: Free with attribution or purchase license

**Download Instructions:**
1. Go to https://loading.io/icon/
2. Browse the icon categories (spinner, progress, dots, etc.)
3. Click on any animation you like
4. Click "Download" → Select "GIF" format
5. Choose size: 128x128 or 256x256 pixels
6. Save to: `frontend/public/assets/animations/gifs/buttons/`

**Recommended Animations:**
- Spinner #1 → `loading-spinner.gif`
- Ripple → `pulse-circle.gif`
- Dots → `loading-dots.gif`

#### 2. **Icons8 Animated Icons** (https://icons8.com/animated-icons)
**Best for**: Icon animations, interactive elements
**License**: Free with link attribution

**Download Instructions:**
1. Go to https://icons8.com/animated-icons
2. Search for: "loading", "arrow", "check", "heart", "star"
3. Click on an animation
4. Select "Download" → Choose "GIF" format
5. Select size: 128 or 256 pixels
6. Save to: `frontend/public/assets/animations/gifs/buttons/`

**Recommended Downloads:**
- Checkmark animation → `check-success.gif`
- Heart beat → `heart-beat.gif`
- Star sparkle → `star-sparkle.gif`
- Gear rotation → `rotating-gear.gif`

#### 3. **LottieFiles** (https://lottiefiles.com/free)
**Best for**: Smooth, high-quality animations
**License**: Free (various licenses)

**Download Instructions:**
1. Go to https://lottiefiles.com/free
2. Search for animations: "button", "icon", "loading"
3. Click on animation → "Download"
4. Select "GIF" format (or use their online converter)
5. Export as 128x128 or 256x256
6. Save to: `frontend/public/assets/animations/gifs/buttons/`

#### 4. **Giphy** (https://giphy.com)
**Best for**: Creative, fun animations
**License**: Giphy license (free for non-commercial)

**Search Terms:**
- "loading icon transparent"
- "animated button icon"
- "spinning gear transparent"
- "pulse circle transparent"

**Download Instructions:**
1. Search on Giphy
2. Click animation → "..." menu → "Download"
3. Choose "Small" or "Medium" size
4. Use an online tool to resize if needed
5. Save to: `frontend/public/assets/animations/gifs/buttons/`

#### 5. **Flaticon Animated** (https://www.flaticon.com/animated-icons)
**Best for**: Professional icon animations
**License**: Free with attribution

**Download Instructions:**
1. Go to https://www.flaticon.com/animated-icons
2. Search categories
3. Download as GIF
4. Resize to 128x128 if needed
5. Save to: `frontend/public/assets/animations/gifs/buttons/`

## Quick Download Script

I've created a guide for each specific animation needed:

### 1. Loading Spinner
**Source**: https://loading.io/spinner/double-ring/-rotating-ring
- Download as GIF, 128x128
- Save as: `loading-spinner.gif`

### 2. Pulse Circle
**Source**: https://loading.io/spinner/ripple/-broadcast-ripple-radio-waves
- Download as GIF, 128x128
- Save as: `pulse-circle.gif`

### 3. Bouncing Arrow
**Source**: https://icons8.com/animated-icons/arrow (search "arrow down")
- Download as GIF, 128x128
- Save as: `bouncing-arrow.gif`

### 4. Rotating Gear
**Source**: https://icons8.com/animated-icons/settings (gear icon)
- Download as GIF, 128x128
- Save as: `rotating-gear.gif`

### 5. Wave Ripple
**Source**: https://loading.io/spinner/ripple
- Download as GIF, 128x128
- Save as: `wave-ripple.gif`

### 6. Check Success
**Source**: https://icons8.com/animated-icons/checkmark
- Download as GIF, 128x128
- Save as: `check-success.gif`

### 7. Heart Beat
**Source**: https://icons8.com/animated-icons/heart
- Download as GIF, 128x128
- Save as: `heart-beat.gif`

### 8. Star Sparkle
**Source**: https://icons8.com/animated-icons/star
- Download as GIF, 128x128
- Save as: `star-sparkle.gif`

### 9. Fire Flame
**Source**: https://icons8.com/animated-icons/fire
- Download as GIF, 128x128
- Save as: `fire-flame.gif`

### 10. Lightning Bolt
**Source**: https://icons8.com/animated-icons/lightning
- Download as GIF, 128x128
- Save as: `lightning-bolt.gif`

## Alternative: Generate GIFs Using Free Tools

### Using Canva (Free)
1. Create a design at 128x128 or 256x256
2. Add animated elements
3. Download as GIF
4. Save to assets folder

### Using Figma + Plugins
1. Design icon at 128x128
2. Use "Figmotion" plugin for animation
3. Export as GIF
4. Save to assets folder

## Optimization After Download

Use ImageMagick or online tools to optimize:

```bash
# Resize to 128x128
convert input.gif -resize 128x128 output.gif

# Optimize file size
gifsicle -O3 --colors 128 input.gif -o output.gif
```

## Current Status

The following GIFs need to be downloaded and placed in:
`frontend/public/assets/animations/gifs/buttons/`

- [ ] loading-spinner.gif
- [ ] pulse-circle.gif
- [ ] bouncing-arrow.gif
- [ ] rotating-gear.gif
- [ ] wave-ripple.gif
- [ ] check-success.gif
- [ ] heart-beat.gif
- [ ] star-sparkle.gif
- [ ] fire-flame.gif
- [ ] lightning-bolt.gif

## Quick Links

- Loading.io: https://loading.io/icon/
- Icons8 Animated: https://icons8.com/animated-icons
- LottieFiles: https://lottiefiles.com/free
- Flaticon Animated: https://www.flaticon.com/animated-icons

Once downloaded, the Asset Picker will automatically detect and display them!

