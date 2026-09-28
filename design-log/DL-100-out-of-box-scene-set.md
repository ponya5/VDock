# DL-100: Out-of-box scene set = Media + Claude Code; legacy scene prune

## Problem

Reported after upgrading to a build that includes DL-079's backfill:

- The factory seed list adds **Claude Code, Cursor and Websites** to every
  profile — the requested out-of-box set is **Media + Claude Code only**.
- Pre-existing profiles show stale scenes beside the seeds: a legacy `Home`
  scene (the pre-DL-047 default media scene — its buttons are exactly today's
  Media set, so it's a duplicate with an old name and layout) and a `Claude`
  scene applied from the AI Assistants template gallery (`appId: 'claude'`,
  seven web-shortcut buttons). An upgraded profile ends up showing
  Home + Media + Claude + Claude Code + Cursor + Websites.

## Design

### Seed set shrinks

`FACTORY_SEED_SCENES` → `[{ key: 'claude-code', name: 'Claude Code', build: createClaudeCodeScene }]`.
Cursor and Websites stop being seeded for new profiles and stop being
backfilled into old ones. `createCursorScene` stays — it's still the
"Reset to Default" builder in `FACTORY_IDE_SCENE_BUILDERS`. The now-dead
`createWebsitesScene` is removed (users can rebuild it from the template
gallery — nothing else referenced it). `createDefaultProfile` also stamps
`factorySeedsApplied` with all seed keys so a brand-new profile never enters
the legacy prune pass below.

### One-time legacy prune in `setProfile`

Same philosophy as `isUntouchedLegacyCursorScene`: delete only scenes that
are byte-identical to a known legacy origin — a user-customized scene never
matches, so it's never silently deleted.

The pass runs **only while `factorySeedsApplied` is absent** — i.e. exactly
once, on the first load under this version. Profiles created after this ships
carry the marker from `createDefaultProfile`, so a user who later adds a
"Claude" scene from the template gallery is never pruned (the marker is
already set).

- `isLegacyHomeScene`: `name === 'Home'` and the flattened action-type list
  equals the old default set in order: `volume_up, volume_down, volume_mute,
  media_play_pause, media_previous, media_next, media_stop`.
- `isLegacyClaudeScene`: `name === 'Claude'` and `appId === 'claude'` and the
  button labels equal the template gallery's Claude set in order
  (New Chat, Open Claude, Projects, Upload File, Copy Last, Console, Docs).

Order inside `setProfile`: migrate → ensure `isDefault` Media → legacy prune
→ factory backfill → set marker. A profile left with no `isDefault` scene
still gets Media appended first, so pruning Home can never strand a profile
without a default.

### Tests

Update `default-scene.test.ts` seed expectations (`Media + Claude Code`,
marker `['claude-code']`), add prune tests: untouched Home/Claude removed on
first load, customized variants survive, post-marker profiles never pruned.

## Implementation Plan

- [ ] `defaultProfile.ts`: trim `FACTORY_SEED_SCENES`, drop `createWebsitesScene`,
      add `isLegacyHomeScene`/`isLegacyClaudeScene`, stamp `factorySeedsApplied`
      in `createDefaultProfile`
- [ ] `dashboard.ts` `setProfile`: prune pass gated on marker absence
- [ ] Update + add tests in `default-scene.test.ts`

## Implementation Results

All three plan items landed, plus one deviation:

- `defaultProfile.ts` — `FACTORY_SEED_SCENES` is now `[claude-code]` only;
  `createWebsitesScene` deleted, `createCursorScene` kept (still reachable
  via `createFactoryIdeScene` → template gallery/reset). `createDefaultProfile`
  stamps `factorySeedsApplied: ['claude-code']` so a fresh profile never
  enters the legacy-prune path. `isLegacyHomeScene` /
  `isLegacyClaudeScene` exported signature checkers: Home = name 'Home' +
  exact ordered 7-action media set; Claude = name 'Claude' + `appId
  'claude'` + exact ordered 7-label template set.
- `dashboard.ts` — prune pass runs inside `setProfile` only when
  `factorySeedsApplied` is absent, and **before** the isDefault ensure
  (deviation: a pruned legacy `Home` carrying `isDefault` can no longer
  strand the profile without a default).
- Verified against this machine's real profile: Home (7 media actions,
  exact order) and Claude (`appId claude`, 7 template labels) match the
  signatures byte-for-byte → both prune; Media stays `isDefault`; Claude
  Code backfills. Net: Media + Claude Code.
- Tests — `default-scene.test.ts`: seed expectation `['Custom Scene',
  'Media', 'Claude Code']` + `factorySeedsApplied === ['claude-code']`;
  deleted-seed-stays-deleted now exercises Claude Code; three new prune
  tests (untouched Home+Claude pruned; customized Home survives; marked
  profile never prunes). `default-profile.test.ts`: name expectation to
  `['Media', 'Claude Code']`; the Cursor-density test now builds via
  `createFactoryIdeScene('Cursor')` since Cursor is no longer seeded.
- README "four working scenes" copy corrected to two.

**Tests:** vitest **325/325**, `vue-tsc` clean, `npm run build` clean
(`dist/` rebuilt — the panel loads the bundle).
