// Avatar assets for profile selection
export interface Avatar {
  id: string
  name: string
  url: string
  type: 'image' | 'gif'
  category: 'animals' | 'characters' | 'abstract' | 'nature' | 'tech'
}

export const AVATARS: Avatar[] = [
  // Avatar Collection 1-9
  { id: 'avatar-1', name: 'Avatar 1', url: '/api/avatars/1.png', type: 'image', category: 'characters' },
  { id: 'avatar-2', name: 'Avatar 2', url: '/api/avatars/2.png', type: 'image', category: 'characters' },
  { id: 'avatar-3', name: 'Avatar 3', url: '/api/avatars/3.png', type: 'image', category: 'characters' },
  { id: 'avatar-4', name: 'Avatar 4', url: '/api/avatars/4.png', type: 'image', category: 'characters' },
  { id: 'avatar-5', name: 'Avatar 5', url: '/api/avatars/5.png', type: 'image', category: 'characters' },
  { id: 'avatar-6', name: 'Avatar 6', url: '/api/avatars/6.png', type: 'image', category: 'characters' },
  { id: 'avatar-7', name: 'Avatar 7', url: '/api/avatars/7.png', type: 'image', category: 'characters' },
  { id: 'avatar-8', name: 'Avatar 8', url: '/api/avatars/8.png', type: 'image', category: 'characters' },
  { id: 'avatar-9', name: 'Avatar 9', url: '/api/avatars/9.png', type: 'image', category: 'characters' },
  
  // Avatar Collection 10-18
  { id: 'avatar-10', name: 'Avatar 10', url: '/api/avatars/10.png', type: 'image', category: 'characters' },
  { id: 'avatar-11', name: 'Avatar 11', url: '/api/avatars/11.png', type: 'image', category: 'characters' },
  { id: 'avatar-12', name: 'Avatar 12', url: '/api/avatars/12.png', type: 'image', category: 'characters' },
  { id: 'avatar-13', name: 'Avatar 13', url: '/api/avatars/13.png', type: 'image', category: 'characters' },
  { id: 'avatar-14', name: 'Avatar 14', url: '/api/avatars/14.png', type: 'image', category: 'characters' },
  { id: 'avatar-15', name: 'Avatar 15', url: '/api/avatars/15.png', type: 'image', category: 'characters' },
  { id: 'avatar-16', name: 'Avatar 16', url: '/api/avatars/16.png', type: 'image', category: 'characters' },
  { id: 'avatar-17', name: 'Avatar 17', url: '/api/avatars/17.png', type: 'image', category: 'characters' },
  { id: 'avatar-18', name: 'Avatar 18', url: '/api/avatars/18.png', type: 'image', category: 'characters' }
]

export const AVATAR_CATEGORIES = [
  { id: 'animals', name: 'Animals', icon: 'fas fa-paw' },
  { id: 'characters', name: 'Characters', icon: 'fas fa-user' },
  { id: 'abstract', name: 'Abstract', icon: 'fas fa-shapes' },
  { id: 'nature', name: 'Nature', icon: 'fas fa-leaf' },
  { id: 'tech', name: 'Technology', icon: 'fas fa-microchip' }
]

export function getAvatarsByCategory(category: string): Avatar[] {
  return AVATARS.filter(avatar => avatar.category === category)
}

export function getAvatarById(id: string): Avatar | undefined {
  return AVATARS.find(avatar => avatar.id === id)
}
