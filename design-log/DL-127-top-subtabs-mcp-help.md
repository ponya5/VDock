# DL-127 — In-content top sub-tabs + MCP help & self-test

## Problem

Two navigation complaints:

1. Appearance's sub-pages (Buttons / Layout & sidebar / Background /
   Screen saver) hide inside a collapsed sidebar group — one extra click
   and zero visible affordance. Integrations is worse: a single long
   scroll of six unrelated sections (auto-switch, agent alerts,
   triggers, MCP, running apps, recent actions) with no navigation at
   all.
2. The MCP panel says "Let local agents act on the deck" and dumps a
   raw tool list — it never explains what MCP *is*, how to wire a client
   up, or lets you check it actually works.

## Design

**Top sub-tab bar** — a `.subtab-bar` strip inside `.main`, between the
sticky `.topbar` and the scrolling `.content`. It renders whenever the
active tab has sections, so both Appearance and Integrations get
always-visible section tabs:

- Appearance: Buttons · Layout & sidebar · Background · Screen saver
  (same ids as before — `appearanceSubTab` is unchanged).
- Integrations: new `integrationSubTab` — **Apps & scenes**
  (auto-switch + running apps, the app-follow pair), **Agent alerts**,
  **Triggers** (panel + the recent-actions activity list), **MCP
  server**.

The sidebar keeps only top-level items — the Appearance chevron and its
`.nav-sub` collapse go away.

URL + search keep working: `?tab=integration&sub=mcp` resolves the sub
per active tab (previously `sub` only mapped appearance ids), the
"Open in browser" standalone link carries the integration sub too, and
search entries gain `subTab` so "MCP server" lands on its own tab.
`topbarMeta` shows `Integrations · MCP server` per-sub crumbs.

**MCP info modal** (`components/settings/McpInfoModal.vue`) — a `?`
button in the MCP panel head opens:

- What MCP is, in one paragraph (Model Context Protocol — the standard
  way agents call tools; VDock's endpoint makes the deck a tool server).
- The capability list grouped as Control (press buttons, run actions,
  switch scenes, push notifications) vs Read state (deck info, scenes,
  buttons, volume, now-playing, agent states) vs Write (set volume).
- Copy-pasteable client configs: Cursor `.cursor/mcp.json`, Claude
  Desktop via `mcp-remote`, and a raw curl `initialize` — the same
  snippets `docs/mcp.md` ships.
- Access notes: localhost-only by default; Bearer JWT when auth is on.
- **Self-test**: POSTs `[initialize, tools/list]` as one batch through
  `apiClient`, then reports "N tools in X ms" on success, the server's
  own error on 503 (disabled), or unreachable on network failure.

## Trade-offs

- Top tabs duplicate the role the sidebar sub-nav played for Appearance
  only; other tabs have no subs so the bar simply doesn't render — no
  layout shift for single-page tabs.
- Recent-actions (the raw action-id activity list) moves under Triggers
  rather than getting a sixth tab — it's automation activity, and the
  honest grouping beats a mostly-empty tab.
- Self-test goes through `apiClient` so it exercises the real auth path
  too — when `REQUIRE_AUTH` is on, a stale token surfaces as the gate,
  not a fake green check.

## Implementation Results

Shipped as designed:

- `SettingsView.vue`: `.subtab-bar` tablist strip renders under the
  topbar for any tab with sections; the Appearance sidebar group is a
  plain nav item again (collapse, chevron and `.nav-sub` styles all
  removed — dead selectors purged from the touch-action/reduced-motion
  lists too, and the new `.subtab` added to both so touch + a11y behavior
  match the buttons that were there before).
- `integrationSubTab` + `integrationSubs` (apps / alerts / triggers /
  mcp); each integration `<section>`/`TriggersPanel` is `v-if`-gated by
  sub. `PAGE_META` gained `integration/*` crumbs so the topbar reads
  "Integrations · MCP server" etc.
- `?tab=integration&sub=mcp` resolves correctly;
  `openSettingsInBrowserTab` carries the integration sub; search entries
  for all five integration settings now carry `subTab` so results land
  on the right section.
- `components/settings/McpInfoModal.vue`: explanation + grouped
  capability list + Cursor / Claude Desktop / curl snippets (each with a
  Copy button via `navigator.clipboard` + toast) + access/limitations
  notes + the self-test.

Self-test: one `[initialize, tools/list]` batch POST through
`apiClient`. Success → "Connected — vdock X.Y, N tools in M ms";
failures surface the server's own JSON-RPC error, "disabled" on 503,
"endpoint unreachable" on network failure, and "malformed response" when
`serverInfo`/`tools` are missing. Disabled while `mcpEnabled` is off.

Verified live via Playwright on the production bundle: `?sub=mcp` lands
on the MCP tab with only that section rendered; the modal opens from
"Help & test"; real self-test → **"Connected — vdock 2.1.0, 11 tools in
5 ms"**; Appearance shows 4 top tabs with the live-preview rail intact.
`settings-subtabs.test.ts` (12 tests: source assertions + mounted modal
behavior incl. disabled/RPC-error/503/malformed paths). Suite: 490
frontend tests, vue-tsc clean, dist rebuilt.
