type FontAwesomeIconTuple = [string, string]

export function normalizeFaIcon(icon: unknown): FontAwesomeIconTuple {
  if (Array.isArray(icon) && icon.length >= 2) {
    const prefix = String(icon[0] || 'fas')
    const iconName = String(icon[1] || 'circle-question').replace(/^fa-/, '')
    return [prefix, iconName]
  }

  if (typeof icon === 'string') {
    const trimmedIcon = icon.trim()
    if (!trimmedIcon) {
      return ['fas', 'circle-question']
    }

    if (trimmedIcon.includes(':')) {
      const [prefix, iconName] = trimmedIcon.split(':')
      return [prefix || 'fas', iconName.replace(/^fa-/, '')]
    }

    const parts = trimmedIcon.split(/\s+/)
    if (parts.length >= 2) {
      return [parts[0], parts[1].replace(/^fa-/, '')]
    }

    return ['fas', trimmedIcon.replace(/^fa-/, '')]
  }

  if (icon && typeof icon === 'object') {
    const iconRecord = icon as Record<string, unknown>

    if (typeof iconRecord.value === 'string') {
      return normalizeFaIcon(iconRecord.value)
    }

    if (typeof iconRecord.icon === 'string') {
      return normalizeFaIcon(iconRecord.icon)
    }
  }

  return ['fas', 'circle-question']
}
