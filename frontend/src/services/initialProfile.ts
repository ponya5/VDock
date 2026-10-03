import type { Profile } from '@/types'

/**
 * DL-147 (X7) — pick the profile a device lands on at boot, and decide when
 * (not) to create one.
 *
 * A phone/tablet that wakes on flaky Wi-Fi used to fall through "profile
 * fetch failed -> empty profile list -> create a brand new default profile",
 * leaving a duplicate "My VDock" on the server. Creation now needs a list
 * the backend actually answered, empty, on a desktop/panel device.
 */
export type InitialProfileOutcome =
  /** A profile was loaded into the dashboard. */
  | 'loaded'
  /** The backend could not be reached (or a profile fetch failed): offer Retry. */
  | 'unreachable'
  /** Backend reachable and empty, on a phone/tablet: set up on the desktop first. */
  | 'needs-desktop-setup'
  /** First run on a desktop/panel: a default profile was created. */
  | 'created'

export interface InitialProfileDeps {
  lastProfileId: string | null
  canCreateProfile: boolean
  getProfile: (id: string) => Promise<Profile | null>
  /** Resolves true when the backend answered the list request. */
  loadProfiles: () => Promise<boolean>
  profiles: () => Array<{ id: string }>
  setProfile: (profile: Profile) => void
  createDefaultProfile: () => Promise<void>
}

export async function loadInitialProfile(deps: InitialProfileDeps): Promise<InitialProfileOutcome> {
  if (deps.lastProfileId) {
    const profile = await deps.getProfile(deps.lastProfileId)
    if (profile) {
      deps.setProfile(profile)
      return 'loaded'
    }
  }

  const reachable = await deps.loadProfiles()
  const [first] = deps.profiles()
  if (first) {
    const profile = await deps.getProfile(first.id)
    if (profile) {
      deps.setProfile(profile)
      return 'loaded'
    }
    return 'unreachable'
  }

  if (!reachable) return 'unreachable'
  if (!deps.canCreateProfile) return 'needs-desktop-setup'
  await deps.createDefaultProfile()
  return 'created'
}
