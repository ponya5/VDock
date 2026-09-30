# DL-121 — MCP server endpoint (JSON-RPC 2.0 over HTTP POST)

## Background

VDock already exposes the deck to humans (the panel UI) and to local agent
*hooks* (`/api/agent-events`). What it lacks is a tool surface for agent
*clients*: Claude Desktop, Cursor and other MCP-capable agents cannot press
deck buttons, switch scenes, or read panel state. Feature research §3 calls
for an MCP server so an agent can treat the deck as a set of tools.

MCP's "Streamable HTTP" transport is, at its core, a single POST endpoint
speaking JSON-RPC 2.0 (with an optional SSE upgrade for server-initiated
messages). VDock is a Werkzeug threading app — SSE long-lived connections are
not practical here — so we implement the POST/JSON-RPC subset, which is all
tool clients need to call `tools/list` + `tools/call`.

## Problem

- The deck's verbs (press a button, run an action, switch scene, notify) are
  scattered across socket handlers and internal services; none are reachable
  by an external agent.
- The endpoint must not become a remote-command hole: it is machine-local
  like the agent-hooks surface, with Bearer-token escape for setups where
  `Config.REQUIRE_AUTH` is on.
- `app.py` cannot be imported from a route module (circular import), so the
  action executor and socket emitter arrive via injected setters — and the
  module must degrade to honest `isError` tool results when they are absent.
- `services/now_playing.py` is being built in parallel (W1); the
  `get_now_playing` tool must tolerate its absence and its agreed contract:
  a `latest()` function returning the last emitted payload dict or `None`.

## Design

`backend/routes/mcp.py` — blueprint `mcp_bp`.

**Transport.** `POST /api/mcp` accepts a single JSON-RPC 2.0 message or a
batch array. `GET /api/mcp` answers `405 {"error": "POST only"}` so clients
probing for SSE get a clean answer instead of a 404. Batches of pure
notifications answer `202` with an empty body, per the JSON-RPC spec.

**Access.** Same `_localhost_only` pattern as `routes/agent_events.py`
(`request.remote_addr in 127.0.0.1/::1/localhost`). When
`Config.REQUIRE_AUTH` is true, a valid `Authorization: Bearer <jwt>`
(`auth.AuthManager.verify_token`) also passes — that is the documented way
to run an MCP client on another machine. Non-localhost without a token gets
401 when auth is enabled, 403 otherwise.

**Injection.** Module-level `_executor`/`_emitter` with
`set_executor(fn)`/`set_emitter(fn)`, mirroring `job_runner`/`agent_events`.
app.py wires `action_executor` and `socketio.emit` later; executor-dependent
tools (`press_button`, `run_action`) return an `isError` result when no
executor is injected rather than raising. `_executor` accepts either an
object with `.execute_action(action_data)` (the real `ActionExecutor`) or a
plain callable — both are what `set_executor` may reasonably receive.

**Methods.**

| Method | Result |
|---|---|
| `initialize` | `{protocolVersion:'2025-06-18', capabilities:{tools:{listChanged:false}}, serverInfo:{name:'vdock', version:'2.1.0'}}` |
| `ping` | `{}` |
| `notifications/*` | `null` (request form); notifications carry no `id` so they produce no response |
| `tools/list` | `{tools:[{name, description, inputSchema}]}` |
| `tools/call` `{name, arguments?}` | `{content:[{type:'text',text}], structuredContent, isError?}` |
| anything else | `-32601` |

Errors: `-32700` unparseable body, `-32600` invalid envelope (non-object,
missing `jsonrpc:'2.0'`/`method`, empty batch), `-32601` unknown method,
`-32602` bad params (`tools/call` without a string `name`, `arguments` not an
object, unknown tool name), `-32603` for tool-side exceptions that escape.
Tool *failures* (action failed, button not found) are `isError:true`
results, not JSON-RPC errors — the transport succeeded.

**Tools.** Each maps onto existing machinery; nothing new is invented.

- `deck_info` — `{version, profile:{id,name}, scenes, buttons,
  active_scene, profiles}` counted from the *active* profile file. Active
  profile = `activeProfileId` in `DATA_DIR/user_settings.json`; fallback is
  a profile containing an `isActive` scene, else the first `*.json` in
  `Config.PROFILES_DIR`.
- `list_scenes` — `[{name, page_count, pages, active}]` for the active
  profile (that is what `navigate_scene` targets).
- `list_buttons` `{scene?}` — `[{id, label, scene, page, action:{type}}]`;
  scans scene pages, legacy top-level pages and `dockedButtons`.
- `press_button` `{button_id}` or `{scene, button}` — resolves through the
  profile JSONs (active profile first; scene + label matched
  case-insensitively) then `executor.execute_action(button.action)`.
  Disabled buttons refuse with `isError`.
- `run_action` `{action:{type,config}}` — straight to the executor.
- `switch_scene` `{scene}` — emits `navigate_scene {scene}`; the tool result
  says the switch is asynchronous (the panel's frontend store owns it).
- `show_notification` `{title, message}` — emits `panel_notification
  {source:'mcp', title≤80, message≤300, ts}`.
- `get_volume` — `actions.cross_platform_action.read_output_volume()` →
  `{value, muted}`.
- `set_volume` `{value:0-100}` — there is **no module-level setter** in
  `cross_platform_action`; the write path is `CrossPlatformAction`
  `action:'volume_set'` (COM worker on Windows, osascript/amixer elsewhere,
  nircmd fallback). The tool instantiates that action directly, so it works
  even before the executor is injected.
- `get_now_playing` — `try: from services import now_playing`; missing
  module → `isError` "unavailable". Present: `now_playing.latest()` payload,
  or `{playing:false}` when `latest()` is absent/returns `None`.
- `get_agent_states` — `integrations.agent_state.snapshot()`.

**Server version.** `SERVER_VERSION = '2.1.0'` mirrors the string app.py's
`/api/health` reports; noted for the orchestrator to centralize if wanted.

## Implementation Plan

1. `backend/routes/mcp.py` — blueprint, JSON-RPC dispatch, tools above.
2. `backend/tests/test_mcp.py` — bare Flask app + `mcp_bp` (the real app.py
   does not register it yet, and must not be imported): lifecycle
   (initialize/tools/list/tools/call/ping), batch, every error code,
   `press_button` against a `tmp_path` profiles dir, localhost guard,
   missing-executor `isError`.
3. `docs/mcp.md` — Claude Desktop / Cursor config pointing at
   `http://127.0.0.1:5000/api/mcp`, with the no-SSE/stdio limitation and the
   localhost-only boundary documented.

## Design Proof

- Claude Desktop / Cursor `initialize` → `notifications/initialized` →
  `tools/list` → `tools/call` works over plain POST.
- A batch `[ping, ping]` returns two results; a batch of notifications
  returns HTTP 202.
- Garbage body → `-32700`; `{"jsonrpc":"2.0","id":1}` → `-32600`; unknown
  method → `-32601`; `tools/call` without `name` → `-32602`.
- `press_button` on a seeded temp profile executes the button's action via
  the injected fake executor; unknown button → `isError`.
- Remote `remote_addr` without token → 403 (or 401 when REQUIRE_AUTH);
  valid Bearer + REQUIRE_AUTH → passes.

## Implementation Results

Implemented and verified — `pytest tests/test_mcp.py`: 40 green; full
backend suite: 1056 green.

**Built**

- `backend/routes/mcp.py` — blueprint `mcp_bp`, one route
  `/api/mcp` (GET → 405 JSON + `Allow: POST`; POST → JSON-RPC 2.0).
  Single messages and batch arrays; all-notification inputs answer `202`
  empty. Errors `-32700/-32600/-32601/-32602/-32603` per spec; unknown tool
  names are `-32602`, tool-side failures are `isError:true` results with
  `structuredContent`.
- Injection seams `set_emitter(fn)` / `set_executor(executor)` matching the
  contract; `_run_action` accepts either an object with
  `.execute_action(action_data)` (the real `ActionExecutor`) or a plain
  callable, and normalizes `ActionResult.to_dict()`/dict results.
- All eleven tools: `deck_info`, `list_scenes`, `list_buttons(scene?)`,
  `press_button(button_id | scene+button | button)`, `run_action`,
  `switch_scene`, `show_notification`, `get_volume`, `set_volume`,
  `get_now_playing`, `get_agent_states`.
- `backend/tests/test_mcp.py` — bare Flask app + `mcp_bp` (never imports
  app.py), tmp-path profiles, fake executor/emitter.
- `docs/mcp.md` — endpoint, Cursor `url` config, Claude Desktop via
  `mcp-remote`, curl examples, tool table, limits.

**Verified live** (real `app` + registered blueprint, test client):

- `initialize` → `{protocolVersion 2025-06-18, capabilities.tools
  {listChanged:false}, serverInfo {vdock 2.1.0}}`.
- `deck_info` read the real `My VDock` profile: 4 scenes, 31 buttons,
  `active_scene: 'Media'`.
- `switch_scene` emitted `navigate_scene {'scene':'Media'}`;
  `show_notification` emitted `panel_notification {source:'mcp',…}`.
- `get_volume` rode the real COM audio worker: `{value: 18, muted: false}`.

**Deviations**

- `set_volume` uses `CrossPlatformAction({'action':'volume_set'})` directly
  rather than the executor: there is no module-level setter in
  `cross_platform_action` (only `read_output_volume`), and the direct
  instantiation keeps the tool working before the executor is wired.
- `get_now_playing`: the spec'd contract was `now_playing.latest()`; W1
  actually shipped `snapshot()` + `latest_track()` + `available()`. The tool
  accepts `latest()`/`snapshot()`/`latest_track()` (first callable wins) and
  folds in `available()` when present — no change needed from W1.
- Tool-argument validation errors surface as `isError` results, not
  `-32602` — `-32602` is reserved for the JSON-RPC envelope (missing/invalid
  `params.name`, non-object `arguments`, unknown tool).

**Notes for the orchestrator**

- app.py wiring needed: `from routes.mcp import mcp_bp` +
  `register_blueprint(mcp_bp)` + `set_emitter(lambda e,p: socketio.emit(e,p))`
  + `set_executor(action_executor)`; `limiter.exempt(mcp_bp)` — MCP clients
  may poll.
- `SERVER_VERSION='2.1.0'` in mcp.py mirrors `/api/health`; consider a
  shared constant later.

### Follow-up — Settings configurability pass

Added an enable switch: `mcpEnabled` (default on) lives in the regular
`user_settings.json` the panel syncs, read per request by `_mcp_enabled()`
in `routes/mcp.py`. When off, `POST /api/mcp` answers 503
`{success:false, error:"MCP server is disabled (Settings → Integrations)"}`
after the localhost/Bearer gate; GET keeps its 405. The Settings panel
(Settings → Integrations → MCP server) gained the switch and hides the
endpoint/tools rows while disabled. Tests cover the 503 and default-on.
