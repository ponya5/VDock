# DL-079: Backfill factory scenes + IDE scene → agent-bar resolution

## Background

Reported on a first launch over a pre-existing profile (scenes: `Home`,
migrated `Media`, hand-added `Claude`):

1. The profile never got the factory IDE scenes — `createDefaultProfile()`
  seeds Media + Claude Code + Cursor + Websites for new profiles, but
  `setProfile`'s migration appends only Media when `isDefault` is missing.
2. The manually-added "Claude" template scene never showed the agent status
  bar: it stamps `appId: 'claude'` (a plugin id, not an app-profile id), and
  `resolveSceneProfileId` returns a stamped `appId` verbatim — an unknown id
  dead-ends resolution and shadows the command-vote/exe fallbacks.

User direction: backfill **all** missing factory scenes; fix resolution for
Claude **and** other IDEs; resolution-only fix (no new UI surfaces).

## Design

### Backfill (one-shot)

- `FACTORY_SEED_SCENES` in `defaultProfile.ts` — ordered
  `{ key, name, build }` list (Claude Code, Cursor, Websites) shared by
  `createDefaultProfile` and the migration.
- `Profile.factorySeedsApplied?: string[]` records applied/present seed keys
  → a deliberately deleted seed stays deleted (unlike Media, which must
  always exist as the `isDefault` scene). A same-named scene counts as
  present, matching the `isFactoryIdeSceneName` convention.

### Resolution (appDetection.ts)

`resolveSceneProfileId` order becomes:

1. `appId` via `canonicalAppId()` (`APP_ID_ALIASES`: `claude`→`claude-code`,
  `github-copilot`→`copilot`), trusted while profiles are unloaded or when it
  names a loaded profile; otherwise falls through.
2. Button command/action-type votes (unchanged).
3. `triggeredByApp`/integration exe (unchanged).
4. Scene name normalized-equal to a profile id, label, or alias key.

`canonicalAppId` lives in `data/appBackgrounds.ts` so `appBackgroundById`
applies the same alias — a `Claude` scene also gets the bundled Claude Code
wallpaper. The two factory IDE scenes get `appId` stamped — previously they
resolved only via button votes and therefore had no bundled wallpaper either
(`appForScene` doesn't consult votes).

Out of scope: `createSceneForApp` button upgrades, a SceneEditor app picker.

## Implementation Results

Both halves landed as designed:

- `defaultProfile.ts` — exported `FACTORY_SEED_SCENES` (Claude Code → Cursor →
  Websites), `createDefaultProfile` builds from it; `seedScene` gained an
  optional `appId` param and both factory IDE scenes are stamped
  (`claude-code`, `cursor`).
- `types/index.ts` — `Profile.factorySeedsApplied?: string[]`.
- `stores/dashboard.ts` — `setProfile` backfills missing factory seeds once,
  name-deduped, marker persisted on the profile.
- `data/appBackgrounds.ts` — `APP_ID_ALIASES` (`claude`→`claude-code`,
  `github-copilot`→`copilot`), `normalizeAppKey`, `canonicalAppId`;
  `appBackgroundById` resolves through it.
- `services/appDetection.ts` — `resolveSceneProfileId`: aliased `appId`
  trusted only pre-load/when it names a real profile, then command votes →
  exe → new `profileIdBySceneName` fallback (normalized id/label/alias
  equality); `SceneLink` gained `name`.

### Verification

- Frontend: 59 files / 260 tests green; `vue-tsc --noEmit` clean.
- New tests pin: alias resolution (`appId:'claude'` → `claude-code`),
  unknown-`appId` fall-through to command votes, name matching
  (`'Cursor'`→`cursor`, `'Claude Code'`/`'Claude'`→`claude-code`,
  `'My Cursor tricks'`→null), and the one-shot backfill (append once, no
  dup on reload, deleted seed stays deleted, same-named scene counts as
  present).
- One pre-existing test's assertion ("default scene is last") was stale by
  construction after the backfill — updated to assert the real invariant
  (index 0 untouched, exactly one `isDefault`, default sits right after the
  pre-existing scenes).

### Live verification (running app, dev servers + Chrome DevTools)

- Scene nav on the pre-existing profile:
  `Home, Media, Claude, Claude Code, Cursor, Websites` — backfilled seeds
  appear, the hand-made `Claude` scene is preserved, and after a reload each
  scene appears exactly once (backfill is idempotent).
- `Claude` scene (manually added, `appId:'claude'`): `.agent-action-bar`
  renders — state pill "Claude Code / Status unavailable", target chip
  "No session", actions Submit / Continue / Interrupt, all enabled. Scene
  also renders the bundled `claude-code.png` wallpaper via the same alias.
- `Claude Code` (backfilled): identical bar. `Cursor` (backfilled): bar with
  its own state actions (Submit / Continue / Stop / New Chat).
- Negative cases: `Media` and `Home` scenes show no agent bar.
- Screenshot captured during verification shows the bar over the Claude Code
  wallpaper on the `Claude` scene.
