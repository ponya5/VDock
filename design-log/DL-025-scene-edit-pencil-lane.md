# DL-025 — Scene Edit Pencil Lane (edit-mode pill overlap)

## Request

On the 7" (1024×600) panel, in edit mode the per-scene pencil badges in the
header overlapped the scene-pill labels — unreadable and cluttered.

## Root cause

`GlassPillSceneSelector` rendered an `.edit-badges` overlay layer inside the
pill container, positioning each badge at `(i+1) * segmentPercent%` —
equal-percentage boundaries. But `.segment` items are `flex: 0 1 auto`
(content-sized, `min-width: 96px`), so badges drifted off their real segment
edges and covered the truncated labels. The ~55px touch-scaled badge on a
~48px pill also spilled past the pill vertically.

## Approaches considered

- **Badge strip above pills** (container `padding-top`): works, but grows the
  header ~61px — pushes the dashboard grid down and clips the bottom row on a
  600px-tall screen (verified: `.theme-dark` is a hidden-overflow scroll
  container; it had scrolled 34px when the header grew). Rejected.
- **Lane on every pill** (`padding-right` on all segments): each pill grows
  ~56px → the row overflows into horizontal scroll. Rejected.
- **Lane on the active pill only** (chosen): one pencil, on the pill it
  edits. Tap another scene to move the pencil there. Zero overlap, minimal
  geometry change, unambiguous target.

## Implementation (`GlassPillSceneSelector.vue`)

- Badge moved from the `.edit-badges` overlay into its own `.segment` as an
  absolutely-positioned span (`role="button"`, Enter/Space wired,
  `@click.stop` so it doesn't trigger scene select).
- `.pill-edit .segment.is-active` gets `padding-right: badge + 12px` (the
  reserved lane) plus `min-width: 96px + badge + 14px` so icon + label keep
  ~50px+ of room beside it.
- Badge anchored `right: 5px; top: 50%; translateY(-50%)` — always its real
  segment edge, scrolls with horizontal pill overflow.
- `--pill-badge: clamp(34px, 44px*touch-multiplier, 44px)` — capped at 44px
  so it fits inside the pill.
- `.segment-label` gained `min-width: 0` — flex items can't shrink below
  intrinsic content width without it, so the label overflowed into the lane
  instead of ellipsizing.

## Verification (live, 1024×600)

- Exactly 1 badge, on the active segment; fully inside it (`insideSeg: true`)
- `overlapsLabel: false`, `overlapsIcon: false`
- Active pill widened 96→154px; label readable
- Header height unchanged; no layout shift of the grid
- vue-tsc clean; 49 files / 176 tests pass; build succeeds
