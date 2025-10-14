# VDock Asset Repository

Welcome to the VDock Asset Repository! This directory contains all visual assets used throughout the VDock application, including icons, animations, and backgrounds.

## 📁 Directory Structure

```
assets/
├── icons/                      # Icon collections
│   ├── fontawesome-extended/   # Extended FontAwesome icon categories
│   │   ├── system/            # System & OS icons
│   │   ├── media/             # Media control icons
│   │   ├── gaming/            # Gaming & entertainment icons
│   │   ├── productivity/      # Productivity & work icons
│   │   ├── streaming/         # Streaming & content creation icons
│   │   └── social/            # Social media icons
│   ├── custom/                # Custom icon collections
│   │   ├── svg/              # SVG format icons
│   │   └── png/              # PNG format icons
│   ├── themed-sets/           # Themed icon collections
│   │   ├── gaming/           # Gaming theme
│   │   ├── productivity/     # Productivity theme
│   │   ├── streaming/        # Streaming theme
│   │   └── creative/         # Creative theme
│   └── index.json            # Icon metadata
├── animations/                 # Animated assets
│   ├── gifs/                  # GIF animations
│   │   ├── buttons/          # Button animations
│   │   ├── backgrounds/      # Background animations
│   │   └── effects/          # Effect animations
│   ├── videos/                # Video assets
│   │   ├── buttons/          # Button videos
│   │   └── backgrounds/      # Background videos
│   └── index.json            # Animation metadata
├── backgrounds/               # Background assets
│   ├── dashboard/            # Dashboard backgrounds
│   │   ├── gradients/       # CSS gradients
│   │   ├── patterns/        # Pattern backgrounds
│   │   ├── images/          # Static images
│   │   ├── animated/        # Animated backgrounds
│   │   └── dynamic/         # Dynamic/video backgrounds
│   ├── buttons/              # Button backgrounds
│   │   ├── static/          # Static button backgrounds
│   │   ├── animated/        # Animated button backgrounds
│   │   └── video/           # Video button backgrounds
│   └── index.json           # Background metadata
├── attribution/              # License & attribution info
│   ├── licenses.json        # License details
│   └── sources.json         # Asset sources
└── metadata.json            # Master metadata file
```

## 🎨 Asset Categories

### Icons

#### FontAwesome Extended (96+ icons)
- **System**: Power, restart, sleep, lock, settings, network, wifi, etc.
- **Media**: Play, pause, stop, volume controls, music, video, etc.
- **Gaming**: Controllers, platforms (Xbox, PlayStation, Steam), dice, trophy, etc.
- **Productivity**: Calendar, tasks, clock, charts, briefcase, lightbulb, etc.
- **Streaming**: Broadcast, camera, microphone, OBS, chat, donations, etc.
- **Social**: Facebook, Twitter, Instagram, Discord, Twitch, GitHub, etc.

#### Custom Icons (8+ icons)
- SVG icons from Heroicons, Lucide, Feather, Phosphor
- High-quality, scalable vector graphics
- MIT licensed from trusted open-source projects

#### Themed Sets (40+ icons)
- **Gaming**: Curated gaming-focused icons
- **Productivity**: Work and productivity icons
- **Streaming**: Content creation icons
- **Creative**: Artistic and design icons

### Backgrounds

#### Dashboard Gradients (10 gradients)
- Ocean Breeze, Sunset Glow, Forest Mist
- Royal Purple, Golden Hour, Midnight City
- Emerald Water, Cosmic Fusion, Arctic Paradise, Velvet Sun

#### Dashboard Patterns (8 patterns)
- Circuit Board, Hexagon Grid, Wave Pattern
- Diamond Grid, Dot Matrix, Triangular Mesh
- Crosshatch, Spiral Pattern

#### Button Backgrounds
- Static image backgrounds
- Animated GIF backgrounds
- Video backgrounds (< 5MB)

### Animations

#### GIF Animations (5+ animations)
- Loading Spinner, Pulse Glow, Bounce Arrow
- Rotating Gear, Wave Ripple
- Optimized for button use, high quality

#### Video Assets
- Premium quality video backgrounds
- Optimized for < 5MB file size
- Loopable and performant

## 📝 Asset Metadata Format

Each asset category includes an `index.json` file with metadata:

```json
{
  "category": "category-name",
  "description": "Category description",
  "assets": [
    {
      "id": "unique-asset-id",
      "name": "Display Name",
      "tags": ["tag1", "tag2"],
      "url": "/assets/path/to/asset",
      "format": "svg|png|gif|mp4|css",
      "color": "#hexcolor",
      "size": 1024,
      "dimensions": { "width": 128, "height": 128 }
    }
  ]
}
```

## 🔍 Using Assets in VDock

### Through the Asset Picker
1. Open Button Editor
2. Click "Browse Icons", "Browse Media", or "Browse Backgrounds"
3. Search, filter, and preview assets
4. Select an asset to apply it to your button

### Programmatically
```typescript
import { assetManager } from '@/utils/assetManager'

// Search for assets
const results = assetManager.searchAssets('gaming', 'icon')

// Get asset by ID
const asset = assetManager.getAsset('game-controller-xbox')

// Get all assets in a category
const icons = assetManager.getAssetsByCategory('fontawesome-gaming')
```

## 📄 Licensing & Attribution

All assets in this repository are properly licensed and attributed:

### Licenses Used
- **MIT License**: Most custom icons (Heroicons, Lucide, Feather, Phosphor)
- **FontAwesome Free**: FontAwesome icons (Font Awesome Free License)
- **CC0**: Some public domain assets
- **CC-BY-4.0**: Creative Commons with attribution

### Attribution Files
- `attribution/licenses.json`: Detailed license information
- `attribution/sources.json`: Asset source tracking

### Adding New Assets
When adding new assets, ensure:
1. Proper licensing (open-source or compatible)
2. Update relevant `index.json` files
3. Add attribution to `attribution/sources.json`
4. Optimize file sizes (< 5MB for videos/GIFs)
5. Use descriptive IDs and tags

## 🎯 Asset Guidelines

### Icons
- **Format**: SVG preferred, PNG acceptable
- **Size**: 64x64 to 256x256 pixels
- **Color**: Single color or multi-color
- **Naming**: kebab-case (e.g., `game-controller-xbox`)

### Animations (GIF)
- **Format**: GIF
- **Size**: < 2MB for buttons, < 5MB for backgrounds
- **Dimensions**: 64x64 to 512x512 pixels
- **Optimization**: Use tools like gifsicle or ImageMagick

### Animations (Video)
- **Format**: MP4 (H.264) or WebM
- **Size**: < 5MB
- **Dimensions**: 720p or 1080p
- **Optimization**: Use ffmpeg with appropriate compression

### Backgrounds
- **Gradients**: CSS format (linear-gradient, radial-gradient)
- **Images**: JPG/PNG, optimized for web
- **Patterns**: CSS or SVG
- **Videos**: MP4/WebM, < 5MB, loopable

## 🚀 Performance Considerations

### Asset Loading
- Assets are lazy-loaded when needed
- Metadata is cached in memory
- Progressive loading for large collections

### Optimization
- All images are web-optimized
- Videos are compressed for web delivery
- CSS gradients have zero file size
- FontAwesome icons are vector-based

### Caching
- Browser caching enabled for all assets
- Asset manager maintains in-memory cache
- Metadata is loaded once on initialization

## 🔧 Maintenance

### Adding New Assets
1. Place asset file in appropriate directory
2. Update corresponding `index.json`
3. Add attribution if from external source
4. Test in Asset Picker

### Removing Assets
1. Delete asset file
2. Remove from `index.json`
3. Update any references in codebase
4. Clean up attribution records

### Updating Metadata
- Run asset scanner to regenerate metadata
- Verify all links and references
- Update version numbers

## 📊 Statistics

- **Total Icons**: 130+ across all categories
- **Total Backgrounds**: 18 gradients & patterns
- **Total Animations**: Framework for unlimited assets
- **File Size**: Optimized for web delivery
- **Load Time**: < 100ms for metadata

## 🤝 Contributing

When contributing new assets:
1. Ensure proper licensing
2. Optimize file sizes
3. Follow naming conventions
4. Update metadata files
5. Add attribution information
6. Test in the application

## 📞 Support

For issues or questions about assets:
- Check the asset metadata files
- Review attribution information
- Consult the VDock documentation
- Open an issue on GitHub

---

**Last Updated**: October 14, 2024  
**Version**: 1.0.0  
**Maintainer**: VDock Development Team
