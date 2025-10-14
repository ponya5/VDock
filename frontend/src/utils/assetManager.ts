/**
 * Asset Manager Utility
 * Handles loading, caching, and management of VDock assets
 */

export interface AssetMetadata {
  id: string
  name: string
  category: string
  type: 'icon' | 'animation' | 'background'
  format: string
  size?: number
  dimensions?: { width: number; height: number }
  tags: string[]
  source?: string
  license?: string
  url: string
  thumbnail?: string
}

export interface AssetCategory {
  id: string
  name: string
  description: string
  assets: AssetMetadata[]
}

class AssetManager {
  private cache = new Map<string, any>()
  private metadata = new Map<string, AssetMetadata>()
  private categories = new Map<string, AssetCategory>()

  /**
   * Initialize the asset manager by loading metadata
   */
  async initialize(): Promise<void> {
    try {
      // Load master metadata
      const masterMetadata = await this.loadJSON('/assets/metadata.json')
      
      // Load icon categories
      await this.loadIconCategories()
      
      // Load animation categories
      await this.loadAnimationCategories()
      
      // Load background categories
      await this.loadBackgroundCategories()
      
      console.log('Asset Manager initialized successfully')
    } catch (error) {
      console.error('Failed to initialize Asset Manager:', error)
    }
  }

  /**
   * Load JSON file with caching
   */
  private async loadJSON(url: string): Promise<any> {
    if (this.cache.has(url)) {
      return this.cache.get(url)
    }

    try {
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error(`Failed to load ${url}: ${response.statusText}`)
      }
      
      const data = await response.json()
      this.cache.set(url, data)
      return data
    } catch (error) {
      console.error(`Error loading ${url}:`, error)
      return null
    }
  }

  /**
   * Load icon categories and metadata
   */
  private async loadIconCategories(): Promise<void> {
    const iconIndex = await this.loadJSON('/assets/icons/index.json')
    if (!iconIndex) return

    // Load FontAwesome extended categories
    for (const [categoryId, indexPath] of Object.entries(iconIndex.categories['fontawesome-extended'])) {
      const categoryData = await this.loadJSON(`/assets/${indexPath}`)
      if (categoryData) {
        const assets: AssetMetadata[] = categoryData.icons.map((icon: any) => ({
          id: icon.id,
          name: icon.name,
          category: `fontawesome-${categoryId}`,
          type: 'icon' as const,
          format: 'fontawesome',
          tags: icon.tags || [],
          url: '', // FontAwesome icons don't have URLs
          icon: icon.icon,
          color: icon.color
        }))

        this.categories.set(`fontawesome-${categoryId}`, {
          id: `fontawesome-${categoryId}`,
          name: `FontAwesome ${categoryId.charAt(0).toUpperCase() + categoryId.slice(1)}`,
          description: categoryData.description,
          assets
        })

        // Add to metadata map
        assets.forEach(asset => this.metadata.set(asset.id, asset))
      }
    }

    // Load custom icons
    for (const [formatId, indexPath] of Object.entries(iconIndex.categories.custom)) {
      const categoryData = await this.loadJSON(`/assets/${indexPath}`)
      if (categoryData && categoryData.icons) {
        const assets: AssetMetadata[] = categoryData.icons.map((icon: any) => ({
          id: icon.id,
          name: icon.name,
          category: `custom-${formatId}`,
          type: 'icon' as const,
          format: formatId,
          tags: icon.tags || [],
          url: icon.url,
          source: icon.source,
          license: icon.license,
          color: icon.color
        }))

        this.categories.set(`custom-${formatId}`, {
          id: `custom-${formatId}`,
          name: `Custom ${formatId.toUpperCase()}`,
          description: categoryData.description,
          assets
        })

        // Add to metadata map
        assets.forEach(asset => this.metadata.set(asset.id, asset))
      }
    }

    // Load themed icon sets
    for (const [themeId, indexPath] of Object.entries(iconIndex.categories['themed-sets'])) {
      const categoryData = await this.loadJSON(`/assets/${indexPath}`)
      if (categoryData && categoryData.icons) {
        const assets: AssetMetadata[] = categoryData.icons.map((icon: any) => ({
          id: icon.id,
          name: icon.name,
          category: `themed-${themeId}`,
          type: 'icon' as const,
          format: 'fontawesome',
          tags: icon.tags || [],
          url: '', // FontAwesome icons don't have URLs
          icon: icon.icon,
          color: icon.color
        }))

        this.categories.set(`themed-${themeId}`, {
          id: `themed-${themeId}`,
          name: `${categoryData.theme || themeId.charAt(0).toUpperCase() + themeId.slice(1)}`,
          description: categoryData.description,
          assets
        })

        // Add to metadata map
        assets.forEach(asset => this.metadata.set(asset.id, asset))
      }
    }
  }

  /**
   * Load animation categories and metadata
   */
  private async loadAnimationCategories(): Promise<void> {
    const animationIndex = await this.loadJSON('/assets/animations/index.json')
    if (!animationIndex) return

    // Load GIF animations
    for (const [categoryId, indexPath] of Object.entries(animationIndex.categories.gifs)) {
      const categoryData = await this.loadJSON(`/assets/${indexPath}`)
      if (categoryData && categoryData.animations) {
        const assets: AssetMetadata[] = categoryData.animations.map((anim: any) => ({
          id: anim.id,
          name: anim.name,
          category: `gif-${categoryId}`,
          type: 'animation' as const,
          format: 'gif',
          size: anim.size,
          dimensions: anim.dimensions,
          tags: anim.tags || [],
          url: anim.url,
          thumbnail: anim.thumbnail
        }))

        this.categories.set(`gif-${categoryId}`, {
          id: `gif-${categoryId}`,
          name: `GIF ${categoryId.charAt(0).toUpperCase() + categoryId.slice(1)}`,
          description: categoryData.description,
          assets
        })

        // Add to metadata map
        assets.forEach(asset => this.metadata.set(asset.id, asset))
      }
    }
  }

  /**
   * Load background categories and metadata
   */
  private async loadBackgroundCategories(): Promise<void> {
    const backgroundIndex = await this.loadJSON('/assets/backgrounds/index.json')
    if (!backgroundIndex) return

    // Load gradient backgrounds
    const gradientData = await this.loadJSON('/assets/backgrounds/dashboard/gradients/index.json')
    if (gradientData) {
      const assets: AssetMetadata[] = gradientData.gradients.map((gradient: any) => ({
        id: gradient.id,
        name: gradient.name,
        category: 'dashboard-gradients',
        type: 'background' as const,
        format: 'css',
        tags: gradient.tags || [],
        url: gradient.css,
        css: gradient.css,
        colors: gradient.colors
      }))

      this.categories.set('dashboard-gradients', {
        id: 'dashboard-gradients',
        name: 'Dashboard Gradients',
        description: 'CSS gradient backgrounds for dashboard',
        assets
      })

      // Add to metadata map
      assets.forEach(asset => this.metadata.set(asset.id, asset))
    }

    // Load pattern backgrounds
    const patternData = await this.loadJSON('/assets/backgrounds/dashboard/patterns/index.json')
    if (patternData) {
      const assets: AssetMetadata[] = patternData.patterns.map((pattern: any) => ({
        id: pattern.id,
        name: pattern.name,
        category: 'dashboard-patterns',
        type: 'background' as const,
        format: 'css',
        tags: pattern.tags || [],
        url: pattern.css,
        css: pattern.css
      }))

      this.categories.set('dashboard-patterns', {
        id: 'dashboard-patterns',
        name: 'Dashboard Patterns',
        description: 'CSS pattern backgrounds for dashboard',
        assets
      })

      // Add to metadata map
      assets.forEach(asset => this.metadata.set(asset.id, asset))
    }
  }

  /**
   * Get all categories
   */
  getCategories(): AssetCategory[] {
    return Array.from(this.categories.values())
  }

  /**
   * Get category by ID
   */
  getCategory(categoryId: string): AssetCategory | undefined {
    return this.categories.get(categoryId)
  }

  /**
   * Search assets by query
   */
  searchAssets(query: string, type?: 'icon' | 'animation' | 'background'): AssetMetadata[] {
    const results: AssetMetadata[] = []
    const searchTerm = query.toLowerCase()

    for (const asset of this.metadata.values()) {
      if (type && asset.type !== type) continue

      const matchesName = asset.name.toLowerCase().includes(searchTerm)
      const matchesTags = asset.tags.some(tag => tag.toLowerCase().includes(searchTerm))
      const matchesCategory = asset.category.toLowerCase().includes(searchTerm)

      if (matchesName || matchesTags || matchesCategory) {
        results.push(asset)
      }
    }

    return results
  }

  /**
   * Get assets by category
   */
  getAssetsByCategory(categoryId: string): AssetMetadata[] {
    const category = this.categories.get(categoryId)
    return category ? category.assets : []
  }

  /**
   * Get asset by ID
   */
  getAsset(assetId: string): AssetMetadata | undefined {
    return this.metadata.get(assetId)
  }

  /**
   * Get assets by type
   */
  getAssetsByType(type: 'icon' | 'animation' | 'background'): AssetMetadata[] {
    return Array.from(this.metadata.values()).filter(asset => asset.type === type)
  }

  /**
   * Preload asset (for images, videos, etc.)
   */
  async preloadAsset(asset: AssetMetadata): Promise<void> {
    if (asset.type === 'icon' && asset.format === 'fontawesome') {
      // FontAwesome icons don't need preloading
      return
    }

    if (asset.url && !this.cache.has(asset.url)) {
      try {
        if (asset.format === 'css') {
          // CSS gradients don't need preloading
          return
        }

        // For images and other media
        const response = await fetch(asset.url)
        if (response.ok) {
          const blob = await response.blob()
          this.cache.set(asset.url, blob)
        }
      } catch (error) {
        console.warn(`Failed to preload asset ${asset.id}:`, error)
      }
    }
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Get cache size
   */
  getCacheSize(): number {
    return this.cache.size
  }
}

// Export singleton instance
export const assetManager = new AssetManager()

// Auto-initialize when imported
assetManager.initialize()
