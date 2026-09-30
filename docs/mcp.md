# MCP Server — controlling VDock from an agent client

VDock exposes a [Model Context Protocol](https://modelcontextprotocol.io)
endpoint so MCP-capable clients (Claude Desktop, Cursor, custom agents) can
inspect and drive the deck: press buttons, run actions, switch scenes, push
panel notifications, read volume / now-playing / agent state.

## Endpoint

```
POST http://127.0.0.1:5000/api/mcp
Content-Type: application/json
```

One endpoint, JSON-RPC 2.0 over HTTP POST — the request/response subset of
MCP's *Streamable HTTP* transport. Single messages and batch arrays are both
accepted. A `GET` probe answers `405 {"error": "POST only"}`.

**Limitations, honestly:**

- **No SSE stream.** `GET` is not a listening channel — the server cannot
  push unsolicited `notifications/*` to the client. Everything a tool client
  needs (`initialize`, `tools/list`, `tools/call`, `ping`) works.
- **No stdio mode.** The endpoint is HTTP only; stdio-only clients need a
  bridge such as `mcp-remote` (below).
- **Localhost only.** The endpoint is a machine-local control surface, like
  the agent-hooks API. When `REQUIRE_AUTH` is enabled, requests from other
  machines may authenticate with `Authorization: Bearer <jwt>` (a token from
  `POST /api/auth/login`); without auth the connection must be local.

## Client configuration

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "vdock": {
      "url": "http://127.0.0.1:5000/api/mcp"
    }
  }
}
```

### Claude Desktop

Claude Desktop's config file (`claude_desktop_config.json`) launches stdio
servers; bridge it to VDock's HTTP endpoint with `mcp-remote`:

```json
{
  "mcpServers": {
    "vdock": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://127.0.0.1:5000/api/mcp"]
    }
  }
}
```

### Raw JSON-RPC (curl)

```bash
curl -s http://127.0.0.1:5000/api/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize"}'
```

```bash
curl -s http://127.0.0.1:5000/api/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call",
       "params":{"name":"press_button","arguments":{"button":"Mute"}}}'
```

## Methods

| Method | Result |
|---|---|
| `initialize` | `{protocolVersion: '2025-06-18', capabilities: {tools: {listChanged: false}}, serverInfo: {name: 'vdock', version: '<ver>'}}` |
| `ping` | `{}` |
| `notifications/*` | ignored (or `null` when sent with an id) |
| `tools/list` | `{tools: [{name, description, inputSchema}]}` |
| `tools/call` `{name, arguments?}` | `{content: [{type: 'text', text}], structuredContent, isError}` |

JSON-RPC errors: `-32700` parse, `-32600` invalid request, `-32601` unknown
method, `-32602` invalid params (including unknown tool names), `-32603`
internal. Tool-level failures (button not found, executor unwired, hardware
unavailable) come back as `isError: true` results instead.

## Tools

| Tool | Arguments | What it does |
|---|---|---|
| `deck_info` | — | Backend version, active profile, scene/button counts |
| `list_scenes` | — | Scenes in the active profile (`name`, `pages`, `active`) |
| `list_buttons` | `scene?` | Buttons (`id`, `label`, `action.type`), optionally one scene |
| `press_button` | `button_id` *or* `button` (+`scene?`) | Executes the button's configured action |
| `run_action` | `action:{type,config}` | Runs any deck action directly |
| `switch_scene` | `scene` | Emits `navigate_scene`; the panel switches asynchronously |
| `show_notification` | `title`, `message` | Emits `panel_notification` (toast + bell history) |
| `get_volume` | — | Output volume 0-100 + mute |
| `set_volume` | `value` 0-100 | Sets output volume |
| `get_now_playing` | — | Last media snapshot (title/artist/playing), or `playing:false` |
| `get_agent_states` | — | Per-agent live state (`ready`/`working`/`permission`) |

### Typical session

```
→ {"jsonrpc":"2.0","id":1,"method":"initialize"}
→ {"jsonrpc":"2.0","method":"notifications/initialized"}
→ {"jsonrpc":"2.0","id":2,"method":"tools/list"}
→ {"jsonrpc":"2.0","id":3,"method":"tools/call",
   "params":{"name":"press_button","arguments":{"scene":"Media","button":"Mute"}}}
```

`press_button` accepts either `button_id` (exact) or `button` (label or id,
case-insensitive) optionally scoped by `scene`. Use `list_scenes` /
`list_buttons` to discover what's pressable — ids are stable per profile.
